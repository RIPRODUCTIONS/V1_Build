from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path so `app` package is importable when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402 - path manipulation above is required for import


def main() -> None:
    spec = app.openapi()
    out_path = Path(__file__).resolve().parent.parent / "openapi.json"
    out_path.write_text(json.dumps(spec, indent=2))
    print(f"Wrote OpenAPI spec to {out_path}")


if __name__ == "__main__":
    main()
