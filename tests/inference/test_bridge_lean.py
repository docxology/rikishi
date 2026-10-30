"""Pure generation contracts plus root-owned native-packet acceptance scenarios."""

from __future__ import annotations

import ast
import json
import re
import shutil
from hashlib import sha256
from pathlib import Path
from typing import Protocol

import pytest

from rikishi.bridge_compiler import (
    PINNED_SOURCES,
    SUFFIXES,
    _axioms,
    _control_diagnostic,
    control_sources,
    declarations,
    environment_sources,
    lean_source,
    validate_lean,
)
from rikishi.bridge_models import BridgeError, BridgeReport
from rikishi.bridge_study import catalog


class BridgePacket(Protocol):
    root: Path
    path: Path
    sha256: str
    report: BridgeReport


def test_generated_declarations_bind_all_three_witness_namespaces() -> None:
    # Given: the immutable study authority and its three concrete witnesses.
    study = catalog()
    # When: the complete declaration inventory is derived.
    names = declarations(study)
    # Then: every witness has the same explicit inventory with no collisions.
    assert len(names) == len(set(names)) == 51
    assert names == tuple(f"{w.namespace}.{suffix}" for w in study.witnesses for suffix in SUFFIXES)
    assert {name.split(".")[0] for name in names} == {
        "UniformPrior", "BiasedPrior", "ExactCandidate"}


def test_source_constructs_pinned_laws_kernel_and_actual_theorem_instances() -> None:
    # Given: the exact authority, including the first-index/false convention.
    study = catalog()
    # When: Lean source is generated without invoking a tool.
    source = lean_source(study)
    # Then: actual carriers, exact arithmetic and each pinned theorem are present.
    assert source.startswith("module\npublic import FepSketches.finite_information\n")
    assert source.count("noncomputable def prior : FEP.FiniteLaw Bool where") == 3
    assert source.count("noncomputable def candidate : FEP.FiniteLaw Bool where") == 3
    assert source.count("noncomputable def kernel : FEP.FiniteKernel Bool Bool where") == 3
    assert source.count("else 1 - (if x then") == 3
    for theorem in ("posterior_mul_predictive", "finiteKL_nonneg", "finiteKL_self",
                    "finiteKL_eq_crossEntropy_sub_entropy"):
        assert source.count(f".{theorem} ") + source.count(f".{theorem}\n") == 3
    assert re.findall(r"^#print axioms (\S+)$", source, re.MULTILINE) == list(declarations(study))
    assert "sorry" not in source and "axiom " not in source
    for witness in study.witnesses:
        for entity in witness.entities.model_dump().values():
            assert f': String := "{entity}"' in source


@pytest.mark.parametrize("namespace,evidence,false_mass,true_mass", [
    ("UniformPrior", "(1 / 2 : ℝ)", "(1 / 4 : ℝ)", "(3 / 4 : ℝ)"),
    ("BiasedPrior", "(2 / 3 : ℝ)", "(1 / 4 : ℝ)", "(3 / 4 : ℝ)"),
    ("ExactCandidate", "(7 / 12 : ℝ)", "(6 / 7 : ℝ)", "(1 / 7 : ℝ)"),
])
def test_source_proves_independently_expected_rational_posterior(
    namespace: str, evidence: str, false_mass: str, true_mass: str,
) -> None:
    # Given: independently specified exact Bayes results for each authority witness.
    study = catalog()
    # When: the source for that namespace is selected.
    source = lean_source(study).split(f"namespace {namespace}\n")[1].split(f"end {namespace}")[0]
    # Then: the theorem asserts the actual predictive law and pointwise posterior.
    assert f"predictive prior kernel true = {evidence}" in source
    assert f"x = (if x then {true_mass} else {false_mass})" in source


