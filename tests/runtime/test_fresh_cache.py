import json
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from uuid import uuid4

import pytest

from rikishi.cache_inheritance import (
    ADAPTER,
    AUTHORITY,
    Authority,
    CacheDiagnosticError,
    Change,
    Observation,
    Selection,
    _input,
    _run,
    check_observation,
    diagnose_cache_inheritance,
)
from rikishi.cache_jar_identity import jar_content_identity
from rikishi.portable_inputs import PortableInputs
from rikishi.runtime_artifacts import ArtifactError
from rikishi.runtime_process import run_bounded

SIGMA_JAR = ".rikishi/upstream/sigmakee/build/sigmakee.jar"


def _fresh(workspace: Path, label: str) -> Path:
    return workspace / f"fresh-cache-{label}-{uuid4().hex}"


def _copy_project(root: Path, workspace: Path) -> Path:
    destination = _fresh(workspace, "copy")
    spec = Authority.model_validate_json((root / AUTHORITY).read_bytes())
    for relative in {*spec.bindings, *spec.jar_contents, AUTHORITY, ADAPTER,
                     "src/rikishi/cache_inheritance.py", "src/rikishi/cache_jar_identity.py",
                     "src/rikishi/runtime_process.py", "src/rikishi/runtime_artifacts.py",
                     "src/rikishi/kif.py", "scripts/env.sh", ".rikishi/runtime/environment.json"}:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, target)
    return destination


@pytest.fixture(scope="module")
def experiment(project_root: Path, native_workspace: Path) -> Path:
    output = _fresh(native_workspace, "tests")
    result = diagnose_cache_inheritance(project_root, output)
    assert result["status"] == "observed", result
    return output


@pytest.mark.integration
def test_fresh_fragment_controls_and_complete_merge(project_root: Path, experiment: Path):
    result = json.loads((experiment / "result.json").read_text())
    rows = {row["name"]: row["observation"] for row in result["cases"]}

    assert result["observed_case_count"] == 5
    assert result["bindings_stable"] is True
    assert result["semantic_validation"] is False
    assert rows["fragment-original"]["source_formula_count"] == 39
    assert rows["merge-original"]["source_formula_count"] == 5519
    assert (experiment / "merge-original/input.kif").read_bytes() == (
        project_root / ".rikishi/upstream/sumo/Merge.kif").read_bytes()
    for name, row in rows.items():
        assert row["direct_path"] == ["CaseRole", "TotalValuedRelation"]
        assert ("PartialValuedRelation" in row["generated_path"]) == (
            name not in {"fragment-parent-reclassified", "fragment-edge-removed"})
    assert rows["fragment-original"]["parent_partial_inheritable"] is False
    assert rows["fragment-partial-inheritable"]["parent_partial_inheritable"] is True


@pytest.mark.integration
def test_changed_source_fails_original_expectation(
    project_root: Path, experiment: Path, native_workspace: Path,
):
    directory = _fresh(native_workspace, "negative")
    directory.mkdir()
    command = [sys.executable, "-c",
               ("import sys; from pathlib import Path; "
               "from rikishi.cache_inheritance import Authority, Observation, check_observation; "
               "a=Authority.model_validate_json(Path(sys.argv[1]).read_bytes()); "
               "o=Observation.model_validate_json(Path(sys.argv[2]).read_bytes()); "
               "check_observation(o,a.cases[0])"),
               str(project_root / AUTHORITY),
               str(experiment / "fragment-parent-reclassified/observation.json")]

    process = run_bounded(command, cwd=project_root, stdout=directory / "stdout.txt",
                          stderr=directory / "stderr.txt", timeout=10)

    (directory / "receipt.json").write_text(json.dumps({
        "command": command, "returncode": process.returncode, "timed_out": process.timed_out}))
    assert process.returncode != 0 and not process.timed_out
    assert "CacheDiagnosticError" in (directory / "stderr.txt").read_text()


@pytest.mark.parametrize("timeout", [0, 121, True])
def test_invalid_timeout_refuses_writes(tmp_path: Path, timeout: int):
    output = tmp_path / "invalid-timeout"

    with pytest.raises(CacheDiagnosticError, match="timeout"):
        diagnose_cache_inheritance(tmp_path, output, timeout=timeout)

    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("kind", ["outside", "parent", "occupied", "symlink", "ancestor"])
