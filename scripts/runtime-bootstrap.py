from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".rikishi"
RUNTIME = STATE / "runtime"
UPSTREAM = STATE / "upstream"


def run(command: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def archive(url: str, filename: str, digest: str, algorithm: str = "sha512") -> None:
    target = RUNTIME / filename
    if not target.exists():
        run(["curl", "--fail", "--location", "--retry", "3", url, "--output", str(target)])
    with target.open("rb") as source:
        actual = hashlib.file_digest(source, algorithm).hexdigest()
    if actual != digest:
        raise ValueError(f"Checksum mismatch for {target}; preserve and inspect the download")
    with tarfile.open(target) as package:
        package.extractall(RUNTIME, filter="data")


def ensure_repository(destination: Path, pin: dict[str, str]) -> None:
    if not destination.exists():
        run(["git", "init", str(destination)])
        run(["git", "remote", "add", "origin", pin["url"]], destination)
    revision = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=destination,
                              text=True, capture_output=True, check=False)
    if revision.returncode != 0:
        changes = subprocess.check_output(["git", "status", "--porcelain"], cwd=destination, text=True)
        if changes.strip():
            raise RuntimeError(f"{destination.name}: incomplete checkout has local files; refusing overwrite")
        remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=destination,
                                text=True, capture_output=True, check=False)
        if remote.returncode != 0:
            run(["git", "remote", "add", "origin", pin["url"]], destination)
        run(["git", "fetch", "--depth", "1", pin["url"], pin["commit"]], destination)
        run(["git", "checkout", "--detach", pin["commit"]], destination)
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=destination,
                                  text=True, capture_output=True, check=True)
    if revision.stdout.strip() != pin["commit"]:
        raise RuntimeError(f"{destination.name}: expected {pin['commit']}, found {revision.stdout.strip()}; refusing reset")


def copy_corpus(source: Path, kb: Path, revision: str) -> None:
    marker = kb.parent / "sumo-source.json"
    if marker.exists():
        if json.loads(marker.read_text())["commit"] != revision:
            raise RuntimeError("Sigma KB copy comes from a different SUMO pin; preserve it and create a fresh profile")
        return
    files = [item for item in source.rglob("*")
             if not item.relative_to(source).parts[0].startswith(".") and item.is_file()]
    for item in files:
        destination = kb / item.relative_to(source)
        if destination.exists() and (not destination.is_file() or destination.read_bytes() != item.read_bytes()):
            raise RuntimeError(f"Existing unmarked Sigma file differs: {destination}; preserve it before adopting this profile")
    kb.mkdir(parents=True, exist_ok=True)
    for item in files:
        destination = kb / item.relative_to(source)
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)
    marker.write_text(json.dumps({"commit": revision}) + "\n")


def apply_compatibility_patch(checkout: Path, specification: dict[str, str]) -> None:
    patch = ROOT / specification["path"]
    if hashlib.sha256(patch.read_bytes()).hexdigest() != specification["sha256"]:
        raise RuntimeError("Compatibility patch checksum mismatch")
    target = checkout / specification["source"]
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if digest == specification["after_sha256"]:
        return
    if digest != specification["before_sha256"]:
        raise RuntimeError("Compatibility patch source has unexpected edits; refusing overwrite")
    run(["git", "apply", "--check", str(patch)], checkout)
    run(["git", "apply", str(patch)], checkout)
    if hashlib.sha256(target.read_bytes()).hexdigest() != specification["after_sha256"]:
        raise RuntimeError("Compatibility patch produced unexpected content")


