import json
import shutil
import signal
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Literal, assert_never

import pytest

from rikishi.competency import load_study
from rikishi.portable_inputs import (
    PortableInputs,
    PortableInputsError,
    _fetch,
    _publish,
    load_portable_inputs,
    main,
    prepare_portable_inputs,
)


@contextmanager
def serving(body: bytes, *, status: int = 200, length: str | None = None) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(status)
            if length is not None:
                self.send_header("Content-Length", length)
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/input"
        finally:
            server.shutdown()
            thread.join()


def test_transfer_preserves_real_source_bytes(portable_inputs: PortableInputs) -> None:
    body = portable_inputs.merge_bytes
    with serving(body, length=str(len(body))) as url:
        observed, final_url = _fetch(url, load_study().sumo_sha256, 3)
    assert observed == body
    assert final_url == url


def test_new_public_acquisition_verifies_packaged_sources(tmp_path: Path) -> None:
    result = prepare_portable_inputs(tmp_path / "public", reuse=True, timeout=30)
    assert result.merge_bytes == result.source_report.source.text.encode()
    assert result.receipt.merge.sha256 == load_study().sumo_sha256
    assert sha256(result.workbook_bytes).hexdigest() == load_study().workbook_sha256
    assert result.receipt_path.is_file()


@pytest.mark.parametrize(("status", "body", "length", "limit", "code"), [
    (404, b"missing", None, 8, "transfer"),
    (204, b"", None, 8, "http"),
    (200, b"large", "500", 8, "size"),
    (200, b"123456789", None, 8, "size"),
    (200, b"wrong", None, 8, "digest"),
    (200, b"cut", "8", 8, "partial"),
    (200, b"", "8", 8, "partial"),
    (200, b"ok", "invalid", 8, "transfer"),
    (200, b"ok", "-1", 8, "size"),
])
def test_transfer_rejects_wire_failure(status: int, body: bytes, length: str | None,
                                     limit: int, code: str) -> None:
    with (serving(body, status=status, length=length) as url,
          pytest.raises(PortableInputsError) as caught):
        _fetch(url, sha256(b"ok").hexdigest(), 3, limit=limit)
    assert caught.value.code == code


def test_transfer_rejects_elapsed_deadline() -> None:
    with serving(b"ok") as url, pytest.raises(PortableInputsError) as caught:
        _fetch(url, sha256(b"ok").hexdigest(), 1e-12)
    assert caught.value.code in {"timeout", "transfer"}


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), 301])
def test_invalid_timeout_makes_no_files(tmp_path: Path, timeout: float) -> None:
    with pytest.raises(PortableInputsError) as caught:
        prepare_portable_inputs(tmp_path / "new", timeout=timeout)
    assert caught.value.code == "timeout"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("kind", ["file", "directory", "symlink", "dangling"])
def test_occupied_output_is_preserved(
    tmp_path: Path, kind: Literal["file", "directory", "symlink", "dangling"]
) -> None:
    output = tmp_path / "occupied"
    match kind:
        case "file":
            output.write_bytes(b"preserve")
        case "directory":
            output.mkdir()
        case "symlink" | "dangling":
            target = tmp_path / "target"
            if kind == "symlink":
                target.mkdir()
            output.symlink_to(target)
        case unreachable:
            assert_never(unreachable)
    before = sorted((p.name, p.lstat().st_mode) for p in tmp_path.iterdir())
    with pytest.raises(PortableInputsError) as caught:
        prepare_portable_inputs(output)
    assert caught.value.code == "occupied"
    assert sorted((p.name, p.lstat().st_mode) for p in tmp_path.iterdir()) == before
    if kind == "file":
        assert output.read_bytes() == b"preserve"


def test_absent_parent_fails_without_creating_directories(tmp_path: Path) -> None:
    with pytest.raises(PortableInputsError) as caught:
        prepare_portable_inputs(tmp_path / "absent" / "new")
    assert caught.value.code == "parent"
    assert list(tmp_path.iterdir()) == []


@pytest.fixture
def bundle(tmp_path: Path, portable_inputs: PortableInputs) -> Path:
    return Path(shutil.copytree(portable_inputs.directory, tmp_path / "bundle"))


def test_explicit_reuse_reverifies_relocated_bytes(bundle: Path) -> None:
    loaded = prepare_portable_inputs(bundle, reuse=True)
    assert loaded.directory == bundle
    assert loaded.source_report.source.path == load_study().sumo_path
    assert loaded.source_report.source.clean is None
    assert loaded.receipt.acquisition_location != str(bundle)
    assert sha256(loaded.workbook_bytes).hexdigest() == load_study().workbook_sha256


