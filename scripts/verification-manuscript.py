"""Verify artifacts: uv run python scripts/verification-manuscript.py."""

from pathlib import Path

from rikishi.manuscript_verification import verify_manuscript

if __name__ == "__main__":
    verify_manuscript(Path(__file__).resolve().parents[1])