def test_unsafe_and_occupied_destinations_refuse_writes(tmp_path: Path, kind: str):
    project_root = tmp_path / "empty-repository"
    project_root.mkdir()
    directory = project_root / "paths"
    directory.mkdir()
    output = directory / "output"
    expected = CacheDiagnosticError
    if kind == "outside":
        output = project_root.parent / f"fresh-cache-outside-{uuid4().hex}"
    elif kind == "parent":
        output = directory / ".." / f"fresh-cache-parent-{uuid4().hex}"
    elif kind == "occupied":
        output.write_text("preserve")
        expected = FileExistsError
    elif kind == "symlink":
        output.symlink_to(directory / "absent")
        expected = FileExistsError
    elif kind == "ancestor":
        link = directory / "linked"
        link.symlink_to(directory, target_is_directory=True)
        output = link / "output"
        expected = ArtifactError
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    with pytest.raises(expected):
        diagnose_cache_inheritance(project_root, output)

    assert not (directory / "result.json").exists()
    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == before
    if kind == "occupied":
        assert output.read_text() == "preserve"
    if kind == "symlink":
        assert output.is_symlink() and not output.exists()


@pytest.mark.integration
def test_real_deadline_leaves_failed_receipt(project_root: Path, native_workspace: Path):
    output = _fresh(native_workspace, "timeout")

    result = diagnose_cache_inheritance(project_root, output, timeout=1)

    assert result["status"] == "failed"
    assert "timeout" in str(result["error"])
    processes = list(output.rglob("*-process.json"))
    assert any(json.loads(p.read_text())["timed_out"] for p in processes)
    assert json.loads((output / "result.json").read_text()) == result


@pytest.mark.parametrize("failure", ["authority", "binding", "selection", "input", "control", "unsafe-binding"])
@pytest.mark.integration
def test_bad_authority_or_input_preserves_failure_receipt(
    project_root: Path, native_workspace: Path, failure: str,
):
    root = _copy_project(project_root, native_workspace)
    authority = root / AUTHORITY
    value = json.loads(authority.read_text())
    if failure == "authority":
        authority.write_text("{")
    elif failure == "binding":
        (root / "config/sumo.lock.json").write_text("changed")
    elif failure == "selection":
        value["selections"][0]["line"] = 1
    elif failure == "input":
        value["cases"][0]["changes"] = [{"remove": None, "add": "("}]
    elif failure == "control":
        value["cases"][0]["expect_partial"] = False
    elif failure == "unsafe-binding":
        value["bindings"] = {"../escape": "0" * 64}
    if failure != "authority":
        authority.write_text(json.dumps(value))

    result = diagnose_cache_inheritance(root, root / "output")

    assert result["status"] == "failed"
    assert result["observed_case_count"] == 0
    assert "error" in result
    assert json.loads((root / "output/result.json").read_text()) == result


@pytest.mark.parametrize("field", ["direct_path", "generated_path", "generated_sources", "parent_partial_inheritable"])
def test_observation_contract_rejects_corrupted_receipts(
    project_root: Path, experiment: Path, native_workspace: Path, field: str,
):
    value = json.loads((experiment / "fragment-original/observation.json").read_text())
    value[field] = {"direct_path": [], "generated_path": [], "generated_sources": {},
                    "parent_partial_inheritable": True}[field]
    observed = Observation.model_validate(value)
    case = Authority.model_validate_json((project_root / AUTHORITY).read_bytes()).cases[0]

    with pytest.raises(CacheDiagnosticError):
        check_observation(observed, case)

    failed = _fresh(native_workspace, "corrupt-receipt")
    failed.write_text(json.dumps(value))


@pytest.mark.integration
def test_real_java_rejects_malformed_kif(
    project_root: Path, experiment: Path, native_workspace: Path,
):
    directory = _fresh(native_workspace, "java-malformed")
    shutil.copytree(experiment / "fragment-original/sigma", directory / "sigma")
    (directory / "tmp").mkdir()
    (directory / "input.kif").write_text("(instance path TotalValuedRelation\n")
    command = json.loads((experiment / "fragment-original/java-command.json").read_text())
    original = str(experiment / "fragment-original")
    command = [argument.replace(original, str(directory)) for argument in command]
    environment = json.loads((experiment / "fragment-original/environment.json").read_text())
    environment = {k: v.replace(original, str(directory)) for k, v in environment.items()}

    process = run_bounded(command, cwd=directory, stdout=directory / "stdout.txt",
                          stderr=directory / "stderr.txt", timeout=10, environment=environment)

    (directory / "receipt.json").write_text(json.dumps({
        "command": command, "returncode": process.returncode, "timed_out": process.timed_out}))
    assert process.returncode != 0 and not process.timed_out
    assert not (directory / "observation.json").exists()


