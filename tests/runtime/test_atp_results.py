import json

import pytest

from rikishi.runtime_results import interpret_sigma_result


@pytest.mark.parametrize("payload", [
    "{", "null", "[]", '{}',
    '{"status":true,"atp_returncode":0,"stdout_lines":1}',
    '{"status":"Theorem","atp_returncode":false,"stdout_lines":1}',
    '{"status":"Theorem","atp_returncode":"0","stdout_lines":1}',
    '{"status":"Theorem","atp_returncode":0,"stdout_lines":-1}',
    '{"status":"Theorem","atp_returncode":0,"stdout_lines":1,"proved":true}',
])
def test_untrusted_sidecars_fail_closed(tmp_path, payload):
    sidecar = tmp_path / "result.json"
    sidecar.write_text(payload)
    result = interpret_sigma_result(sidecar, 0)
    assert result["outcome"] == "error"
    assert result["status"] == "InvalidATPResult"
    assert not result["proved"]


@pytest.mark.parametrize("identity,java_exit,expected", [
    ("current", 0, "entailed"), ("stale", 0, "error"),
    (None, 0, "error"), ("current", None, "error"),
])
def test_sidecars_bound_to_completed_invocation(tmp_path, identity, java_exit, expected):
    sidecar = tmp_path / "result.json"
    sidecar.write_text(json.dumps({"status": "Theorem", "atp_returncode": 0,
                                  "stdout_lines": 1, "invocation_id": identity}))
    assert interpret_sigma_result(sidecar, java_exit, invocation_id="current")["outcome"] == expected


@pytest.mark.parametrize("status,exit_code", [("ContradictoryAxioms", 3), ("CounterSatisfiable", 9), ("NoSZSStatus", 0)])
def test_failed_atp_cannot_certify_result(tmp_path, status, exit_code):
    sidecar = tmp_path / "result.json"
    sidecar.write_text(json.dumps({"status": status, "atp_returncode": exit_code, "stdout_lines": 1}))
    result = interpret_sigma_result(sidecar, 0)
    assert result["outcome"] == "error"
    assert result["consistency"] == "not_established"


def test_timeout_does_not_read_even_malformed_sidecar(tmp_path):
    sidecar = tmp_path / "result.json"
    sidecar.write_text("broken")
    result = interpret_sigma_result(sidecar, None, True)
    assert result["status"] == "Timeout"
    assert result["outcome"] == "inconclusive"
