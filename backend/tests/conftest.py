import os
import sys

# Ensure the backend package root is on sys.path so `import app` works
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Ensure API runs agent synchronously during tests to avoid Redis requirement
os.environ.setdefault("CI_ENV", "true")
