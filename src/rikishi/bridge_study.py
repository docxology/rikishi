"""One declared rational manifest drives arithmetic, source kernels and Lean inputs."""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
from importlib.resources import files
from typing import Final

from pydantic import TypeAdapter

from rikishi.bridge_models import (
    BridgeError,
    BridgeStudy,
    DecimalValues,
    EnergyValues,
    FiniteWitness,
    NumericalWitness,
)
from rikishi.fep import PIN, free_energy
from rikishi.inference_models import InferenceCase, InferenceStudy, Scenario, SourceClaim
from rikishi.inference_study import cases as inference_cases
from rikishi.kif import parse

AUTHORITY: Final = "data/fep-sumo-bridge-v1.json"
NUMERICAL: Final = TypeAdapter(tuple[NumericalWitness, ...])


def probabilities(values: tuple[str, str]) -> tuple[Fraction, Fraction]:
    """Parse canonical strictly positive rational masses without float conversion."""
    try:
        parsed = (Fraction(values[0]), Fraction(values[1]))
    except (ValueError, ZeroDivisionError) as error:
        raise BridgeError("Witness contains an invalid rational") from error
    if any(str(p) != raw or not 0 < p < 1 for raw, p in zip(values, parsed, strict=True)):
        raise BridgeError("Witness masses must be canonical rationals strictly between zero and one")
    return parsed


def catalog() -> BridgeStudy:
    """Read the versioned authority; catalog construction starts no native process."""
    study = BridgeStudy.model_validate_json(files("rikishi").joinpath(AUTHORITY).read_bytes())
    ids = [w.id for w in study.witnesses]
    namespaces = [w.namespace for w in study.witnesses]
    entities = [v for w in study.witnesses for v in w.entities.model_dump().values()]
    if (not 2 <= len(ids) <= 4 or len(set(ids)) != len(ids)
            or len(set(namespaces)) != len(namespaces) or len(set(entities)) != len(entities)
            or study.formal_revision != PIN):
        raise BridgeError("Witness identities or formal pin are invalid")
    for witness in study.witnesses:
        if sum(probabilities(witness.prior)) != 1 or sum(probabilities(witness.candidate)) != 1:
            raise BridgeError("Prior and candidate must be exactly normalized")
        probabilities(witness.likelihood)
    scenario_ids = [s.id for s in study.scenarios]
    if not scenario_ids or len(set(scenario_ids)) != len(scenario_ids):
        raise BridgeError("Scenario identities must be nonempty and unique")
    for witness in study.witnesses:
        roles = [s.role for s in study.scenarios if s.witness_id == witness.id]
        if sorted(roles) != ["calculation", "model", "representation", "result", "result"]:
            raise BridgeError("Every witness requires model, representation, calculation and two result scenarios")
    if any(s.witness_id not in ids for s in study.scenarios):
        raise BridgeError("Scenario refers to an undeclared witness")
    return study


def study_sha256(study: BridgeStudy) -> str:
    return sha256(study.model_dump_json().encode()).hexdigest()


def exact_posterior(witness: FiniteWitness) -> tuple[Fraction, tuple[Fraction, Fraction]]:
    """Exact Bayes calculation uses the same Bool order as generated Lean."""
    prior, likelihood = probabilities(witness.prior), probabilities(witness.likelihood)
    joint = (prior[0] * likelihood[0], prior[1] * likelihood[1])
    evidence = sum(joint, Fraction())
    return evidence, (joint[0] / evidence, joint[1] / evidence)


def decimal_reference(witness: FiniteWitness, precision: int) -> DecimalValues:
    """Independent direct rational-to-Decimal products and natural logarithms."""
    with localcontext() as context:
        context.prec = precision
        prior, likelihood, candidate = [
            [Decimal(p.numerator) / Decimal(p.denominator) for p in probabilities(values)]
            for values in (witness.prior, witness.likelihood, witness.candidate)
        ]
        joint = [p * l for p, l in zip(prior, likelihood, strict=True)]
        evidence = sum(joint, Decimal())
        posterior = [p / evidence for p in joint]
        energy = sum((q * (q / p).ln() for q, p in zip(candidate, joint, strict=True)), Decimal())
        kl = sum((q * (q / p).ln() for q, p in zip(candidate, posterior, strict=True)), Decimal())
        surprise = -evidence.ln()
        return DecimalValues(
            evidence=str(evidence), surprise=str(surprise), free_energy=str(energy),
            kl_to_posterior=str(kl), exact_posterior=(str(posterior[0]), str(posterior[1])),
            identity_residual=str(energy - surprise - kl))


