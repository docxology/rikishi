"""Independent finite arithmetic and rejected probability-domain controls."""

import math
from pathlib import Path

import pytest

from rikishi.fep import (
    DECLARATIONS,
    SOURCE,
    ProbabilityError,
    demo,
    free_energy,
    inspect_formalization,
)


def test_binary_energy_matches_independent_values():
    result = free_energy([0.5, 0.5], [0.8, 0.2], [0.5, 0.5])
    assert result["evidence"] == pytest.approx(0.5)
    assert result["free_energy"] == pytest.approx(0.916290731874155)
    assert result["surprise"] == pytest.approx(math.log(2))
    assert result["kl_to_posterior"] == pytest.approx(math.log(1.25))
    assert abs(result["identity_residual"]) < 1e-14


def test_demo_minimizes_at_exact_posterior():
    result = demo()
    assert result["optimum"]["free_energy"] == pytest.approx(math.log(2))
    assert result["optimum"]["kl_to_posterior"] == pytest.approx(0)
    assert min(result["scan"], key=lambda x: x["free_energy"])["q_state_zero"] == 0.8


@pytest.mark.parametrize(
    ("prior", "likelihood", "q"),
    [
        ([], [], []),
        ([0.4, 0.4], [0.8, 0.2], [0.5, 0.5]),
        ([0.5, 0.5], [float("nan"), 0.2], [0.5, 0.5]),
        ([0.5, 0.5], [1.1, 0.2], [0.5, 0.5]),
        ([0.5, 0.5], [0.8, 0.2], [-0.1, 1.1]),
        ([0.5, 0.5], [0.8], [0.5, 0.5]),
        ([0.5, 0.5], [0, 0], [0.5, 0.5]),
        ([0.5, 0.5], [0, 1], [0.5, 0.5]),
        ([0.5, 0.5], [0.8, 0.2], [1]),
    ],
)
def test_invalid_models_are_rejected(prior, likelihood, q):
    with pytest.raises(ProbabilityError):
        free_energy(prior, likelihood, q)


def test_zero_candidate_mass_is_well_defined():
    assert free_energy([0, 1], [0, 1], [0, 1])["free_energy"] == 0


def test_missing_formalization_is_rejected(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        inspect_formalization(tmp_path / "absent")


@pytest.mark.parametrize("missing", [False, True])
def test_committed_source_is_inspected_and_missing_declarations_fail(
    tmp_path: Path, missing: bool, git_commit
):
    source = tmp_path / SOURCE
    source.parent.mkdir(parents=True)
    names = DECLARATIONS[:-1] if missing else DECLARATIONS
    source.write_text("\n".join(f"theorem {name} : True := by trivial" for name in names))
    git_commit(tmp_path)
    if missing:
        with pytest.raises(ProbabilityError, match="expected exactly one"):
            inspect_formalization(tmp_path, "HEAD")
    else:
        source.write_text("dirty working content must not become pinned evidence")
        result = inspect_formalization(tmp_path, "HEAD")
        assert len(result["declarations"]) == 3
        assert result["declarations"][0]["line"] == 1
        assert result["commit"] in result["declarations"][0]["url"]
        assert result["working_tree_clean"] is False
