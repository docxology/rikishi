from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from render_manuscript import prepare_renderer


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    checkout = Path(
        os.environ.get("RIKISHI_TEMPLATE_ROOT", root.parent.parent / "Public" / "template")
    ).resolve(strict=True)
    with TemporaryDirectory(prefix="renderer-control-", dir=root / ".rikishi") as directory:
        temporary_root = Path(directory)
        snapshot, sources, archive_hash = prepare_renderer(temporary_root, checkout)
        print(f"Positive control: {len(sources)} archived files verified; archive {archive_hash}")
        metadata = snapshot / "pyproject.toml"
        metadata.write_text(metadata.read_text() + "\n# deliberately altered test snapshot\n")
        try:
            prepare_renderer(temporary_root, checkout)
        except ValueError as error:
            assert "Renderer snapshot differs" in str(error)
            print(f"Negative control rejected altered snapshot: {error}")
        else:
            raise AssertionError("Modified renderer snapshot was accepted")


if __name__ == "__main__":
    main()
