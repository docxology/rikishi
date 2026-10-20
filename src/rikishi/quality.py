"""Evaluate measured line and branch coverage without hiding unmeasured source files."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CoverageError(ValueError):
    pass


class Counts(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)
    num_statements: int = Field(ge=0)
    covered_lines: int = Field(ge=0)
    num_branches: int = Field(ge=0)
    covered_branches: int = Field(ge=0)

    @model_validator(mode="after")
    def check_denominators(self) -> Counts:
        if self.covered_lines > self.num_statements or self.covered_branches > self.num_branches:
            raise CoverageError("Covered counts cannot exceed measured denominators")
        return self


class FileCoverage(BaseModel):
    model_config = ConfigDict(frozen=True)
    summary: Counts
    excluded_lines: list[int] = Field(default_factory=list)


class CoverageDocument(BaseModel):
    model_config = ConfigDict(frozen=True)
    files: dict[str, FileCoverage]


class Policy(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    core_floor: float = Field(ge=90, le=100)
    infrastructure_floor: float = Field(ge=60, le=100)
    infrastructure: list[str]


@dataclass(frozen=True, slots=True)
class ScopeCoverage:
    files: tuple[str, ...]
    covered_lines: int
    statements: int
    covered_branches: int
    branches: int
    floor: float

    @property
    def percent(self) -> float:
        denominator = self.statements + self.branches
        return 100 * (self.covered_lines + self.covered_branches) / denominator if denominator else 100

    @property
    def passed(self) -> bool:
        return self.percent >= self.floor


@dataclass(frozen=True, slots=True)
class CoverageReport:
    core: ScopeCoverage
    infrastructure: ScopeCoverage

    @property
    def passed(self) -> bool:
        return self.core.passed and self.infrastructure.passed

    def to_dict(self) -> dict[str, dict[str, tuple[str, ...] | int | float | bool] | bool]:
        return {
            "passed": self.passed,
            "core": {**asdict(self.core), "percent": self.core.percent, "passed": self.core.passed},
            "infrastructure": {**asdict(self.infrastructure), "percent": self.infrastructure.percent,
                               "passed": self.infrastructure.passed},
        }


def evaluate_coverage(root: Path, coverage_path: Path, policy_path: Path) -> CoverageReport:
    """Gate covered lines plus covered branches against explicit per-scope denominators.

    Every package Python file must occur in the report. Unknown new modules enter
    the core scope; only exact policy paths enter the infrastructure scope.
    """
    root = root.resolve(strict=True)
    policy = Policy.model_validate(tomllib.loads(policy_path.read_text(encoding="utf-8")))
    document = CoverageDocument.model_validate_json(coverage_path.read_bytes())
    expected = {p.relative_to(root).as_posix() for p in (root / "src/rikishi").rglob("*.py")}
    if not expected:
        raise CoverageError("No package Python source files found under src/rikishi")
    infrastructure = set(policy.infrastructure)
    if len(infrastructure) != len(policy.infrastructure) or not infrastructure <= expected:
        raise CoverageError("Infrastructure policy contains duplicate or nonexistent source paths")
    measured: dict[str, Counts] = {}
    for filename, observation in document.files.items():
        path = Path(filename)
        resolved = (path if path.is_absolute() else root / path).resolve()
        if not resolved.is_relative_to(root):
            raise CoverageError(f"Coverage path escapes project: {filename}")
        relative = resolved.relative_to(root).as_posix()
        if relative in measured or relative not in expected:
            raise CoverageError(f"Unexpected or duplicated measured source: {filename}")
        if observation.excluded_lines:
            raise CoverageError(f"Excluded source lines are not admitted by this gate: {filename}")
        measured[relative] = observation.summary
    missing = expected - measured.keys()
    if missing:
        raise CoverageError(f"Unmeasured source files: {', '.join(sorted(missing))}")

    def scope(paths: set[str], floor: float) -> ScopeCoverage:
        return ScopeCoverage(tuple(sorted(paths)),
                             sum(measured[p].covered_lines for p in paths),
                             sum(measured[p].num_statements for p in paths),
                             sum(measured[p].covered_branches for p in paths),
                             sum(measured[p].num_branches for p in paths), floor)

    return CoverageReport(scope(expected - infrastructure, policy.core_floor),
                          scope(infrastructure, policy.infrastructure_floor))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check complete core and infrastructure coverage")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--coverage", type=Path, default=Path("output/coverage.json"))
    parser.add_argument("--policy", type=Path, default=Path("config/coverage.toml"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = evaluate_coverage(args.root, args.root / args.coverage, args.root / args.policy)
    except (OSError, ValueError) as error:
        sys.stderr.write(f"Coverage gate error: {error}\n")
        return 1
    payload = json.dumps(report.to_dict(), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    return 0 if report.passed else 1
