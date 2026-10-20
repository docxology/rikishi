import argparse
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

from rikishi.runtime_results import interpret_sigma_result


def main(root: Path | None = None, argv: list[str] | None = None) -> int:
    root = (root or Path(os.environ.get("RIKISHI_ROOT", Path.cwd()))).resolve()
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="A SUO-KIF query translated by upstream Sigma")
    parser.add_argument("--prover", choices=["e", "v"], default="e")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 300:
        parser.error("timeout must be between 1 and 300 seconds")
    environment = json.loads((root / ".rikishi/runtime/environment.json").read_text())
    sigma_source = Path(environment["SIGMA_SRC"])
    command = [str(Path(environment["JAVA_HOME"]) / "bin/java"), "-Xmx10g", "-Xss2m",
               f"-Duser.home={root / '.rikishi/runtime'}",
               f"-Djava.io.tmpdir={root / '.rikishi/runtime/tmp'}", "-cp",
               f"{sigma_source}/build/sigmakee.jar:{sigma_source}/lib/*",
               str(root / "scripts/runtime/RikishiQuery.java"), "-" + args.prover, "-r", "--timeout", str(args.timeout),
               "--ask", args.query]
    output = (args.output or root / ".rikishi/results" / f"sigma-query-{time.time_ns()}.log").resolve()
    if not output.is_relative_to(root):
        parser.error("output must be inside the repository")
    output.parent.mkdir(parents=True, exist_ok=True)
    result_path = output.with_suffix(output.suffix + ".result.json")
    if result_path.exists():
        parser.error("the ATP result path already exists")
    invocation_id = uuid.uuid4().hex
    environment["RIKISHI_ATP_RESULT"] = str(result_path)
    environment["RIKISHI_INVOCATION_ID"] = invocation_id
    timed_out = False
    returncode = None
    with output.open("x") as log:
        try:
            result = subprocess.run(command, env=dict(os.environ, **environment), check=False,
                                    stdout=log, stderr=subprocess.STDOUT, timeout=600 + args.timeout)
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
    report = interpret_sigma_result(result_path, returncode, timed_out, invocation_id=invocation_id)
    print(json.dumps({**report, "returncode": returncode, "log": str(output),
                      "profile": environment["SIGMA_HOME"], "query": args.query,
                      "prover": args.prover, "invocation_id": invocation_id}, indent=2))
    return 0 if report["outcome"] in {"entailed", "not_entailed"} else 2
