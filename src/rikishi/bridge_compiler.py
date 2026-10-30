"""Concrete finite Lean witnesses and portable retained-evidence validation.

SIZE_OK: the delegated ownership boundary permits this one compiler module only;
its source generation and receipt protocol must share exactly the same derivation.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path
from time import perf_counter
from typing import Final

from pydantic import TypeAdapter

from rikishi.bridge_models import (
    BridgeError,
    BridgeStudy,
    FiniteWitness,
    LeanCommand,
    LeanControl,
    LeanEnvironment,
    LeanEvidence,
)
from rikishi.bridge_study import exact_posterior, probabilities
from rikishi.fep import PIN
from rikishi.formal_verification import (
    CompilationReceipt,
    _cache_snapshot,
    _compile,
    _git,
    _require_stable_cache,
    verify_formalization,
)
from rikishi.inference_models import Frozen
from rikishi.runtime_artifacts import checked_source_path, read_regular

SUFFIXES: Final = (
    "modelEntity", "representationEntity", "calculationEntity", "resultEntity", "agentEntity",
    "prior", "candidate", "kernel", "evidence", "evidence_positive", "posterior",
    "candidate_positive", "posterior_positive", "posterior_reconstruction",
    "kl_nonnegative", "kl_self", "kl_decomposition",
)
PINNED_SOURCES: Final = {
    "lean/FepSketches/finite_probability.lean":
        "d99ae05fec4d012ecbb83601d1e361b01b22458790a316bb2ba3e360dfa11380",
    "lean/FepSketches/finite_information.lean":
        "6827f3ceeee21c9312c5166aefdd4a6cbc50579229813992c3e5a05cadb71d65",
}
PINNED_METADATA: Final = {
    "lake-manifest.json": "9fdcd10229bbd8c886c6786c4c2287898062cd6cbc029a610bf0530c14a8bd1a",
    "lean-toolchain": "ca5f1f601d34c49079e38d7e7041eb0f2a9c227fbc1df0f404820069a052330c",
}
SCOPE: Final = (
    "Concrete rational Bool witnesses elaborated against pinned finite modules; "
    "three rejected Lean controls and declaration-axiom inspection. Portable validation "
    "checks retained bytes and receipt consistency only, performs no new Lean checking, "
    "and does not replay-authenticate absent compiler/dependency artifacts. No SUMO "
    "semantic-preservation theorem, Python-correctness proof, or empirical FEP claim."
)
BASE_ADAPTER: Final = TypeAdapter(CompilationReceipt)
HEADER: Final = "module\npublic import FepSketches.finite_information\n\n@[expose] public section\n"
OPTIONS: Final = ("-DwarningAsError=true",)
LEAN_TIMEOUT_SECONDS: Final = 600


class _Dependencies(Frozen):
    imports: dict[str, str]
    cache_sha256: dict[str, str]
    cache_files: int
    compiler_sha256: str


def declarations(study: BridgeStudy) -> tuple[str, ...]:
    """Return every generated public declaration, in its axiom-report order."""
    return tuple(f"{w.namespace}.{name}" for w in study.witnesses for name in SUFFIXES)


def _real(value: Fraction) -> str:
    return f"({value.numerator} / {value.denominator} : ℝ)"


def _witness_source(witness: FiniteWitness) -> str:
    prior, candidate = probabilities(witness.prior), probabilities(witness.candidate)
    likelihood = probabilities(witness.likelihood)
    if sum(prior) != 1 or sum(candidate) != 1:
        raise BridgeError("Lean witness laws must be exactly normalized")
    evidence, posterior = exact_posterior(witness)
    p0, p1, q0, q1, l0, l1, z, r0, r1 = map(
        _real, (*prior, *candidate, *likelihood, evidence, *posterior))
    entities = "\n".join(f'def {role}Entity : String := "{entity}"'
                         for role, entity in witness.entities.model_dump().items())
    post = "FEP.FiniteKernel.posterior prior kernel true evidence_positive"
    return f"""
namespace {witness.namespace}
-- Identifiers bind authored labels only. Bool.false is index 0; Bool.true is index 1.
{entities}

noncomputable def prior : FEP.FiniteLaw Bool where
  mass x := if x then {p1} else {p0}
  nonneg x := by cases x <;> norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num

