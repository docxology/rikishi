from __future__ import annotations

import hashlib
import json
import shutil
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, Literal, assert_never

import pytest

from rikishi.runtime_artifacts import SZS_STATUS, load_capture, receipt, verified_bytes
from rikishi.runtime_query import run_query
from rikishi.runtime_results import ATPResult, ExpectedATPInvocation, interpret_sigma_result

QUERY: Final = "(subclass ReviewChild ReviewOther)"


@pytest.mark.parametrize("prefix", ["%", "%%", "#"])
@pytest.mark.parametrize("status", ["ResourceOut", "Theorem", "CounterSatisfiable"])
@pytest.mark.parametrize("ending", ["", "\n", "\r\n", " \t\r\n", " for temp-comb\n",
                                    " for input name.p\r\n"])
def test_native_status_line_grammar(prefix: str, status: str, ending: str) -> None:
    # Given: a supported complete native status line with horizontal whitespace.
    stdout = f"\t {prefix}\tSZS status {status}{ending}"
    # When: the shared parser reads that line.
    statuses = SZS_STATUS.findall(stdout)
    # Then: it returns exactly the complete status token.
    assert statuses == [status]


@pytest.mark.parametrize("stdout", [
    "SZS status Theorem", "echo %% SZS status Theorem", "%%% SZS status Theorem",
    "## SZS status Theorem", "%# SZS status Theorem", "#% SZS status Theorem",
    "% % SZS status Theorem", "%\nSZS status Theorem", "% SZS status\nTheorem",
    "% SZS status Theorem extra", "% SZS status Theorem_forged", "% SZS status Theorem1",
    "% SZS status Theorem-forged", "% SZS status Theoremé", "% SZS status Theorem for ",
    "% SZS status Theorem for\nproblem", '\"%% SZS status Theorem\"',
    "\v% SZS status Theorem", "%\rSZS status Theorem",
])
def test_forged_or_malformed_status_lines_have_no_authority(stdout: str) -> None:
    # Given: text outside the supported line grammar.
    # When: the shared parser reads it.
    statuses = SZS_STATUS.findall(stdout)
    # Then: embedded or partial status text supplies no recognized status.
    assert statuses == []


@dataclass(frozen=True, slots=True)
class NativeResourceOut:
    sidecar: Path
    capture: Path
    expected: ExpectedATPInvocation


@pytest.fixture(scope="module")
def native_resourceout(project_root: Path, tmp_path_factory: pytest.TempPathFactory) -> NativeResourceOut:
    root = tmp_path_factory.mktemp("native-resourceout")
    for relative in ("config/sumo.lock.json", "scripts/runtime/RikishiQuery.java",
                     ".rikishi/upstream/eprover/PROVER/eprover"):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project_root / relative, target)
    profile = root / "profile"
    kb = profile / "KBs"
    kb.mkdir(parents=True)
    (kb / "Review.kif").write_text(
        "(instance subclass BinaryPredicate)\n(domain subclass 1 Class)\n"
        "(domain subclass 2 Class)\n(subclass ReviewChild ReviewParent)\n"
        "(subclass ReviewOther ReviewObject)\n"
    )
    (kb / "config.xml").write_text(
        f'<configuration><preference name="baseDir" value="{profile}"/>'
        f'<preference name="kbDir" value="{kb}"/><preference name="sumoDir" value="{kb}"/>'
        '<preference name="sumokbname" value="Review"/>'
        '<preference name="loadLexicons" value="false"/>'
        '<preference name="loadFresh" value="true"/><preference name="cache" value="yes"/>'
        '<kb name="Review"><constituent filename="Review.kif"/></kb></configuration>'
    )
    environment = json.loads((project_root / ".rikishi/runtime/environment.json").read_text())
    environment["SIGMA_HOME"] = str(profile)
    environment_path = root / ".rikishi/runtime/environment.json"
    environment_path.parent.mkdir(parents=True)
    environment_path.write_text(json.dumps(environment))
    binary = root / ".rikishi/upstream/eprover/PROVER/eprover"
    executable_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
    # Keep the native five-CPU-second exhaustion experiment independent of host scheduling.
    report = run_query(root, QUERY, prover="e", timeout=5, prover_wall_timeout=300,
                       output=root / "query.log")
    (root / "native-result.json").write_text(json.dumps(report, indent=2))
    capture_path = root / "query.log.artifacts/capture.json"
    capture = load_capture(capture_path)
    assert capture.provenance["prover_sha256"] == executable_sha256
    assert capture.provenance["query_sha256"] == hashlib.sha256(QUERY.encode()).hexdigest()
    assert report["invocation_id"] == capture.invocation_id
    # Qualify the original before applying custody/status mutations to its copies.
    assert capture.returncode == 8 and capture.timed_out is False, report
    assert report["status"] == "ResourceOut" and report["evidence"] == "sha256_verified", report
    assert SZS_STATUS.findall(verified_bytes(capture.stdout, capture_path.parent).decode()) == ["ResourceOut"]
    assert report["budgets"] == {"mode": "explicit-wall", "native_limit_seconds": 5,
                                  "prover_wall_seconds": 300, "java_wall_seconds": 900}
    budget_bytes = Path(report["budgets_path"]).read_bytes()
    assert json.loads(budget_bytes) == report["budgets"]
    assert hashlib.sha256(budget_bytes).hexdigest() == capture.provenance["query_budgets_sha256"]
    assert "--cpu-limit=5" in capture.command
    expected = ExpectedATPInvocation(capture.invocation_id, binary, capture.provenance, prover="e")
    return NativeResourceOut(root / "query.log.result.json", capture_path, expected)


