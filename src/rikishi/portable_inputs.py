"""Acquire pinned public study inputs; never produce native experiment observations."""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import stat
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from http.client import HTTPException
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from typing import Final, Literal
from urllib.error import URLError
from urllib.request import Request, urlopen

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError

from rikishi import __version__
from rikishi.competency import Study, load_study
from rikishi.sumo_demonstrations import (
    FrozenSource,
    SumoReport,
    _derive,
    validate_sumo_report,
)

_LIMIT: Final = 8 * 1024 * 1024
_FILES: Final = ("Merge.kif", "workbook.xlsx", "source-report.json", "receipt.json")


class PortableInputsError(ValueError):
    """An actionable acquisition or verification failure with a stable error code."""

    def __init__(self, code: str, target: str, detail: str) -> None:
        self.code = code
        self.target = target
        self.detail = detail
        super().__init__(f"{code}: {target}: {detail}")


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True, allow_inf_nan=False)


class SourceReceipt(_Strict):
    filename: str
    source_url: str
    request_url: str
    final_url: str
    status: Literal[200]
    bytes: int = Field(gt=0, le=_LIMIT)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class AcquisitionReceipt(_Strict):
    schema_version: Literal[1]
    scope: Literal["pinned-public-source-derivation-only"]
    study_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    acquired_at: AwareDatetime
    acquisition_location: str = Field(min_length=1)
    merge: SourceReceipt
    workbook: SourceReceipt
    source_report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class PortableInputs:
    directory: Path
    source_report: SumoReport
    source_report_path: Path
    workbook_bytes: bytes
    workbook_path: Path
    merge_bytes: bytes
    merge_path: Path
    receipt: AcquisitionReceipt
    receipt_path: Path


def _request_url(study: Study) -> str:
    """Map the packaged GitHub blob identity to its exact immutable raw URL."""
    prefix = "https://github.com/ontologyportal/sumo/blob/"
    suffix = f"{study.sumo_commit}/Merge.kif"
    if study.sumo_url != prefix + suffix:
        raise PortableInputsError("authority", study.sumo_url, "Unexpected packaged SUMO URL")
    return "https://raw.githubusercontent.com/ontologyportal/sumo/" + suffix


def _verify(raw: bytes, digest: str, target: str) -> None:
    if sha256(raw).hexdigest() != digest:
        raise PortableInputsError("digest", target, "Complete-byte SHA-256 differs from study pin")


