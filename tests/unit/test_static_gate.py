import json
import subprocess


def test_real_type_checker_rejects_incorrect_assignment(tmp_path):
    (tmp_path / "pyrightconfig.json").write_text(json.dumps({
        "typeCheckingMode": "standard", "include": ["example.py"],
    }))
    source = tmp_path / "example.py"
    source.write_text('count: int = 7\n')
    command = ["uv", "run", "basedpyright", "--project", str(tmp_path), "--outputjson"]
    positive = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    assert positive.returncode == 0, positive.stdout + positive.stderr
    assert json.loads(positive.stdout)["summary"]["errorCount"] == 0
    source.write_text('count: int = "incorrect"\n')
    negative = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    assert negative.returncode != 0
    diagnostics = json.loads(negative.stdout)
    assert diagnostics["summary"]["errorCount"] > 0
    assert any(row.get("rule") == "reportAssignmentType" for row in diagnostics["generalDiagnostics"])