noncomputable def candidate : FEP.FiniteLaw Bool where
  mass x := if x then {q1} else {q0}
  nonneg x := by cases x <;> norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num

noncomputable def kernel : FEP.FiniteKernel Bool Bool where
  mass x y := if y then (if x then {l1} else {l0})
              else 1 - (if x then {l1} else {l0})
  nonneg x y := by cases x <;> cases y <;> norm_num
  sum_one x := by cases x <;> rw [Fintype.sum_bool] <;> norm_num

theorem evidence : FEP.FiniteKernel.predictive prior kernel true = {z} := by
  norm_num [FEP.FiniteKernel.predictive_mass, prior, kernel, Fintype.sum_bool]

theorem evidence_positive : 0 < FEP.FiniteKernel.predictive prior kernel true := by
  rw [evidence]; norm_num

theorem posterior (x : Bool) :
    {post} x = (if x then {r1} else {r0}) := by
  cases x <;> norm_num [FEP.FiniteKernel.posterior,
    FEP.FiniteKernel.predictive_mass, prior, kernel, Fintype.sum_bool]

theorem candidate_positive (x : Bool) : 0 < candidate x := by
  cases x <;> norm_num [candidate]

theorem posterior_positive (x : Bool) : 0 < {post} x := by
  rw [posterior]; cases x <;> norm_num

theorem posterior_reconstruction (x : Bool) :
    {post} x * FEP.FiniteKernel.predictive prior kernel true =
      prior x * kernel x true :=
  FEP.FiniteKernel.posterior_mul_predictive prior kernel true evidence_positive x

theorem kl_nonnegative :
    0 ≤ FEP.FiniteInformation.finiteKL candidate ({post}) :=
  FEP.FiniteInformation.finiteKL_nonneg candidate ({post})

theorem kl_self : FEP.FiniteInformation.finiteKL
    ({post}) ({post}) = 0 :=
  FEP.FiniteInformation.finiteKL_self ({post})

theorem kl_decomposition :
    FEP.FiniteInformation.finiteKL candidate ({post}) =
      FEP.FiniteInformation.crossEntropy candidate ({post}) -
        FEP.FiniteInformation.entropy candidate :=
  FEP.FiniteInformation.finiteKL_eq_crossEntropy_sub_entropy
    candidate ({post}) posterior_positive

end {witness.namespace}
"""


def lean_source(study: BridgeStudy) -> str:
    """Derive actual normalized laws, exact Bayes witnesses and pinned KL instances."""
    names = [w.namespace for w in study.witnesses]
    if (study.formal_revision != PIN or study.formal_sources != PINNED_SOURCES
            or len(names) != 3 or len(set(names)) != len(names)):
        raise BridgeError("Lean witnesses require three distinct namespaces and exact pinned sources")
    return HEADER + "".join(_witness_source(w) for w in study.witnesses) + "\n" + "\n".join(
        f"#print axioms {name}" for name in declarations(study)) + "\n"


def control_sources(study: BridgeStudy) -> tuple[tuple[str, str], ...]:
    """Derive three independently rejected inputs; none is accepted evidence."""
    lean_source(study)
    witness = study.witnesses[0]
    _, posterior = exact_posterior(witness)
    namespace = witness.namespace
    imported = "module\npublic import BridgeWitnesses\n\n@[expose] public section\n"
    return (
        ("invalid-normalization", HEADER.replace("finite_information", "finite_probability") + """
noncomputable def BridgeControls.invalidNormalization : FEP.FiniteLaw Bool where
  mass _ := 1
  nonneg _ := by norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num
#print axioms BridgeControls.invalidNormalization
"""),
        ("wrong-posterior", imported + f"""
theorem BridgeControls.wrongPosterior :
    FEP.FiniteKernel.posterior {namespace}.prior {namespace}.kernel true
      {namespace}.evidence_positive false = {_real(posterior[0] + 1)} := by
  rw [{namespace}.posterior]; norm_num
#print axioms BridgeControls.wrongPosterior
"""),
        ("admitted-proof", "module\n\n@[expose] public section\n" + """
