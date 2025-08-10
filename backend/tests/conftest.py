import os
import sys

# Ensure the backend package root and repo root are on sys.path so imports work
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_ROOT = os.path.abspath(os.path.join(BACKEND_ROOT, ".."))
for p in (BACKEND_ROOT, REPO_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

# Ensure API runs agent synchronously during tests to avoid Redis requirement
os.environ.setdefault("CI_ENV", "true")
