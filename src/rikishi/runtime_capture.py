"""Invocation-local native executable adapter; never changes an upstream checkout."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from rikishi.runtime_artifacts import (
    COMMAND_POLICY,
    PATH_POLICY,
    ArtifactError,
    Capture,
    IncludedArtifact,
    ProverKind,
    checked_source_path,
    expanded_problem,
    read_regular,
    receipt,
    validate_prover_command,
)
from rikishi.runtime_process import run_bounded
from rikishi.runtime_tptp import TPTPError, parse_tptp


def capture_prover(
    command: list[str], directory: Path, *, invocation_id: str,
    provenance: dict[str, str], timeout: float,
    prover: ProverKind = "e",
) -> Capture:
    """Save the exact submitted problem and transitive includes before launch."""
    if not command:
        raise ArtifactError("prover command is empty")
    executable = Path(command[0]).resolve(strict=True)
    if (not Path(command[0]).is_absolute()
            or hashlib.sha256(read_regular(executable)).hexdigest() != provenance.get("prover_sha256")):
        raise ArtifactError("command executable does not match its recorded prover hash")
    validate_prover_command(command, prover)
    source = checked_source_path(Path(command[-1]))
    run_command = [str(executable), *command[1:-1], str(source)]
    problem = directory / "problem.p"
    problem.write_bytes(read_regular(source))
    snapshots = [(Path(command[-1]), problem)]
    includes: list[IncludedArtifact] = []
    seen: set[str] = set()
    saved_sources: dict[str, Path] = {}

    def save_includes(path: Path) -> None:
        try:
            statements = parse_tptp(read_regular(path).decode("utf-8"))
        except TPTPError as error:
            raise ArtifactError(f"unsupported TPTP input: {error}") from error
        for statement in statements:
            if statement.kind != "include":
                continue
            if statement.include_path is None:
                raise ArtifactError("include directive has no path")
            lexical = path.parent / statement.include_path
            target = checked_source_path(lexical)
            if str(target) in seen:
                snapshots.append((lexical, saved_sources[str(target)]))
                continue
            seen.add(str(target))
            saved = directory / f"include-{len(includes)}.p"
            saved.write_bytes(read_regular(target))
            saved_sources[str(target)] = saved
            snapshots.append((lexical, saved))
            includes.append(IncludedArtifact(**receipt(saved, directory).model_dump(), source=str(target)))
            save_includes(target)

    save_includes(source)
    stdout, stderr = directory / "stdout.txt", directory / "stderr.txt"
    process = run_bounded(run_command, cwd=source.parent, stdout=stdout, stderr=stderr, timeout=timeout)
    for lexical, saved in snapshots:
        original = checked_source_path(lexical)
        if read_regular(original) != read_regular(saved):
            raise ArtifactError(f"ATP input changed during execution: {original}")
    if hashlib.sha256(read_regular(executable)).hexdigest() != provenance["prover_sha256"]:
        raise ArtifactError("prover executable changed during execution")
    capture = Capture(
        path_policy=PATH_POLICY,
        command_policy=COMMAND_POLICY, prover=prover,
        invocation_id=invocation_id, command=run_command, source_problem=str(source),
        problem=receipt(problem, directory), includes=includes,
        stdout=receipt(stdout, directory), stderr=receipt(stderr, directory),
        returncode=process.returncode, timed_out=process.timed_out, provenance=provenance,
    )
    expanded_problem(capture, directory)
    with (directory / "capture.json").open("x") as stream:
        stream.write(capture.model_dump_json(indent=2))
    return capture


def main(environment: Mapping[str, str] | None = None, argv: Sequence[str] | None = None) -> int:
    environment = os.environ if environment is None else environment
    directory = Path(environment["RIKISHI_ATP_CAPTURE"])
    kind = environment.get("RIKISHI_PROVER_KIND", "e")
    prover: ProverKind
    if kind == "e":
        prover = "e"
    elif kind == "v":
        prover = "v"
    else:
        raise ArtifactError("unsupported native prover kind")
    capture = capture_prover(
        [environment["RIKISHI_REAL_PROVER"], *(sys.argv[1:] if argv is None else argv)], directory,
        invocation_id=environment["RIKISHI_INVOCATION_ID"],
        provenance=json.loads(environment["RIKISHI_PROVENANCE"]),
        timeout=float(environment["RIKISHI_PROVER_WALL_TIMEOUT"]),
        prover=prover,
    )
    sys.stdout.buffer.write(read_regular(directory / capture.stdout.path))
    sys.stderr.buffer.write(read_regular(directory / capture.stderr.path))
    return capture.returncode if capture.returncode >= 0 else 128 - capture.returncode


if __name__ == "__main__":
    raise SystemExit(main())
