"""Offline consistency replay of a retained fresh-cache experiment.

Recorded absolute paths are lexical identities, never live filesystem inputs.
This verifies retained custody and controls, not historical process authenticity.
"""

from __future__ import annotations

import hashlib
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Annotated, Final
from zipfile import ZipFile

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from rikishi.cache_inheritance import (
    ADAPTER,
    AUTHORITY,
    Authority,
    NativeEnvironment,
    Observation,
    _input,
    check_observation,
)
from rikishi.cache_jar_identity import JarContentIdentity, jar_content_identity
from rikishi.manuscript_provenance import require_evidence
from rikishi.runtime_artifacts import (
    checked_source_path,
    jar_classes_sha256,
    normalized_source_identity,
    read_regular,
)

_Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
_Bindings: Final = TypeAdapter(dict[str, _Digest])
_Command: Final = TypeAdapter(list[str])
_Jars: Final = TypeAdapter(dict[str, JarContentIdentity])
_SOURCE_FILES: Final = (
    AUTHORITY, ADAPTER, "src/rikishi/cache_inheritance.py", "src/rikishi/cache_jar_identity.py",
    "src/rikishi/runtime_process.py", "src/rikishi/runtime_artifacts.py", "src/rikishi/kif.py",
    "scripts/env.sh", ".rikishi/runtime/environment.json",
)
_SIGMA: Final = ".rikishi/upstream/sigmakee/build/sigmakee.jar"
_MERGE: Final = ".rikishi/upstream/sumo/Merge.kif"
_CONFIG: Final = (b'<configuration><preference name="cache" value="true" />'
                  b'<preference name="cacheDisjoint" value="false" /></configuration>\n')


