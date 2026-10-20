from pathlib import Path

from rikishi.runtime_server import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1])
