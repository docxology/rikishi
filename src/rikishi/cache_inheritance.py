"""Fresh Sigma cache observations, bounded to versioned inputs and installed tools."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from rikishi.cache_jar_identity import JarContentBinding, jar_content_identity
from rikishi.kif import parse
from rikishi.runtime_artifacts import checked_source_path, jar_classes_sha256, read_regular
from rikishi.runtime_process import run_bounded

AUTHORITY: Final = "src/rikishi/data/fresh-cache-v1.json"
ADAPTER: Final = "scripts/runtime/FreshCacheDiagnostic.java"
PARTIAL: Final = "PartialValuedRelation"


class CacheDiagnosticError(ValueError):
    """A diagnostic receipt or controlled observation did not satisfy its contract."""


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class Selection(Frozen):
    line: int = Field(gt=0)
    text: str


class Change(Frozen):
    remove: str | None
    add: str | None


class Case(Frozen):
    name: str = Field(pattern=r"^[a-z][a-z0-9-]+$")
    scope: Literal["minimal_fragment", "full_merge_only"]
    changes: list[Change]
    expect_partial: bool
    expect_inheritable: bool


class Resources(Frozen):
    heap_mb: Literal[768]
    metaspace_mb: Literal[192]
    code_cache_mb: Literal[64]
    processors: Literal[2]
    max_wall_seconds: Literal[120]


class Authority(Frozen):
    schema_version: Literal[2]
    bindings: dict[str, str]
    jar_contents: dict[str, JarContentBinding] = Field(min_length=1)
    selections: list[Selection] = Field(min_length=1)
    resource_policy: Resources
    cases: list[Case] = Field(min_length=1)


class NativeEnvironment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", strict=True)
    JAVA_HOME: str
    SIGMA_HOME: str


class Observation(Frozen):
    schema_version: Literal[1]
    source_formula_count: int = Field(gt=0)
    formula_count_after_build: int = Field(gt=0)
    direct_path: list[str]
    direct_parent: list[str]
    cached_path: list[str]
    generated_path: list[str]
    generated_sources: dict[str, str]
    parent_partial_inheritable: bool
    instance_transitive_relations: list[str]
    subrelation_parents: list[str]
    parse_warnings: list[str]
    semantic_validation: Literal[False]


def _save(path: Path, value: JsonValue) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(read_regular(checked_source_path(path), limit=256 << 20)).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CacheDiagnosticError(message)


def check_observation(observed: Observation, case: Case) -> None:
    """Reject a mismatched control; success establishes no ontology semantics."""
    _require(set(observed.direct_path) == {"CaseRole", "TotalValuedRelation"},
             "direct path classification changed")
    _require(set(observed.generated_path) == set(observed.cached_path) - set(observed.direct_path),
             "generated/direct classification mismatch")
    _require(all(observed.generated_sources.get(t) == "FreshCache_Cache.kif"
                 for t in observed.generated_path), "generated formula source mismatch")
    _require((PARTIAL in observed.generated_path) == case.expect_partial,
             f"{case.name}: generated partial classification differs from control")
    _require(observed.parent_partial_inheritable == case.expect_inheritable,
             f"{case.name}: inheritable classification differs from control")


def _input(spec: Authority, case: Case, merge: bytes) -> bytes:
    lines = merge.decode("utf-8").splitlines()
    _require(all(s.line <= len(lines) and lines[s.line - 1] == s.text for s in spec.selections),
             "source selection differs from cited Merge.kif lines")
    text = (merge.decode("utf-8") if case.scope == "full_merge_only" else
            "\n".join(s.text for s in spec.selections) + "\n")
    for change in case.changes:
        if change.remove is not None:
            _require(text.splitlines().count(change.remove) == 1, "change must match one source line")
            text = "\n".join(line for line in text.splitlines() if line != change.remove) + "\n"
        if change.add is not None:
            text += change.add + "\n"
    _require(bool(list(parse(text))), "empty KIF input")
    return text.encode("utf-8")


def _run(command: list[str], directory: Path, phase: str, deadline: float,
         environment: dict[str, str]) -> None:
    started = time.monotonic()
    _save(directory / f"{phase}-command.json", list[JsonValue](command))
    result = run_bounded(command, cwd=directory, stdout=directory / f"{phase}-stdout.txt",
                         stderr=directory / f"{phase}-stderr.txt",
                         timeout=max(0.001, deadline - started), environment=environment)
    _save(directory / f"{phase}-process.json", {
        "returncode": result.returncode, "timed_out": result.timed_out,
        "elapsed_seconds": time.monotonic() - started,
    })
    _require(not result.timed_out, f"{phase}: wall-clock timeout")
    _require(result.returncode == 0, f"{phase}: exit {result.returncode}; see retained stderr")


def diagnose_cache_inheritance(root: Path, output: Path, *, timeout: int = 60) -> dict[str, JsonValue]:
    """Build fresh source-only KBs; retain failed probes and stable pre/post bindings.

    The output must be an unoccupied repository-local directory with an existing
    parent. Invalid destinations/timeouts raise before writes. Operational failures
    return a failed receipt with completed observations and no semantic authority.
    """
    root = checked_source_path(root)
    _require(type(timeout) is int and 1 <= timeout <= 120, "timeout must be 1..120 integer seconds")
    output = output if output.is_absolute() else root / output
    _require(output.is_relative_to(root) and ".." not in output.parts, "output must be repository-local")
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    checked_source_path(output.parent)
    vaults = [p for p in (root, *root.parents) if p.name == "GitVault" and os.path.ismount(p)]
    _require(bool(vaults), "mounted GitVault repository required")
    _require(all(Path(p).resolve().is_relative_to(vaults[0]) for p in (sys.prefix, sys.base_prefix)),
             "both Python prefixes must resolve on GitVault")
    output.mkdir()
    deadline = time.monotonic() + timeout
    report: dict[str, JsonValue] = {"status": "failed", "semantic_validation": False,
        "freshcache_scope": "none", "observed_case_count": 0, "cases": [],
        "output": str(output), "timeout_seconds": timeout}
    bindings: dict[Path, str] = {}
    before_saved = False
    cases: list[JsonValue] = []
    try:
        spec = Authority.model_validate_json(read_regular(root / AUTHORITY))
        _require(len({c.name for c in spec.cases}) == len(spec.cases), "duplicate case names")
        for relative, digest in spec.bindings.items():
            _require(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
                     "unsafe binding path")
            path = root / relative
            bindings[path] = _sha(path)
            _require(bindings[path] == digest, f"installed binding differs: {relative}")
        sigma_relative = ".rikishi/upstream/sigmakee/build/sigmakee.jar"
        sigma_jar = root / sigma_relative
        revision = json.loads(read_regular(root / "config/sumo.lock.json"))["repositories"]["sigmakee"]["commit"]
        _require(sigma_relative in spec.jar_contents, "Sigma JAR content binding required")
        _require(spec.jar_contents[sigma_relative].source_revision == revision,
                 "Sigma content authority source revision differs from lock")
        jar_content: dict[str, JsonValue] = {}
        for relative, expected in spec.jar_contents.items():
            _require(not Path(relative).is_absolute() and ".." not in Path(relative).parts
                     and Path(relative).as_posix() == relative and relative.endswith(".jar"),
                     "unsafe JAR content binding path")
            _require(relative == sigma_relative or (relative in spec.bindings
                     and expected.source_revision is None), "dependency JAR exact binding required")
            path = root / relative
            observed_identity = jar_content_identity(path, source_revision=expected.source_revision)
            bindings[path] = observed_identity.archive_sha256
            jar_content[str(path)] = observed_identity.model_dump(mode="json")
            _require(relative == sigma_relative or observed_identity.archive_sha256 == spec.bindings[relative],
                     f"installed dependency archive differs: {relative}")
            _require(observed_identity.content_sha256 == expected.content_sha256,
                     f"installed JAR content differs: {relative}")
        _require({p for p in bindings if p.suffix == ".jar"} == {
                 root / relative for relative in spec.jar_contents}, "incomplete JAR content bindings")
        _save(output / "jar-content.json", jar_content)
        native = NativeEnvironment.model_validate_json(read_regular(root / ".rikishi/runtime/environment.json"))
        java_home = checked_source_path(Path(native.JAVA_HOME))
        _require(java_home.is_relative_to(vaults[0]), "Java toolchain must be on GitVault")
        java, javac = java_home / "bin/java", java_home / "bin/javac"
        for path in [root / p for p in [AUTHORITY, ADAPTER, "src/rikishi/cache_inheritance.py",
                     "src/rikishi/runtime_process.py", "src/rikishi/runtime_artifacts.py",
                     "src/rikishi/cache_jar_identity.py", "src/rikishi/kif.py", "scripts/env.sh",
                     ".rikishi/runtime/environment.json"]] + [
                     java, javac, java_home / "release", java_home / "lib/modules",
                     java_home / "lib/server/libjvm.dylib", Path(native.SIGMA_HOME) / "KBs/config.xml"]:
            bindings[path] = _sha(path)
        _save(output / "bindings-before.json", {str(p): h for p, h in bindings.items()})
        before_saved = True
        sources = output / "sources"
        sources.mkdir()
        authority_sources = {root / relative for relative in spec.bindings
                             if Path(relative).suffix != ".jar"}
        for path in bindings:
            if path in authority_sources or path == sigma_jar or path.suffix in {
                    ".java", ".py", ".json", ".xml", ".patch", ".sh"}:
                destination = sources / str(path.relative_to(root) if path.is_relative_to(root) else path.name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(read_regular(path))
        jars = sorted(p for p in bindings if p.suffix == ".jar")
        _require(sigma_jar in jars and len(jars) > 1, "Sigma and dependency JAR bindings required")
        with zipfile.ZipFile(sigma_jar) as archive:
            stamp = archive.read("version.properties")
        (sources / "sigma-version.properties").write_bytes(stamp)
        for jar in jars:
            with zipfile.ZipFile(jar) as archive:
                _require("FreshCacheDiagnostic.class" not in archive.namelist(), "adapter class shadows a dependency")
        _save(output / "jar-classes.json", {str(p): jar_classes_sha256(p) for p in jars})
        classes = output / "classes"
        classes.mkdir()
        classpath = os.pathsep.join(str(p) for p in jars)
        environment = {k: v for k, v in os.environ.items() if k not in {
            "JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "JAVA_OPTS", "CLASSPATH",
            "SIGMA_HOME", "SIGMA_SRC", "ONTOLOGYPORTAL_GIT", "CATALINA_HOME"}}
        environment.update(HOME=str(output), TMPDIR=str(output))
        _run([str(java), "-version"], output, "java-version", deadline, environment)
        _run([str(javac), "-version"], output, "javac-version", deadline, environment)
        _run([str(javac), "-proc:none", "-implicit:none", "-cp", classpath, "-d", str(classes),
              str(sources / ADAPTER)], output, "compile", deadline, environment)
        _require([p.name for p in classes.iterdir()] == ["FreshCacheDiagnostic.class"],
                 "unexpected adapter class output")
        bindings[classes / "FreshCacheDiagnostic.class"] = _sha(classes / "FreshCacheDiagnostic.class")
        _save(output / "adapter-class.json", {str(classes / "FreshCacheDiagnostic.class"):
                                               bindings[classes / "FreshCacheDiagnostic.class"]})
        for case in spec.cases:
            directory = output / case.name
            (directory / "sigma/KBs").mkdir(parents=True)
            (directory / "tmp").mkdir()
            config = directory / "sigma/KBs/config.xml"
            config.write_text('<configuration><preference name="cache" value="true" />'
                              '<preference name="cacheDisjoint" value="false" /></configuration>\n')
            problem = directory / "input.kif"
            problem.write_bytes(_input(spec, case, read_regular(root / ".rikishi/upstream/sumo/Merge.kif")))
            bindings.update({problem: _sha(problem), config: _sha(config)})
            _save(directory / "input-bindings.json", {str(p): bindings[p] for p in [problem, config]})
            env = dict(environment, SIGMA_HOME=str(directory / "sigma"), HOME=str(directory),
                       TMPDIR=str(directory / "tmp"))
            _save(directory / "environment.json", {k: env[k] for k in ["SIGMA_HOME", "HOME", "TMPDIR"]})
            _run([str(java), "-Xmx768m", "-Xss2m", "-XX:MaxMetaspaceSize=192m",
                  "-XX:ReservedCodeCacheSize=64m", "-XX:ActiveProcessorCount=2",
                  f"-Duser.home={directory}", f"-Djava.io.tmpdir={directory / 'tmp'}", "-cp",
                  str(classes) + os.pathsep + classpath, "FreshCacheDiagnostic", str(directory),
                  str(problem), str(directory / "observation.json")], directory, "java", deadline, env)
            observed = Observation.model_validate_json(read_regular(directory / "observation.json"))
            check_observation(observed, case)
            cases.append({"name": case.name, "scope": case.scope, "observation": observed.model_dump(mode="json")})
        report.update(status="observed", freshcache_scope="minimal_fragment_and_full_merge_only"
                      if {c.scope for c in spec.cases} == {"minimal_fragment", "full_merge_only"}
                      else spec.cases[0].scope)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        report["error"] = f"{type(error).__name__}: {error}"
    if not before_saved:
        _save(output / "bindings-before.json", {str(p): h for p, h in bindings.items()})
    after: dict[str, JsonValue] = {}
    for path, before in bindings.items():
        try:
            after[str(path)] = _sha(path)
        except (OSError, ValueError) as error:
            after[str(path)] = f"unavailable: {error}"
        if after[str(path)] != before:
            report.update(status="failed", error="source/toolchain/input bindings changed")
    _save(output / "bindings-after.json", after)
    report.update(observed_case_count=len(cases), cases=cases, bindings_stable=all(
        after[str(p)] == h for p, h in bindings.items()))
    if report["status"] != "observed":
        report["freshcache_scope"] = "none"
    _save(output / "result.json", report)
    return report
