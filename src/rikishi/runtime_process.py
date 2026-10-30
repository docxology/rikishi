"""Bound native process trees and retain their real output, including failures."""

from __future__ import annotations

import os
import signal
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProcessResult:
    returncode: int
    timed_out: bool


def _terminate_group(process: subprocess.Popen[bytes]) -> int:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError as error:
        if process.poll() is None:
            error.add_note(f"Process group {process.pid} may still be running; termination was denied.")
            raise
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            error.add_note(f"Process group {process.pid} may still be running; termination was denied.")
            raise
    return process.wait()


def run_bounded(
    command: Sequence[str], *, cwd: Path, stdout: Path, stderr: Path,
    timeout: float, environment: Mapping[str, str] | None = None,
) -> ProcessResult:
    """Run a fresh process group; terminate descendants on timeout or interruption."""
    if timeout <= 0:
        raise ValueError("wall-clock timeout must be positive")
    with stdout.open("xb") as out, stderr.open("xb") as err:
        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(
                command, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                stdout=out, stderr=err, start_new_session=True,
            )
            return ProcessResult(process.wait(timeout=timeout), False)
        except BaseException as error:
            if process is None:
                raise
            returncode = _terminate_group(process)
            if isinstance(error, subprocess.TimeoutExpired):
                return ProcessResult(returncode, True)
            raise
