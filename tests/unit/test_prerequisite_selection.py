"""Drive real pytest selection and retain full-gate prerequisite failures."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from xml.etree import ElementTree

import pytest

POLICY: Final = Path(__file__).resolve().parents[1] / "fixtures/prerequisites.py"


@dataclass(frozen=True, slots=True)
class PytestRun:
    returncode: int
    stdout: str
    stderr: str
    cases: tuple[str, ...]
    errors: int


def _suite(directory: Path, files: dict[str, str], *, weakened: bool = False) -> None:
    """Write an isolated real suite using the exact current collection plugin."""
    source = POLICY.read_text()
    if weakened:
        node = next(node for node in ast.parse(source).body
                    if isinstance(node, ast.FunctionDef) and node.name == "prerequisite")
        lines = source.splitlines(keepends=True)
        assert node.end_lineno is not None
        source = "".join(lines[:node.body[0].lineno - 1] + ["    return None\n"]
                         + lines[node.end_lineno:])
    (directory / "selection_policy.py").write_text(source)
    (directory / "pytest.ini").write_text(
        "[pytest]\naddopts = --strict-markers\nmarkers = integration: requires native evidence\n")
    (directory / "conftest.py").write_text(
        "import pytest\npytest_plugins = ('selection_policy',)\n"
        "@pytest.fixture\ndef bridge_packet():\n"
        "    raise RuntimeError('native-prerequisite-invoked')\n"
        "@pytest.fixture\ndef dependent(bridge_packet):\n    return bridge_packet\n")
    for name, text in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def _run(directory: Path, label: str, *arguments: str) -> PytestRun:
    """Retain actual command, streams, status and JUnit in the isolated test directory."""
    xml = directory / f"{label}.xml"
    command = [sys.executable, "-B", "-m", "pytest", "-c", str(directory / "pytest.ini"),
               "--confcutdir", str(directory), "-p", "no:cacheprovider", "-q",
               "--basetemp", str(directory / f"tmp-{label}"),
               "--junitxml", str(xml), *arguments]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTEST_ADDOPTS", None)
    process = subprocess.run(command, cwd=directory, env=environment,
                             capture_output=True, check=False, timeout=30)
    (directory / f"{label}.stdout").write_bytes(process.stdout)
    (directory / f"{label}.stderr").write_bytes(process.stderr)
    (directory / f"{label}.json").write_text(json.dumps({
        "command": command, "returncode": process.returncode,
        "cwd": str(directory), "plugin_autoload_disabled": True,
    }, indent=2) + "\n")
    tree = ElementTree.parse(xml)
    return PytestRun(process.returncode, process.stdout.decode(), process.stderr.decode(),
                     tuple(case.attrib["name"] for case in tree.findall(".//testcase")),
                     len(tree.findall(".//error")))


@pytest.fixture
def dependency_suite(tmp_path: Path) -> Path:
    _suite(tmp_path, {"tests/test_dependency.py": (
        "def test_direct(bridge_packet):\n    assert bridge_packet\n"
        "def test_transitive(dependent):\n    assert dependent\n"
        "def test_portable():\n    assert 6 * 7 == 42\n")})
    return tmp_path


def test_portable_selection_excludes_direct_and_transitive_native_dependencies(
    dependency_suite: Path,
) -> None:
    # Given a real fixture that fails if selected, and a portable sibling.
    # When pytest applies the portable expression after the current collection hook.
    result = _run(dependency_suite, "portable", "-m", "not integration")
    # Then only the genuine portable sibling executes successfully.
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.cases == ("test_portable",)
    assert result.errors == 0


def test_full_selection_keeps_native_assertions_and_fails_on_missing_prerequisites(
    dependency_suite: Path,
) -> None:
    # Given the same real missing-prerequisite suite.
    # When no selection expression excludes integration tests.
    result = _run(dependency_suite, "full")
    # Then both native consumers remain selected and reach their intended failure.
    assert result.returncode == 1
    assert set(result.cases) == {"test_direct", "test_transitive", "test_portable"}
    assert result.errors == 2
    assert "native-prerequisite-invoked" in result.stdout


def test_weakened_classifier_is_detected_by_actual_portable_execution(tmp_path: Path) -> None:
    # Given the same hook with only its classification predicate disabled.
    _suite(tmp_path, {"tests/test_dependency.py": (
        "def test_native(bridge_packet):\n    assert bridge_packet\n"
        "def test_portable():\n    assert 1 + 1 == 2\n")}, weakened=True)
    # When the nominal portable selector executes.
    result = _run(tmp_path, "weakened-portable", "-m", "not integration")
    # Then the wrong native admission is detected by a real fixture failure.
    assert result.returncode == 1
    assert result.errors == 1
    assert set(result.cases) == {"test_native", "test_portable"}
    assert "native-prerequisite-invoked" in result.stdout


@pytest.mark.parametrize("path,fixture", [
    ("tests/manuscript/test_cache_replay.py", "packet"),
    ("tests/manuscript/test_native_manuscript.py", "saved_fresh_cache"),
    ("tests/runtime/test_fresh_cache.py", "experiment"),
    ("tests/manuscript/test_office_content.py", "package"),
])
def test_generic_fixture_names_are_classified_only_in_their_native_module(
    tmp_path: Path, path: str, fixture: str,
) -> None:
    # Given a native module and unrelated portable module with the same fixture name.
    native = (f"import pytest\n@pytest.fixture\ndef {fixture}():\n"
              "    raise RuntimeError('scoped-native-prerequisite')\n"
              f"def test_native({fixture}):\n    assert {fixture}\n"
              "def test_pure_sibling():\n    assert 2 * 3 == 6\n")
    portable = (f"import pytest\n@pytest.fixture\ndef {fixture}():\n    return 7\n"
                f"def test_unrelated({fixture}):\n    assert {fixture} == 7\n")
    _suite(tmp_path, {path: native, "tests/test_unrelated.py": portable})
    # When selecting portable tests through the actual hook.
    result = _run(tmp_path, "scoped-portable", "-m", "not integration")
    # Then the portable sibling and unrelated same-name fixture remain executable.
    assert result.returncode == 0, result.stdout + result.stderr
    assert set(result.cases) == {"test_pure_sibling", "test_unrelated"}


@pytest.mark.parametrize("path,name", [
    ("tests/manuscript/test_office_content.py", "test_original_aligned_and_combining_negation_fail"),
    ("tests/manuscript/test_office_content.py", "test_no_tables_is_exact_identity"),
    ("tests/manuscript/test_office_content.py", "test_complete_shared_body_gathered_context_is_source_derived"),
    ("tests/manuscript/test_office_content.py", "test_context_display_operator_mutation_is_rejected"),
    ("tests/manuscript/test_office_layout.py", "test_native_reference_repairs_effective_link_and_caption_policy"),
    ("tests/manuscript/test_reading_policy.py", "test_pandoc_preserves_native_header_policy"),
    ("tests/manuscript/test_witness_abstracts.py", "test_percentage_width_does_not_force_a_distorting_html_height"),
    ("tests/manuscript/test_bridge_figures.py", "test_offline_template_script_syntax_with_rejecting_control"),
])
def test_direct_installed_tool_cases_are_classified_without_excluding_pure_siblings(
    tmp_path: Path, path: str, name: str,
) -> None:
    # Given two parameterized installed-tool cases and a pure sibling in the same module.
    _suite(tmp_path, {path: (
        "import pytest\n@pytest.mark.parametrize('case', [1, 2])\n"
        f"def {name}(case):\n    raise RuntimeError('installed-tool-prerequisite')\n"
        "def test_pure_sibling():\n    assert 2 ** 3 == 8\n")})
    # When the real selector uses each item's unparameterized function identity.
    result = _run(tmp_path, "direct-portable", "-m", "not integration")
    # Then both installed-tool cases are excluded without suppressing the pure test.
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.cases == ("test_pure_sibling",)


def test_selected_node_sets_partition_full_collection(dependency_suite: Path) -> None:
    # Given three collected tests split by the real prerequisite classifier.
    # When all, portable, and integration collections are observed independently.
    full = _run(dependency_suite, "collect-full", "--collect-only")
    portable = _run(dependency_suite, "collect-portable", "--collect-only", "-m", "not integration")
    native = _run(dependency_suite, "collect-native", "--collect-only", "-m", "integration")
    # Then filtering partitions the inventory without losing or duplicating tests.
    def node_ids(result: PytestRun) -> set[str]:
        assert result.returncode == 0, result.stdout + result.stderr
        return {line for line in result.stdout.splitlines() if line.startswith("tests/") and "::" in line}

    whole, source, installed = map(node_ids, (full, portable, native))
    assert len(whole) == 3 and len(source) == 1 and len(installed) == 2
    assert source.isdisjoint(installed) and source | installed == whole