class SavedCase(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    name: str
    scope: str
    observation: Observation


class SavedResult(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    status: str
    freshcache_scope: str
    semantic_validation: bool
    bindings_stable: bool
    observed_case_count: int
    output: str
    cases: list[SavedCase]


class SavedProcess(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", allow_inf_nan=False)
    returncode: int
    timed_out: bool
    elapsed_seconds: float = Field(ge=0)


def _read(path: Path) -> bytes:
    return read_regular(checked_source_path(path))


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _bindings(path: Path) -> dict[str, str]:
    bindings = _Bindings.validate_json(_read(path), strict=True)
    require_evidence(bool(bindings), f"Fresh-cache empty binding manifest: {path.name}")
    for identity in bindings:
        normalized_source_identity(identity)
    return bindings


def _bound(data: bytes, digest: str | None, label: str) -> None:
    require_evidence(_sha(data) == digest, f"Fresh-cache retained binding differs: {label}")


def _process(directory: Path, phase: str, command: list[str]) -> None:
    process = SavedProcess.model_validate_json(_read(directory / f"{phase}-process.json"))
    require_evidence(process.returncode == 0 and not process.timed_out,
                     f"Fresh-cache unsuccessful saved process: {phase}")
    require_evidence(_Command.validate_json(_read(directory / f"{phase}-command.json")) == command,
                     f"Fresh-cache saved command differs: {phase}")
    for stream in ("stdout", "stderr"):
        _read(directory / f"{phase}-{stream}.txt")


def replay_cache(directory: Path) -> None:
    """Require the current packaged authority and coherent saved source/input custody."""
    result = SavedResult.model_validate_json(_read(directory / "result.json"))
    require_evidence(result.status == "observed"
                     and result.freshcache_scope == "minimal_fragment_and_full_merge_only"
                     and result.semantic_validation is False and result.bindings_stable is True
                     and result.observed_case_count == len(result.cases),
                     "Fresh-cache experiment status, scope or bindings differ")
    authority_bytes = _read(directory / "sources" / AUTHORITY)
    packaged = files("rikishi").joinpath("data/fresh-cache-v1.json").read_bytes()
    require_evidence(authority_bytes == packaged, "Fresh-cache retained authority differs from package")
    authority = Authority.model_validate_json(authority_bytes)
    before = _bindings(directory / "bindings-before.json")
    after = _bindings(directory / "bindings-after.json")
    require_evidence(all(after.get(key) == digest for key, digest in before.items()),
                     "Fresh-cache initial bindings differ from after")
    origins = [PurePosixPath(key).parent.parent.parent.parent for key in before
               if key.endswith("/" + AUTHORITY)]
    require_evidence(len(origins) == 1, "Fresh-cache authority binding inventory differs")
    origin = origins[0]
    output = PurePosixPath(normalized_source_identity(result.output))
    require_evidence(output.is_relative_to(origin), "Fresh-cache recorded output escapes origin")
    _bound(authority_bytes, before.get(str(origin / AUTHORITY)), AUTHORITY)
    require_evidence([(case.name, case.scope) for case in result.cases]
                     == [(case.name, case.scope) for case in authority.cases],
                     "Fresh-cache experiment case inventory differs")
    native = NativeEnvironment.model_validate_json(
        _read(directory / "sources/.rikishi/runtime/environment.json"))
    java_home = PurePosixPath(normalized_source_identity(native.JAVA_HOME))
    sigma_home = PurePosixPath(normalized_source_identity(native.SIGMA_HOME))
    initial = {str(origin / name) for name in (*authority.bindings, *_SOURCE_FILES)}
    initial.update(str(origin / name) for name in authority.jar_contents)
    initial.update(str(java_home / name) for name in (
        "bin/java", "bin/javac", "release", "lib/modules", "lib/server/libjvm.dylib"))
    initial.add(str(sigma_home / "KBs/config.xml"))
    require_evidence(set(before) == initial, "Fresh-cache initial binding inventory differs")
    for relative, digest in authority.bindings.items():
        require_evidence(before.get(str(origin / relative)) == digest,
                         f"Fresh-cache authority binding differs: {relative}")
    sources = directory / "sources"
    required_sources = {name for name in authority.bindings if not name.endswith(".jar")}
    required_sources.update(_SOURCE_FILES)
    required_sources.add(_SIGMA)
    require_evidence(all((sources / name).is_file() for name in required_sources),
                     "Fresh-cache required retained sources missing")
    for path in sources.rglob("*"):
        if path.is_file() and path != sources / "sigma-version.properties":
            relative = path.relative_to(sources).as_posix()
            _bound(_read(path), before.get(str(origin / relative)), relative)
    sigma_content = jar_content_identity(sources / _SIGMA,
                                        source_revision=authority.jar_contents[_SIGMA].source_revision)
    with ZipFile(sources / _SIGMA) as archive:
        require_evidence(_read(sources / "sigma-version.properties") == archive.read("version.properties"),
                         "Fresh-cache retained Sigma version stamp differs")
    jars = _Jars.validate_json(_read(directory / "jar-content.json"), strict=True)
    require_evidence(set(jars) == {str(origin / name) for name in authority.jar_contents},
                     "Fresh-cache JAR content inventory differs")
    for relative, expected in authority.jar_contents.items():
        identity = str(origin / relative)
        recorded = jars[identity]
        require_evidence(all(getattr(recorded, field) == getattr(expected, field)
                             for field in type(expected).model_fields)
                         and recorded.archive_sha256 == before[identity],
                         f"Fresh-cache JAR authority or archive binding differs: {relative}")
    require_evidence(sigma_content == jars[str(origin / _SIGMA)],
                     "Fresh-cache retained Sigma content differs")
    classes = _bindings(directory / "jar-classes.json")
    require_evidence(set(classes) == set(jars)
                     and classes[str(origin / _SIGMA)] == jar_classes_sha256(sources / _SIGMA),
                     "Fresh-cache supplementary Sigma classes differ")
    merged = dict(before)
    adapter = _bindings(directory / "adapter-class.json")
    class_id = str(output / "classes/FreshCacheDiagnostic.class")
    require_evidence(set(adapter) == {class_id}, "Fresh-cache adapter binding inventory differs")
    merged.update(adapter)
    _bound(_read(directory / "classes/FreshCacheDiagnostic.class"), adapter[class_id], "adapter class")
    classpath = ":".join(sorted(jars))
    java, javac = str(java_home / "bin/java"), str(java_home / "bin/javac")
    _process(directory, "java-version", [java, "-version"])
    _process(directory, "javac-version", [javac, "-version"])
    _process(directory, "compile", [javac, "-proc:none", "-implicit:none", "-cp", classpath,
                                    "-d", str(output / "classes"), str(output / "sources" / ADAPTER)])
    merge = _read(sources / _MERGE)
    for case, recorded in zip(authority.cases, result.cases, strict=True):
        location = output / case.name
        local = directory / case.name
        inputs = _bindings(local / "input-bindings.json")
        expected_inputs = {str(location / name) for name in ("input.kif", "sigma/KBs/config.xml")}
        require_evidence(set(inputs) == expected_inputs and not merged.keys() & inputs.keys(),
                         "Fresh-cache case binding inventory differs")
        merged.update(inputs)
        for name in ("input.kif", "sigma/KBs/config.xml"):
            data = _read(local / name)
            _bound(data, inputs[str(location / name)], f"{case.name}/{name}")
            expected_bytes = _input(authority, case, merge) if name == "input.kif" else _CONFIG
            require_evidence(data == expected_bytes, f"Fresh-cache controlled input differs: {case.name}")
        environment = TypeAdapter(dict[str, str]).validate_json(_read(local / "environment.json"))
        require_evidence(environment == {"SIGMA_HOME": str(location / "sigma"),
                                        "HOME": str(location), "TMPDIR": str(location / "tmp")},
                         "Fresh-cache case environment differs")
        _process(local, "java", [java, "-Xmx768m", "-Xss2m", "-XX:MaxMetaspaceSize=192m",
                 "-XX:ReservedCodeCacheSize=64m", "-XX:ActiveProcessorCount=2",
                 f"-Duser.home={location}", f"-Djava.io.tmpdir={location / 'tmp'}", "-cp",
                 str(output / "classes") + ":" + classpath, "FreshCacheDiagnostic", str(location),
                 str(location / "input.kif"), str(location / "observation.json")])
        observed = Observation.model_validate_json(_read(local / "observation.json"))
        require_evidence(observed == recorded.observation,
                         "Fresh-cache observation differs from raw report")
        check_observation(observed, case)
    require_evidence(not before.keys() & adapter.keys()
                     and after == merged,
                     "Fresh-cache merged before/adapter/input bindings differ from after")