def main() -> None:
    parser = argparse.ArgumentParser()
    profiles = parser.add_mutually_exclusive_group()
    profiles.add_argument("--core-only", action="store_true", help="Load the default upstream core and mid-level profile")
    profiles.add_argument("--all-domains", action="store_true", help="Explore every top-level KIF, including demo subsets")
    args = parser.parse_args()
    vault = Path(os.environ.get("RIKISHI_VAULT_ROOT", str(ROOT.parents[3]))).resolve()
    if not vault.is_mount():
        raise RuntimeError("GitVault must be mounted before bootstrap")
    if not ROOT.is_relative_to(vault):
        raise RuntimeError("Bootstrap checkout must reside on GitVault")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    UPSTREAM.mkdir(exist_ok=True)
    tmp = RUNTIME / "tmp"
    tmp.mkdir(exist_ok=True)
    os.environ["TMPDIR"] = str(tmp)
    lock = json.loads((ROOT / "config/sumo.lock.json").read_text())
    for name, pin in lock["repositories"].items():
        ensure_repository(UPSTREAM / name, pin)
    changes = subprocess.check_output(["git", "status", "--porcelain"], cwd=UPSTREAM / "sumo", text=True)
    if changes.strip():
        raise RuntimeError("SUMO source checkout has local changes; refusing to certify it as pinned")
    for specification in lock["patches"]:
        apply_compatibility_patch(UPSTREAM / specification["repository"], specification)
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        java = RUNTIME / "jdk-21.0.12.1+1/Contents/Home"
        if not java.exists():
            archive("https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jdk_aarch64_mac_hotspot_21.0.12.1_1.tar.gz", "jdk.tar.gz", "3623232f33a9c3baadf304480b2535f9a3cba8a58d42ecbb438ba267315d9998", "sha256")
    else:
        java = Path(os.environ["JAVA_HOME"]).resolve()
        if not java.is_relative_to(vault):
            raise RuntimeError("Set JAVA_HOME to an external Java 21+ installation")
    ant = RUNTIME / "apache-ant-1.10.18"
    if not ant.exists():
        archive("https://archive.apache.org/dist/ant/binaries/apache-ant-1.10.18-bin.tar.gz", "ant-1.10.18.tar.gz", "c510d744876d8da48dabc9495b023b6ec5284a0f18b40ee50d98ce099e791ca5c73e3cd4c80d3c90d3efc03f9620be43aad0a373ed47198284f7e3373e0db2c3")
    tomcat = RUNTIME / "apache-tomcat-9.0.123"
    if not tomcat.exists():
        archive("https://archive.apache.org/dist/tomcat/tomcat-9/v9.0.123/bin/apache-tomcat-9.0.123.tar.gz", "tomcat.tar.gz", "64b1130e719399c0a409e6996081433b16af8d9c89266c7aaa9849af70a1815feca91e13896f5ccc41451dc5759716d1c84882682de955822c30509de102f290")
    wordnet = RUNTIME / "WordNet-3.0"
    if not wordnet.exists():
        archive("https://wordnetcode.princeton.edu/3.0/WordNet-3.0.tar.gz", "wordnet.tar.gz", "640db279c949a88f61f851dd54ebbb22d003f8b90b85267042ef85a3781d3a52", "sha256")
    vampire = RUNTIME / "vampire"
    if platform.system() == "Darwin" and platform.machine() == "arm64" and not vampire.exists():
        package = RUNTIME / "vampire.zip"
        if not package.exists():
            run(["curl", "--fail", "--location", "--retry", "3", "https://github.com/vprover/vampire/releases/download/v5.1.0/vampire-macOS-ARM64.zip", "--output", str(package)])
        with package.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if digest != "02d88d0669813909e7838e0d05c278fade6e1125f48c68b75e107ce0456cd21b":
            raise ValueError("Vampire archive checksum mismatch")
        with zipfile.ZipFile(package) as bundle:
            vampire.write_bytes(bundle.read("vampire"))
        vampire.chmod(0o755)
    sigma = STATE / "sigma" / ("all-domains" if args.all_domains else "core")
    kb = sigma / "KBs"
    copy_corpus(UPSTREAM / "sumo", kb, lock["repositories"]["sumo"]["commit"])
    shutil.copytree(wordnet / "dict", kb / "WordNetMappings", dirs_exist_ok=True)
    config = ET.parse(UPSTREAM / "sigmakee/scripts/installation/config.xml")
    graphviz = shutil.which("dot")
    if graphviz is None:
        raise RuntimeError("Graphviz dot must be installed and available on PATH")
    settings = {
        "baseDir": str(sigma), "kbDir": str(kb), "sumoDir": str(UPSTREAM / "sumo"),
        "graphDir": str(sigma / "graph"), "inferenceTestDir": str(kb / "tests"),
        "eproverExec": str(UPSTREAM / "eprover/PROVER/eprover"),
        "vampireExec": str(vampire),
        "graphVizExec": graphviz,
        "loadLexicons": "true", "hostname": "localhost", "port": "8085",
        "loadFresh": "false", "cache": "yes",
    }
    for preference in config.getroot().findall("preference"):
        name = preference.attrib["name"]
        if name in settings:
            preference.set("value", settings[name])
    if args.all_domains:
        knowledge_base = config.getroot().find("kb")
        assert knowledge_base is not None
        knowledge_base.clear()
        knowledge_base.set("name", "SUMO")
        for source in sorted(kb.glob("*.kif")):
            ET.SubElement(knowledge_base, "constituent", {"filename": source.name})
    config_path = kb / "config.xml"
    config_bytes = ET.tostring(config.getroot(), encoding="utf-8", xml_declaration=True)
    if not config_path.exists() or config_path.read_bytes() != config_bytes:
        config_path.write_bytes(config_bytes)
    server = ET.parse(tomcat / "conf/server.xml")
    server.getroot().set("port", "8006")
    server.getroot().set("address", "127.0.0.1")
    for connector in server.getroot().iter("Connector"):
        connector.set("address", "127.0.0.1")
        connector.set("port", "8085")
    server_path = tomcat / "conf/server.xml"
    server_bytes = ET.tostring(server.getroot(), encoding="utf-8", xml_declaration=True)
    if server_path.read_bytes() != server_bytes:
        server_path.write_bytes(server_bytes)
    env = dict(os.environ, JAVA_HOME=str(java), CATALINA_HOME=str(tomcat), SIGMA_HOME=str(sigma),
               ONTOLOGYPORTAL_GIT=str(UPSTREAM), SIGMA_SRC=str(UPSTREAM / "sigmakee"),
               ANT_OPTS=f"-Duser.home={RUNTIME} -Djava.io.tmpdir={tmp}",
               JAVA_OPTS=f"-Duser.home={RUNTIME} -Djava.io.tmpdir={tmp}")
    run([str(java / "bin/java"), "-version"], env=env)
    run(["./configure"], UPSTREAM / "eprover", env)
    run(["make", "-j4"], UPSTREAM / "eprover", env)
    run([str(ant / "bin/ant"), "dist"], UPSTREAM / "sigmakee", env)
    deployment = tomcat / "webapps/sigma"
    with zipfile.ZipFile(tomcat / "webapps/sigma.war") as application:
        for name in application.namelist():
            if not (deployment / name).resolve().is_relative_to(deployment.resolve()):
                raise RuntimeError("Sigma WAR contains an unsafe deployment path")
        application.extractall(deployment)
    (RUNTIME / "environment.json").write_text(json.dumps({key: env[key] for key in (
        "JAVA_HOME", "CATALINA_HOME", "SIGMA_HOME", "ONTOLOGYPORTAL_GIT", "SIGMA_SRC", "JAVA_OPTS")}, indent=2) + "\n")
    print("Bootstrap complete. Run uv run python scripts/runtime-sigma.py start")


if __name__ == "__main__":
    main()