def test_three_control_sources_have_distinct_actual_failure_obligations() -> None:
    # Given: the same generated module used by accepted witnesses.
    study = catalog()
    # When: the real negative Lean sources are derived.
    controls = dict(control_sources(study))
    # Then: normalization, numerical posterior and admitted proof are each exercised.
    assert tuple(controls) == ("invalid-normalization", "wrong-posterior", "admitted-proof")
    assert "mass _ := 1" in controls["invalid-normalization"]
    assert "sum_one := by rw [Fintype.sum_bool]; norm_num" in controls["invalid-normalization"]
    assert "UniformPrior.evidence_positive false = (5 / 4 : ℝ)" in controls["wrong-posterior"]
    assert "rw [UniformPrior.posterior]; norm_num" in controls["wrong-posterior"]
    assert "theorem BridgeControls.admittedProof : False := by sorry" in controls["admitted-proof"]
    assert "#print axioms BridgeControls.admittedProof" in controls["admitted-proof"]


def test_positive_environments_keep_control_imports_and_separate_declarations() -> None:
    # Given: the same three rejected inputs and their paired valid environments.
    study = catalog()
    controls = dict(control_sources(study))
    # When: the independent positive declarations are generated.
    environments = environment_sources(study)
    # Then: each shares exactly its control's imports without changing the main inventory.
    assert tuple(e[0] for e in environments) == tuple(controls)
    for identity, text, names in environments:
        assert re.findall(r"^(?:public )?import .+$", text, re.MULTILINE) == re.findall(
            r"^(?:public )?import .+$", controls[identity], re.MULTILINE)
        assert re.findall(r"^#print axioms (\S+)$", text, re.MULTILINE) == list(names)
        assert not set(names) & set(declarations(study))
        assert "sorry" not in text and "axiom " not in text


@pytest.fixture(params=[
    ("invalid-normalization", ("9:13: error: unsolved goals\n⊢ False\n"
     "'BridgeControls.invalidNormalization' depends on axioms: "
     "[propext, sorryAx, Classical.choice, Quot.sound]\n")),
    ("wrong-posterior", ("8:60: error: unsolved goals\n⊢ False\n"
     "'BridgeControls.wrongPosterior' depends on axioms: "
     "[propext, sorryAx, Classical.choice, Quot.sound]\n")),
    ("admitted-proof", ("5:8: error: declaration uses `sorry`\n"
     "'BridgeControls.admittedProof' depends on axioms: [sorryAx]\n")),
])
def control_rejection(request: pytest.FixtureRequest, tmp_path: Path) -> tuple[Path, str, str]:
    """Pinned compiler diagnostics, kept separate from the validator's derivation."""
    identity, suffix = request.param
    path = tmp_path / f"{identity}.lean"
    return path, dict(control_sources(catalog()))[identity], f"{path}:{suffix}"


def test_control_diagnostic_accepts_located_semantic_failure(
    control_rejection: tuple[Path, str, str],
) -> None:
    # Given: the pinned compiler's intended error and exact named axiom report.
    source, generated, output = control_rejection
    # When: the shared live/replay diagnostic guard inspects it.
    result = _control_diagnostic(source, generated, output)
    # Then: this actual proof failure is accepted as a negative control.
    assert result is None


@pytest.mark.parametrize("mutation", [
    "import", "syntax", "resource", "position", "source", "declaration", "axiom", "extra",
])
def test_control_diagnostic_rejects_environment_errors_and_unbound_proof_failures(
    control_rejection: tuple[Path, str, str], mutation: str,
) -> None:
    # Given: a failure that must not count as the intended mathematical rejection.
    source, generated, output = control_rejection
    changed = {
        "import": f"{source}:2:0: error: object file of module Missing does not exist\n",
        "syntax": f"{source}:1:0: error: unexpected token\n",
        "resource": f"{source}:9:13: error: maximum number of heartbeats exceeded\n",
        "position": output.replace(f"{source}:", f"{source}:1", 1),
        "source": output.replace(str(source), str(source.with_name("other.lean")), 1),
        "declaration": output.replace("'BridgeControls.", "'Other.", 1),
        "axiom": output.replace("sorryAx", "Unapproved.assumption"),
        "extra": output + f"{source}:2:0: error: import failed\n",
    }[mutation]
    # When / Then: neither live compilation nor portable replay may credit it.
    with pytest.raises(BridgeError):
        _control_diagnostic(source, generated, changed)


