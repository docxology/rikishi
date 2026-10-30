from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import FrameType

import pytest

from rikishi.runtime_process import run_bounded


def _state(pid: int) -> str:
    result = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)],
                            capture_output=True, text=True, check=False, timeout=5)
    assert result.returncode in {0, 1}, result.stderr
    return result.stdout.strip()


def _await_zombie(pid: int) -> None:
    deadline = time.monotonic() + 5
    while not _state(pid).startswith("Z"):
        assert time.monotonic() < deadline, f"child {pid} did not exit"
        time.sleep(0.005)


@contextmanager
def _after_failed_wait(action: Callable[[subprocess.Popen[bytes]], None]) -> Iterator[list[int]]:
    observed: list[int] = []

    def profile(frame: FrameType, event: str, value: object) -> None:
        if (event == "return" and frame.f_code is subprocess.Popen.wait.__code__
                and value is None and not observed and frame.f_back is not None
                and frame.f_back.f_code is run_bounded.__code__):
            process = frame.f_locals["self"]
            observed.append(process.pid)
            action(process)

    previous = sys.getprofile()
    sys.setprofile(profile)
    try:
        yield observed
    finally:
        sys.setprofile(previous)


@pytest.mark.parametrize("reap", [False, True])
def test_timeout_survives_real_child_exit_before_group_signal(tmp_path: Path, reap: bool) -> None:
    def exit_before_signal(process: subprocess.Popen[bytes]) -> None:
        _await_zombie(process.pid)
        if reap:
            assert process.poll() == 17

    code = "import sys,time; time.sleep(.03); print('completed',flush=True); sys.exit(17)"
    with _after_failed_wait(exit_before_signal) as observed:
        result = run_bounded([sys.executable, "-c", code], cwd=tmp_path,
                             stdout=tmp_path / "out", stderr=tmp_path / "err", timeout=0.001)

    assert len(observed) == 1
    assert result.timed_out
    assert result.returncode == 17
    assert (tmp_path / "out").read_text() == "completed\n"
    assert (tmp_path / "err").read_text() == ""
    assert _state(observed[0]) == ""


def test_timeout_kills_live_descendant_after_leader_exits(tmp_path: Path) -> None:
    def exit_before_signal(process: subprocess.Popen[bytes]) -> None:
        _await_zombie(process.pid)
        descendant = int((tmp_path / "out").read_text())
        assert _state(descendant) and not _state(descendant).startswith("Z")
        assert process.poll() == 17

    code = (
        "import subprocess,sys,time; "
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        "print(child.pid,flush=True); time.sleep(.03); sys.exit(17)"
    )
    try:
        with _after_failed_wait(exit_before_signal) as observed:
            result = run_bounded([sys.executable, "-c", code], cwd=tmp_path,
                                 stdout=tmp_path / "out", stderr=tmp_path / "err", timeout=0.001)
        assert len(observed) == 1
        assert result.timed_out
        assert result.returncode == 17
        descendant = int((tmp_path / "out").read_text())
        state = _state(descendant)
        assert not state or state.startswith("Z")
    finally:
        if (tmp_path / "out").exists() and (tmp_path / "out").read_text().strip():
            descendant = int((tmp_path / "out").read_text())
            if (state := _state(descendant)) and not state.startswith("Z"):
                os.kill(descendant, signal.SIGKILL)


def test_interrupt_survives_real_child_exit_before_cleanup(tmp_path: Path) -> None:
    code = "import os,signal; print('completed',flush=True); os.kill(os.getppid(),signal.SIGINT)"
    with pytest.raises(KeyboardInterrupt):
        run_bounded([sys.executable, "-c", code], cwd=tmp_path,
                    stdout=tmp_path / "out", stderr=tmp_path / "err", timeout=5)
    assert (tmp_path / "out").read_text() == "completed\n"


def test_interrupt_after_real_launch_cleans_up_before_reraising(tmp_path: Path) -> None:
    observed: list[subprocess.Popen[bytes]] = []

    def trace(frame: FrameType, event: str, value: object) -> Callable:
        if (event == "line" and frame.f_code is run_bounded.__code__
                and frame.f_locals.get("process") is not None and not observed):
            process = frame.f_locals["process"]
            observed.append(process)
            assert process.poll() is None
            os.kill(os.getpid(), signal.SIGINT)
        return trace

    previous = sys.gettrace()
    try:
        sys.settrace(trace)
        try:
            with pytest.raises(KeyboardInterrupt):
                run_bounded([sys.executable, "-c", "import time; time.sleep(20)"], cwd=tmp_path,
                            stdout=tmp_path / "out", stderr=tmp_path / "err", timeout=10)
        finally:
            sys.settrace(previous)
        assert len(observed) == 1
        assert observed[0].returncode == -signal.SIGKILL
        assert _state(observed[0].pid) == ""
    finally:
        for process in observed:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def test_interrupt_kills_real_descendant_before_reraising(tmp_path: Path) -> None:
    code = (
        "import os,signal,subprocess,sys,time; "
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        "print(os.getpid(),child.pid,flush=True); os.kill(os.getppid(),signal.SIGINT); time.sleep(60)"
    )
    try:
        with pytest.raises(KeyboardInterrupt):
            run_bounded([sys.executable, "-c", code], cwd=tmp_path,
                        stdout=tmp_path / "out", stderr=tmp_path / "err", timeout=5)
        parent, descendant = map(int, (tmp_path / "out").read_text().split())
        assert _state(parent) == ""
        state = _state(descendant)
        assert not state or state.startswith("Z")
    finally:
        if (tmp_path / "out").exists() and (tmp_path / "out").read_text().strip():
            _, descendant = map(int, (tmp_path / "out").read_text().split())
            if (state := _state(descendant)) and not state.startswith("Z"):
                os.kill(descendant, signal.SIGKILL)
