from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path

import pytest

from rikishi.cli import parser
from rikishi.publication_bridge import load_bridge_context
from rikishi.publication_inference import load_inference_context
from rikishi.runtime_artifacts import ArtifactError

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs/manuscript.md"
REPORT = Path("output/inference/inference-report.json")
STAGED_REPORT = Path("output/manuscript/inference/inference-report.json")


def _shell_blocks(markdown: str) -> list[str]:
    return re.findall(r"```(?:bash|sh)\n(.*?)```", markdown, re.DOTALL)


def _commands(markdown: str) -> list[list[str]]:
    commands: list[list[str]] = []
    for block in _shell_blocks(markdown):
        for line in block.replace("\\\n", " ").splitlines():
            tokens = shlex.split(line, comments=True)
            if tokens:
                commands.append(tokens)
    return commands


def _uv_payload(tokens: list[str]) -> list[str]:
    if tokens[:2] != ["uv", "run"]:
        return []
    payload = tokens[2:]
    while payload and payload[0] in {"--locked", "--no-sync"}:
        payload = payload[1:]
    return payload


def _require_workflow(markdown: str, prefix: str = "inference") -> None:
    report = Path(f"output/{prefix}/{prefix}-report.json")
    staged_report = Path(f"output/manuscript/{prefix}/{prefix}-report.json")
    alias_name = "REPORT_SHA256" if prefix == "inference" else "BRIDGE_SHA256"
    supplied_name = "INFERENCE_REPORT_SHA256" if prefix == "inference" else "BRIDGE_REPORT_SHA256"
    runs: list[int] = []
    verified: list[int] = []
    staged: list[int] = []
    renders: list[int] = []
    digests: set[str] = set()
    alias: list[int] = []
    assignments: list[int] = []
    cli = parser()
    for position, tokens in enumerate(_commands(markdown)):
        if tokens == ["readonly", f"{alias_name}=${supplied_name}"]:
            alias.append(position)
        assignment_tokens = (
            tokens[1:] if tokens[0] in {"readonly", "export", "declare", "typeset"} else tokens[:1]
        )
        if any(re.match(rf"{alias_name}\+?=", token) for token in assignment_tokens):
            assignments.append(position)
        assert not (tokens[0] in {"read", "unset"} and alias_name in tokens), (
            "The digest alias must stay immutable"
        )
        payload = _uv_payload(tokens)
        if payload == ["python", "scripts/render_manuscript.py"]:
            renders.append(position)
        if not payload or payload[0] != "rikishi":
            continue
        arguments = payload[1:]
        if not arguments or arguments[0] not in {f"{prefix}-run", f"{prefix}-verify"}:
            continue
        args = cli.parse_args(arguments)
        if args.command == f"{prefix}-run":
            assert args.output == report.parent, f"The renderer consumes {report.parent}"
            assert args.prover == "both", "Publication requires both native provers"
            runs.append(position)
        else:
            assert args.sha256, "Replay requires a separately retained digest"
            digests.add(args.sha256)
            if args.report == report:
                verified.append(position)
            else:
                assert args.report == staged_report, "Replay must check the source or staged report"
                staged.append(position)
    assert runs, "The fresh recipe must generate the selected campaign"
    assert verified, "The recipe must verify the selected report before rendering"
    assert renders, "The recipe must invoke the native manuscript renderer"
    assert staged, "The staged copy must be checked against the trusted digest"
    assert digests == {f"${alias_name}"}, (
        "Source and staged replay must use the retained digest alias"
    )
    assert len(alias) == 1 and assignments == alias, "Bind the supplied digest once with readonly"
    assert alias[0] < min(verified), "Bind the supplied digest before verification"
    assert min(runs) < min(verified) < min(renders), "Generate, verify, then render"
    assert min(renders) < min(staged), "Verify the staged report after rendering"


def test_manuscript_recipe_has_complete_ordered_inference_prerequisite() -> None:
    _require_workflow(GUIDE.read_text(encoding="utf-8"))


def test_manuscript_recipe_has_complete_ordered_bridge_prerequisite() -> None:
    _require_workflow(GUIDE.read_text(encoding="utf-8"), "bridge")


def test_documented_shell_blocks_parse_with_real_bash() -> None:
    blocks = _shell_blocks(GUIDE.read_text(encoding="utf-8"))
    assert blocks
    for block in blocks:
        result = subprocess.run(
            ["bash", "-n"], input=block, text=True, capture_output=True, check=False
        )
        assert result.returncode == 0, result.stderr


def test_publication_rejects_a_missing_inference_packet(tmp_path: Path) -> None:
    with pytest.raises(ArtifactError, match="cannot read evidence"):
        load_inference_context(tmp_path)


def test_publication_rejects_a_missing_bridge_packet(tmp_path: Path) -> None:
    with pytest.raises(ArtifactError, match="cannot read evidence"):
        load_bridge_context(tmp_path, decimal_places=6)


