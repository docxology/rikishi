import json
import math
from importlib.resources import files
from pathlib import Path

import pytest
from pydantic import JsonValue, ValidationError

from rikishi.fep import DemoParameters, demo, load_demo_parameters


@pytest.fixture
def model_document() -> dict[str, JsonValue]:
    return {
        "prior": [0.25, 0.75],
        "likelihood": [0.9, 0.1],
        "candidate": [0.6, 0.4],
        "scan_points": 9,
        "state_labels": ["left", "right"],
    }


@pytest.fixture
def parameters_path(tmp_path: Path, model_document: dict[str, JsonValue]) -> Path:
    path = tmp_path / "model.json"
    path.write_text(json.dumps(model_document), encoding="utf-8")
    return path


def test_packaged_authority_is_used_by_default_demo() -> None:
    # Given the installed package resource, independently of the checkout path.
    authority = files("rikishi").joinpath("data", "fep-example.json").read_text("utf-8")
    # When default parameters are loaded.
    parameters = load_demo_parameters()
    # Then the full model agrees with its sole authority and the default call.
    assert json.loads(parameters.model_dump_json()) == json.loads(authority)
    assert demo() == demo(parameters)


def test_changed_json_model_reaches_calculations(parameters_path: Path) -> None:
    # Given a model with different prior, likelihood, candidate and labels.
    parameters = load_demo_parameters(parameters_path)
    # When the configured demo is calculated.
    result = demo(parameters)
    # Then independent joint masses 0.225 and 0.075 determine the result.
    assert parameters.state_labels == ("left", "right")
    assert result["prior"] == [0.25, 0.75]
    assert result["likelihood"] == [0.9, 0.1]
    assert result["candidate"] == [0.6, 0.4]
    assert result["result"]["evidence"] == pytest.approx(0.3)
    assert result["result"]["exact_posterior"] == pytest.approx([0.75, 0.25])
    assert result["result"]["free_energy"] == pytest.approx(
        0.6 * math.log(0.6 / 0.225) + 0.4 * math.log(0.4 / 0.075)
    )
    assert result["optimum"]["free_energy"] == pytest.approx(-math.log(0.3))
    assert result["optimum"]["kl_to_posterior"] == pytest.approx(0)


@pytest.mark.parametrize("scan_points", [2, 9, 14])
def test_changed_json_count_and_model_reach_entire_curve(
    tmp_path: Path, model_document: dict[str, JsonValue], scan_points: int
) -> None:
    # Given a real configuration with a count different from the packaged count.
    model_document["scan_points"] = scan_points
    path = tmp_path / "curve.json"
    path.write_text(json.dumps(model_document), encoding="utf-8")
    parameters = load_demo_parameters(path)
    # When the full inclusive binary scan runs.
    scan = demo(parameters)["scan"]
    # Then every configured point follows the independently known joint model.
    assert len(scan) == scan_points
    for index, point in enumerate(scan):
        q = index / (scan_points - 1)
        expected = 0.0
        if q > 0:
            expected += q * math.log(q / 0.225)
        if q < 1:
            expected += (1 - q) * math.log((1 - q) / 0.075)
        assert point["q_state_zero"] == q
        assert point["free_energy"] == pytest.approx(expected)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("prior", [0.4, 0.4]),
        ("candidate", [0.4, 0.4]),
        ("candidate", [-0.1, 1.1]),
        ("likelihood", [1.1, 0.2]),
        ("likelihood", [float("nan"), 0.2]),
        ("likelihood", [float("inf"), 0.2]),
        ("likelihood", [0.0, 0.0]),
        ("prior", [True, 0.0]),
        ("likelihood", ["0.9", 0.1]),
        ("candidate", None),
        ("scan_points", 0),
        ("scan_points", 1),
        ("scan_points", -1),
        ("scan_points", True),
        ("scan_points", 9.0),
        ("scan_points", "9"),
        ("scan_points", None),
        ("state_labels", ["left", "left"]),
        ("state_labels", ["", "right"]),
        ("state_labels", ["left", "  "]),
        ("state_labels", ["left", 1]),
    ],
)
def test_invalid_configuration_is_rejected_without_fallback(
    tmp_path: Path, model_document: dict[str, JsonValue], field: str, value: JsonValue
) -> None:
    # Given a real JSON file containing a malformed value.
    model_document[field] = value
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(model_document), encoding="utf-8")
    # When the file crosses the model boundary, then it fails explicitly.
    with pytest.raises(ValidationError):
        load_demo_parameters(path)


