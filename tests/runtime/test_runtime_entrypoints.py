import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from uuid import uuid4

import pytest

from rikishi.runtime_query import QueryBudgets, _query_budgets, run_query
from rikishi.runtime_query import main as query
from rikishi.runtime_query_profile import snapshot_profile, verify_profile
from rikishi.runtime_server import main as server


def test_imports_do_not_parse_arguments_or_launch_runtime(tmp_path):
    probe = (
        "import importlib, sys; sys.argv=['import-probe', '--invalid-import-option']; "
        "[importlib.import_module(name) for name in sys.argv_modules]; print('import-safe')"
    )
    modules = ["rikishi.runtime_query", "rikishi.runtime_setup", "rikishi.runtime_server"]
    environment = dict(os.environ, RIKISHI_ROOT=str(tmp_path))
    command = "import sys; sys.argv_modules=" + repr(modules) + "; " + probe
    result = subprocess.run([sys.executable, "-c", command], cwd=tmp_path,
                            env=environment, capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "import-safe"
    assert not (tmp_path / ".rikishi").exists()
    (tmp_path / "unsafe_import.py").write_text("import argparse\nargparse.ArgumentParser().parse_args()\n")
    command = "import sys; sys.argv_modules=['unsafe_import']; " + probe
    control = subprocess.run([sys.executable, "-c", command], cwd=tmp_path,
                             env=environment, capture_output=True, text=True, timeout=10, check=False)
    assert control.returncode == 2
    assert "unrecognized arguments" in control.stderr
    assert "import-safe" not in control.stdout


@pytest.mark.parametrize("timeout", ["0", "301"])
def test_query_rejects_invalid_timeout_before_reading_environment(tmp_path, timeout):
    with pytest.raises(SystemExit) as caught:
        query(tmp_path, ["(subclass Human Animal)", "--timeout", timeout])
    assert caught.value.code == 2


def test_query_api_rejects_invalid_prover_and_external_output(tmp_path):
    root = tmp_path / "empty-repository"
    root.mkdir()
    with pytest.raises(ValueError, match="prover must"):
        run_query(root, "(subclass Human Animal)", prover="invalid")
    with pytest.raises(ValueError, match="inside the repository"):
        run_query(root, "(subclass Human Animal)", output=tmp_path / "unowned.log")
    assert list(root.iterdir()) == []
    assert not (tmp_path / "unowned.log").exists()


@pytest.mark.parametrize("wall", [0, -1, 3601, True, 1.5, float("inf")])
def test_query_rejects_invalid_wall_budget_before_environment(tmp_path, wall):
    with pytest.raises(ValueError, match="prover_wall_seconds"):
        run_query(tmp_path, "(subclass Human Animal)", prover_wall_timeout=wall)
    assert list(tmp_path.iterdir()) == []


def test_query_cli_rejects_invalid_wall_budget_before_environment(tmp_path, capsys):
    with pytest.raises(SystemExit) as caught:
        query(tmp_path, ["(subclass Human Animal)", "--prover-wall-timeout", "0"])
    assert caught.value.code == 2
    assert "prover_wall_seconds" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("native", [0, 301, True, 1.5, "15", float("nan")])
def test_query_native_budget_is_strict_before_environment(tmp_path, native):
    with pytest.raises(ValueError, match="native_limit_seconds"):
        run_query(tmp_path, "(subclass Human Animal)", timeout=native)
    assert list(tmp_path.iterdir()) == []


def test_explicit_wall_preserves_native_limit_and_declares_distinct_java_budget():
    default = _query_budgets(5, None)
    explicit = _query_budgets(5, 10)
    assert default.model_dump() == {"mode": "default", "native_limit_seconds": 5,
                                    "prover_wall_seconds": 10, "java_wall_seconds": 605}
    assert explicit.model_dump() == {"mode": "explicit-wall", "native_limit_seconds": 5,
                                     "prover_wall_seconds": 10, "java_wall_seconds": 610}


@pytest.mark.parametrize("mode,wall,java", [("default", 300, 605), ("explicit-wall", 10, 605)])
def test_saved_budget_policy_rejects_inconsistent_mode(mode, wall, java):
    with pytest.raises(ValueError, match="Budget values differ"):
        QueryBudgets(mode=mode, native_limit_seconds=5, prover_wall_seconds=wall,
                     java_wall_seconds=java)


@pytest.mark.integration
def test_installed_bootstrap_is_repeatable(project_root, tmp_path):
    """Build a real private installation twice without redeploying a live service."""
    source = project_root / ".rikishi"
    canonical = snapshot_profile(source / "sigma/core")
    war = source / "runtime/apache-tomcat-9.0.123/webapps/sigma.war"
    original_war = (hashlib.sha256(war.read_bytes()).hexdigest(), war.stat().st_mtime_ns)
    private = tmp_path / "installed-bootstrap"
    shutil.copytree(project_root / "config", private / "config")

    def omit_live_monitor_socket(directory, names):
        # A running source repository's IPC endpoint is not a Git object or build input.
        return [name for name in names if Path(directory).name == ".git"
                and name == "fsmonitor--daemon.ipc"
                and stat.S_ISSOCK((Path(directory) / name).lstat().st_mode)]

    for path in (source / "upstream").rglob("*"):
        if path.is_symlink():
            assert not Path(os.readlink(path)).is_absolute()
            assert path.resolve().is_relative_to(source / "upstream")
    shutil.copytree(source / "upstream", private / ".rikishi/upstream",
                    symlinks=True, ignore=omit_live_monitor_socket)
    runtime = private / ".rikishi/runtime"
    for name in ("jdk-21.0.12.1+1", "apache-ant-1.10.18", "WordNet-3.0"):
        shutil.copytree(source / "runtime" / name, runtime / name)
    shutil.copy2(source / "runtime/vampire", runtime / "vampire")
    tomcat = runtime / "apache-tomcat-9.0.123"
    for name in ("bin", "lib", "conf"):
        shutil.copytree(source / "runtime/apache-tomcat-9.0.123" / name, tomcat / name)
    for name in ("webapps", "temp", "work", "logs"):
        (tomcat / name).mkdir()
    for checkout in (private / ".rikishi/upstream").iterdir():
        subprocess.run(["git", "-C", str(checkout), "config", "--local",
                        "core.fsmonitor", "false"], check=True, capture_output=True)
    environment = dict(os.environ, RIKISHI_ROOT=str(private),
                       RIKISHI_VAULT_ROOT=str(project_root.parents[3]))
    for attempt in range(2):
        completed = subprocess.run(
            [sys.executable, "-c", "from rikishi.runtime_setup import main; main([])"],
            cwd=private, env=environment, capture_output=True, text=True, timeout=1800,
            check=False,
        )
        (private / f"bootstrap-{attempt}.stdout").write_text(completed.stdout)
        (private / f"bootstrap-{attempt}.stderr").write_text(completed.stderr)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        installed = json.loads((runtime / "environment.json").read_text())
        for key in ("JAVA_HOME", "CATALINA_HOME", "SIGMA_HOME", "ONTOLOGYPORTAL_GIT",
                    "SIGMA_SRC"):
            assert Path(installed[key]).resolve().is_relative_to(private)
        assert (tomcat / "webapps/sigma.war").is_file()
        assert (tomcat / "webapps/sigma/WEB-INF/web.xml").is_file()
        assert not (runtime / "tomcat.pid").exists()
        verify_profile(canonical)
        assert (hashlib.sha256(war.read_bytes()).hexdigest(), war.stat().st_mtime_ns) == original_war


@pytest.mark.integration
def test_real_native_query_binds_structured_result(project_root, tmp_path, capsys):
    output = project_root / ".rikishi/results" / (uuid4().hex + ".log")
    outcome = query(project_root, ["(subclass Human Animal)", "--output", str(output),
                                   "--prover-wall-timeout", "300"])
    report = json.loads(capsys.readouterr().out)
    sidecar = json.loads(output.with_suffix(".log.result.json").read_text())
    assert outcome == 0
    assert report["budgets"] == {"mode": "explicit-wall", "native_limit_seconds": 15,
                                  "prover_wall_seconds": 300, "java_wall_seconds": 900}
    budget_bytes = Path(report["budgets_path"]).read_bytes()
    assert json.loads(budget_bytes) == report["budgets"]
    assert hashlib.sha256(budget_bytes).hexdigest() == report["provenance"]["query_budgets_sha256"]
    assert report["outcome"] == "entailed"
    assert report["consistency"] == "not_established"
    assert report["validation_scope"] == "translated_query_only"
    assert not report["semantic_validation"]
    assert report["evidence"] == "sha256_verified"
    assert report["negative_control_context"] == "contradictory_translated_axioms_previously_observed"
    assert report["negative_control_context_binding"]["scope"] == (
        "complete_translated_background_statement_sequence"
    )
    assert sidecar["invocation_id"] == report["invocation_id"]
    with pytest.raises(SystemExit):
        query(project_root, ["(subclass Human Animal)", "--output", str(output)])


def test_status_with_real_http(tmp_path, capsys):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Sigma status fixture" * 10)

    runtime = tmp_path / ".rikishi/runtime"
    runtime.mkdir(parents=True)
    (runtime / "environment.json").write_text("{}")
    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as http:
        thread = Thread(target=http.serve_forever)
        thread.start()
        try:
            server(tmp_path, ["status", "--url", f"http://127.0.0.1:{http.server_port}/sigma/KBs.jsp"])
        finally:
            http.shutdown()
            thread.join()
    report = json.loads(capsys.readouterr().out)
    assert report["http_status"] == 200
    assert report["body_bytes"] > 100
