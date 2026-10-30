from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import TypedDict

from rikishi.fep import DECLARATIONS, PIN

MODULES = ("finite_probability", "finite_information")


class FormalVerificationError(RuntimeError):
    pass


class CompilationReceipt(TypedDict):
    commit: str
    workspace: str
    compiler: str
    compiler_version: str
    compiler_sha256: str
    source_sha256: dict[str, str]
    dependency_revisions: dict[str, str]
    compiled_sha256: dict[str, str]
    import_artifacts_sha256: dict[str, str]
    dependency_cache_sha256: dict[str, str]
    dependency_cache_files: int
    declaration_axioms: str
    commands: list[list[str]]
    scope: str


def _git(repo: Path, *arguments: str) -> bytes:
    return subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *arguments], check=True,
                          capture_output=True, timeout=30).stdout


def verify_formalization(
    repo: Path, compiler: Path, output: Path, *, revision: str = PIN,
    packages: Path | None = None, timeout: int = 180,
) -> CompilationReceipt:
    """Compile pinned finite modules in a new workspace using checked dependency revisions.

    The canonical checkout and its build tree are read-only inputs. This verifies
    Lean elaboration and reports declaration axioms; it proves no SUMO translation.
    """
    if not 1 <= timeout <= 600:
        raise ValueError("compiler timeout must be between 1 and 600 seconds")
    repo = repo.resolve(strict=True)
    compiler = compiler.resolve(strict=True)
    compiler_digest = hashlib.sha256(compiler.read_bytes()).hexdigest()
    commit = _git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    expected = _git(repo, "show", f"{commit}:lean/lean-toolchain").decode().strip()
    manifest = json.loads(_git(repo, "show", f"{commit}:lean/lake-manifest.json"))
    version = subprocess.run([str(compiler), "--version"], check=True, capture_output=True,
                             text=True, timeout=10).stdout.strip()
    match = re.search(r"lean4:v([0-9.]+)$", expected)
    if match is None or f"version {match.group(1)}," not in version:
        raise FormalVerificationError("Compiler version differs from pinned lean-toolchain")
    package_root = (packages or repo / "lean/.lake/packages").resolve(strict=True)
    output = output.resolve()
    if any(output.is_relative_to(directory)
           for directory in (repo, package_root, compiler.parent.parent)):
        raise FormalVerificationError("Output overlaps canonical input")
    revisions: dict[str, str] = {}
    libraries = []
    for dependency in manifest["packages"]:
        name, pin = dependency["name"], dependency["rev"]
        checkout = package_root / name
        if not checkout.resolve().is_relative_to(package_root):
            raise FormalVerificationError(f"Dependency escapes package root: {name}")
        actual = _git(checkout, "rev-parse", "HEAD").decode().strip()
        dirty = _git(checkout, "status", "--porcelain", "--untracked-files=no").strip()
        if actual != pin or dirty:
            raise FormalVerificationError(f"Dependency revision or tracked source differs: {name}")
        library = checkout / ".lake/build/lib/lean"
        revisions[name] = actual
        libraries.append(library)
    cache_roots = [*libraries, compiler.parent.parent / "lib/lean"]
    if any(output.is_relative_to(library.resolve()) for library in cache_roots):
        raise FormalVerificationError("Output overlaps canonical input")
    if output.exists():
        raise FileExistsError(output)
    before, cache_files = _cache_snapshot(cache_roots)
    output.mkdir(parents=True, exist_ok=False)
    sources = output / "FepSketches"
    sources.mkdir()
    compiled = output / "lib/FepSketches"
    compiled.mkdir(parents=True)
    temporary = output / "tmp"
    temporary.mkdir()
    home = output / "home"
    home.mkdir()
    environment = {"PATH": str(compiler.parent) + os.pathsep + os.defpath,
                   "HOME": str(home), "TMPDIR": str(temporary),
                   "LEAN_PATH": os.pathsep.join(str(p) for p in [compiled.parent, *libraries])}
    source_hashes: dict[str, str] = {}
    compiled_hashes: dict[str, str] = {}
    import_hashes: dict[str, str] = {}
    commands: list[list[str]] = []
    for name in MODULES:
        relative = f"lean/FepSketches/{name}.lean"
        raw = _git(repo, "show", f"{commit}:{relative}")
        source = sources / f"{name}.lean"
        source.write_bytes(raw)
        source_hashes[relative] = hashlib.sha256(raw).hexdigest()
        target = compiled / f"{name}.olean"
        command = [str(compiler), "-DwarningAsError=true", "-o", str(target), str(source)]
        commands.append(command)
        _compile(command, output, environment, timeout, output / f"{name}.log")
        compiled_hashes[target.relative_to(output).as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
        dependency_command = [str(compiler), "--deps", str(source)]
        commands.append(dependency_command)
        dependencies = _compile(dependency_command, output, environment,
                                timeout, output / f"{name}-imports.log")
        for line in dependencies.splitlines():
            artifact = Path(line).resolve(strict=True)
            for candidate in (artifact, Path(str(artifact) + ".private"), Path(str(artifact) + ".server")):
                if candidate.is_file():
                    import_hashes[str(candidate)] = hashlib.sha256(candidate.read_bytes()).hexdigest()
    audit = output / "DeclarationAudit.lean"
    module_header = "module\n" if (compiled / "finite_information.olean.private").is_file() else ""
    audit.write_text(module_header + "import FepSketches.finite_information\n" + "\n".join(
        f"#print axioms FEP.FiniteInformation.{name}" for name in DECLARATIONS
    ) + "\n", encoding="utf-8")
    commands.append([str(compiler), str(audit)])
    axioms = _compile(commands[-1], output, environment, timeout,
                      output / "declaration-axioms.log")
    _check_axioms(axioms)
    source_hashes["generated/DeclarationAudit.lean"] = hashlib.sha256(audit.read_bytes()).hexdigest()
    compiled_hashes.update({path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in sorted(compiled.iterdir()) if path.is_file()})
    after, after_files = _cache_snapshot(cache_roots)
    _require_stable_cache(before, after)
    if cache_files != after_files:
        raise FormalVerificationError("Compiled dependency inventory changed during verification")
    if hashlib.sha256(compiler.read_bytes()).hexdigest() != compiler_digest:
        raise FormalVerificationError("Compiler executable changed during verification")
    for name, pin in revisions.items():
        checkout = package_root / name
        if (_git(checkout, "rev-parse", "HEAD").decode().strip() != pin
                or _git(checkout, "status", "--porcelain", "--untracked-files=no").strip()):
            raise FormalVerificationError(f"Dependency source changed during verification: {name}")
    receipt = CompilationReceipt(
        commit=commit, workspace=str(output), compiler=str(compiler), compiler_version=version,
        compiler_sha256=compiler_digest,
        source_sha256=source_hashes, dependency_revisions=revisions,
        compiled_sha256=compiled_hashes, import_artifacts_sha256=import_hashes,
        dependency_cache_sha256=after, dependency_cache_files=cache_files,
        declaration_axioms=axioms,
        commands=commands,
        scope="Pinned finite-module Lean elaboration and declaration-axiom inspection with stable complete compiled-library snapshots, a superset of transitive imports; no SUMO equivalence or empirical FEP claim.",
    )
    (output / "verification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def _cache_snapshot(libraries: list[Path]) -> tuple[dict[str, str], int]:
    roots: dict[str, str] = {}
    count = 0
    for library in libraries:
        for component in (library, *library.parents):
            if component.is_symlink():
                raise FormalVerificationError(f"Symlinked compiled dependency: {component}")
        digest = hashlib.sha256()
        for artifact in sorted(library.rglob("*")):
            if artifact.is_symlink():
                raise FormalVerificationError(f"Symlinked compiled dependency: {artifact}")
            if artifact.is_file() and artifact.name.endswith((
                ".olean", ".olean.private", ".olean.server", ".ir", ".ir.sig", ".so", ".dylib",
            )):
                digest.update(artifact.relative_to(library).as_posix().encode() + b"\x00")
                digest.update(hashlib.sha256(artifact.read_bytes()).digest())
                count += 1
        roots[str(library.resolve())] = digest.hexdigest()
    return roots, count


def _require_stable_cache(before: dict[str, str], after: dict[str, str]) -> None:
    if before != after:
        raise FormalVerificationError("Compiled dependency cache changed during verification")


def _check_axioms(text: str) -> None:
    allowed = {"propext", "Classical.choice", "Quot.sound"}
    for name in DECLARATIONS:
        marker = f"'FEP.FiniteInformation.{name}' "
        matches = [line.removeprefix(marker) for line in text.splitlines() if line.startswith(marker)]
        if len(matches) != 1:
            raise FormalVerificationError(f"Missing or repeated declaration audit: {name}")
        if matches[0] == "does not depend on any axioms":
            continue
        parsed = re.fullmatch(r"depends on axioms: \[(.*)\]", matches[0])
        if parsed is None or set(parsed.group(1).split(", ")) - allowed:
            raise FormalVerificationError(f"Unapproved declaration axioms: {name}: {matches[0]}")


def _compile(command: list[str], directory: Path, environment: dict[str, str],
             timeout: int, log: Path) -> str:
    try:
        result = subprocess.run(command, cwd=directory, env=environment, capture_output=True,
                                text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as error:
        log.write_bytes((error.stdout or b"") + (error.stderr or b"")
                        + f"\nCompiler exceeded {timeout} seconds\n".encode())
        raise FormalVerificationError(f"Compiler exceeded {timeout} seconds; see {log}") from error
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise FormalVerificationError(f"Lean rejected input (exit {result.returncode}); see {log}")
    return result.stdout
