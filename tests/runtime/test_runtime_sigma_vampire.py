from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from rikishi.runtime import prove
from rikishi.runtime_artifacts import (
    SZS_STATUS,
    expanded_problem,
    load_capture,
    read_regular,
)
from rikishi.runtime_context import (
    CONTRADICTORY_BACKGROUND_SHA256,
    CONTRADICTORY_CORE_BINDINGS,
    CONTRADICTORY_VAMPIRE_BINDINGS,
    recorded_negative_context,
)
from rikishi.runtime_diagnostics import diagnose
from rikishi.runtime_process import run_bounded
from rikishi.runtime_query import run_query
from rikishi.runtime_results import ExpectedATPInvocation, interpret_sigma_result, verify_invocation
from rikishi.runtime_tptp import parse_tptp


@pytest.fixture
def isolated_sigma(project_root: Path, tmp_path: Path) -> Path:
    for relative in ("config/sumo.lock.json", "scripts/runtime/RikishiQuery.java",
                     ".rikishi/runtime/vampire", ".rikishi/upstream/eprover/PROVER/eprover"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project_root / relative, target)
    profile = tmp_path / "profile"
    kb = profile / "KBs"
    kb.mkdir(parents=True)
    (kb / "Tiny.kif").write_text(
        "(instance subclass BinaryPredicate)\n(domain subclass 1 Class)\n"
        "(domain subclass 2 Class)\n(subclass Human Animal)\n(subclass Artifact Object)\n"
    )
    (kb / "config.xml").write_text(
        f'<configuration><preference name="baseDir" value="{profile}"/>'
        f'<preference name="kbDir" value="{kb}"/>'
        f'<preference name="sumoDir" value="{kb}"/>'
        '<preference name="sumokbname" value="Tiny"/>'
        '<preference name="loadLexicons" value="false"/>'
        '<preference name="loadFresh" value="true"/>'
        '<preference name="cache" value="yes"/>'
        '<kb name="Tiny"><constituent filename="Tiny.kif"/></kb></configuration>'
    )
    environment = json.loads((project_root / ".rikishi/runtime/environment.json").read_text())
    environment["SIGMA_HOME"] = str(profile)
    (tmp_path / ".rikishi/runtime/environment.json").write_text(json.dumps(environment))
    return tmp_path


@pytest.mark.integration
@pytest.mark.parametrize("goal,status", [("Animal", "Theorem"), ("Artifact", "CounterSatisfiable")])
def test_sigma_translated_query_uses_supported_vampire_and_exact_isolated_inputs(
    isolated_sigma: Path, goal: str, status: str,
) -> None:
    output = isolated_sigma / "query.log"
    result = run_query(isolated_sigma, f"(subclass Human {goal})", prover="v", timeout=5,
                       output=output)
    assert result["status"] == status, result
    assert result["proved"] == (status == "Theorem")
    assert result["outcome"] == ("entailed" if status == "Theorem" else "not_entailed")
    assert result["semantic_validation"] is False
    assert result["validation_scope"] == "translated_query_only"
    assert result["negative_control_context"] == "unknown"
    assert result["negative_control_context_binding"] is None
    assert result["evidence"] == "sha256_verified"
    directory = output.with_suffix(".log.artifacts")
    capture = load_capture(directory / "capture.json")
    assert capture.command[1:-1] == ["--proof", "tptp", "--mode", "casc", "-t", "5"]
    assert Path(capture.source_problem).is_relative_to(directory / "sigma-profile")
    assert all(Path(item.source).is_relative_to(directory / "sigma-profile") for item in capture.includes)
    manifest = json.loads((directory / "profile-inputs.json").read_text())
    assert {entry["path"] for entry in manifest["files"]} == {"KBs/Tiny.kif", "KBs/config.xml"}
    assert not (isolated_sigma / "profile/KBs/Tiny.tptp").exists()
    assert not (isolated_sigma / "profile/KBs/temp-comb.tptp").exists()
    assert not (isolated_sigma / "profile/KBs/kbmanager.ser").exists()
    sidecar = output.with_suffix(".log.result.json")
    expected = ExpectedATPInvocation(capture.invocation_id, isolated_sigma / ".rikishi/runtime/vampire",
                                     capture.provenance, prover="v")
    verify_invocation(capture, expected)
    payload = json.loads(sidecar.read_text())
    assert payload["stdout_lines"] == len((directory / "stdout.txt").read_bytes().splitlines())
    assert payload["atp_returncode"] == capture.returncode
    assert capture.returncode in ({0} if status == "Theorem" else {0, 1})
    frozen = expanded_problem(capture, directory)
    (directory / "sigma-profile").rename(directory / "moved-profile")
    assert expanded_problem(load_capture(directory / "capture.json"), directory) == frozen
    diagnostics = diagnose(directory / "capture.json", isolated_sigma, timeout=5,
                           output=isolated_sigma / "diagnostic")
    assert diagnostics["status"] == status
    assert (diagnostics["premise_count"] > 0) == (status == "Theorem")
    for mutation in ("family", "executable", "query", "invocation", "profile"):
        provenance = dict(capture.provenance)
        if mutation in {"query", "profile"}:
            provenance["query_sha256" if mutation == "query" else "profile_inputs_sha256"] = "0" * 64
        forged = ExpectedATPInvocation(
            "stale" if mutation == "invocation" else capture.invocation_id,
            isolated_sigma / (".rikishi/upstream/eprover/PROVER/eprover" if mutation == "executable"
                              else ".rikishi/runtime/vampire"), provenance,
            prover="e" if mutation == "family" else "v",
        )
        assert interpret_sigma_result(sidecar, 0, expected=forged)["outcome"] == "error"


