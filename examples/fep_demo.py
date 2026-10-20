from __future__ import annotations

import json

from rikishi.fep import demo

if __name__ == "__main__":
    print(json.dumps(demo(), indent=2, allow_nan=False))
