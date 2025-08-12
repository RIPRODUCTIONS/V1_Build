import importlib
import sys
from pathlib import Path

# Add backend to path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from fastapi.testclient import TestClient

    mod = importlib.import_module('app.main')
except Exception as e:
    print('Failed to import app.main:', e, file=sys.stderr)
    sys.exit(1)

app = None
if hasattr(mod, 'create_app'):
    app = mod.create_app()
elif hasattr(mod, 'app'):
    app = mod.app
else:
    print('Neither create_app() nor app found in app.main', file=sys.stderr)
    sys.exit(1)

with TestClient(app) as c:
    for path in ('/health', '/healthz', '/'):
        r = c.get(path)
        if r.status_code in (200, 204):
            sys.exit(0)
    print('No health endpoint returned 200/204', file=sys.stderr)
    sys.exit(1)
