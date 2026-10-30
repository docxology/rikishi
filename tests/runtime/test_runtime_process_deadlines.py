from __future__ import annotations

import errno
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import FrameType
from typing import BinaryIO

import pytest

from rikishi.runtime_process import run_bounded


def _denied_runner(directory: Path) -> None:
    processes: list[subprocess.Popen[bytes]] = []
    streams: list[BinaryIO] = []
    failures: list[float] = []
    started = time.monotonic()

    def profile(frame: FrameType, event: str, value: object) -> None:
        if (event == "call" and frame.f_code is subprocess.Popen.wait.__code__
                and frame.f_back is not None
                and frame.f_back.f_code is run_bounded.__code__ and not processes):
            process = frame.f_locals["self"]
            processes.append(process)
            streams.extend(frame.f_back.f_locals[name] for name in ("out", "err"))
            (directory / "leader.json").write_text(json.dumps({"pid": process.pid}))
        if event == "c_exception" and value is os.killpg:
            failures.append(time.monotonic() - started)

    previous = sys.getprofile()
    sys.setprofile(profile)
    try:
        try:
            run_bounded(
                [sys.executable, "-c", ("import sys,time; print('out',flush=True); "
                 "print('err',file=sys.stderr,flush=True); time.sleep(20)")],
                cwd=directory, stdout=directory / "out", stderr=directory / "err", timeout=0.05,
            )
        except PermissionError as error:
            process = processes[0]
            result = {
                "exception": type(error).__name__, "errno": error.errno,
                "notes": getattr(error, "__notes__", []), "pid": process.pid,
                "elapsed_seconds": time.monotonic() - started,
                "alive_at_delivery": process.poll() is None,
                "streams_closed": [stream.closed for stream in streams],
                "signal_failure_seconds": failures,
            }
            pending = directory / "delivery.pending"
            pending.write_text(json.dumps(result))
            pending.rename(directory / "delivery.json")
        else:
            raise AssertionError("Denied cleanup must not return a ProcessResult")
    finally:
        sys.setprofile(previous)
    assert sys.stdin.readline() == "reap\n"
    returncode = processes[0].wait(timeout=5)
    (directory / "reaped.json").write_text(json.dumps({"returncode": returncode}))


@pytest.mark.integration
def test_denied_signal_delivers_error_before_child_exit(tmp_path: Path) -> None:
    with (tmp_path / "observer.stdout").open("xb") as out, (
        tmp_path / "observer.stderr"
    ).open("xb") as err:
        observer = subprocess.Popen(
            ["sandbox-exec", "-p", "(version 1) (allow default) (deny signal)",
             sys.executable, "-B", "-W", "default::ResourceWarning", __file__, str(tmp_path)],
            stdin=subprocess.PIPE, stdout=out, stderr=err,
        )
        try:
            deadline = time.monotonic() + 8
            while not (tmp_path / "delivery.json").exists():
                assert observer.poll() is None, (tmp_path / "observer.stderr").read_text()
                assert time.monotonic() < deadline, "cleanup failure exceeded delivery deadline"
                time.sleep(0.01)
            delivery = json.loads((tmp_path / "delivery.json").read_text())
            assert delivery["exception"] == "PermissionError" and delivery["errno"] == errno.EPERM
            assert delivery["elapsed_seconds"] < 5, delivery
            assert delivery["alive_at_delivery"], delivery
            assert any(str(delivery["pid"]) in note for note in delivery["notes"]), delivery
            assert delivery["streams_closed"] == [True, True], delivery
            assert len(delivery["signal_failure_seconds"]) == 1, delivery
            assert delivery["signal_failure_seconds"][0] <= delivery["elapsed_seconds"]
            state = subprocess.run(
                ["ps", "-o", "stat=", "-p", str(delivery["pid"])],
                capture_output=True, text=True, check=True, timeout=5,
            ).stdout.strip()
            assert state and not state.startswith("Z"), state
            deadline = time.monotonic() + 5
            while ((tmp_path / "out").read_text() != "out\n"
                   or (tmp_path / "err").read_text() != "err\n"):
                assert time.monotonic() < deadline, "live child did not write its output"
                time.sleep(0.01)
        finally:
            leader = tmp_path / "leader.json"
            if leader.exists():
                pid = json.loads(leader.read_text())["pid"]
                try:
                    os.killpg(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if observer.stdin is not None:
                observer.stdin.write(b"reap\n")
                observer.stdin.close()
            try:
                observer.wait(timeout=5)
            except subprocess.TimeoutExpired:
                observer.kill()
                observer.wait(timeout=5)
                raise
        assert observer.returncode == 0, (tmp_path / "observer.stderr").read_text()
    assert json.loads((tmp_path / "reaped.json").read_text())["returncode"] == -signal.SIGKILL
    assert (tmp_path / "out").read_text() == "out\n"
    assert (tmp_path / "err").read_text() == "err\n"


@pytest.mark.parametrize("outcome", ["exit", "timeout", "launch-error"])
def test_output_descriptors_close_after_real_process_outcome(tmp_path: Path, outcome: str) -> None:
    streams: list[BinaryIO] = []
    descriptors: list[int] = []

    def profile(frame: FrameType, event: str, value: object) -> None:
        if (event == "call" and frame.f_code is subprocess.Popen.__init__.__code__
                and frame.f_back is not None and frame.f_back.f_code is run_bounded.__code__):
            streams.extend(frame.f_locals[name] for name in ("stdout", "stderr"))
            descriptors.extend(stream.fileno() for stream in streams)

    command = [sys.executable, "-c", ("import sys; print('out'); "
               "print('err',file=sys.stderr); sys.exit(17)")]
    if outcome == "timeout":
        command = [sys.executable, "-c", "import time; time.sleep(20)"]
    elif outcome == "launch-error":
        command = [str(tmp_path / "absent-executable")]
    previous = sys.getprofile()
    sys.setprofile(profile)
    try:
        if outcome == "launch-error":
            with pytest.raises(FileNotFoundError):
                run_bounded(command, cwd=tmp_path, stdout=tmp_path / "out",
                            stderr=tmp_path / "err", timeout=0.05)
        else:
            result = run_bounded(command, cwd=tmp_path, stdout=tmp_path / "out",
                                 stderr=tmp_path / "err", timeout=0.05 if outcome == "timeout" else 5)
            assert result.timed_out == (outcome == "timeout")
            assert result.returncode == (-signal.SIGKILL if outcome == "timeout" else 17)
    finally:
        sys.setprofile(previous)
    assert len(streams) == 2 and all(stream.closed for stream in streams)
    for descriptor in descriptors:
        with pytest.raises(OSError) as error:
            os.fstat(descriptor)
        assert error.value.errno == errno.EBADF


if __name__ == "__main__":
    _denied_runner(Path(sys.argv[1]))
