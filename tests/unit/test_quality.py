import json

import pytest

from rikishi.quality import CoverageError, evaluate_coverage, main


@pytest.fixture
def coverage_fixture(tmp_path):
    package = tmp_path / "src/rikishi"
    package.mkdir(parents=True)
    for name in ("core.py", "native.py"):
        (package / name).write_text("value = 1\n")
    policy = tmp_path / "coverage.toml"
    policy.write_text('core_floor = 90.0\ninfrastructure_floor = 60.0\n'
                      'infrastructure = ["src/rikishi/native.py"]\n')
    report = tmp_path / "coverage.json"
    data = {"files": {
        "src/rikishi/core.py": {"summary": {"num_statements": 8, "covered_lines": 8,
                                          "num_branches": 2, "covered_branches": 1}},
        "src/rikishi/native.py": {"summary": {"num_statements": 5, "covered_lines": 3,
                                            "num_branches": 0, "covered_branches": 0}},
    }}
    report.write_text(json.dumps(data))
    return tmp_path, policy, report, data


def test_scope_denominators_and_cli_receipt(coverage_fixture, capsys):
    root, policy, path, _ = coverage_fixture
    report = evaluate_coverage(root, path, policy)
    assert report.core.percent == 90
    assert report.infrastructure.percent == 60
    assert report.passed is True
    output = root / "receipts/gate.json"
    assert main(["--root", str(root), "--coverage", str(path), "--policy", str(policy),
                 "--output", str(output)]) == 0
    assert json.loads(output.read_text()) == json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("scope", ["core", "native"])
def test_failing_scope_cannot_be_hidden_by_other_scope(coverage_fixture, scope, capsys):
    root, policy, path, data = coverage_fixture
    data["files"][f"src/rikishi/{scope}.py"]["summary"]["covered_lines"] -= 1
    path.write_text(json.dumps(data))
    assert evaluate_coverage(root, path, policy).passed is False
    assert main(["--root", str(root), "--coverage", str(path), "--policy", str(policy)]) == 1
    assert json.loads(capsys.readouterr().out)["passed"] is False


@pytest.mark.parametrize("corruption", ["missing", "extra", "duplicate", "escape", "excluded",
                                        "negative", "denominator", "bad-json"])
def test_missing_or_invalid_observations_are_rejected(coverage_fixture, corruption):
    root, policy, path, data = coverage_fixture
    row = data["files"]["src/rikishi/core.py"]
    match corruption:
        case "missing":
            del data["files"]["src/rikishi/core.py"]
        case "extra":
            data["files"]["other.py"] = row
        case "duplicate":
            data["files"][str(root / "src/rikishi/core.py")] = row
        case "escape":
            data["files"]["../outside.py"] = row
        case "excluded":
            row["excluded_lines"] = [1]
        case "negative":
            row["summary"]["num_branches"] = -1
        case "denominator":
            row["summary"]["covered_branches"] = 3
        case "bad-json":
            path.write_text("{")
    if corruption != "bad-json":
        path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        evaluate_coverage(root, path, policy)


@pytest.mark.parametrize("paths", [
    '["src/rikishi/native.py", "src/rikishi/native.py"]', '["src/rikishi/missing.py"]',
])
def test_policy_cannot_silently_misclassify_files(coverage_fixture, paths):
    root, policy, path, _ = coverage_fixture
    policy.write_text(f"core_floor = 90.0\ninfrastructure_floor = 60.0\ninfrastructure = {paths}\n")
    with pytest.raises(CoverageError, match="duplicate or nonexistent"):
        evaluate_coverage(root, path, policy)


def test_new_module_defaults_to_core_and_empty_infrastructure_has_no_denominator(coverage_fixture):
    root, policy, path, data = coverage_fixture
    policy.write_text("core_floor = 90.0\ninfrastructure_floor = 60.0\ninfrastructure = []\n")
    data["files"]["src/rikishi/native.py"]["summary"]["covered_lines"] = 5
    path.write_text(json.dumps(data))
    report = evaluate_coverage(root, path, policy)
    assert report.core.statements == 13
    assert report.infrastructure.percent == 100
    assert report.infrastructure.files == ()


def test_main_reports_missing_inputs(coverage_fixture, capsys):
    root, policy, _, _ = coverage_fixture
    assert main(["--root", str(root), "--policy", str(policy)]) == 1
    assert "Coverage gate error" in capsys.readouterr().err


def test_empty_source_tree_cannot_produce_a_green_gate(tmp_path):
    policy = tmp_path / "coverage.toml"
    policy.write_text("core_floor = 90.0\ninfrastructure_floor = 60.0\ninfrastructure = []\n")
    report = tmp_path / "coverage.json"
    report.write_text('{"files": {}}')
    with pytest.raises(CoverageError, match="No package Python source"):
        evaluate_coverage(tmp_path, report, policy)