def numerical_witness(witness: FiniteWitness, study: BridgeStudy) -> NumericalWitness:
    """Compare existing finite Python execution to an independent exact-input reference."""
    raw = free_energy(*[[float(p) for p in probabilities(values)] for values in (
        witness.prior, witness.likelihood, witness.candidate)])
    result = EnergyValues(
        evidence=raw["evidence"], surprise=raw["surprise"], free_energy=raw["free_energy"],
        kl_to_posterior=raw["kl_to_posterior"],
        exact_posterior=(raw["exact_posterior"][0], raw["exact_posterior"][1]),
        identity_residual=raw["identity_residual"])
    reference = decimal_reference(witness, study.decimal_precision)
    pairs = [(result.evidence, reference.evidence), (result.surprise, reference.surprise),
             (result.free_energy, reference.free_energy),
             (result.kl_to_posterior, reference.kl_to_posterior),
             *zip(result.exact_posterior, reference.exact_posterior, strict=True)]
    error = max(float(abs(Decimal.from_float(actual) - Decimal(expected)))
                for actual, expected in pairs)
    evidence, posterior = exact_posterior(witness)
    prior, likelihood = probabilities(witness.prior), probabilities(witness.likelihood)
    residuals = tuple(str(posterior[i] * evidence - prior[i] * likelihood[i]) for i in range(2))
    passed = (error <= study.tolerance and abs(result.identity_residual) <= study.tolerance
              and abs(Decimal(reference.identity_residual)) <= Decimal(str(study.tolerance))
              and result.kl_to_posterior >= -study.tolerance
              and result.free_energy + study.tolerance >= result.surprise
              and all(value == "0" for value in residuals))
    return NumericalWitness(
        witness_id=witness.id, input=witness, evidence=str(evidence),
        exact_posterior=(str(posterior[0]), str(posterior[1])), result=result, reference=reference,
        max_reference_error=error, reconstruction_residuals=(residuals[0], residuals[1]),
        tolerance=study.tolerance, passed=passed)


def numerical(study: BridgeStudy) -> tuple[NumericalWitness, ...]:
    return tuple(numerical_witness(witness, study) for witness in study.witnesses)


def mass_facts(witness: FiniteWitness) -> tuple[str, ...]:
    """KIF numbers are uninterpreted exact-input labels, never arithmetic axioms."""
    _, posterior = exact_posterior(witness)
    rows = (("Prior", probabilities(witness.prior)),
            ("Likelihood", probabilities(witness.likelihood)),
            ("Candidate", probabilities(witness.candidate)), ("Posterior", posterior))
    return tuple(
        f"(bridgeRationalMass {witness.entities.model} Bridge{role} BridgeState{index} "
        f"{mass.numerator} {mass.denominator})"
        for role, masses in rows for index, mass in enumerate(masses))


def extension(study: BridgeStudy) -> str:
    """Preserve the entire authored interpretation separately from upstream formulas."""
    facts = list(study.local_rules)
    facts.extend(a for scenario in study.scenarios for a in scenario.assumptions)
    facts.extend(a for witness in study.witnesses for a in mass_facts(witness))
    return "\n".join(dict.fromkeys(facts)) + "\n"


def derive_source_claims(study: BridgeStudy, source: bytes) -> tuple[SourceClaim, ...]:
    if sha256(source).hexdigest() != study.source_sha256:
        raise BridgeError("Complete SUMO bytes differ from the authority")
    formulas = {f.line: f for f in parse(source.decode("utf-8"), study.source_path)}
    selected = {s.line for scenario in study.scenarios for s in scenario.selections}
    claims: list[SourceClaim] = []
    for line in sorted(selected | set(study.context_lines)):
        if line not in formulas:
            raise BridgeError(f"Source selector is not a complete formula: {line}")
        formula = formulas[line]
        claims.append(SourceClaim(source_path=study.source_path, line=line,
                                  end_line=line + formula.text.count("\n"), raw_kif=formula.text,
                                  sha256=sha256(formula.text.encode()).hexdigest()))
    return tuple(claims)


def cases(study: BridgeStudy, claims: tuple[SourceClaim, ...]) -> tuple[InferenceCase, ...]:
    """Use the existing strict compiler and five-control experiment generator unchanged."""
    witnesses = {w.id: w for w in study.witnesses}
    scenarios: list[Scenario] = [s.model_copy(update={"assumptions": [*s.assumptions,
                  *mass_facts(witnesses[s.witness_id])]}) for s in study.scenarios]
    adapter = InferenceStudy(
        schema_version=1, study_id=study.study_id, source_path=study.source_path,
        source_sha256=study.source_sha256, source_commit=study.source_commit,
        lock_sha256=study.lock_sha256, source_url="https://github.com/ontologyportal/sumo",
        semantic_scope=study.semantic_scope, supported_syntax=[], scenarios=scenarios)
    return tuple(inference_cases(adapter, list(claims)))
