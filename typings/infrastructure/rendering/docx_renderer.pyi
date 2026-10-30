from pathlib import Path
from typing import Protocol

class RenderResult(Protocol):
    @property
    def output_path(self) -> Path: ...

def render_docx(source: Path, output: Path, *, title: str, author: str,
                extra_args: list[str], reference_doc: Path | None = None) -> RenderResult: ...
