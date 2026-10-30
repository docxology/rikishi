from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile

from rikishi.inference_models import InferenceReport
from rikishi.runtime_artifacts import (
    ProverKind,
    checked_source_path,
    load_capture,
    read_regular,
    verified_bytes,
)


def report_path(root: Path, relative: str) -> Path:
    selected = Path(relative)
    if selected.is_absolute() or ".." in selected.parts or not relative.strip():
        raise ValueError("report must be a nonempty repository-relative path without parent steps")
    root = root.resolve(strict=True)
    if not (root / selected).exists() and not (root / selected).is_symlink():
        raise FileNotFoundError(relative)
    path = checked_source_path(root / selected)
    if not path.is_relative_to(root):
        raise ValueError("report escapes the repository")
    return path


def _report(root: Path, relative: str, digest: str) -> InferenceReport:
    from rikishi.inference_replay import validate_inference_report

    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("sha256 must contain exactly 64 lowercase hexadecimal characters")
    return validate_inference_report(report_path(root, relative), trusted_report_sha256=digest)


def inspect_report(root: Path, relative: str, digest: str) -> dict[str, object]:
    return _report(root, relative, digest).model_dump(mode="json")


@dataclass(frozen=True, slots=True)
class CaseSelection:
    report: str
    sha256: str
    case_id: str
    prover: ProverKind


def inspect_case(root: Path, selection: CaseSelection) -> dict[str, object]:
    report = _report(root, selection.report, selection.sha256)
    run = next((item for item in report.cases
                if item.id == selection.case_id and item.prover == selection.prover), None)
    if run is None:
        raise KeyError("Inference case not found in the verified report")
    path = report_path(root, selection.report).parent / run.capture
    capture = load_capture(path, run.invocation_id)
    return {"case": run.model_dump(mode="json"), "command": capture.command,
            "problem": verified_bytes(capture.problem, path.parent).decode("utf-8"),
            "stdout": verified_bytes(capture.stdout, path.parent).decode("utf-8"),
            "stderr": verified_bytes(capture.stderr, path.parent).decode("utf-8"),
            "scope": "Exact captured problem and native output; proof steps are not independently checked."}


def published_report(root: Path) -> dict[str, object]:
    descriptor = root / "output/inference/published.json"
    if not descriptor.exists() and not descriptor.is_symlink():
        raise FileNotFoundError(descriptor)
    payload = json.loads(read_regular(checked_source_path(descriptor)))
    if (not isinstance(payload, dict) or set(payload) != {"report", "sha256"}
            or not isinstance(payload["report"], str) or not isinstance(payload["sha256"], str)):
        raise ValueError("published inference descriptor must contain report and sha256 strings")
    return {"descriptor": payload, "report": inspect_report(root, payload["report"], payload["sha256"]),
            "authority": "Replay against the locally published digest; independently retain the digest for transfer verification."}


def publish_report(root: Path, relative: str, digest: str) -> dict[str, str]:
    _report(root, relative, digest)
    folder = root.resolve(strict=True)
    for part in ("output", "inference"):
        folder = folder / part
        if folder.exists() or folder.is_symlink():
            checked_source_path(folder)
        else:
            folder.mkdir()
        if not folder.is_dir():
            raise ValueError("Inference publication parent must be a directory")
    descriptor = {"report": relative, "sha256": digest}
    data = (json.dumps(descriptor, indent=2) + "\n").encode()
    target = folder / "published.json"
    if target.exists() or target.is_symlink():
        previous = read_regular(checked_source_path(target))
        if previous == data:
            return descriptor
        with (folder / f"published-before-{time.time_ns()}.json").open("xb") as stream:
            stream.write(previous)
    if sha256(read_regular(report_path(root, relative))).hexdigest() != digest:
        raise ValueError("Inference report changed before publication")
    with NamedTemporaryFile(prefix=".inference-publication-", dir=folder, delete=False) as stream:
        stream.write(data)
        temporary = Path(stream.name)
    os.replace(temporary, target)
    return descriptor