def _fetch(url: str, digest: str, timeout: float, *, limit: int = _LIMIT) -> tuple[bytes, str]:
    """Bound each socket operation and the transfer loop; verify complete bytes."""
    deadline = monotonic() + timeout
    request = Request(url, headers={"Accept-Encoding": "identity", "User-Agent": f"rikishi/{__version__}"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise PortableInputsError("http", url, f"Expected HTTP 200, got {response.status}")
            length = response.headers.get("Content-Length")
            expected = int(length) if length is not None else None
            if expected is not None and (expected < 0 or expected > limit):
                raise PortableInputsError("size", url, f"Content-Length exceeds {limit} bytes")
            chunks: list[bytes] = []
            size = 0
            while True:
                if monotonic() >= deadline:
                    raise PortableInputsError("timeout", url, "Transfer deadline exceeded")
                chunk = response.read1(min(64 * 1024, limit + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > limit:
                    raise PortableInputsError("size", url, f"Transfer exceeds {limit} bytes")
            if expected is not None and size != expected:
                raise PortableInputsError("partial", url, f"Received {size} of {expected} bytes")
            raw = b"".join(chunks)
            _verify(raw, digest, url)
            return raw, response.geturl()
    except PortableInputsError:
        raise
    except (OSError, URLError, HTTPException, ValueError) as error:
        raise PortableInputsError("transfer", url, str(error)) from error


def _read(path: Path, limit: int = _LIMIT) -> bytes:
    """Reject symlinks/nonregular files and bound reads even if a file grows."""
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise PortableInputsError("file", str(path), "Expected a bounded regular file")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise PortableInputsError("size", str(path), "File grew past read limit")
    return raw


def _report(merge: bytes, study: Study) -> SumoReport:
    """Keep logical study identity distinct from downloaded location and Git audit."""
    return validate_sumo_report(_derive(FrozenSource(
        path=study.sumo_path, ontology_path="Merge.kif", commit=study.sumo_commit,
        clean=None, text=merge.decode("utf-8"), sha256=study.sumo_sha256)))


def _study_digest(study: Study) -> str:
    return sha256(study.model_dump_json().encode()).hexdigest()


def load_portable_inputs(directory: Path) -> PortableInputs:
    """Reverify an explicit completed bundle offline, without historical fallbacks."""
    study = load_study()
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise PortableInputsError("directory", str(directory), "Run prepare_portable_inputs first")
        if {p.name for p in directory.iterdir()} != set(_FILES):
            raise PortableInputsError("inventory", str(directory), "Expected exactly four bundle files")
        raw_receipt = _read(directory / "receipt.json", 64 * 1024)
        receipt = AcquisitionReceipt.model_validate_json(raw_receipt)
        if receipt.study_sha256 != _study_digest(study):
            raise PortableInputsError("authority", str(directory), "Receipt differs from packaged study")
        contents: list[bytes] = []
        for entry, name, digest, source_url, request_url in (
            (receipt.merge, "Merge.kif", study.sumo_sha256, study.sumo_url, _request_url(study)),
            (receipt.workbook, "workbook.xlsx", study.workbook_sha256,
             study.workbook_url, study.workbook_url),
        ):
            if (entry.filename, entry.sha256, entry.source_url, entry.request_url) != (
                name, digest, source_url, request_url
            ) or entry.final_url != request_url:
                raise PortableInputsError("identity", str(directory), "Receipt source identity differs")
            raw = _read(directory / name)
            _verify(raw, digest, str(directory / name))
            if len(raw) != entry.bytes:
                raise PortableInputsError("size", str(directory / name), "Receipt byte count differs")
            contents.append(raw)
        merge, workbook = contents
        report_bytes = _read(directory / "source-report.json")
        _verify(report_bytes, receipt.source_report_sha256, str(directory / "source-report.json"))
        report = validate_sumo_report(SumoReport.model_validate_json(report_bytes))
        if report != _report(merge, study):
            raise PortableInputsError("report", str(directory), "Report differs from acquired source")
        return PortableInputs(directory=directory, source_report=report,
                              source_report_path=directory / "source-report.json",
                              workbook_bytes=workbook, workbook_path=directory / "workbook.xlsx",
                              merge_bytes=merge, merge_path=directory / "Merge.kif",
                              receipt=receipt, receipt_path=directory / "receipt.json")
    except PortableInputsError:
        raise
    except (OSError, ValueError, ValidationError) as error:
        raise PortableInputsError("bundle", str(directory), str(error)) from error


def _publish(output: Path, payloads: tuple[bytes, bytes, bytes, bytes]) -> None:
    """Commit receipt last using exclusive links; clean only our files on failure."""
    with TemporaryDirectory(prefix=f".{output.name}-", dir=output.parent) as temporary:
        staging = Path(temporary)
        for name, raw in zip(_FILES, payloads, strict=True):
            (staging / name).write_bytes(raw)
        reservation: os.stat_result | None = None
        linked: list[Path] = []
        complete = False
        previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
        try:
            try:
                output.mkdir()
                reservation = output.stat()
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            for name in _FILES:
                target = output / name
                linked.append(target)
                os.link(staging / name, target)
            complete = True
        finally:
            if (not complete and reservation is not None and output.exists()
                    and os.path.samestat(output.lstat(), reservation)):
                for target in reversed(linked):
                    if target.exists() and os.path.samestat(
                        target.lstat(), (staging / target.name).stat()
                    ):
                        target.unlink()
                if not any(output.iterdir()):
                    output.rmdir()


def prepare_portable_inputs(output: Path, *, reuse: bool = False,
                            timeout: float = 30) -> PortableInputs:
    """Acquire only packaged public pins into a new bundle, or explicitly reverify it."""
    if not math.isfinite(timeout) or timeout <= 0 or timeout > 300:
        raise PortableInputsError("timeout", str(output), "Use a finite timeout in (0, 300] seconds")
    if output.exists() or output.is_symlink():
        if reuse:
            return load_portable_inputs(output)
        raise PortableInputsError("occupied", str(output), "Choose a new output or pass --reuse")
    if not output.parent.is_dir():
        raise PortableInputsError("parent", str(output.parent), "Create the parent directory first")
    study = load_study()
    try:
        merge_url = _request_url(study)
        merge, merge_final = _fetch(merge_url, study.sumo_sha256, timeout)
        workbook, workbook_final = _fetch(study.workbook_url, study.workbook_sha256, timeout)
        if merge_final != merge_url or workbook_final != study.workbook_url:
            raise PortableInputsError("identity", str(output), "Unexpected redirected source URL")
        report = _report(merge, study)
        report_bytes = report.model_dump_json(indent=2).encode()
        receipt = AcquisitionReceipt(
            schema_version=1, scope="pinned-public-source-derivation-only",
            study_sha256=_study_digest(study), acquired_at=datetime.now(UTC),
            acquisition_location=str(output.resolve()),
            merge=SourceReceipt(filename="Merge.kif", source_url=study.sumo_url,
                                request_url=merge_url, final_url=merge_final, status=200,
                                bytes=len(merge), sha256=study.sumo_sha256),
            workbook=SourceReceipt(filename="workbook.xlsx", source_url=study.workbook_url,
                                   request_url=study.workbook_url, final_url=workbook_final,
                                   status=200, bytes=len(workbook), sha256=study.workbook_sha256),
            source_report_sha256=sha256(report_bytes).hexdigest())
        _publish(output, (merge, workbook, report_bytes, receipt.model_dump_json(indent=2).encode()))
        return load_portable_inputs(output)
    except PortableInputsError:
        raise
    except (OSError, ValueError) as error:
        raise PortableInputsError("acquisition", str(output), str(error)) from error


def main(argv: Sequence[str] | None = None) -> int:
    """Thin CLI argument and error adapter for the same verified public API."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args(argv)
    try:
        result = prepare_portable_inputs(args.output, reuse=args.reuse, timeout=args.timeout)
    except PortableInputsError as error:
        print(json.dumps({"status": "error", "code": error.code, "detail": str(error)}))
        return 1
    print(json.dumps({"status": "verified", "receipt": str(result.receipt_path),
                      "merge_sha256": result.receipt.merge.sha256,
                      "workbook_sha256": result.receipt.workbook.sha256}))
    return 0
