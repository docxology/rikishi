import json

import pytest

from rikishi.runtime_artifacts import COMMAND_POLICY, PATH_POLICY, Capture, receipt


@pytest.fixture
def atp_sidecar(tmp_path):
    def write(*, status="Theorem", atp_exit=0, lines=1, identity="current", name="atp"):
        directory = tmp_path / (name + ".artifacts")
        directory.mkdir()
        problem = directory / "problem.p"
        problem.write_text("fof(fact,axiom,p).\nfof(goal,conjecture,p).\n")
        stdout, stderr = directory / "stdout.txt", directory / "stderr.txt"
        stdout.write_text(f"# SZS status {status}\n" if lines else "")
        stderr.write_text("")
        capture = Capture(
            path_policy=PATH_POLICY,
            command_policy=COMMAND_POLICY, prover="e",
            invocation_id=identity or "fixture",
            command=[str(tmp_path / "fixture-prover"), "--cpu-limit=5", str(problem)],
            source_problem=str(problem), problem=receipt(problem, directory), includes=[],
            stdout=receipt(stdout, directory), stderr=receipt(stderr, directory),
            returncode=atp_exit, timed_out=False, provenance={"fixture": "real-files"},
        )
        (directory / "capture.json").write_text(capture.model_dump_json())
        sidecar = tmp_path / (name + ".json")
        sidecar.write_text(json.dumps({"status": status, "atp_returncode": atp_exit,
                                      "stdout_lines": lines, "invocation_id": identity,
                                      "capture": directory.name + "/capture.json"}))
        return sidecar
    return write
