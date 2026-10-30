from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import FrameType, FunctionType
from typing import Final

from pydantic import BaseModel, ConfigDict

from rikishi import runtime_process
from rikishi.runtime_artifacts import Capture, ProverKind, load_capture, read_regular
from rikishi.runtime_capture import capture_prover

STOP_SOURCE: Final = (
    "#include <signal.h>\n#include <unistd.h>\n"
    "__attribute__((constructor)) static void hold_for_timeout(void) {\n"
    "    if (raise(SIGSTOP) != 0) _exit(125);\n}\n"
)


class NativeControlRequest(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    command: list[str]
    prover: ProverKind
    stopped: bool


def _save(path: Path, payload) -> None:
    with path.open("x") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")


def _platform() -> tuple[str, str, list[str]]:
    match sys.platform:
        case "darwin":
            return "DYLD_INSERT_LIBRARIES", "stop.dylib", ["-dynamiclib"]
        case "linux":
            return "LD_PRELOAD", "stop.so", ["-shared", "-fPIC"]
    raise AssertionError(f"native timeout controls require Darwin or Linux, got {sys.platform}")


def _state(pid: int) -> str:
    result = subprocess.run(["ps", "-o", "stat=,pgid=,comm=", "-p", str(pid)],
                            capture_output=True, text=True, check=False, timeout=5)
    assert result.returncode in {0, 1}, result.stderr
    return result.stdout.strip()


def _executable(pid: int, state: str) -> Path:
    match sys.platform:
        case "darwin":
            return Path(state.split(maxsplit=2)[2])
        case "linux":
            return Path(os.readlink(f"/proc/{pid}/exe"))
    raise AssertionError(f"unsupported executable observation platform: {sys.platform}")


def _kill_group(pid: int) -> str:
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return "already absent at signal delivery"
    return "SIGKILL delivered"


def _worker(directory: Path) -> None:
    request = NativeControlRequest.model_validate_json((directory / "request.json").read_bytes())
    loader_key, library_name, _ = _platform()
    library = directory / library_name
    original_environment = dict(os.environ)
    previous = sys.gettrace()
    launched: list[subprocess.Popen[bytes]] = []
    observed: list[int] = []
    injected: list[str] = []
    history: list[dict[str, str | int]] = []
    execute_child = vars(subprocess.Popen)["_execute_child"]
    assert isinstance(execute_child, FunctionType), "CPython Popen child-creation trace seam is unavailable"

    def trace(frame: FrameType, event: str, _value) -> Callable:
        caller = frame.f_back
        if (event == "call" and frame.f_code is subprocess.Popen.__init__.__code__
                and caller is not None and caller.f_code is runtime_process.run_bounded.__code__):
            assert frame.f_locals["args"] == request.command
            if request.stopped:
                assert frame.f_locals["env"] is None
                frame.f_locals["env"] = {**os.environ, loader_key: str(library)}
                injected.append(str(library))
        if event == "line" and frame.f_code is execute_child.__code__:
            process = frame.f_locals["self"]
            if (getattr(process, "_child_created", False) and not launched
                    and frame.f_locals["args"] == request.command):
                launched.append(process)
                _save(directory / "native.json", {"pid": process.pid, "command": request.command})
        if (event == "call" and frame.f_code is subprocess.Popen.wait.__code__
                and caller is not None and caller.f_code is runtime_process.run_bounded.__code__
                and not observed):
            process = frame.f_locals["self"]
            observed.append(process.pid)
            assert launched == [process]
            deadline = time.monotonic() + 5
            if request.stopped:
                assert os.getpgid(process.pid) == process.pid
                while True:
                    pid, status = os.waitpid(process.pid, os.WNOHANG | os.WUNTRACED)
                    if pid:
                        break
                    assert time.monotonic() < deadline, "native loader did not acknowledge SIGSTOP"
                    os.sched_yield()
                state = _state(pid)
                history.append({"pid": pid, "wait_status": status, "state": state})
                assert pid == process.pid and os.WIFSTOPPED(status), history
                assert os.WSTOPSIG(status) == signal.SIGSTOP, history
                assert state.startswith("T") and "X" not in state.split()[0], history
                assert _executable(pid, state) == Path(request.command[0]), history
                assert process.poll() is None
            else:
                while not (state := _state(process.pid)).startswith("Z"):
                    assert state and time.monotonic() < deadline, (process.pid, state)
                history.append({"pid": process.pid, "state": state})
        return trace

    executable_hash = hashlib.sha256(read_regular(Path(request.command[0]))).hexdigest()
    provenance = {"prover_sha256": executable_hash, "scheduling_instrumentation": "none"}
    if request.stopped:
        provenance.update({"scheduling_instrumentation": "native-loader-constructor-SIGSTOP-v1",
                           "scheduling_loader": loader_key,
                           "scheduling_source_sha256": hashlib.sha256(STOP_SOURCE.encode()).hexdigest(),
                           "scheduling_library_sha256": hashlib.sha256(library.read_bytes()).hexdigest()})
    module = Path(runtime_process.__file__).resolve()
    _save(directory / "runtime-binding.json", {"path": str(module),
          "sha256": hashlib.sha256(module.read_bytes()).hexdigest()})
    try:
        sys.settrace(trace)
        try:
            capture = capture_prover(request.command, directory, invocation_id="native-wait-control",
                                     provenance=provenance, timeout=0.02 if request.stopped else 0.000001,
                                     prover=request.prover)
        finally:
            sys.settrace(previous)
        assert load_capture(directory / "capture.json") == capture
        assert capture.command == request.command and capture.prover == request.prover
        assert len(launched) == len(observed) == 1
        assert len(injected) == int(request.stopped)
    finally:
        sys.settrace(previous)
        try:
            for process in launched:
                if process.poll() is None:
                    history.append({"cleanup": _kill_group(process.pid)})
                process.wait(timeout=5)
        finally:
            _save(directory / "observations.json", {"history": history, "injected": injected,
                  "trace_restored": sys.gettrace() is previous,
                  "environment_unchanged": dict(os.environ) == original_environment,
                  "returncodes": [process.returncode for process in launched],
                  "remaining_states": [_state(process.pid) for process in launched]})


def capture_native_control(
    command: list[str], directory: Path, *, prover: ProverKind, stopped: bool,
) -> Capture:
    assert sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 12), (
        "native timeout controls require CPython 3.12 trace-frame semantics")
    _, library_name, options = _platform()
    directory.mkdir()
    request = NativeControlRequest(command=command, prover=prover, stopped=stopped)
    (directory / "request.json").write_text(request.model_dump_json(indent=2))
    if stopped:
        source, library = directory / "stop.c", directory / library_name
        source.write_text(STOP_SOURCE)
        compiler = ["cc", *options, "-O2", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(library)]
        with (directory / "compiler.stdout").open("xb") as out, (
            directory / "compiler.stderr"
        ).open("xb") as err:
            compiler_process = subprocess.Popen(compiler, stdout=out, stderr=err,
                                                stdin=subprocess.DEVNULL, start_new_session=True)
            try:
                compiler_process.wait(timeout=20)
            finally:
                if compiler_process.poll() is None:
                    _kill_group(compiler_process.pid)
                compiler_process.wait(timeout=5)
        _save(directory / "compiler.json", {"command": compiler, "returncode": compiler_process.returncode,
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        assert compiler_process.returncode == 0, (directory / "compiler.stderr").read_text()
    deadline_expired = False
    cleanup: list[str] = []
    native_state = "no native pid recorded"
    with (directory / "worker.stdout").open("xb") as out, (
        directory / "worker.stderr"
    ).open("xb") as err:
        observer = subprocess.Popen([sys.executable, "-B", __file__, str(directory)],
                                    stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                    start_new_session=True)
        try:
            observer.wait(timeout=20)
        except subprocess.TimeoutExpired:
            deadline_expired = True
        finally:
            try:
                native = directory / "native.json"
                if native.exists():
                    pid = json.loads(native.read_text())["pid"]
                    if _state(pid):
                        cleanup.append(_kill_group(pid))
                    native_state = _state(pid)
            finally:
                try:
                    if observer.poll() is None:
                        cleanup.append("observer " + _kill_group(observer.pid))
                    observer.wait(timeout=5)
                finally:
                    _save(directory / "supervisor.json", {"worker_returncode": observer.returncode,
                          "deadline_expired": deadline_expired, "cleanup": cleanup,
                          "native_state_after_worker": native_state})
    assert not deadline_expired, "native control worker exceeded external 20-second deadline"
    assert observer.returncode == 0, (directory / "worker.stderr").read_text()
    observations = json.loads((directory / "observations.json").read_text())
    assert observations["trace_restored"] and observations["environment_unchanged"], observations
    assert observations["remaining_states"] == [""] and native_state == "", observations
    return load_capture(directory / "capture.json")


if __name__ == "__main__":
    _worker(Path(sys.argv[1]).resolve())
