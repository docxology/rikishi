import argparse
import json
import os
import subprocess
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("action", choices=["start", "stop", "status", "run"])
args = parser.parse_args()
environment = json.loads((root / ".rikishi/runtime/environment.json").read_text())
env = dict(os.environ, **environment)
env["CATALINA_PID"] = str(root / ".rikishi/runtime/tomcat.pid")
env["CATALINA_OPTS"] = "-Xmx10g -Xss2m -Dfile.encoding=UTF-8"
if args.action == "status":
    with urllib.request.urlopen("http://127.0.0.1:8085/sigma/KBs.jsp", timeout=15) as response:
        print(json.dumps({"url": response.url, "http_status": response.status,
                          "body_bytes": len(response.read())}))
elif args.action == "run":
    subprocess.run([str(Path(env["CATALINA_HOME"]) / "bin/catalina.sh"), "run"], env=env, check=True)
else:
    script = "startup.sh" if args.action == "start" else "shutdown.sh"
    if args.action == "stop":
        env.pop("CATALINA_PID", None)
    subprocess.run([str(Path(env["CATALINA_HOME"]) / "bin" / script)], env=env, check=True)