@pytest.mark.integration
@pytest.mark.parametrize("options", ["--proof tptp --mode casc --output_axiom_names on", "--mode casc"])
def test_java_dispatch_rejects_unmanaged_options_before_native_launch(
    isolated_sigma: Path, options: str,
) -> None:
    environment = json.loads((isolated_sigma / ".rikishi/runtime/environment.json").read_text())
    sigma = Path(environment["SIGMA_SRC"])
    capture = isolated_sigma / "rejected-capture"
    capture.mkdir()
    temporary = isolated_sigma / "java-tmp"
    temporary.mkdir()
    environment.update({"VAMPIRE_OPTS": options, "RIKISHI_ATP_CAPTURE": str(capture),
                        "RIKISHI_PROVER_ADAPTER": str(isolated_sigma / "unused-adapter"),
                        "RIKISHI_ATP_RESULT": str(isolated_sigma / "rejected-result.json")})
    command = [str(Path(environment["JAVA_HOME"]) / "bin/java"),
               f"-Duser.home={temporary}", f"-Djava.io.tmpdir={temporary}", "-cp",
               f"{sigma}/build/sigmakee.jar:{sigma}/lib/*",
               str(isolated_sigma / "scripts/runtime/RikishiQuery.java"),
               "-v", "-r", "--timeout", "1", "--ask", "(subclass Human Animal)"]
    process = run_bounded(command, cwd=isolated_sigma, environment=dict(os.environ, **environment),
                          stdout=isolated_sigma / "rejected.stdout", stderr=isolated_sigma / "rejected.stderr",
                          timeout=30)
    assert process.returncode != 0 and not process.timed_out
    assert "Unsupported Vampire invocation options" in (isolated_sigma / "rejected.stderr").read_text()
    assert list(capture.iterdir()) == []
    assert not (isolated_sigma / "rejected-result.json").exists()


@pytest.mark.integration
@pytest.mark.parametrize("tamper_budget", [False, True])
def test_live_query_checks_saved_budget_after_real_solver_execution(
    isolated_sigma: Path, project_root: Path, tamper_budget: bool,
) -> None:
    # A real executable wrapper forwards every argument to the unchanged real solver.
    binary = isolated_sigma / ".rikishi/runtime/vampire"
    solver = binary.with_name("vampire-native")
    original_solver_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    assert original_solver_sha == hashlib.sha256(
        (project_root / ".rikishi/runtime/vampire").read_bytes()).hexdigest()
    binary.rename(solver)
    mutation = 'printf "\\n" >> "$RIKISHI_ATP_CAPTURE/budgets.json"\n' if tamper_budget else ""
    binary.write_text("#!/bin/sh\nset -eu\n"
                      'printf \'%s\\0\' "$@" > "$RIKISHI_ATP_CAPTURE/forwarded-argv.bin"\n'
                      + mutation + "exec " + shlex.quote(str(solver)) + ' "$@"\n')
    binary.chmod(0o700)
    wrapper_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    output = isolated_sigma / "budget-control.log"

    report = run_query(isolated_sigma, "(subclass Human Animal)", prover="v", timeout=5,
                       prover_wall_timeout=300, output=output)

    directory = output.with_suffix(".log.artifacts")
    capture = load_capture(directory / "capture.json")
    sidecar = json.loads(output.with_suffix(".log.result.json").read_text())
    assert sidecar["status"] == "Theorem" and sidecar["atp_returncode"] == 0
    assert capture.returncode == 0 and capture.timed_out is False
    assert SZS_STATUS.findall((directory / capture.stdout.path).read_text()) == ["Theorem"]
    forwarded = (directory / "forwarded-argv.bin").read_bytes().decode().split("\0")
    assert forwarded[-1] == "" and forwarded[:-1] == capture.command[1:]
    assert capture.command[0] == str(binary)
    assert capture.provenance["prover_sha256"] == wrapper_sha
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == wrapper_sha
    assert hashlib.sha256(solver.read_bytes()).hexdigest() == original_solver_sha
    budget_sha = hashlib.sha256((directory / "budgets.json").read_bytes()).hexdigest()
    assert (budget_sha != capture.provenance["query_budgets_sha256"]) == tamper_budget
    if tamper_budget:
        assert report["status"] == "ProvenanceChanged" and report["outcome"] == "error"
        assert report["evidence"] == "not_verified" and report["proved"] is False
    else:
        assert report["status"] == "Theorem" and report["outcome"] == "entailed"
        assert report["evidence"] == "sha256_verified" and report["proved"] is True
    (isolated_sigma / "control-receipt.json").write_text(json.dumps({
        "tampered": tamper_budget, "wrapper_sha256": wrapper_sha,
        "delegated_solver_sha256_before_and_after": original_solver_sha,
        "forwarded_argv": forwarded[:-1], "capture_command": capture.command,
        "saved_budget_sha256": budget_sha,
        "trusted_budget_sha256": capture.provenance["query_budgets_sha256"],
        "raw_status": sidecar["status"], "parent_status": report["status"],
    }, indent=2) + "\n")