@pytest.mark.parametrize("remove", ["(instance missing Relation)", "(instance path TotalValuedRelation)"])
def test_changes_require_exactly_one_source_anchor(
    project_root: Path, portable_inputs: PortableInputs, remove: str,
):
    spec = Authority.model_validate_json((project_root / AUTHORITY).read_bytes())
    case = spec.cases[0].model_copy(update={"changes": []})
    case = case.model_copy(update={"changes": [Change(remove=remove, add=None)]})
    merge = portable_inputs.merge_bytes
    if remove == "(instance path TotalValuedRelation)":
        spec = spec.model_copy(update={"selections": spec.selections + [spec.selections[-2]]})

    with pytest.raises(CacheDiagnosticError, match="one source line"):
        _input(spec, case, merge)


@pytest.mark.integration
@pytest.mark.parametrize("change", ["replace", "remove"])
def test_live_binding_change_invalidates_success(
    project_root: Path, native_workspace: Path, change: str,
):
    root = _copy_project(project_root, native_workspace)
    output = root / "output"
    target = root / "config/sumo.lock.json"
    watcher = [sys.executable, "-c",
               ("import sys,time; from pathlib import Path; "
                "marker=Path(sys.argv[1]); deadline=time.monotonic()+15; "
                "exec('while not marker.exists():\\n if time.monotonic()>deadline: raise TimeoutError()'); "
                "target=Path(sys.argv[2]); "
                "target.write_text('changed') if sys.argv[3]=='replace' else target.rename(target.with_suffix('.saved'))"),
               str(output / "fragment-original/java-command.json"), str(target), change]
    with (root / "watcher-stdout.txt").open("xb") as stdout, (
        root / "watcher-stderr.txt").open("xb") as stderr, subprocess.Popen(
            watcher, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL) as process:
        result = diagnose_cache_inheritance(root, output)
        code = process.wait(timeout=20)

    (root / "watcher-receipt.json").write_text(json.dumps({"command": watcher, "returncode": code}))
    assert code == 0, (root / "watcher-stderr.txt").read_text()
    assert result["status"] == "failed"
    assert result["bindings_stable"] is False
    assert result["error"] == "source/toolchain/input bindings changed"


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["repack", "class", "resource", "version", "manifest"])
def test_complete_archive_controls(project_root: Path, native_workspace: Path, mutation: str):
    root = _copy_project(project_root, native_workspace)
    jar = root / SIGMA_JAR
    original = jar.with_suffix(".original-archive")
    jar.rename(original)
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(
        jar, "w", compression=zipfile.ZIP_STORED,
    ) as target:
        changed = False
        for entry in reversed(source.infolist()):
            if entry.is_dir():
                continue
            data = source.read(entry)
            if entry.filename == "META-INF/MANIFEST.MF":
                data = re.sub(rb"(Implementation-Version: [^\r\n]+ built on )[^\r\n]+",
                              rb"\g<1>Thu, 22 Oct 2026 0102 +0000", data)
            if mutation == "class" and not changed and entry.filename.endswith(".class"):
                data += b"altered executable class"
                changed = True
            if mutation == "resource" and entry.filename == "META-INF/LICENSE":
                data += b"altered resource"
            if mutation == "version" and entry.filename == "version.properties":
                data = data.replace(b"build.date=2026-09-24", b"build.date=2026-09-25")
            if mutation == "manifest" and entry.filename == "META-INF/MANIFEST.MF":
                data = data.replace(b"Main-Class: com.articulate.sigma.KB",
                                    b"Main-Class: com.articulate.sigma.KBmanager")
            target.writestr(entry.filename, data)
    spec = Authority.model_validate_json((root / AUTHORITY).read_bytes())
    identity = jar_content_identity(jar, source_revision=spec.jar_contents[SIGMA_JAR].source_revision)

    result = diagnose_cache_inheritance(root, root / "output")

    expected = spec.jar_contents[SIGMA_JAR].content_sha256
    if mutation == "repack":
        assert identity.content_sha256 == expected
        assert result["status"] == "observed", result
        assert result["observed_case_count"] == 5
        assert result["bindings_stable"] is True
        assert jar.read_bytes() == (root / "output/sources" / SIGMA_JAR).read_bytes()
        before = json.loads((root / "output/bindings-before.json").read_bytes())
        after = json.loads((root / "output/bindings-after.json").read_bytes())
        assert before[str(jar)] == identity.archive_sha256 == after[str(jar)]
        assert identity.archive_sha256 != jar_content_identity(original).archive_sha256
    else:
        assert identity.content_sha256 != expected
        assert result["status"] == "failed"
        assert result["observed_case_count"] == 0
        assert "installed JAR content differs" in str(result["error"])


