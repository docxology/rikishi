from pathlib import Path

from rikishi.runtime_query import main

if __name__ == "__main__":
    raise SystemExit(main(Path(__file__).resolve().parents[1]))
