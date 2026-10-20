import argparse
import json
import os
import subprocess
import urllib.request
from pathlib import Path


def main(root: Path | None = None, argv: list[str] | None = None) -> None:
    root = (root or Path(os.environ.get("RIKISHI_ROOT", Path.cwd()))).resolve()
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "status", "run"])
    parser.add_argument("--url", default="http://127.0.0.1:8085/sigma/KBs.jsp")
    args = parser.parse_args(argv)
    environment = json.loads((root / ".rikishi/runtime/environment.json").read_text())
    env = dict(os.environ, **environment)
    env["CATALINA_PID"] = str(root / ".rikishi/runtime/tomcat.pid")
    env["CATALINA_OPTS"] = "-Xmx10g -Xss2m -Dfile.encoding=UTF-8"
    if args.action == "status":
        with urllib.request.urlopen(args.url, timeout=15) as response:
            print(json.dumps({"url": response.url, "http_status": response.status,
                              "body_bytes": len(response.read())}))
        return
    scripts = {"run": ["catalina.sh", "run"], "start": ["startup.sh"], "stop": ["shutdown.sh"]}
    if args.action == "stop":
        env.pop("CATALINA_PID", None)
    script, *arguments = scripts[args.action]
    subprocess.run([str(Path(env["CATALINA_HOME"]) / "bin" / script), *arguments], env=env, check=True)