@pytest.mark.parametrize("identity,position", [
    ("invalid-normalization", "9:13"), ("wrong-posterior", "8:60"),
])
def test_arithmetic_control_requires_false_goal_after_actual_normalization(
    tmp_path: Path, identity: str, position: str,
) -> None:
    # Given: an unsolved arithmetic goal that was not normalized to a contradiction.
    source = tmp_path / f"{identity}.lean"
    text = dict(control_sources(catalog()))[identity]
    name = "invalidNormalization" if identity == "invalid-normalization" else "wrongPosterior"
    output = (f"{source}:{position}: error: unsolved goals\n⊢ 2⁻¹ + 2⁻¹ = 1\n"
              f"'BridgeControls.{name}' depends on axioms: [sorryAx]\n")
    # When / Then: missing tactic support cannot be mistaken for a proof rejection.
    with pytest.raises(BridgeError):
        _control_diagnostic(source, text, output)


@pytest.mark.parametrize("field", ["pin", "source", "count", "namespace", "normalization", "support"])
def test_generation_rejects_changed_formal_binding_or_invalid_law(field: str) -> None:
    # Given: one changed authority obligation, with all other fields held fixed.
    study = catalog()
    changes = {"pin": {"formal_revision": "0" * 40},
               "source": {"formal_sources": dict(PINNED_SOURCES, unexpected="0" * 64)},
               "count": {"witnesses": study.witnesses[:2]},
               "namespace": {"witnesses": (study.witnesses[0], study.witnesses[0], study.witnesses[2])},
               "normalization": {"witnesses": (study.witnesses[0].model_copy(
                   update={"prior": ("1/3", "1/3")}), *study.witnesses[1:])},
               "support": {"witnesses": (study.witnesses[0].model_copy(
                   update={"likelihood": ("0", "1/2")}), *study.witnesses[1:])}}
    changed = study.model_copy(update=changes[field])
    # When / Then: generation rejects rather than emitting impossible proof obligations.
    with pytest.raises(BridgeError):
        lean_source(changed)


@pytest.mark.parametrize("report", [
    "'Witness.good' depends on axioms: [sorryAx]",
    "'Witness.good' depends on axioms: [Bridge.assumption]",
    "'Witness.good' depends on axioms: [Classical.choice, sorryAx]",
    "'Other.good' does not depend on any axioms",
    "'Witness.good' does not depend on any axioms\n'Witness.good' does not depend on any axioms",
    "'Witness.good' does not depend on any axioms\nerror: compiler failed",
    "",
])
def test_axiom_gate_rejects_unapproved_or_incomplete_report(report: str) -> None:
    # Given: a report that must fail even if Lean's process returned zero.
    # When / Then: the axiom gate rejects the named defect.
    with pytest.raises(BridgeError):
        _axioms(report, ("Witness.good",))


@pytest.mark.parametrize("report", [
    "'Witness.good' does not depend on any axioms\n",
    "'Witness.good' depends on axioms: [propext, Classical.choice, Quot.sound]\n",
])
def test_axiom_gate_accepts_only_complete_allowed_report(report: str) -> None:
    # Given: one complete report using only the recorded foundational axioms.
    # When: the report is validated.
    result = _axioms(report, ("Witness.good",))
    # Then: validation returns normally.
    assert result is None


def test_portable_validation_call_graph_contains_no_subprocess() -> None:
    # Given: the real module syntax, without executing any native fixture.
    module = ast.parse(Path(__file__).parents[2].joinpath(
        "src/rikishi/bridge_compiler.py").read_text())
    functions = {n.name: n for n in module.body if isinstance(n, ast.FunctionDef)}
    pending, visited = ["validate_lean"], set()
    # When: all locally reachable validation helpers are traversed.
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        for call in (n for n in ast.walk(functions[name]) if isinstance(n, ast.Call)):
            if isinstance(call.func, ast.Name) and call.func.id in functions:
                pending.append(call.func.id)
            assert not (isinstance(call.func, ast.Attribute)
                        and isinstance(call.func.value, ast.Name)
                        and call.func.value.id == "subprocess")
    # Then: the expected pure validators are reachable, with no native entrypoint.
    assert {"_validate_base", "_validate_dependencies", "lean_source", "control_sources"} <= visited
    assert "compile_witnesses" not in visited


