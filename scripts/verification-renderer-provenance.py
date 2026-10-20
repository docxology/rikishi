from __future__ import annotations

import os
from pathlib import Path

from rikishi.manuscript_provenance import renderer_corruption_control


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    checkout = Path(
        os.environ.get("RIKISHI_TEMPLATE_ROOT", root.parent.parent / "Public" / "template")
    ).resolve(strict=True)
    print("\n".join(renderer_corruption_control(root, checkout)))


if __name__ == "__main__":
    main()
