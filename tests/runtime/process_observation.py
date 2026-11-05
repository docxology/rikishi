"""Read actual process state with unprivileged Darwin/Linux kernel interfaces.

Darwin ABI sources: SDK sys/proc.h (extern_proc prefix and SIDL..SZOMB),
sys/sysctl.h (CTL_KERN, KERN_PROC, KERN_PROC_PID, leading kinfo_proc.kp_proc),
sys/_types/_timeval.h, arm/_types.h and sys/_types.h (LP64 timeval and pid_t).
Executable lookup uses SDK libproc.h proc_pidpath and sys/proc_info.h's
PROC_PIDPATHINFO_MAXSIZE, 4 * MAXPATHLEN (sys/syslimits.h PATH_MAX = 1024).
Unavailable observations raise; only confirmed absence returns an empty state.
"""

from __future__ import annotations

import ctypes
import errno
import math
import os
import sys
import time
from pathlib import Path


class _TimeValue(ctypes.Structure):
    _fields_ = [("seconds", ctypes.c_long), ("microseconds", ctypes.c_int32)]


class _ProcessStart(ctypes.Union):
    _fields_ = [("queue", ctypes.c_void_p * 2), ("started", _TimeValue)]


class _ExternProcPrefix(ctypes.Structure):
    # kinfo_proc begins with extern_proc; ctypes supplies the SDK C ABI padding.
    _fields_ = [("start", _ProcessStart), ("vmspace", ctypes.c_void_p),
                ("sigacts", ctypes.c_void_p), ("flags", ctypes.c_int32),
                ("status", ctypes.c_int8), ("pid", ctypes.c_int32)]


def _pid(pid: int) -> None:
    if type(pid) is not int or not 1 <= pid <= 2 ** 31 - 1:
        raise ValueError("process PID must be a positive signed 32-bit integer")


def _darwin_state(pid: int) -> str:
    if ctypes.sizeof(ctypes.c_void_p) != 8 or ctypes.sizeof(ctypes.c_long) != 8:
        raise RuntimeError("process observation requires the documented Darwin LP64 ABI")
    library = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    query = library.sysctl
    query.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_uint, ctypes.c_void_p,
                      ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t]
    query.restype = ctypes.c_int
    selection = (ctypes.c_int * 4)(1, 14, 1, pid)
    length = ctypes.c_size_t()
    ctypes.set_errno(0)
    if query(selection, 4, None, ctypes.byref(length), None, 0) != 0:
        error = ctypes.get_errno()
        raise OSError(error or errno.EIO, f"sysctl process size unavailable for PID {pid}")
    if length.value == 0:
        return ""
    minimum = ctypes.sizeof(_ExternProcPrefix)
    if not minimum <= length.value <= 64 * 1024:
        raise RuntimeError(f"unexpected bounded kinfo_proc size for PID {pid}: {length.value}")
    capacity = length.value
    buffer = ctypes.create_string_buffer(capacity)
    ctypes.set_errno(0)
    if query(selection, 4, buffer, ctypes.byref(length), None, 0) != 0:
        error = ctypes.get_errno()
        raise OSError(error or errno.EIO, f"sysctl process state unavailable for PID {pid}")
    if length.value == 0:
        return ""
    if not minimum <= length.value <= capacity:
        raise RuntimeError(f"truncated or oversized kinfo_proc for PID {pid}: {length.value}")
    info = _ExternProcPrefix.from_buffer_copy(buffer.raw)
    states = {1: "I", 2: "R", 3: "S", 4: "T", 5: "Z"}
    if info.pid != pid or info.status not in states:
        raise RuntimeError(f"unexpected kinfo_proc PID/state: {info.pid}/{info.status}, requested {pid}")
    return states[info.status]


def _linux_state(pid: int) -> str:
    try:
        with Path(f"/proc/{pid}/stat").open("rb") as stream:
            raw = stream.read(64 * 1024 + 1)
    except FileNotFoundError:
        if not Path("/proc/self/stat").is_file():
            raise RuntimeError("Linux process filesystem is unavailable") from None
        return ""
    boundary = raw.rfind(b") ")
    if len(raw) > 64 * 1024 or boundary < 0:
        raise RuntimeError(f"invalid bounded Linux process record for PID {pid}")
    identity, separator, _ = raw.partition(b" (")
    status = raw[boundary + 2:].split(maxsplit=1)[0]
    if separator != b" (" or identity != str(pid).encode() or status not in {
        b"R", b"S", b"D", b"Z", b"T", b"t", b"X", b"x", b"K", b"W", b"P", b"I",
    }:
        raise RuntimeError(f"unexpected Linux process PID/state for requested PID {pid}")
    return status.decode("ascii")


def process_state(pid: int) -> str:
    """Return the actual kernel state, including Z, or confirmed absence as ''."""
    _pid(pid)
    if sys.platform == "darwin":
        return _darwin_state(pid)
    if sys.platform == "linux":
        return _linux_state(pid)
    raise RuntimeError(f"unsupported process observation platform: {sys.platform}")


def wait_for_process_exit(pid: int, *, timeout: float = 5) -> str:
    """Require observed zombie/absence within five seconds; never infer exit from a signal.

    The caller owns signal delivery and any child reaping. This method only
    observes the supplied PID; unavailable reads propagate and live processes
    fail at the deadline. It does not alter native execution deadlines.
    """
    _pid(pid)
    if type(timeout) not in {int, float} or not math.isfinite(timeout) or not 0 < timeout <= 5:
        raise ValueError("use a finite timeout in (0, 5] seconds for exit observation")
    deadline = time.monotonic() + timeout
    while True:
        state = process_state(pid)
        remaining = deadline - time.monotonic()
        if remaining < 0:
            raise TimeoutError(f"PID {pid} exit was not observed before the deadline; state={state!r}")
        if state in {"", "Z"}:
            return state
        time.sleep(min(0.005, remaining))


def process_executable(pid: int) -> Path:
    """Inspect the actual executable; absence and permission failures remain errors."""
    _pid(pid)
    if sys.platform == "darwin":
        library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        query = library.proc_pidpath
        query.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        query.restype = ctypes.c_int
        buffer = ctypes.create_string_buffer(4096)
        ctypes.set_errno(0)
        length = query(pid, buffer, ctypes.sizeof(buffer))
        if length <= 0:
            error = ctypes.get_errno()
            raise OSError(error or errno.EIO, f"process executable unavailable for PID {pid}")
        if length >= ctypes.sizeof(buffer) or not buffer.value.startswith(b"/"):
            raise RuntimeError(f"invalid bounded process executable for PID {pid}")
        return Path(os.fsdecode(buffer.value))
    if sys.platform == "linux":
        return Path(os.readlink(f"/proc/{pid}/exe"))
    raise RuntimeError(f"unsupported executable observation platform: {sys.platform}")