def test_complete_snapshot_custody(project_root: Path, experiment: Path):
    spec = Authority.model_validate_json((project_root / AUTHORITY).read_bytes())
    before = json.loads((experiment / "bindings-before.json").read_bytes())
    content = json.loads((experiment / "jar-content.json").read_bytes())
    assert set(content) == {str(project_root / relative) for relative in spec.jar_contents}
    for relative in [p for p in spec.bindings if not p.endswith(".jar")] + [SIGMA_JAR]:
        saved = experiment / "sources" / relative
        assert saved.read_bytes() == (project_root / relative).read_bytes()
    for relative in spec.jar_contents:
        assert content[str(project_root / relative)]["archive_sha256"] == before[str(project_root / relative)]


@pytest.mark.integration
@pytest.mark.parametrize("failure", ["schema1", "duplicate-case", "missing-sigma", "revision",
                                     "unsafe-jar", "missing-dependency", "incomplete-content"])
def test_jar_authority_errors_preserve_red_receipts(
    project_root: Path, native_workspace: Path, failure: str,
):
    root = _copy_project(project_root, native_workspace)
    authority = root / AUTHORITY
    value = json.loads(authority.read_bytes())
    if failure == "schema1":
        value["schema_version"] = 1
        value.pop("jar_contents")
    elif failure == "duplicate-case":
        value["cases"].append(value["cases"][0])
    elif failure == "missing-sigma":
        value["jar_contents"].pop(SIGMA_JAR)
    elif failure == "revision":
        value["jar_contents"][SIGMA_JAR]["source_revision"] = "0" * 40
    elif failure == "unsafe-jar":
        value["jar_contents"]["../escape.jar"] = value["jar_contents"][SIGMA_JAR]
    elif failure == "missing-dependency":
        value["bindings"].pop(".rikishi/upstream/sigmakee/lib/sigmaUtils.jar")
    elif failure == "incomplete-content":
        value["jar_contents"].pop(".rikishi/upstream/sigmakee/lib/sigmaUtils.jar")
    authority.write_text(json.dumps(value))

    result = diagnose_cache_inheritance(root, root / "output")

    assert result["status"] == "failed"
    assert result["observed_case_count"] == 0
    assert (root / "output/bindings-before.json").is_file()
    assert (root / "output/bindings-after.json").is_file()
    assert "error" in result


def test_empty_input_is_rejected(project_root: Path):
    spec = Authority.model_validate_json((project_root / AUTHORITY).read_bytes())
    spec = spec.model_copy(update={"selections": [Selection(line=1, text="; only a comment")]})
    with pytest.raises(CacheDiagnosticError, match="empty KIF"):
        _input(spec, spec.cases[0], b"; only a comment\n")


def test_real_process_error_retains_exit_status(tmp_path: Path):
    output = tmp_path / "nonzero-process"
    output.mkdir()
    with pytest.raises(CacheDiagnosticError, match="exit 7"):
        _run([sys.executable, "-c", "raise SystemExit(7)"], output, "negative",
             time.monotonic() + 10, {})
    assert json.loads((output / "negative-process.json").read_bytes())["returncode"] == 7


@pytest.mark.integration
@pytest.mark.parametrize("failure", ["shadow", "adapter-outputs", "compile", "java-home"])
def test_real_tool_and_adapter_errors(project_root: Path, native_workspace: Path, failure: str):
    root = _copy_project(project_root, native_workspace)
    if failure == "shadow":
        jar = root / SIGMA_JAR
        with zipfile.ZipFile(jar, "a") as archive:
            archive.writestr("FreshCacheDiagnostic.class", b"shadow class must never load")
        authority = root / AUTHORITY
        value = json.loads(authority.read_bytes())
        value["jar_contents"][SIGMA_JAR]["content_sha256"] = jar_content_identity(
            jar, source_revision=value["jar_contents"][SIGMA_JAR]["source_revision"],
        ).content_sha256
        authority.write_text(json.dumps(value))
    elif failure == "adapter-outputs":
        with (root / ADAPTER).open("a") as stream:
            stream.write("\nclass UnexpectedExtraDiagnosticClass {}\n")
    elif failure == "compile":
        (root / ADAPTER).write_text("invalid java source\n")
    elif failure == "java-home":
        environment = root / ".rikishi/runtime/environment.json"
        value = json.loads(environment.read_bytes())
        value["JAVA_HOME"] = "/usr"
        environment.write_text(json.dumps(value))

    result = diagnose_cache_inheritance(root, root / "output")

    assert result["status"] == "failed", result
    assert result["observed_case_count"] == 0
    assert {"shadow": "shadows", "adapter-outputs": "unexpected adapter class output",
            "compile": "compile: exit", "java-home": "Java toolchain must be on GitVault"}[
                failure] in str(result["error"])
