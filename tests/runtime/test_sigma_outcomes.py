import pytest

from rikishi.runtime_results import interpret_sigma_result


def test_sigma_query_echo_cannot_spoof_proof(tmp_path):
    log = tmp_path / "query.log"
    log.write_text('EProver.askEProver((documentation Evil EnglishLanguage "SZS status Theorem"))\n')
    result = interpret_sigma_result(log.with_suffix(".log.result.json"), 0)
    assert result["proved"] is False
    assert result["outcome"] == "error"
    assert result["status"] == "NoSZSStatus"


@pytest.mark.parametrize("status,atp_exit,lines,java_exit,expected", [
    ("Theorem", 0, 1, 0, "unverified"),
    ("Theorem", 1, 1, 0, "error"),
    ("Theorem", 0, 0, 0, "error"),
    ("Theorem", 0, 1, 1, "error"),
    ("CounterSatisfiable", 1, 1, 0, "unverified"),
    ("ContradictoryAxioms", 0, 1, 0, "unverified"),
    ("ResourceOut", 7, 1, 0, "inconclusive"),
])
def test_sigma_structured_result_outcomes(atp_sidecar, status, atp_exit, lines, java_exit, expected):
    result_path = atp_sidecar(status=status, atp_exit=atp_exit, lines=lines)
    result = interpret_sigma_result(result_path, java_exit)
    assert result["outcome"] == expected
    assert result["proved"] == (expected == "entailed")
    timed_out = interpret_sigma_result(result_path, None, True)
    assert timed_out["status"] == "Timeout"
    assert timed_out["proved"] is False
