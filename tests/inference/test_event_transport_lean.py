import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from rikishi.formal_verification import _cache_snapshot


@pytest.mark.integration
def test_event_transport_proofs_and_same_import_controls(project_root: Path,
                                                        tmp_path: Path) -> None:
    # Given the existing separately verified compiler/cache authority, unchanged.
    authority = json.loads((project_root / "output/formalization/verification.json").read_text())
    compiler = Path(authority["compiler"])
    assert hashlib.sha256(compiler.read_bytes()).hexdigest() == authority["compiler_sha256"]
    libraries = [Path(path) for path in authority["dependency_cache_sha256"]]
    before, count = _cache_snapshot(libraries)
    assert before == authority["dependency_cache_sha256"]
    assert count == authority["dependency_cache_files"]
    environment = {**os.environ, "LEAN_PATH": os.pathsep.join(map(str, libraries))}
    declarations = ("pullback_union", "pullback_intersection", "pullback_complement",
                    "collapse_intersection_failure")
    sources = (
        (project_root / "examples/EventTransport.lean", "EventTransport", 0),
        (project_root / "tests/fixtures/EventPositive.lean", "EventPositive", 0),
        (project_root / "tests/fixtures/EventRejected.lean", "EventRejected", 1),
    )
    # When the actual compiler elaborates the statements and both same-import controls.
    for original, stem, expected in sources:
        source = tmp_path / f"{stem}.lean"
        shutil.copy2(original, source)
        target = tmp_path / f"{stem}.olean"
        command = [str(compiler), "-o", str(target), str(source)]
        process = subprocess.run(command, cwd=tmp_path, env=environment,
                                 capture_output=True, text=True, timeout=180, check=False)
        (tmp_path / f"{stem}.stdout").write_text(process.stdout)
        (tmp_path / f"{stem}.stderr").write_text(process.stderr)
        (tmp_path / f"{stem}.receipt.json").write_text(json.dumps({
            "argv": command, "exit_code": process.returncode,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "compiler_sha256": authority["compiler_sha256"],
        }, indent=2) + "\n")
        # Then rejection concerns the intended false membership, never missing imports.
        assert process.returncode == expected, process.stdout + process.stderr
        assert target.exists() is (expected == 0)
        if stem == "EventTransport":
            assert process.stdout.splitlines() == [
                f"'RikishiEventTransport.{name}' does not depend on any axioms"
                for name in declarations]
        if expected == 1:
            assert "Application type mismatch" in process.stdout
            assert "false ∈ {true}" in process.stdout
            assert "unknown module prefix" not in process.stdout
    # No upstream source, toolchain or dependency-cache modification is permitted.
    after, after_count = _cache_snapshot(libraries)
    assert (after, after_count) == (before, count)
