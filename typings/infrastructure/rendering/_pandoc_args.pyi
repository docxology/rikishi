from collections.abc import Sequence
from pathlib import Path

def combined_pandoc_args(resource_dirs: Sequence[Path], bibliographies: Sequence[Path],
                         *, edition: str) -> list[str]: ...