@pytest.mark.parametrize("prefix", ["inference", "bridge"])
def test_documented_digest_alias_is_immutable_in_real_bash(prefix: str) -> None:
    alias_name = "REPORT_SHA256" if prefix == "inference" else "BRIDGE_SHA256"
    supplied_name = "INFERENCE_REPORT_SHA256" if prefix == "inference" else "BRIDGE_REPORT_SHA256"
    blocks = _shell_blocks(GUIDE.read_text(encoding="utf-8"))
    alias = next(
        line.strip()
        for block in blocks
        for line in block.splitlines()
        if line.strip().startswith(f"readonly {alias_name}=")
    )
    assignment = f'{supplied_name}="first-retained-value"\n'
    script = assignment + alias + f'\nprintf "%s\\n" "${alias_name}"\n{alias_name}="replacement"\n'
    result = subprocess.run(["bash"], input=script, text=True, capture_output=True, check=False)
    assert result.returncode != 0 and "readonly" in result.stderr
    assert result.stdout == "first-retained-value\n"
    mutable = (
        assignment
        + alias.removeprefix("readonly ")
        + f'\n{alias_name}="replacement"\nprintf "%s\\n" "${alias_name}"\n'
    )
    control = subprocess.run(["bash"], input=mutable, text=True, capture_output=True, check=False)
    assert control.returncode == 0 and control.stdout == "replacement\n"


@pytest.mark.parametrize(
    "tokens, expected",
    [
        (
            ["uv", "run", "--locked", "rikishi", "inference-catalog"],
            ["rikishi", "inference-catalog"],
        ),
        (
            ["uv", "run", "--locked", "--no-sync", "python", "scripts/render_manuscript.py"],
            ["python", "scripts/render_manuscript.py"],
        ),
        (["echo", "uv", "run", "rikishi"], []),
        (["printf", "uv", "run", "rikishi"], []),
    ],
)
def test_only_actual_uv_invocations_have_payloads(tokens: list[str], expected: list[str]) -> None:
    assert _uv_payload(tokens) == expected


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-campaign",
        "single-prover",
        "wrong-output",
        "missing-replay",
        "wrong-report",
        "missing-digest",
        "render-first",
        "missing-staged-replay",
        "different-staged-digest",
        "echo-only",
        "digest-reassignment",
        "missing-readonly",
        "echoed-renderer",
        "python-code-renderer-token",
        "exported-digest-reassignment",
    ],
)
@pytest.mark.parametrize("prefix", ["inference", "bridge"])
def test_recipe_contract_rejects_broken_workflows(mutation: str, prefix: str) -> None:
    alias_name = "REPORT_SHA256" if prefix == "inference" else "BRIDGE_SHA256"
    supplied_name = "INFERENCE_REPORT_SHA256" if prefix == "inference" else "BRIDGE_REPORT_SHA256"
    report = Path(f"output/{prefix}/{prefix}-report.json")
    staged_report = Path(f"output/manuscript/{prefix}/{prefix}-report.json")
    run = f"uv run --locked rikishi {prefix}-run output/{prefix} --prover both"
    verify = f'uv run --locked rikishi {prefix}-verify {report} --sha256 "${alias_name}"'
    render = "uv run --locked python scripts/render_manuscript.py"
    staged = verify.replace(str(report), str(staged_report))
    alias = f'readonly {alias_name}="${supplied_name}"'
    valid = f"```bash\n{alias}\n{run}\n{verify}\n{render}\n{staged}\n```"
    _require_workflow(valid, prefix)
    match mutation:
        case "missing-campaign":
            broken = valid.replace(run, "")
        case "single-prover":
            broken = valid.replace("--prover both", "--prover e")
        case "wrong-output":
            broken = valid.replace(f"{prefix}-run output/{prefix}", f"{prefix}-run output/other")
        case "missing-replay":
            broken = valid.replace(verify, "")
        case "wrong-report":
            broken = valid.replace(
                f"{prefix}-verify output/{prefix}/", f"{prefix}-verify output/other/"
            )
        case "missing-digest":
            broken = valid.replace(f' --sha256 "${alias_name}"', "")
        case "render-first":
            broken = f"```bash\n{alias}\n{render}\n{run}\n{verify}\n{staged}\n```"
        case "missing-staged-replay":
            broken = valid.replace(staged, "")
        case "different-staged-digest":
            broken = valid.replace(staged, staged.replace(f"${alias_name}", "$OTHER_SHA256"))
        case "echo-only":
            broken = (
                f"```bash\n{alias}\n"
                + "\n".join(f"echo {line}" for line in (run, verify, render, staged))
                + "\n```"
            )
        case "digest-reassignment":
            broken = valid.replace(staged, f'{alias_name}="$OTHER_SHA256"\n' + staged)
        case "missing-readonly":
            broken = valid.replace(f"readonly {alias_name}=", f"{alias_name}=")
        case "echoed-renderer":
            broken = valid.replace(render, "echo " + render)
        case "python-code-renderer-token":
            broken = valid.replace(
                render, 'uv run python -c "print(1)" scripts/render_manuscript.py'
            )
        case "exported-digest-reassignment":
            broken = valid.replace(staged, f'export {alias_name}="$OTHER_SHA256"\n' + staged)
        case _:
            pytest.fail(f"Unknown negative control: {mutation}")
    assert broken != valid
    with pytest.raises((AssertionError, SystemExit)):
        _require_workflow(broken, prefix)