@pytest.mark.integration
def test_native_packet_has_all_concrete_axioms_and_three_real_rejections(
    bridge_packet: BridgePacket,
) -> None:
    # Given: root's one real freshly generated campaign, never a duplicate compiler run.
    evidence = bridge_packet.report.lean
    directory = bridge_packet.path.parent
    # When: retained Lean evidence is validated independently of live dependencies.
    result = validate_lean(directory, catalog(), evidence)
    # Then: all declarations were audited, with all three controls genuinely rejected.
    assert result is None
    assert evidence.declarations == declarations(catalog())
    assert len(evidence.controls) == 3 and all(c.rejected for c in evidence.controls)
    assert all(c.command.returncode > 0 for c in evidence.controls)
    assert all("-DwarningAsError=true" in c.command.command for c in evidence.controls)
    assert "sorryAx" not in evidence.declaration_axioms
    admitted = next(c for c in evidence.controls if c.id == "admitted-proof")
    assert "sorryAx" in (directory / admitted.command.log).read_text()
    assert "declaration uses `sorry`" in (directory / admitted.command.log).read_text()
    assert tuple(e.id for e in evidence.environments) == tuple(c.id for c in evidence.controls)
    assert all(e.command.returncode == 0 for e in evidence.environments)
    for environment in evidence.environments:
        _axioms(environment.declaration_axioms, environment.declarations)


@pytest.mark.integration
def test_real_lean_packet_replays_after_campaign_relocation(
    bridge_packet: BridgePacket, tmp_path: Path,
) -> None:
    # Given: only retained Lean/base artifacts copied away from the original campaign.
    copied = tmp_path / "copied"
    copied.mkdir()
    for name in ("lean-base", "lean"):
        shutil.copytree(bridge_packet.path.parent / name, copied / name)
    # When: portable validation uses the relocated bytes and historical path identities.
    result = validate_lean(copied, catalog(), bridge_packet.report.lean)
    # Then: validation needs no source checkout, compiler executable or dependency cache.
    assert result is None