theorem BridgeControls.admittedProof : False := by sorry
#print axioms BridgeControls.admittedProof
"""),
    )


def environment_sources(study: BridgeStudy) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Pair each rejected obligation with an allowed proof under identical imports."""
    controls = dict(control_sources(study))
    _, posterior = exact_posterior(study.witnesses[0])
    normalization = controls["invalid-normalization"].replace(
        "BridgeControls.invalidNormalization", "BridgeEnvironments.validNormalization").replace(
        "mass _ := 1", "mass x := if x then 1 else 0").replace(
        "nonneg _ := by norm_num", "nonneg x := by cases x <;> norm_num")
    correct = controls["wrong-posterior"].replace(
        "BridgeControls.wrongPosterior", "BridgeEnvironments.correctPosterior").replace(
        f"false = {_real(posterior[0] + 1)}", f"false = {_real(posterior[0])}")
    checked = controls["admitted-proof"].replace(
        "BridgeControls.admittedProof", "BridgeEnvironments.checkedProof").replace(
        ": False := by sorry", ": True := by exact True.intro")
    return (("invalid-normalization", normalization, ("BridgeEnvironments.validNormalization",)),
            ("wrong-posterior", correct, ("BridgeEnvironments.correctPosterior",)),
            ("admitted-proof", checked, ("BridgeEnvironments.checkedProof",)))


def _axioms(text: str, names: tuple[str, ...]) -> None:
    lines = text.splitlines()
    if len(lines) != len(names):
        raise BridgeError("Lean declaration-axiom inventory differs")
    for line, name in zip(lines, names, strict=True):
        match = re.fullmatch(rf"'{re.escape(name)}' (.*)", line)
        if match is None:
            raise BridgeError(f"Missing or reordered Lean axiom report: {name}")
        report = match[1]
        if report == "does not depend on any axioms":
            continue
        parsed = re.fullmatch(r"depends on axioms: \[(.*)\]", report)
        if parsed is None or set(parsed[1].split(", ")) - {"propext", "Classical.choice", "Quot.sound"}:
            raise BridgeError(f"Unapproved Lean declaration axioms: {name}")


