import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from rikishi.fep import DECLARATIONS, PIN
from rikishi.formal_verification import (
    FormalVerificationError,
    _cache_snapshot,
    _compile,
    _require_stable_cache,
    verify_formalization,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def compiler(project_root):
    return project_root.parents[3] / "Local/runtimes/elan/toolchains/leanprover--lean4---v4.35.0/bin/lean"


@pytest.fixture
def formal_repo(tmp_path, git_commit):
    root = tmp_path / "formal"
    source = root / "lean/FepSketches"
    source.mkdir(parents=True)
    (root / "lean/.lake/packages").mkdir(parents=True)
    (root / "lean/lean-toolchain").write_text("leanprover/lean4:v4.35.0\n")
    (root / "lean/lake-manifest.json").write_text('{"packages": []}')
    (source / "finite_probability.lean").write_text("theorem fixture : True := by trivial\n")
    (source / "finite_information.lean").write_text(
        "import FepSketches.finite_probability\nnamespace FEP.FiniteInformation\n" +
        "\n".join(f"theorem {name} : True := by trivial" for name in DECLARATIONS) +
        "\nend FEP.FiniteInformation\n")
    git_commit(root)
    return root


@pytest.fixture
def module_formal_repo(formal_repo, git_commit):
    source = formal_repo / "lean/FepSketches"
    probability = source / "finite_probability.lean"
    probability.write_text("module\npublic section\n" + probability.read_text())
    information = source / "finite_information.lean"
    information.write_text("module\n" + information.read_text().replace(
        "import FepSketches.finite_probability\n",
        "public import FepSketches.finite_probability\npublic section\n", 1,
    ))
    git_commit(formal_repo)
    return formal_repo


def test_module_audit_uses_module_imports_and_matches_native_legacy_axioms(
    module_formal_repo, compiler, tmp_path
):
    output = tmp_path / "compiled-module"
    result = verify_formalization(module_formal_repo, compiler, output, revision="HEAD")
    audit = (output / "DeclarationAudit.lean").read_text()
    assert audit.startswith("module\n")
    legacy = output / "LegacyAudit.lean"
    legacy.write_text(audit.removeprefix("module\n"))
    reference = _compile(
        [str(compiler), str(legacy)], output,
        dict(os.environ, LEAN_PATH=str(output / "lib")), 180, output / "legacy-axioms.log",
    )
    assert result["declaration_axioms"] == reference
    assert reference.splitlines() == [
        f"'FEP.FiniteInformation.{name}' does not depend on any axioms" for name in DECLARATIONS
    ]


@pytest.mark.parametrize("admission", ["axiom", "suppressed-sorry"])
def test_module_axiom_audit_rejects_real_admissions(
    module_formal_repo, compiler, tmp_path, git_commit, admission
):
    source = module_formal_repo / "lean/FepSketches/finite_information.lean"
    name = DECLARATIONS[0]
    proof = (
        f"private axiom unapproved : True\ntheorem {name} : True := unapproved"
        if admission == "axiom" else
        f"set_option warningAsError false in\ntheorem {name} : True := by sorry"
    )
    source.write_text(source.read_text().replace(f"theorem {name} : True := by trivial", proof))
    git_commit(module_formal_repo)
    output = tmp_path / "rejected-module"
    with pytest.raises(FormalVerificationError, match=f"Unapproved declaration axioms: {name}"):
        verify_formalization(module_formal_repo, compiler, output, revision="HEAD")
    assert not (output / "verification.json").exists()
    assert (output / "DeclarationAudit.lean").read_text().startswith("module\n")
    axioms = (output / "declaration-axioms.log").read_text().splitlines()
    dependency = axioms[0].split("[", 1)[1].removesuffix("]")
    if admission == "axiom":
        assert re.fullmatch(
            r"_private\.FepSketches\.finite_information\.[0-9]+\.FEP\.FiniteInformation\.unapproved",
            dependency,
        )
    else:
        assert dependency == "sorryAx"
    assert axioms == [f"'FEP.FiniteInformation.{name}' depends on axioms: [{dependency}]", *[
        f"'FEP.FiniteInformation.{other}' does not depend on any axioms" for other in DECLARATIONS[1:]
    ]]


def test_pinned_finite_modules_really_compile_with_checked_dependencies(project_root, compiler, tmp_path):
    repository = project_root.parents[2] / "ActiveInferenceInstitute/Public/fep_formal"
    output = project_root / ".rikishi/formal-verification" / uuid.uuid4().hex
    result = verify_formalization(repository, compiler, output)
    assert result["commit"] == PIN
    assert result["dependency_revisions"]["mathlib"] == "56a005855ea17e0b0958f73ec801ae140b0a1679"
    assert {"lib/FepSketches/finite_probability.olean", "lib/FepSketches/finite_information.olean"} <= result["compiled_sha256"].keys()
    for relative, digest in result["compiled_sha256"].items():
        assert hashlib.sha256((output / relative).read_bytes()).hexdigest() == digest
    assert "sorryAx" not in result["declaration_axioms"]
    assert result["import_artifacts_sha256"]
    assert result["dependency_cache_files"] > len(result["import_artifacts_sha256"])
    for path, digest in result["import_artifacts_sha256"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    published = project_root / "output/formalization/verification.json"
    published.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output / "verification.json", published)


def test_real_committed_source_not_dirty_worktree_and_occupied_output_refused(
    formal_repo, compiler, tmp_path
):
    (formal_repo / "lean/FepSketches/finite_information.lean").write_text("invalid dirty source")
    output = tmp_path / "compiled"
    result = verify_formalization(formal_repo, compiler, output, revision="HEAD")
    assert result["compiled_sha256"]
    with pytest.raises(FileExistsError):
        verify_formalization(formal_repo, compiler, output, revision="HEAD")


@pytest.mark.parametrize("proof", ["by exact False.elim", "by sorry"])
def test_real_lean_rejects_incorrect_or_admitted_proof(formal_repo, compiler, tmp_path, git_commit, proof):
    source = formal_repo / "lean/FepSketches/finite_information.lean"
    source.write_text(source.read_text().replace("by trivial", proof))
    git_commit(formal_repo)
    output = tmp_path / "rejected"
    with pytest.raises(FormalVerificationError, match="Lean rejected"):
        verify_formalization(formal_repo, compiler, output, revision="HEAD")
    assert not (output / "verification.json").exists()
    assert (output / "finite_information.log").stat().st_size > 0


def test_wrong_compiler_pin_and_dependency_drift_refused(formal_repo, compiler, tmp_path, git_commit):
    (formal_repo / "lean/lean-toolchain").write_text("leanprover/lean4:v0.0.0\n")
    git_commit(formal_repo)
    with pytest.raises(FormalVerificationError, match="Compiler version"):
        verify_formalization(formal_repo, compiler, tmp_path / "wrong-pin", revision="HEAD")
    (formal_repo / "lean/lean-toolchain").write_text("leanprover/lean4:v4.35.0\n")
    dependency = formal_repo / "lean/.lake/packages/library"
    dependency.mkdir()
    (dependency / "file").write_text("Original")
    revision = git_commit(dependency)
    (formal_repo / "lean/lake-manifest.json").write_text(json.dumps({"packages": [
        {"name": "library", "rev": revision}]}))
    git_commit(formal_repo)
    (dependency / "file").write_text("Changed")
    with pytest.raises(FormalVerificationError, match="Dependency revision"):
        verify_formalization(formal_repo, compiler, tmp_path / "dirty-dependency", revision="HEAD")


def test_output_inside_canonical_input_is_refused(formal_repo, compiler):
    output = formal_repo / "generated"
    with pytest.raises(FormalVerificationError, match="Output overlaps canonical input"):
        verify_formalization(formal_repo, compiler, output, revision="HEAD")
    assert not output.exists()


@pytest.mark.parametrize("placement", ["ancestor", "ancestor-sibling", "nested"])
def test_symlinked_cache_output_is_refused_before_writing(
    formal_repo, compiler, tmp_path, git_commit, placement
):
    dependency = formal_repo / "lean/.lake/packages/library"
    dependency.mkdir()
    (dependency / "source").write_text("pinned source")
    revision = git_commit(dependency)
    (formal_repo / "lean/lake-manifest.json").write_text(json.dumps({"packages": [
        {"name": "library", "rev": revision}]}))
    git_commit(formal_repo)
    external = tmp_path / "external-cache"
    external.mkdir()
    library = dependency / ".lake/build/lib/lean"
    if placement.startswith("ancestor"):
        (dependency / ".lake").symlink_to(external, target_is_directory=True)
        library.mkdir(parents=True)
        output = (external / "build/lib/lean/generated" if placement == "ancestor"
                  else external / "sibling")
    else:
        library.mkdir(parents=True)
        (library / "Linked").symlink_to(external, target_is_directory=True)
        output = external / "generated"
    with pytest.raises(FormalVerificationError):
        verify_formalization(formal_repo, compiler, output, revision="HEAD")
    assert not output.exists()


def test_transitive_lean_cache_change_is_detected_even_with_unchanged_direct_import(
    compiler, tmp_path
):
    library = tmp_path / "lib"
    library.mkdir()
    environment = dict(os.environ, LEAN_PATH=str(library))
    leaf = tmp_path / "Leaf.lean"
    bridge = tmp_path / "Bridge.lean"
    target = tmp_path / "Target.lean"
    leaf.write_text("def auditLeafValue : Nat := 1\n")
    bridge.write_text("import Leaf\ndef auditBridgeValue : Nat := auditLeafValue\n")
    target.write_text("import Bridge\n#reduce auditBridgeValue\n")
    for source in (leaf, bridge):
        subprocess.run([str(compiler), "-o", str(library / f"{source.stem}.olean"), str(source)],
                       cwd=tmp_path, env=environment, capture_output=True, check=True)
    first = subprocess.run([str(compiler), str(target)], cwd=tmp_path, env=environment,
                           capture_output=True, text=True, check=True).stdout
    direct_hash = hashlib.sha256((library / "Bridge.olean").read_bytes()).hexdigest()
    before, _ = _cache_snapshot([library])
    _require_stable_cache(before, _cache_snapshot([library])[0])
    leaf.write_text("def auditLeafValue : Nat := 2\n")
    subprocess.run([str(compiler), "-o", str(library / "Leaf.olean"), str(leaf)],
                   cwd=tmp_path, env=environment, capture_output=True, check=True)
    second = subprocess.run([str(compiler), str(target)], cwd=tmp_path, env=environment,
                            capture_output=True, text=True, check=True).stdout
    assert first.strip() == "1"
    assert second.strip() == "2"
    assert hashlib.sha256((library / "Bridge.olean").read_bytes()).hexdigest() == direct_hash
    with pytest.raises(FormalVerificationError, match="Compiled dependency cache changed"):
        _require_stable_cache(before, _cache_snapshot([library])[0])


def test_symlinked_transitive_lean_cache_is_refused(compiler, tmp_path):
    library = tmp_path / "lib"
    library.mkdir()
    external = tmp_path / "external-cache"
    external.mkdir()
    (library / "Linked").symlink_to(external, target_is_directory=True)
    source = tmp_path / "Linked"
    source.mkdir()
    leaf = source / "Leaf.lean"
    bridge = tmp_path / "Bridge.lean"
    target = tmp_path / "Target.lean"
    environment = dict(os.environ, LEAN_PATH=str(library))
    leaf.write_text("def auditLeafValue : Nat := 1\n")
    bridge.write_text("import Linked.Leaf\ndef auditBridgeValue : Nat := auditLeafValue\n")
    target.write_text("import Bridge\n#reduce auditBridgeValue\n")

    def compile_leaf():
        subprocess.run([str(compiler), "-o", str(external / "Leaf.olean"), str(leaf)],
                       cwd=tmp_path, env=environment, capture_output=True, check=True)

    def evaluate():
        return subprocess.run([str(compiler), str(target)], cwd=tmp_path, env=environment,
                              capture_output=True, text=True, check=True).stdout.strip()

    compile_leaf()
    subprocess.run([str(compiler), "-o", str(library / "Bridge.olean"), str(bridge)],
                   cwd=tmp_path, env=environment, capture_output=True, check=True)
    first = evaluate()
    bridge_digest = hashlib.sha256((library / "Bridge.olean").read_bytes()).hexdigest()
    leaf.write_text("def auditLeafValue : Nat := 2\n")
    compile_leaf()
    assert (first, evaluate()) == ("1", "2")
    assert hashlib.sha256((library / "Bridge.olean").read_bytes()).hexdigest() == bridge_digest
    with pytest.raises(FormalVerificationError, match="Symlinked compiled dependency"):
        _cache_snapshot([library])