@pytest.mark.parametrize("field", ["prior", "likelihood", "candidate", "state_labels"])
@pytest.mark.parametrize("length", [0, 1, 3])
def test_binary_dimension_is_required(
    tmp_path: Path, model_document: dict[str, JsonValue], field: str, length: int
) -> None:
    # Given an otherwise valid configuration with a nonbinary vector.
    model_document[field] = ["state"] * length if field == "state_labels" else [1 / 3] * length
    path = tmp_path / "dimension.json"
    path.write_text(json.dumps(model_document), encoding="utf-8")
    # When loading the binary demo, then nonbinary models are rejected.
    with pytest.raises(ValidationError):
        load_demo_parameters(path)


@pytest.mark.parametrize("zero_field", ["prior", "likelihood"])
def test_supported_candidate_cannot_hide_unsupported_scan_endpoint(
    tmp_path: Path, model_document: dict[str, JsonValue], zero_field: str
) -> None:
    # Given a finite supported candidate but a zero joint mass at the other state.
    model_document[zero_field] = [0.0, 1.0]
    model_document["candidate"] = [0.0, 1.0]
    path = tmp_path / "support.json"
    path.write_text(json.dumps(model_document), encoding="utf-8")
    # When validating the inclusive scan, then its infinite endpoint is refused.
    with pytest.raises(ValidationError, match="positive joint support"):
        load_demo_parameters(path)


def test_positive_underflowed_joint_mass_keeps_finite_scan(
    tmp_path: Path, model_document: dict[str, JsonValue]
) -> None:
    model_document["prior"] = [1e-300, 1.0]
    model_document["likelihood"] = [1e-300, 0.5]
    model_document["candidate"] = [0.0, 1.0]
    path = tmp_path / "underflow.json"
    path.write_text(json.dumps(model_document), encoding="utf-8")
    parameters = load_demo_parameters(path)
    result = demo(parameters)
    assert result["scan"][-1]["free_energy"] == pytest.approx(-2 * math.log(1e-300))
    assert all(math.isfinite(point["free_energy"]) for point in result["scan"])


@pytest.mark.parametrize("text", ["{", "[]", "null", "{}"])
def test_malformed_or_incomplete_json_is_rejected(tmp_path: Path, text: str) -> None:
    # Given malformed, nonobject or incomplete real JSON input.
    path = tmp_path / "invalid.json"
    path.write_text(text, encoding="utf-8")
    # When loading, then the packaged example does not silently replace it.
    with pytest.raises(ValidationError):
        load_demo_parameters(path)


def test_unknown_configuration_field_is_rejected(
    tmp_path: Path, model_document: dict[str, JsonValue]
) -> None:
    # Given a typo beside the otherwise valid model.
    model_document["scan_point"] = 5
    path = tmp_path / "unknown.json"
    path.write_text(json.dumps(model_document), encoding="utf-8")
    # When loading, then an unrecognized setting fails explicitly.
    with pytest.raises(ValidationError, match="extra_forbidden"):
        load_demo_parameters(path)


def test_missing_configuration_is_not_replaced_with_defaults(tmp_path: Path) -> None:
    # Given a missing explicit configuration file.
    path = tmp_path / "missing.json"
    # When loading, then the original filesystem failure is preserved.
    with pytest.raises(FileNotFoundError):
        load_demo_parameters(path)


def test_direct_constructor_checks_the_real_model() -> None:
    # Given well-typed values with an unnormalized prior.
    # When constructing directly, then bypassing JSON does not bypass validation.
    with pytest.raises(ValidationError, match="prior must sum to one"):
        DemoParameters(
            prior=(0.25, 0.25),
            likelihood=(0.9, 0.1),
            candidate=(0.6, 0.4),
            scan_points=9,
            state_labels=("left", "right"),
        )


def test_zero_candidate_mass_and_unnormalized_likelihood_are_valid(
    parameters_path: Path,
) -> None:
    # Given a valid model and a candidate on the boundary of its positive support.
    parameters = load_demo_parameters(parameters_path)
    candidate = parameters.model_copy(
        update={"candidate": (0.0, 1.0), "likelihood": (0.9, 0.2)}
    )
    # When calculating it, then no likelihood normalization or strict q positivity is added.
    result = demo(candidate)
    assert result["result"]["free_energy"] == pytest.approx(-math.log(0.15))


def test_demo_rejects_an_unvalidated_model_copy(parameters_path: Path) -> None:
    # Given Pydantic's explicit validation-bypassing copy API.
    parameters = load_demo_parameters(parameters_path)
    invalid = parameters.model_copy(update={"scan_points": 1})
    # When passing it into the public demo boundary, then invalid settings are refused.
    with pytest.raises(ValidationError):
        demo(invalid)