@pytest.mark.parametrize("name", ["Merge.kif", "workbook.xlsx", "source-report.json"])
def test_reuse_rejects_modified_bytes_without_repair(bundle: Path, name: str) -> None:
    target = bundle / name
    altered = target.read_bytes() + b"mutation"
    target.write_bytes(altered)
    with pytest.raises(PortableInputsError) as caught:
        prepare_portable_inputs(bundle, reuse=True)
    assert caught.value.code == "digest"
    assert target.read_bytes() == altered


@pytest.mark.parametrize("field", ["filename", "sha256", "source_url", "request_url", "final_url",
                                   "bytes", "status"])
@pytest.mark.parametrize("source", ["merge", "workbook"])
def test_reuse_rejects_forged_source_receipt(bundle: Path, source: str, field: str) -> None:
    path = bundle / "receipt.json"
    receipt = json.loads(path.read_bytes())
    receipt[source][field] = 201 if field in {"bytes", "status"} else "forged"
    path.write_text(json.dumps(receipt))
    with pytest.raises(PortableInputsError):
        load_portable_inputs(bundle)


@pytest.mark.parametrize("field", ["schema_version", "scope", "study_sha256", "acquired_at",
                                   "acquisition_location", "merge", "workbook",
                                   "source_report_sha256"])
def test_reuse_rejects_missing_receipt_identity(bundle: Path, field: str) -> None:
    path = bundle / "receipt.json"
    receipt = json.loads(path.read_bytes())
    del receipt[field]
    path.write_text(json.dumps(receipt))
    with pytest.raises(PortableInputsError) as caught:
        load_portable_inputs(bundle)
    assert caught.value.code == "bundle"


def test_reuse_rejects_coherently_rehashed_source(bundle: Path) -> None:
    source = bundle / "Merge.kif"
    source.write_bytes(source.read_bytes() + b"\n; changed source\n")
    path = bundle / "receipt.json"
    receipt = json.loads(path.read_bytes())
    receipt["merge"]["sha256"] = sha256(source.read_bytes()).hexdigest()
    receipt["merge"]["bytes"] = source.stat().st_size
    path.write_text(json.dumps(receipt))
    with pytest.raises(PortableInputsError) as caught:
        load_portable_inputs(bundle)
    assert caught.value.code == "identity"


def test_reuse_rejects_different_study_authority(bundle: Path) -> None:
    path = bundle / "receipt.json"
    receipt = json.loads(path.read_bytes())
    receipt["study_sha256"] = "a" * 64
    path.write_text(json.dumps(receipt))
    with pytest.raises(PortableInputsError) as caught:
        load_portable_inputs(bundle)
    assert caught.value.code == "authority"


def test_load_requires_explicit_existing_bundle(tmp_path: Path) -> None:
    with pytest.raises(PortableInputsError) as caught:
        load_portable_inputs(tmp_path / "missing")
    assert caught.value.code == "directory"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("field", ["path", "commit", "clean"])
def test_reuse_rejects_rehashed_report_identity(bundle: Path, field: str) -> None:
    report_path = bundle / "source-report.json"
    report = json.loads(report_path.read_bytes())
    report["source"][field] = {"path": "other/Merge.kif", "commit": "a" * 40,
                                "clean": True}[field]
    report_path.write_text(json.dumps(report))
    receipt_path = bundle / "receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["source_report_sha256"] = sha256(report_path.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(PortableInputsError) as caught:
        load_portable_inputs(bundle)
    assert caught.value.code == "report"


@pytest.mark.parametrize("kind", ["missing", "extra", "symlink", "oversize", "directory"])
def test_reuse_rejects_invalid_inventory(
    bundle: Path, kind: Literal["missing", "extra", "symlink", "oversize", "directory"]
) -> None:
    target = bundle / "workbook.xlsx"
    match kind:
        case "extra":
            (bundle / "unexpected").write_bytes(b"x")
        case "oversize":
            with target.open("wb") as stream:
                stream.truncate(8 * 1024 * 1024 + 1)
        case "missing" | "symlink" | "directory":
            target.rename(bundle.parent / "saved")
            match kind:
                case "symlink":
                    target.symlink_to(bundle.parent / "saved")
                case "directory":
                    target.mkdir()
                case "missing":
                    assert not target.exists()
                case unreachable:
                    assert_never(unreachable)
        case unreachable:
            assert_never(unreachable)
    with pytest.raises(PortableInputsError):
        load_portable_inputs(bundle)