def _inventory(directory: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in ("lean-base", "lean"):
        subtree = checked_source_path(directory / name)
        for path in sorted(subtree.rglob("*")):
            checked_source_path(path)
            if not path.is_dir():
                result[path.relative_to(directory).as_posix()] = sha256(read_regular(path)).hexdigest()
    return result


def _commands(compiler: str, campaign: Path) -> tuple[tuple[str, ...], ...]:
    lean = campaign / "lean"
    source = lean / "BridgeWitnesses.lean"
    return ((compiler, *OPTIONS, "-o", str(lean / "BridgeWitnesses.olean"), str(source)),
            (compiler, "--deps", str(source)))


def _control_command(compiler: str, source: Path) -> tuple[str, ...]:
    return compiler, *OPTIONS, str(source)


def _accepted_command(command: tuple[str, ...], lean: Path, environment: dict[str, str],
                      log: Path) -> tuple[LeanCommand, str]:
    started = perf_counter()
    text = _compile(list(command), lean, environment, LEAN_TIMEOUT_SECONDS, log)
    elapsed = perf_counter() - started
    receipt = LeanCommand(command=command, returncode=0,
                          timeout_seconds=LEAN_TIMEOUT_SECONDS, elapsed_seconds=elapsed,
                          log=f"lean/logs/{log.name}", log_sha256=sha256(log.read_bytes()).hexdigest())
    return receipt, text


def _control_diagnostic(source: Path, generated: str, output: str) -> None:
    """Require the pinned compiler's intended proof failure, with no other errors."""
    names = {"invalid-normalization": "invalidNormalization",
             "wrong-posterior": "wrongPosterior", "admitted-proof": "admittedProof"}
    if source.stem not in names:
        raise BridgeError("Unknown Lean control diagnostic")
    admitted = source.stem == "admitted-proof"
    offset = (generated.index("theorem ") + len("theorem ") if admitted else
              generated.rindex(":= by") + len(":= "))
    line = generated.count("\n", 0, offset) + 1
    column = offset - generated.rfind("\n", 0, offset) - 1
    message = "declaration uses `sorry`" if admitted else "unsolved goals\n⊢ False"
    pattern = (rf"{re.escape(str(source))}:{line}:{column}: error: {re.escape(message)}\n"
               rf"'BridgeControls\.{names[source.stem]}' depends on axioms: \[([^\]\n]+)\]")
    match = re.fullmatch(pattern, output.strip())
    if match is None:
        raise BridgeError(f"Lean control rejection diagnostic differs: {source.stem}")
    axioms = match[1].split(", ")
    allowed = {"sorryAx"} if admitted else {"sorryAx", "propext", "Classical.choice", "Quot.sound"}
    if "sorryAx" not in axioms or set(axioms) - allowed or len(axioms) != len(set(axioms)):
        raise BridgeError(f"Lean control rejection axioms differ: {source.stem}")


def _rejected_control(command: tuple[str, ...], lean: Path,
                      environment: dict[str, str]) -> LeanCommand:
    log = lean / "logs" / f"{Path(command[-1]).stem}.log"
    started = perf_counter()
    try:
        result = subprocess.run(command, cwd=lean, env=environment, capture_output=True,
                                text=True, timeout=LEAN_TIMEOUT_SECONDS, check=False)
    except subprocess.TimeoutExpired as error:
        log.write_bytes((error.stdout or b"") + (error.stderr or b"")
                        + f"\nLean control exceeded {LEAN_TIMEOUT_SECONDS} seconds\n".encode())
        raise BridgeError(f"Lean control timed out; see {log}") from error
    elapsed = perf_counter() - started
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 1:
        raise BridgeError(f"Lean control did not produce a rejected elaboration: {log}")
    _control_diagnostic(Path(command[-1]), read_regular(Path(command[-1])).decode(),
                        result.stdout + result.stderr)
    return LeanCommand(command=command, returncode=result.returncode,
                       timeout_seconds=LEAN_TIMEOUT_SECONDS, elapsed_seconds=elapsed,
                       log=f"lean/logs/{log.name}", log_sha256=sha256(log.read_bytes()).hexdigest())


def compile_witnesses(root: Path, output: Path, study: BridgeStudy) -> LeanEvidence:
    """Run later under native admission; canonical sources and caches remain read-only."""
    source = lean_source(study)
    root = checked_source_path(root)
    repo = checked_source_path(Path(os.environ.get("RIKISHI_FEP_REPO", str(
        root.parents[2] / "ActiveInferenceInstitute/Public/fep_formal"))))
    compiler = checked_source_path(Path(os.environ.get("RIKISHI_LEAN", str(
        root.parents[3] / "Local/runtimes/elan/toolchains/leanprover--lean4---v4.35.0/bin/lean"))))
    output = output.absolute()
    checked_source_path(output if output.exists() else output.parent)
    if any(output.is_relative_to(p) or p.is_relative_to(output)
           for p in (repo, compiler.parent.parent)):
        raise BridgeError("Lean campaign overlaps canonical inputs")
    if any((output / name).exists() or (output / name).is_symlink()
           for name in ("lean-base", "lean")):
        raise BridgeError("Lean campaign output is already occupied")
    output.mkdir(exist_ok=True)
    base_started = perf_counter()
    base = verify_formalization(repo, compiler, output / "lean-base", revision=PIN,
                                timeout=LEAN_TIMEOUT_SECONDS)
    base_elapsed = perf_counter() - base_started
    for name in PINNED_METADATA:
        (output / "lean-base" / name).write_bytes(_git(repo, "show", f"{PIN}:lean/{name}"))
    lean = output / "lean"
    lean.mkdir()
    for directory in ("logs", "controls", "environments", "home", "tmp"):
        (lean / directory).mkdir()
    (lean / "BridgeWitnesses.lean").write_text(source, encoding="utf-8")
    libraries = [Path(path) for path in base["dependency_cache_sha256"]]
    # The verifier just checked this complete after-snapshot against its baseline.
    # Reuse that boundary; the full after-snapshot below still guards this phase.
    before = dict(base["dependency_cache_sha256"])
    count = base["dependency_cache_files"]
    environment = {"PATH": str(compiler.parent) + os.pathsep + os.defpath,
                   "HOME": str(lean / "home"), "TMPDIR": str(lean / "tmp"),
                   "LEAN_PATH": os.pathsep.join(map(str, [lean, output / "lean-base/lib",
                        *[p for p in libraries if p != compiler.parent.parent / "lib/lean"]]))}
    commands: list[LeanCommand] = []
    texts: list[str] = []
    for index, command in enumerate(_commands(str(compiler), output)):
        log = lean / "logs" / ("witnesses.log", "dependencies.log")[index]
        receipt, text = _accepted_command(command, lean, environment, log)
        texts.append(text)
        commands.append(receipt)
    _axioms(texts[0], declarations(study))
    imports: dict[str, str] = {}
    for line in texts[1].splitlines():
        artifact = checked_source_path(Path(line))
        for path in (artifact, Path(str(artifact) + ".private"), Path(str(artifact) + ".server")):
            if path.exists():
                imports[str(checked_source_path(path))] = sha256(read_regular(path)).hexdigest()
    controls: list[LeanControl] = []
    environments: list[LeanEnvironment] = []
    for (identity, text), (environment_id, good, names) in zip(
            control_sources(study), environment_sources(study), strict=True):
        if identity != environment_id:
            raise BridgeError("Lean control and environment order differs")
        good_path = lean / "environments" / f"{identity}.lean"
        good_path.write_text(good, encoding="utf-8")
        positive, axioms = _accepted_command(_control_command(str(compiler), good_path), lean,
                                             environment, lean / "logs" / f"{identity}-environment.log")
        _axioms(axioms, names)
        environments.append(LeanEnvironment(id=identity,
                            source=f"lean/environments/{identity}.lean",
                            source_sha256=sha256(good.encode()).hexdigest(), command=positive,
                            declarations=names, declaration_axioms=axioms))
        path = lean / "controls" / f"{identity}.lean"
        path.write_text(text, encoding="utf-8")
        command = _rejected_control(_control_command(str(compiler), path), lean, environment)
        controls.append(LeanControl(id=identity, source=f"lean/controls/{path.name}",
                        source_sha256=sha256(path.read_bytes()).hexdigest(), command=command,
                        rejected=True))
    after, after_count = _cache_snapshot(libraries)
    _require_stable_cache(before, after)
    if count != after_count or count != base["dependency_cache_files"]:
        raise BridgeError("Lean dependency cache inventory changed")
    if sha256(read_regular(compiler)).hexdigest() != base["compiler_sha256"]:
        raise BridgeError("Lean compiler changed during witness compilation")
    dependencies = _Dependencies(imports=imports, cache_sha256=after, cache_files=count,
                                 compiler_sha256=base["compiler_sha256"])
    (lean / "dependencies.json").write_text(dependencies.model_dump_json(indent=2) + "\n")
    evidence = LeanEvidence(
        revision=PIN, source="lean/BridgeWitnesses.lean", source_sha256=sha256(source.encode()).hexdigest(),
        declarations=declarations(study), declaration_axioms=texts[0], commands=tuple(commands),
        controls=tuple(controls), environments=tuple(environments), artifacts=_inventory(output),
        base_timeout_seconds=LEAN_TIMEOUT_SECONDS, base_elapsed_seconds=base_elapsed,
        base_receipt_sha256=sha256((output / "lean-base/verification.json").read_bytes()).hexdigest(),
        compiler_sha256=base["compiler_sha256"], scope=SCOPE)
    validate_lean(output, study, evidence)
    return evidence


def validate_lean(directory: Path, study: BridgeStudy, evidence: LeanEvidence) -> None:
    """Check retained consistency without subprocesses or original live dependencies."""
    directory = checked_source_path(directory)
    artifacts = _inventory(directory)
    if artifacts != evidence.artifacts or any(not re.fullmatch(r"[0-9a-f]{64}", d)
                                               for d in artifacts.values()):
        raise BridgeError("Lean artifact inventory or hashes differ")
    source = lean_source(study)
    if (evidence.revision != PIN or evidence.scope != SCOPE
            or evidence.source != "lean/BridgeWitnesses.lean"
            or evidence.source_sha256 != sha256(source.encode()).hexdigest()
            or read_regular(directory / evidence.source) != source.encode()
            or evidence.declarations != declarations(study)
            or evidence.base_timeout_seconds != LEAN_TIMEOUT_SECONDS
            or not isfinite(evidence.base_elapsed_seconds)):
        raise BridgeError("Lean generated source, declarations or boundary differs")
    raw = read_regular(directory / "lean-base/verification.json")
    base = BASE_ADAPTER.validate_json(raw, strict=True)
    if (sha256(raw).hexdigest() != evidence.base_receipt_sha256 or base["commit"] != PIN
            or base["compiler_sha256"] != evidence.compiler_sha256
            or not re.fullmatch(r"[0-9a-f]{64}", evidence.compiler_sha256)
            or not base["compiler_version"].startswith("Lean (version 4.35.0,")):
        raise BridgeError("Lean base receipt, pin or compiler binding differs")
    _validate_base(directory, base)
    original = Path(base["workspace"]).parent
    if (not Path(base["workspace"]).is_absolute() or Path(base["workspace"]).name != "lean-base"
            or not Path(base["compiler"]).is_absolute()
            or tuple(c.command for c in evidence.commands) != _commands(base["compiler"], original)
            or tuple(c.log for c in evidence.commands) !=
                ("lean/logs/witnesses.log", "lean/logs/dependencies.log")
            or any(c.returncode != 0 for c in evidence.commands)):
        raise BridgeError("Lean successful commands differ")
    _axioms(evidence.declaration_axioms, declarations(study))
    if read_regular(directory / evidence.commands[0].log).decode() != evidence.declaration_axioms:
        raise BridgeError("Lean axiom log differs")
    expected_environments = environment_sources(study)
    if tuple(e.id for e in evidence.environments) != tuple(e[0] for e in expected_environments):
        raise BridgeError("Lean environment inventory differs")
    for retained, (identity, text, names) in zip(evidence.environments, expected_environments,
                                                strict=True):
        path = f"lean/environments/{identity}.lean"
        if (retained.source != path or retained.source_sha256 != sha256(text.encode()).hexdigest()
                or read_regular(directory / path) != text.encode()
                or retained.declarations != names
                or retained.command.command != _control_command(base["compiler"], original / path)
                or retained.command.log != f"lean/logs/{identity}-environment.log"
                or retained.command.returncode != 0
                or read_regular(directory / retained.command.log).decode() != retained.declaration_axioms):
            raise BridgeError(f"Lean positive environment differs: {identity}")
        _axioms(retained.declaration_axioms, names)
    expected = control_sources(study)
    if tuple(c.id for c in evidence.controls) != tuple(i for i, _ in expected):
        raise BridgeError("Lean control inventory differs")
    for control, (identity, text) in zip(evidence.controls, expected, strict=True):
        path = f"lean/controls/{identity}.lean"
        if (control.source != path or control.source_sha256 != sha256(text.encode()).hexdigest()
                or read_regular(directory / path) != text.encode() or not control.rejected
                or control.command.command != _control_command(base["compiler"], original / path)
                or control.command.log != f"lean/logs/{identity}.log"
                or control.command.returncode != 1):
            raise BridgeError(f"Lean rejected control differs: {identity}")
        log = read_regular(directory / control.command.log).decode()
        _control_diagnostic(original / path, text, log)
    for command in (*evidence.commands, *(e.command for e in evidence.environments),
                    *(c.command for c in evidence.controls)):
        if (artifacts.get(command.log) != command.log_sha256
                or command.timeout_seconds != LEAN_TIMEOUT_SECONDS
                or not isfinite(command.elapsed_seconds) or command.timed_out):
            raise BridgeError("Lean command log digest or execution budget differs")
    _validate_dependencies(directory, base)


def _validate_base(directory: Path, base: CompilationReceipt) -> None:
    """Bind original pinned bytes, base products and complete dependency metadata."""
    for name, digest in PINNED_SOURCES.items():
        relative = f"lean-base/{name.removeprefix('lean/')}"
        if base["source_sha256"].get(name) != digest or sha256(
                read_regular(directory / relative)).hexdigest() != digest:
            raise BridgeError("Retained finite module differs from committed pin")
    for name, digest in PINNED_METADATA.items():
        if sha256(read_regular(directory / "lean-base" / name)).hexdigest() != digest:
            raise BridgeError("Retained Lean manifest or toolchain differs from committed pin")
    expected_audit = "module\nimport FepSketches.finite_information\n" + "\n".join(
        f"#print axioms FEP.FiniteInformation.{name}" for name in (
            "finiteKL_nonneg", "finiteKL_self", "finiteKL_eq_crossEntropy_sub_entropy")) + "\n"
    if (read_regular(directory / "lean-base/DeclarationAudit.lean") != expected_audit.encode()
            or base["source_sha256"] != dict(PINNED_SOURCES, **{
                "generated/DeclarationAudit.lean": sha256(expected_audit.encode()).hexdigest()})):
        raise BridgeError("Lean base audit source differs")
    _axioms(base["declaration_axioms"], tuple(f"FEP.FiniteInformation.{name}" for name in (
        "finiteKL_nonneg", "finiteKL_self", "finiteKL_eq_crossEntropy_sub_entropy")))
    if read_regular(directory / "lean-base/declaration-axioms.log").decode() != base["declaration_axioms"]:
        raise BridgeError("Lean base axiom log differs")
    workspace, compiler = Path(base["workspace"]), base["compiler"]
    expected_commands: list[list[str]] = []
    for name in ("finite_probability", "finite_information"):
        source = str(workspace / f"FepSketches/{name}.lean")
        expected_commands.extend([[compiler, "-DwarningAsError=true", "-o",
            str(workspace / f"lib/FepSketches/{name}.olean"), source], [compiler, "--deps", source]])
    expected_commands.append([compiler, str(workspace / "DeclarationAudit.lean")])
    if base["commands"] != expected_commands:
        raise BridgeError("Lean base commands differ")
    required = {f"lib/FepSketches/{name}.olean{suffix}" for name in
                ("finite_probability", "finite_information") for suffix in ("", ".private", ".server")}
    if not required <= base["compiled_sha256"].keys():
        raise BridgeError("Lean base compiled products are incomplete")
    for relative, digest in base["compiled_sha256"].items():
        if (not relative.startswith("lib/FepSketches/") or ".." in Path(relative).parts
                or sha256(read_regular(checked_source_path(directory / "lean-base" / relative))).hexdigest()
                != digest):
            raise BridgeError("Retained Lean base product differs")
    for suffix in ("", ".private", ".server"):
        read_regular(directory / f"lean/BridgeWitnesses.olean{suffix}")


def _validate_dependencies(directory: Path, base: CompilationReceipt) -> None:
    """Validate hashes as retained observations, never as live dependency replay."""
    dependency = _Dependencies.model_validate_json(read_regular(directory / "lean/dependencies.json"))
    # The fixed manifest bytes bind this JSON shape; this parse never consults live checkouts.
    manifest = json.loads(read_regular(directory / "lean-base/lake-manifest.json"))
    revisions = {p["name"]: p["rev"] for p in manifest["packages"]}
    if (base["dependency_revisions"] != revisions or not base["import_artifacts_sha256"]
            or dependency.cache_sha256 != base["dependency_cache_sha256"]
            or dependency.cache_files != base["dependency_cache_files"]
            or dependency.cache_files <= 0 or len(dependency.cache_sha256) != len(revisions) + 1
            or dependency.compiler_sha256 != base["compiler_sha256"] or not dependency.imports):
        raise BridgeError("Lean dependency receipts differ or are incomplete")
    for observations in (dependency.imports, dependency.cache_sha256, base["import_artifacts_sha256"]):
        if any(not Path(p).is_absolute() or not re.fullmatch(r"[0-9a-f]{64}", d)
               for p, d in observations.items()):
            raise BridgeError("Lean dependency hash observations are malformed")
    imports = read_regular(directory / "lean/logs/dependencies.log").decode().splitlines()
    if not imports or not set(imports) <= dependency.imports.keys():
        raise BridgeError("Lean dependency log differs from recorded import hashes")
    workspace = Path(base["workspace"])
    primary = "lib/FepSketches/finite_information.olean"
    if str(workspace / primary) not in imports:
        raise BridgeError("Lean witness required finite_information import is missing")
    for suffix in ("", ".private", ".server"):
        relative = primary + suffix
        if (relative not in base["compiled_sha256"]
                or dependency.imports.get(str(workspace / relative)) != base["compiled_sha256"][relative]):
            raise BridgeError("Lean witness required finite_information artifact binding differs")
    for relative, digest in base["compiled_sha256"].items():
        original = str(workspace / relative)
        if original in dependency.imports and dependency.imports[original] != digest:
            raise BridgeError("Lean witness import differs from retained base artifact")
