import os
import sys

import pytest

from rikishi.fep import DECLARATIONS
from rikishi.formal_verification import (
    FormalVerificationError,
    _cache_snapshot,
    _check_axioms,
    _compile,
    verify_formalization,
)


def test_axiom_contract_accepts_standard_basis_and_no_axioms():
    _check_axioms("\n".join(f"'FEP.FiniteInformation.{name}' depends on axioms: "
                            "[propext, Classical.choice, Quot.sound]" for name in DECLARATIONS))
    _check_axioms("\n".join(f"'FEP.FiniteInformation.{name}' does not depend on any axioms"
                            for name in DECLARATIONS))


@pytest.mark.parametrize("value", ["sorryAx", "FabricatedProof", "unknown audit format", ""])
def test_omitted_or_unapproved_axiom_evidence_is_rejected(value):
    text = "\n".join(f"'FEP.FiniteInformation.{name}' depends on axioms: [{value}]"
                     for name in DECLARATIONS) if value else ""
    with pytest.raises(FormalVerificationError):
        _check_axioms(text)


def test_unknown_and_duplicate_audit_records_are_rejected():
    good = "\n".join(f"'FEP.FiniteInformation.{name}' does not depend on any axioms"
                     for name in DECLARATIONS)
    with pytest.raises(FormalVerificationError):
        _check_axioms(good + "\n" + good.splitlines()[0])
    with pytest.raises(FormalVerificationError):
        _check_axioms(good.replace("does not depend on any axioms", "unexpected output"))


@pytest.mark.parametrize("timeout", [0, 601])
def test_invalid_compiler_bounds_rejected_before_source_access(tmp_path, timeout):
    with pytest.raises(ValueError, match="compiler timeout"):
        verify_formalization(tmp_path / "missing", tmp_path / "lean", tmp_path / "out",
                             timeout=timeout)


@pytest.mark.parametrize("kind", ["root", "ancestor", "directory", "file", "dangling"])
def test_compiled_cache_symlinks_fail_explicitly(tmp_path, kind):
    library = tmp_path / "library"
    target = tmp_path / "target"
    target.mkdir()
    (target / "Leaf.olean").write_bytes(b"actual fixture bytes")
    if kind == "root":
        library.symlink_to(target, target_is_directory=True)
    elif kind == "ancestor":
        alias = tmp_path / "alias"
        alias.symlink_to(target, target_is_directory=True)
        (target / "nested").mkdir()
        library = alias / "nested"
    else:
        library.mkdir()
        if kind == "directory":
            (library / "Linked").symlink_to(target, target_is_directory=True)
        else:
            destination = target / ("missing.olean" if kind == "dangling" else "Leaf.olean")
            (library / "Leaf.olean").symlink_to(destination)
    with pytest.raises(FormalVerificationError, match="Symlinked compiled dependency"):
        _cache_snapshot([library])


def test_compiler_process_timeout_retains_partial_output(tmp_path):
    command = [sys.executable, "-u", "-c",
               "import time; print('before-timeout', flush=True); time.sleep(5)"]
    log = tmp_path / "compiler.log"
    with pytest.raises(FormalVerificationError, match="Compiler exceeded"):
        _compile(command, tmp_path, dict(os.environ), 1, log)
    assert "before-timeout" in log.read_text()
    assert "Compiler exceeded 1 seconds" in log.read_text()
