"""Calibrate real live, stopped, zombie and reaped process observations."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
from process_observation import process_executable, process_state, wait_for_process_exit


def _wait_state(pid: int, expected: str) -> None:
    deadline = time.monotonic() + 5
    while (observed := process_state(pid)) != expected:
        assert observed, f"owned child {pid} disappeared before expected state {expected}"
        assert time.monotonic() < deadline, (pid, expected, observed)
        time.sleep(0.005)


def test_actual_child_live_stopped_zombie_and_reaped() -> None:
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    try:
        assert process_state(process.pid) in {"I", "R", "S"}
        assert process_executable(process.pid).samefile(Path(sys.executable))
        os.kill(process.pid, signal.SIGSTOP)
        _wait_state(process.pid, "T")
        os.kill(process.pid, signal.SIGCONT)
        deadline = time.monotonic() + 5
        while (state := process_state(process.pid)) == "T":
            assert time.monotonic() < deadline, (process.pid, state)
            time.sleep(0.005)
        assert state in {"I", "R", "S"}
        os.kill(process.pid, signal.SIGKILL)
        assert wait_for_process_exit(process.pid) == "Z"
        assert process.wait(timeout=5) == -signal.SIGKILL
        assert process_state(process.pid) == ""
        assert wait_for_process_exit(process.pid) == ""
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)


def test_exit_observation_deadline_rejects_an_actual_live_child() -> None:
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    try:
        with pytest.raises(TimeoutError, match="exit was not observed"):
            wait_for_process_exit(process.pid, timeout=0.02)
        assert process_state(process.pid) in {"I", "R", "S"}
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)


@pytest.mark.parametrize("timeout", [0, -1, 6, float("nan"), float("inf"), True])
def test_exit_observation_rejects_unbounded_or_invalid_deadline(timeout) -> None:
    with pytest.raises(ValueError, match="finite timeout"):
        wait_for_process_exit(os.getpid(), timeout=timeout)


@pytest.mark.parametrize("pid", [0, -1, True, 1.5, 2 ** 31])
def test_process_observation_rejects_invalid_pid(pid) -> None:
    with pytest.raises(ValueError, match="positive signed 32-bit"):
        process_state(pid)
    with pytest.raises(ValueError, match="positive signed 32-bit"):
        process_executable(pid)
