import re
from pathlib import Path
from typing import Final
from urllib.parse import unquote, urlsplit

import pytest

INLINE_LINK: Final = re.compile(r"\[[^\]\n]*\]\(<?([^\s)>]+)>?(?:\s+\"[^\"\n]*\")?\)")


def _missing_local_links(root: Path, *, include_generated: bool = True) -> list[str]:
    documents = [root / name for name in ("README.md", "AGENTS.md")]
    documents.extend(sorted((root / "docs").rglob("*.md")))
    missing = []
    for document in documents:
        if not document.is_file():
            continue
        text = re.sub(r"```[^\n]*\n.*?```", "", document.read_text(), flags=re.DOTALL)
        for match in INLINE_LINK.finditer(text):
            href = match.group(1)
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            target = document.parent / unquote(url.path)
            if not include_generated:
                resolved = target.resolve()
                generated = (root / "output", root / "dist", root / ".omo/evidence")
                if any(resolved.is_relative_to(path.resolve()) for path in generated):
                    continue
            if not target.exists():
                missing.append(f"{document.relative_to(root)}: {href}")
    return missing


@pytest.mark.integration
def test_authored_documentation_links_resolve(project_root: Path) -> None:
    # Given the actual checkout's maintained guides.
    # When resolving their relative file links.
    missing = _missing_local_links(project_root)
    # Then every local target remains present.
    assert missing == []


def test_distributed_documentation_links_resolve(project_root: Path) -> None:
    # Given maintained guides, without assuming generated or private evidence.
    # When checking source/distribution links only.
    missing = _missing_local_links(project_root, include_generated=False)
    # Then every source target exists independently of a native production run.
    assert missing == []


def test_source_link_scope_does_not_hide_missing_guides(tmp_path: Path) -> None:
    # Given absent generated artifacts and one absent ordinary source guide.
    (tmp_path / "README.md").write_text(
        "[Edition](output/pdf/result.pdf)\n[Wheel](dist/package.whl)\n"
        "[Receipt](.omo/evidence/current/seal.json)\n[Guide](docs/missing.md)\n"
        "[Other private source](.omo/not-evidence.md)\n"
        "[Escaped receipt](.omo/evidence/../source.md)\n"
    )
    # When the explicitly source-only check runs.
    missing = _missing_local_links(tmp_path, include_generated=False)
    # Then only known generated roots are excluded; source mistakes still fail.
    assert missing == ["README.md: docs/missing.md", "README.md: .omo/not-evidence.md",
                       "README.md: .omo/evidence/../source.md"]
    assert len(_missing_local_links(tmp_path)) == 6


@pytest.mark.parametrize("href", ["missing.md", "nested/missing.md"])
def test_missing_documentation_target_is_reported(tmp_path: Path, href: str) -> None:
    # Given an actual document with an absent target.
    (tmp_path / "README.md").write_text(f"[Guide]({href})\n")
    # When resolving its link.
    missing = _missing_local_links(tmp_path)
    # Then the diagnostic identifies both source and target.
    assert missing == [f"README.md: {href}"]


def test_links_resolve_from_their_guide_with_encoded_paths(tmp_path: Path) -> None:
    # Given local, remote, anchor, titled, and illustrative fenced links.
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide space.md").write_text("# Topic\n")
    (docs / "README.md").write_text(
        '[Guide](<guide%20space.md> "Read more")\n'
        "[Remote](https://example.invalid/missing.md)\n"
        "[Anchor](#topic)\n"
        "```markdown\n[Example](absent-example.md)\n```\n"
    )
    # When resolving the guide's paths.
    missing = _missing_local_links(tmp_path)
    # Then external links and examples do not become filesystem requirements.
    assert missing == []
