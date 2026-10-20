import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from uuid import uuid4

import pytest

from rikishi.runtime_query import main as query
from rikishi.runtime_server import main as server
from rikishi.runtime_setup import main as setup


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


@pytest.mark.integration
def test_installed_bootstrap_is_repeatable():
    setup([])


@pytest.mark.integration
def test_real_native_query_binds_structured_result(project_root, tmp_path, capsys):
    output = project_root / ".rikishi/results" / (uuid4().hex + ".log")
    outcome = query(project_root, ["(subclass Human Animal)", "--output", str(output)])
    report = json.loads(capsys.readouterr().out)
    sidecar = json.loads(output.with_suffix(".log.result.json").read_text())
    assert outcome == 0
    assert report["outcome"] == "entailed"
    assert report["consistency"] == "not_established"
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
