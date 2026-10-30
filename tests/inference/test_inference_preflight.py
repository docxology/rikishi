from pathlib import Path

import pytest

from rikishi.inference_models import InferenceError
from rikishi.inference_runner import run_inference
from rikishi.inference_study import catalog


@pytest.mark.parametrize("prover,timeout", [
    ("z", 5), ("both", 0), ("e", 301), ("v", True), ("e", 1.5), ("both", "5"),
])
def test_invalid_resource_policy_fails_before_output_creation(tmp_path, prover, timeout):
    output = tmp_path / "campaign"
    with pytest.raises(InferenceError):
        run_inference(tmp_path, output, prover=prover, timeout=timeout)
    assert not output.exists()


def test_output_escape_and_symlink_are_rejected_before_writes(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(InferenceError, match="inside"):
        run_inference(root, tmp_path / "outside")
    (root / "linked").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(InferenceError, match="inside"):
        run_inference(root, root / "linked/campaign")


def test_changed_source_and_lock_are_rejected_before_native_execution(tmp_path, portable_inputs):
    study = catalog()
    source = tmp_path / study.source_path
    source.parent.mkdir(parents=True)
    source.write_bytes(portable_inputs.merge_bytes + b"\n; changed\n")
    with pytest.raises(InferenceError, match="Complete source"):
        run_inference(tmp_path, Path("campaign"))
    source.write_bytes(portable_inputs.merge_bytes)
    (tmp_path / "config").mkdir()
    (tmp_path / "config/sumo.lock.json").write_text("{}")
    with pytest.raises(InferenceError, match="Source lock"):
        run_inference(tmp_path, Path("campaign"))
    assert not (tmp_path / "campaign").exists()


def test_missing_native_binary_is_an_explicit_preflight_failure(tmp_path, portable_inputs, project_root):
    study = catalog()
    source = tmp_path / study.source_path
    source.parent.mkdir(parents=True)
    source.write_bytes(portable_inputs.merge_bytes)
    (tmp_path / "config").mkdir()
    (tmp_path / "config/sumo.lock.json").write_bytes((project_root / "config/sumo.lock.json").read_bytes())
    with pytest.raises(FileNotFoundError, match="not installed"):
        run_inference(tmp_path, Path("campaign"), prover="v")
    assert not (tmp_path / "campaign").exists()
