import argparse
import hashlib
import json
import os
import shlex
import sys
import time
import uuid
from pathlib import Path
from typing import Literal, Self, assert_never

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from rikishi.runtime_artifacts import jar_classes_sha256, load_capture, read_regular, verified_bytes
from rikishi.runtime_context import (
    CONTEXT_FINGERPRINT_POLICY,
    CONTRADICTORY_STATEMENT_COUNT,
    CONTRADICTORY_STATEMENT_SHA256,
    recorded_negative_context,
)
from rikishi.runtime_process import run_bounded
from rikishi.runtime_query_profile import prepare_profile, verify_copied_inputs, verify_profile
from rikishi.runtime_results import ExpectedATPInvocation, interpret_sigma_result


class _QueryBudgetInput(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    native_limit_seconds: int = Field(ge=1, le=300)
    prover_wall_seconds: int | None = Field(default=None, ge=1, le=3600)


class QueryBudgets(BaseModel):
    """Declared native, adapter-wall and Java-wall limits for one query."""

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    mode: Literal["default", "explicit-wall"]
    native_limit_seconds: int = Field(ge=1, le=300)
    prover_wall_seconds: int = Field(ge=1, le=3600)
    java_wall_seconds: int = Field(ge=601, le=4200)

    @model_validator(mode="after")
    def consistent_policy(self) -> Self:
        match self.mode:
            case "default":
                wall = self.native_limit_seconds + 5
                java = 600 + self.native_limit_seconds
            case "explicit-wall":
                wall = self.prover_wall_seconds
                java = 600 + wall
            case unreachable:
                assert_never(unreachable)
        if self.prover_wall_seconds != wall or self.java_wall_seconds != java:
            raise PydanticCustomError("query_budget_policy", "Budget values differ from mode {mode}",
                                      {"mode": self.mode})
        return self


def _query_budgets(native: int, wall: int | None) -> QueryBudgets:
    requested = _QueryBudgetInput(native_limit_seconds=native, prover_wall_seconds=wall)
    match requested.prover_wall_seconds:
        case None:
            return QueryBudgets(mode="default", native_limit_seconds=requested.native_limit_seconds,
                                prover_wall_seconds=requested.native_limit_seconds + 5,
                                java_wall_seconds=600 + requested.native_limit_seconds)
        case int() as explicit:
            return QueryBudgets(mode="explicit-wall", native_limit_seconds=requested.native_limit_seconds,
                                prover_wall_seconds=explicit, java_wall_seconds=600 + explicit)
        case unreachable:
            assert_never(unreachable)


def run_query(
    root: Path, query: str, *, prover: str = "e", timeout: int = 15, output: Path | None = None,
    prover_wall_timeout: int | None = None,
) -> dict[str, object]:
    """Submit a native query and verify its saved input/output before interpreting it."""
    budgets = _query_budgets(timeout, prover_wall_timeout)
    root = root.resolve()
    if prover not in {"e", "v"}:
        raise ValueError("prover must be e or v")
    output = (output or root / ".rikishi/results" / f"sigma-query-{time.time_ns()}.log").resolve()
    if not output.is_relative_to(root):
        raise ValueError("output must be inside the repository")
    environment = json.loads((root / ".rikishi/runtime/environment.json").read_text())
    sigma_source = Path(environment["SIGMA_SRC"])
    output.parent.mkdir(parents=True, exist_ok=True)
    result_path = output.with_suffix(output.suffix + ".result.json")
    capture_dir = output.with_suffix(output.suffix + ".artifacts")
    if result_path.exists() or output.exists() or capture_dir.exists():
        raise FileExistsError("the query output or ATP evidence path already exists")
    capture_dir.mkdir()
    profile_source = Path(environment["SIGMA_HOME"])
    profile = capture_dir / "sigma-profile"
    snapshot = prepare_profile(profile_source, profile)
    profile_manifest = capture_dir / "profile-inputs.json"
    profile_manifest.write_bytes(snapshot.manifest())
    temporary = capture_dir / "tmp"
    temporary.mkdir()
    budget_path = capture_dir / "budgets.json"
    with budget_path.open("xb") as stream:
        stream.write((budgets.model_dump_json(indent=2) + "\n").encode("utf-8"))
    command = [str(Path(environment["JAVA_HOME"]) / "bin/java"), "-Xmx10g", "-Xss2m",
               f"-Duser.home={capture_dir}", f"-Djava.io.tmpdir={temporary}", "-cp",
               f"{sigma_source}/build/sigmakee.jar:{sigma_source}/lib/*",
               str(root / "scripts/runtime/RikishiQuery.java"), "-" + prover, "-r", "--timeout",
               str(budgets.native_limit_seconds),
               "--ask", query]
    invocation_id = uuid.uuid4().hex
    environment["RIKISHI_ATP_RESULT"] = str(result_path)
    environment["RIKISHI_INVOCATION_ID"] = invocation_id
    binary = (root / ".rikishi/upstream/eprover/PROVER/eprover" if prover == "e"
              else root / ".rikishi/runtime/vampire")
    bindings = {"prover": binary, "sigma_jar": sigma_source / "build/sigmakee.jar",
                "sumo_lock": root / "config/sumo.lock.json",
                "profile_config": profile_source / "KBs/config.xml",
                "profile_inputs": profile_manifest,
                "java_adapter": root / "scripts/runtime/RikishiQuery.java",
                "query_runner": Path(__file__),
                "query_budgets": budget_path,
                "profile_adapter": Path(__file__).with_name("runtime_query_profile.py")}
    provenance = {name + "_sha256": hashlib.sha256(read_regular(path)).hexdigest()
                  for name, path in bindings.items()}
    provenance["sigma_classes_sha256"] = jar_classes_sha256(bindings["sigma_jar"])
    provenance["query_sha256"] = hashlib.sha256(query.encode()).hexdigest()
    provenance.update({"query_budget_mode": budgets.mode,
                       "query_native_limit_seconds": str(budgets.native_limit_seconds),
                       "query_prover_wall_seconds": str(budgets.prover_wall_seconds),
                       "query_java_wall_seconds": str(budgets.java_wall_seconds)})
    adapter = capture_dir / "prover-adapter"
    with adapter.open("x") as stream:
        stream.write("#!/bin/sh\nexec " + shlex.quote(sys.executable)
                     + ' -m rikishi.runtime_capture "$@"\n')
    adapter.chmod(0o700)
    environment.update({"RIKISHI_ATP_CAPTURE": str(capture_dir),
                        "SIGMA_HOME": str(profile), "TMPDIR": str(temporary),
                        "VAMPIRE_OPTS": "--proof tptp --mode casc",
                        "RIKISHI_PROVER_ADAPTER": str(adapter),
                        "RIKISHI_REAL_PROVER": str(binary),
                        "RIKISHI_PROVER_KIND": prover,
                        "RIKISHI_PROVER_WALL_TIMEOUT": str(budgets.prover_wall_seconds),
                        "RIKISHI_PROVENANCE": json.dumps(provenance)})
    errors = output.with_suffix(output.suffix + ".stderr")
    verify_copied_inputs(snapshot, profile)
    process = run_bounded(command, cwd=root, stdout=output, stderr=errors,
                          environment=dict(os.environ, **environment), timeout=budgets.java_wall_seconds)
    verify_profile(snapshot)
    verify_copied_inputs(snapshot, profile, after_execution=True)
    report = interpret_sigma_result(result_path, process.returncode, process.timed_out,
                                    invocation_id=invocation_id,
                                    expected=ExpectedATPInvocation(invocation_id, binary, provenance,
                                                                   prover="e" if prover == "e" else "v"))
    if any(hashlib.sha256(read_regular(path)).hexdigest() != provenance[name + "_sha256"]
           for name, path in bindings.items()):
        report.update(status="ProvenanceChanged", outcome="error", proved=False, evidence="not_verified")
    context = "unknown"
    context_binding = None
    if report["evidence"] == "sha256_verified":
        capture = load_capture(capture_dir / "capture.json", invocation_id)
        context = recorded_negative_context(
            provenance, [item.sha256 for item in capture.includes],
            background_bytes=[verified_bytes(item, capture_dir) for item in capture.includes],
        )
        if context == "contradictory_translated_axioms_previously_observed":
            context_binding = {
                "scope": "complete_translated_background_statement_sequence",
                "fingerprint_policy": CONTEXT_FINGERPRINT_POLICY,
                "sha256": CONTRADICTORY_STATEMENT_SHA256,
                "count": CONTRADICTORY_STATEMENT_COUNT,
            }
    return {**report, "returncode": process.returncode, "log": str(output),
            "budgets": budgets.model_dump(mode="json"), "budgets_path": str(budget_path),
            "stderr_log": str(errors), "capture": str(capture_dir / "capture.json"),
            "profile": str(profile_source), "execution_profile": str(profile),
            "profile_inputs": str(profile_manifest), "query": query,
            "prover": prover, "invocation_id": invocation_id,
            "provenance": provenance, "negative_control_context": context,
            "negative_control_context_binding": context_binding}


def main(root: Path | None = None, argv: list[str] | None = None) -> int:
    root = (root or Path(os.environ.get("RIKISHI_ROOT", Path.cwd()))).resolve()
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="A SUO-KIF query translated by upstream Sigma")
    parser.add_argument("--prover", choices=["e", "v"], default="e")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--prover-wall-timeout", type=int, default=None,
                        help="Explicit prover wall limit (1..3600 seconds); native --timeout is unchanged")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = run_query(root, args.query, prover=args.prover, timeout=args.timeout, output=args.output,
                           prover_wall_timeout=args.prover_wall_timeout)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2))
    return 0 if report["outcome"] in {"entailed", "not_entailed"} else 2