@pytest.fixture(scope="module")
def core_queries(project_root: Path, native_workspace: Path) -> Path:
    directory = (native_workspace
                 / ("core-controls-" + uuid4().hex))
    directory.mkdir()
    for label, query, prover in (("positive", "(subclass Human Animal)", "v"),
                                 ("negative", "(subclass Human Artifact)", "v"),
                                 ("e-regression", "(subclass Human Animal)", "e")):
        # Preserve the native five-second Vampire timeout control; the E positive
        # regression gets an explicit larger native budget after its CPU5 ResourceOut.
        report = run_query(project_root, query, prover=prover, timeout=60 if prover == "e" else 5,
                           prover_wall_timeout=300,
                           output=directory / (label + ".log"))
        (directory / (label + ".json")).write_text(json.dumps(report, indent=2))
    return directory


@pytest.mark.integration
def test_frozen_core_contains_conjecture_free_vampire_refutation(
    project_root: Path, core_queries: Path,
) -> None:
    source = core_queries / "negative.log.artifacts/capture.json"
    capture = load_capture(source)
    binary = project_root / ".rikishi/runtime/vampire"
    verify_invocation(capture, ExpectedATPInvocation(capture.invocation_id, binary,
                                                   capture.provenance, prover="v"))
    frozen = expanded_problem(capture, source.parent)
    fixture = parse_tptp((project_root / "tests/runtime/fixtures/path-contradiction.p").read_text())
    names = {item.name for item in fixture}
    selected = [item for item in parse_tptp(frozen) if item.name in names]
    assert len(selected) == len(names) == 4
    assert {item.name: item.text.split() for item in selected} == {
        item.name: item.text.split() for item in fixture}
    problem = core_queries / "background-subset.p"
    problem.write_text("\n".join(item.text for item in selected) + "\n")
    result = prove(problem, project_root, timeout=5, prover="v", output=core_queries / "native")
    assert result["status"] == "Unsatisfiable"
    assert all("conjecture" not in item.text for item in selected)
    diagnostics = diagnose(core_queries / "native/capture.json", project_root, timeout=5,
                           output=core_queries / "diagnostic")
    assert diagnostics["subset_status"] == "Unsatisfiable"
    assert set(diagnostics["premise_names"]) == names
    assert hashlib.sha256(read_regular(binary)).hexdigest() == capture.provenance["prover_sha256"]


@pytest.mark.integration
def test_actual_core_queries_disclose_bound_contradiction_without_changing_query_scope(
    core_queries: Path,
) -> None:
    for label in ("positive", "negative", "e-regression"):
        report = json.loads((core_queries / (label + ".json")).read_text())
        assert report["evidence"] == "sha256_verified", report
        assert report["negative_control_context"] == "contradictory_translated_axioms_previously_observed"
        assert report["negative_control_context_binding"] == {
            "scope": "complete_translated_background_statement_sequence",
            "fingerprint_policy": "tptp-statement-text-newline-join-v1",
            "sha256": "ab478bdfc42d614399c8e016a3bfbfc36f9a4578d029e8ac56bbf23144c959df",
            "count": 36697,
        }
        assert report["semantic_validation"] is False
        assert report["validation_scope"] == "translated_query_only"
        assert report["consistency"] == "not_established"
        if label == "negative":
            assert report["status"] == "Timeout", report
            assert report["outcome"] == "inconclusive"
            assert report["proved"] is False
            assert report["atp_returncode"] == 1
            assert report["returncode"] == 0
        else:
            assert report["outcome"] == "entailed", report


@pytest.mark.parametrize("family", ["e", "v"])
@pytest.mark.parametrize("changed", [None, "prover", "classes", "lock", "config", "background", "extra"])
def test_context_binding_requires_every_pinned_identity(family: str, changed: str | None) -> None:
    bindings = dict(CONTRADICTORY_CORE_BINDINGS if family == "e" else CONTRADICTORY_VAMPIRE_BINDINGS)
    keys = {"prover": "prover_sha256", "classes": "sigma_classes_sha256",
            "lock": "sumo_lock_sha256", "config": "profile_config_sha256"}
    backgrounds = [CONTRADICTORY_BACKGROUND_SHA256]
    if changed in keys:
        bindings[keys[changed]] = "0" * 64
    elif changed == "background":
        backgrounds = ["0" * 64]
    elif changed == "extra":
        backgrounds.append("0" * 64)
    context = recorded_negative_context(bindings, backgrounds)
    assert context == ("contradictory_translated_axioms_previously_observed"
                       if changed is None else "unknown")
