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
    ("current", 0, "unverified"), ("stale", 0, "error"),
    (None, 0, "error"), ("current", None, "error"),
])
def test_sidecars_bound_to_completed_invocation(atp_sidecar, identity, java_exit, expected):
    sidecar = atp_sidecar(identity=identity)
    assert interpret_sigma_result(sidecar, java_exit, invocation_id="current")["outcome"] == expected


@pytest.mark.parametrize("status,exit_code", [("ContradictoryAxioms", 3), ("CounterSatisfiable", 9), ("NoSZSStatus", 0)])
def test_failed_atp_cannot_certify_result(atp_sidecar, status, exit_code):
    sidecar = atp_sidecar(status=status, atp_exit=exit_code)
    result = interpret_sigma_result(sidecar, 0)
    assert result["outcome"] == "error"
    assert result["consistency"] == "not_established"


def test_timeout_does_not_read_even_malformed_sidecar(tmp_path):
    sidecar = tmp_path / "result.json"
    sidecar.write_text("broken")
    result = interpret_sigma_result(sidecar, None, True)
    assert result["status"] == "Timeout"
    assert result["outcome"] == "inconclusive"