def test_atomic_publication_uses_exclusive_destination(tmp_path: Path) -> None:
    output = tmp_path / "occupied"
    output.mkdir()
    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
    with pytest.raises(FileExistsError):
        _publish(output, (b"a", b"b", b"c", b"d"))
    assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == prior_mask
    assert list(output.iterdir()) == []
    assert list(tmp_path.iterdir()) == [output]


def test_write_failure_leaves_no_output_or_staging(tmp_path: Path) -> None:
    code = """
import resource
import signal
import sys
from pathlib import Path
from rikishi.portable_inputs import _publish
signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
# The one-byte failure applies to publication, not the interpreter's coverage exit hook.
original = resource.getrlimit(resource.RLIMIT_FSIZE)
resource.setrlimit(resource.RLIMIT_FSIZE, (1, original[1]))
try:
    assert resource.getrlimit(resource.RLIMIT_FSIZE)[0] == 1
    _publish(Path(sys.argv[1]), (b'a', b'bb', b'c', b'd'))
except OSError as error:
    print(type(error).__name__, error.errno)
    raise SystemExit(23)
finally:
    resource.setrlimit(resource.RLIMIT_FSIZE, original)
raise SystemExit(0)
"""
    completed = subprocess.run([sys.executable, "-c", code, str(tmp_path / "new")],
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 23, completed.stdout + completed.stderr
    assert "27" in completed.stdout
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("failure", ["collision", "replacement", "symlink", "interrupt",
                                   "interrupt_after_link", "interrupt_after_mkdir"])
def test_partial_publication_preserves_foreign_files(tmp_path: Path, failure: str) -> None:
    code = """
import os
import signal
import sys
from pathlib import Path
from rikishi.portable_inputs import _publish
output = Path(sys.argv[1])
mode = sys.argv[2]
armed = True
signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGUSR1})
initial_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
def coordinate(frame, event, argument):
    global armed
    after_link = mode == 'interrupt_after_link' and (output / 'Merge.kif').exists()
    after_mkdir = mode == 'interrupt_after_mkdir' and output.is_dir()
    before_next = (mode not in {'interrupt_after_link', 'interrupt_after_mkdir'}
                   and frame.f_locals.get('name') == 'workbook.xlsx' and output.is_dir())
    if (armed and event == 'line' and frame.f_code is _publish.__code__
            and (after_link or after_mkdir or before_next)):
        armed = False
        if mode in {'interrupt', 'interrupt_after_link', 'interrupt_after_mkdir'}:
            os.kill(os.getpid(), signal.SIGINT)
            return coordinate
        if mode in {'replacement', 'symlink'}:
            (output / 'Merge.kif').unlink()
            if mode == 'replacement':
                (output / 'Merge.kif').write_bytes(b'foreign replacement')
            else:
                (output / 'Merge.kif').symlink_to(output / 'workbook.xlsx')
        (output / 'workbook.xlsx').write_bytes(b'foreign collision')
    return coordinate
sys.settrace(coordinate)
try:
    try:
        _publish(output, (b'a', b'b', b'c', b'd'))
    except (FileExistsError, KeyboardInterrupt) as error:
        print(type(error).__name__)
    else:
        raise SystemExit(24)
finally:
    sys.settrace(None)
assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == initial_mask
"""
    output = tmp_path / "new"
    completed = subprocess.run([sys.executable, "-c", code, str(output), failure],
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    if failure in {"interrupt", "interrupt_after_link", "interrupt_after_mkdir"}:
        assert completed.stdout.strip() == "KeyboardInterrupt"
        assert list(tmp_path.iterdir()) == []
    else:
        assert completed.stdout.strip() == "FileExistsError"
        expected = {"workbook.xlsx": b"foreign collision"}
        if failure == "replacement":
            expected["Merge.kif"] = b"foreign replacement"
        if failure == "symlink":
            expected["Merge.kif"] = b"foreign collision"
            assert (output / "Merge.kif").is_symlink()
        assert {p.name: p.read_bytes() for p in output.iterdir()} == expected
        assert list(tmp_path.iterdir()) == [output]


def test_cli_adapter_reuses_verified_bundle(bundle: Path, capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["--output", str(bundle), "--reuse"])
    assert result == 0
    assert json.loads(capsys.readouterr().out)["status"] == "verified"


def test_cli_adapter_reports_occupied_bundle(bundle: Path, capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["--output", str(bundle)])
    assert result == 1
    assert json.loads(capsys.readouterr().out)["code"] == "occupied"