@pytest.fixture
def copied_resourceout(native_resourceout: NativeResourceOut, tmp_path: Path) -> NativeResourceOut:
    capture = load_capture(native_resourceout.capture)
    directory = tmp_path / "copied.artifacts"
    directory.mkdir()
    for artifact in (capture.problem, *capture.includes, capture.stdout, capture.stderr):
        shutil.copy2(native_resourceout.capture.parent / artifact.path, directory / artifact.path)
    shutil.copy2(native_resourceout.capture, directory / "capture.json")
    shutil.copy2(native_resourceout.capture.parent / "budgets.json", directory / "budgets.json")
    sidecar = ATPResult.model_validate_json(native_resourceout.sidecar.read_bytes())
    path = tmp_path / "copied.result.json"
    path.write_text(sidecar.model_copy(update={"capture": "copied.artifacts/capture.json"}).model_dump_json())
    return NativeResourceOut(path, directory / "capture.json", native_resourceout.expected)


@pytest.mark.integration
def test_actual_managed_e_resourceout_retains_verified_inconclusive_outcome(
    native_resourceout: NativeResourceOut,
) -> None:
    # Given: one fresh five-CPU-second Sigma/E query on an isolated Review profile.
    capture = load_capture(native_resourceout.capture)
    report = json.loads((native_resourceout.capture.parent.parent / "native-result.json").read_text())
    stdout = verified_bytes(capture.stdout, native_resourceout.capture.parent).decode("utf-8")
    assert capture.returncode == 8 and capture.timed_out is False
    assert [line for line in stdout.splitlines() if "SZS status" in line] == ["%% SZS status ResourceOut"]
    # When: the reader checks the actual sidecar against the trusted invocation.
    result = interpret_sigma_result(native_resourceout.sidecar, report["returncode"],
                                    expected=native_resourceout.expected)
    # Then: both the live report and saved interpretation are verified and inconclusive.
    for observed in (report, result):
        assert observed["status"] == "ResourceOut", observed
        assert observed["outcome"] == "inconclusive"
        assert observed["evidence"] == "sha256_verified"
        assert observed["atp_returncode"] == 8
        assert observed["proved"] is False
        assert observed["semantic_validation"] is False


