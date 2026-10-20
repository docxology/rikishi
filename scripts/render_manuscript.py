"""Render artifacts: uv run python scripts/render_manuscript.py."""

from pathlib import Path

from rikishi.manuscript import render_manuscript

if __name__ == "__main__":
    render_manuscript(Path(__file__).resolve().parents[1])