@pytest.mark.integration
@pytest.mark.parametrize("mutation", [
    "source", "control", "log", "axioms", "command", "returncode", "timeout", "elapsed",
    "base_timeout", "base_elapsed", "environment_source", "environment_log", "control_diagnostic",
    "base_error", "missing_import", "axioms_synchronized",
])
def test_native_receipt_rejects_tampering_even_with_rehashed_artifacts(
    bridge_packet: BridgePacket, tmp_path: Path, mutation: str,
) -> None:
    # Given: a copied real packet with one intentionally corrupted obligation.
    copied = tmp_path / "tampered"
    copied.mkdir()
    for name in ("lean-base", "lean"):
        shutil.copytree(bridge_packet.path.parent / name, copied / name)
    evidence = bridge_packet.report.lean
    if mutation in {"source", "control", "log"}:
        path = {"source": evidence.source, "control": evidence.controls[0].source,
                "log": evidence.commands[0].log}[mutation]
        (copied / path).write_text("changed retained content\n")
        hashes = dict(evidence.artifacts)
        hashes[path] = sha256((copied / path).read_bytes()).hexdigest()
        evidence = evidence.model_copy(update={"artifacts": hashes})
    if mutation == "axioms":
        evidence = evidence.model_copy(update={"declaration_axioms": "sorryAx"})
    if mutation in {"command", "returncode"}:
        first = evidence.commands[0]
        update = ({"command": (first.command[0], first.command[-1])} if mutation == "command"
                  else {"returncode": 1})
        evidence = evidence.model_copy(update={"commands": (
            first.model_copy(update=update), *evidence.commands[1:])})
    if mutation in {"timeout", "elapsed"}:
        first = evidence.commands[0]
        update = ({"timeout_seconds": 180} if mutation == "timeout"
                  else {"elapsed_seconds": float("inf")})
        evidence = evidence.model_copy(update={"commands": (
            first.model_copy(update=update), *evidence.commands[1:])})
    if mutation in {"base_timeout", "base_elapsed"}:
        update = ({"base_timeout_seconds": 180} if mutation == "base_timeout"
                  else {"base_elapsed_seconds": float("inf")})
        evidence = evidence.model_copy(update=update)
    if mutation in {"environment_source", "environment_log"}:
        first_environment = evidence.environments[0]
        path = (first_environment.source if mutation == "environment_source"
                else first_environment.command.log)
        (copied / path).write_text("changed positive environment\n")
        hashes = dict(evidence.artifacts)
        hashes[path] = sha256((copied / path).read_bytes()).hexdigest()
        evidence = evidence.model_copy(update={"artifacts": hashes})
        if mutation == "environment_log":
            changed_environment = first_environment.model_copy(update={
                "declaration_axioms": "changed positive environment\n",
                "command": first_environment.command.model_copy(update={"log_sha256": hashes[path]}),
            })
            evidence = evidence.model_copy(update={"environments": (
                changed_environment, *evidence.environments[1:])})
    if mutation == "control_diagnostic":
        first_control = evidence.controls[0]
        path = first_control.command.log
        original = first_control.command.command[-1]
        (copied / path).write_text(f"{original}:2:0: error: import failed\n")
        hashes = dict(evidence.artifacts)
        hashes[path] = sha256((copied / path).read_bytes()).hexdigest()
        changed_control = first_control.model_copy(update={
            "command": first_control.command.model_copy(update={"log_sha256": hashes[path]})})
        evidence = evidence.model_copy(update={"artifacts": hashes,
                                               "controls": (changed_control, *evidence.controls[1:])})
    if mutation == "base_error":
        base_path = copied / "lean-base/verification.json"
        base = json.loads(base_path.read_text())
        base["declaration_axioms"] += "error: compiler failed after axiom reports\n"
        base_path.write_text(json.dumps(base, indent=2) + "\n")
        (copied / "lean-base/declaration-axioms.log").write_text(base["declaration_axioms"])
        hashes = dict(evidence.artifacts)
        for path in ("lean-base/verification.json", "lean-base/declaration-axioms.log"):
            hashes[path] = sha256((copied / path).read_bytes()).hexdigest()
        evidence = evidence.model_copy(update={"artifacts": hashes,
            "base_receipt_sha256": hashes["lean-base/verification.json"]})
    if mutation == "missing_import":
        base = json.loads((copied / "lean-base/verification.json").read_text())
        primary = str(Path(base["workspace"]) / "lib/FepSketches/finite_information.olean")
        dependency_path = copied / "lean/dependencies.json"
        dependency = json.loads(dependency_path.read_text())
        for suffix in ("", ".private", ".server"):
            del dependency["imports"][primary + suffix]
        dependency_path.write_text(json.dumps(dependency, indent=2) + "\n")
        command = evidence.commands[1]
        log = copied / command.log
        log.write_text("\n".join(line for line in log.read_text().splitlines() if line != primary) + "\n")
        hashes = dict(evidence.artifacts)
        for path in ("lean/dependencies.json", command.log):
            hashes[path] = sha256((copied / path).read_bytes()).hexdigest()
        evidence = evidence.model_copy(update={"artifacts": hashes, "commands": (
            evidence.commands[0], command.model_copy(update={"log_sha256": hashes[command.log]}))})
    if mutation == "axioms_synchronized":
        lines = evidence.declaration_axioms.splitlines()
        lines[0] = f"'{evidence.declarations[0]}' depends on axioms: [sorryAx]"
        changed_axioms = "\n".join(lines) + "\n"
        command = evidence.commands[0]
        (copied / command.log).write_text(changed_axioms)
        digest = sha256(changed_axioms.encode()).hexdigest()
        evidence = evidence.model_copy(update={"declaration_axioms": changed_axioms,
            "artifacts": dict(evidence.artifacts, **{command.log: digest}),
            "commands": (command.model_copy(update={"log_sha256": digest}), evidence.commands[1])})
    # When / Then: the rederived obligation rejects a self-consistent outer file digest.
    with pytest.raises(BridgeError):
        validate_lean(copied, catalog(), evidence)