@pytest.mark.integration
@pytest.mark.parametrize("prefix", ["%", "%%", "#"])
def test_mixed_prefix_conflicts_reject_even_rehashed_native_stdout(
    copied_resourceout: NativeResourceOut, prefix: str,
) -> None:
    # Given: copied actual stdout containing a conflicting status with matching new receipts.
    capture = load_capture(copied_resourceout.capture)
    directory = copied_resourceout.capture.parent
    stdout = directory / capture.stdout.path
    stdout.write_bytes(stdout.read_bytes() + f"\n{prefix} SZS status Theorem\n".encode())
    capture = capture.model_copy(update={"stdout": receipt(stdout, directory)})
    copied_resourceout.capture.write_text(capture.model_dump_json())
    sidecar = ATPResult.model_validate_json(copied_resourceout.sidecar.read_bytes())
    copied_resourceout.sidecar.write_text(sidecar.model_copy(
        update={"stdout_lines": len(stdout.read_bytes().splitlines())}).model_dump_json())
    # When: the unchanged conflict check reads both recognized statuses.
    result = interpret_sigma_result(copied_resourceout.sidecar, 0, expected=copied_resourceout.expected)
    # Then: hash agreement cannot turn conflicting evidence into an accepted result.
    assert result["status"] == "InvalidATPResult"
    assert result["outcome"] == "error" and result["proved"] is False


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["status", "count", "exit", "invocation", "timeout", "hash"])
def test_native_resourceout_custody_disagreements_are_rejected(
    copied_resourceout: NativeResourceOut,
    mutation: Literal["status", "count", "exit", "invocation", "timeout", "hash"],
) -> None:
    # Given: an isolated copy with one forged sidecar, process field or raw artifact.
    capture = load_capture(copied_resourceout.capture)
    sidecar = ATPResult.model_validate_json(copied_resourceout.sidecar.read_bytes())
    match mutation:
        case "status":
            sidecar = sidecar.model_copy(update={"status": "Theorem"})
        case "count":
            sidecar = sidecar.model_copy(update={"stdout_lines": sidecar.stdout_lines + 1})
        case "exit":
            sidecar = sidecar.model_copy(update={"atp_returncode": 0})
        case "invocation":
            sidecar = sidecar.model_copy(update={"invocation_id": "forged"})
        case "timeout":
            capture = capture.model_copy(update={"timed_out": True})
        case "hash":
            (copied_resourceout.capture.parent / capture.stdout.path).write_bytes(b"changed")
        case unreachable:
            assert_never(unreachable)
    copied_resourceout.capture.write_text(capture.model_dump_json())
    copied_resourceout.sidecar.write_text(sidecar.model_dump_json())
    # When: the reader verifies the altered copy against the original trusted bindings.
    result = interpret_sigma_result(copied_resourceout.sidecar, 0, expected=copied_resourceout.expected)
    # Then: the evidence remains invalid, including a fabricated timeout on native exit 8.
    assert result["status"] == "InvalidATPResult"
    assert result["evidence"] == "not_verified"
    assert result["outcome"] == "error" and result["proved"] is False


@pytest.mark.integration
@pytest.mark.parametrize("binding", ["invocation", "family", "executable", "query", "profile", "input"])
def test_native_resourceout_requires_original_trusted_bindings(
    native_resourceout: NativeResourceOut,
    binding: Literal["invocation", "family", "executable", "query", "profile", "input"],
) -> None:
    # Given: actual native bytes paired with a different caller-supplied binding.
    expected = native_resourceout.expected
    match binding:
        case "invocation":
            expected = replace(expected, invocation_id="forged")
        case "family":
            expected = replace(expected, prover="v")
        case "executable":
            expected = replace(expected, executable=Path(sys.executable))
        case "query" | "profile":
            key = {"query": "query_sha256", "profile": "profile_inputs_sha256"}[binding]
            expected = replace(expected, provenance={**expected.provenance, key: "0" * 64})
        case "input":
            expected = replace(expected, problem_sha256="0" * 64)
        case unreachable:
            assert_never(unreachable)
    # When: the reader checks that trusted expectation.
    result = interpret_sigma_result(native_resourceout.sidecar, 0, expected=expected)
    # Then: recognizing ResourceOut does not relax invocation custody.
    assert result["status"] == "InvalidATPResult"
    assert result["outcome"] == "error" and result["proved"] is False


@pytest.mark.integration
def test_resourceout_cannot_override_outer_failure(native_resourceout: NativeResourceOut) -> None:
    # Given: the retained completed native invocation.
    assert load_capture(native_resourceout.capture).timed_out is False
    # When: the outer process reports failure.
    failed = interpret_sigma_result(native_resourceout.sidecar, 1, expected=native_resourceout.expected)
    # Then: the outer failure is not relabeled as successful completion or proof.
    assert failed["outcome"] == "error" and failed["proved"] is False


@pytest.mark.integration
def test_resourceout_cannot_override_outer_timeout(native_resourceout: NativeResourceOut) -> None:
    # Given: the retained completed native invocation.
    assert load_capture(native_resourceout.capture).timed_out is False
    # When: the outer process reports its own timeout.
    timed_out = interpret_sigma_result(native_resourceout.sidecar, None, True,
                                       expected=native_resourceout.expected)
    # Then: the outer timeout remains explicitly inconclusive without verified evidence.
    assert timed_out["status"] == "Timeout" and timed_out["outcome"] == "inconclusive"
    assert timed_out["evidence"] == "not_verified" and timed_out["proved"] is False
