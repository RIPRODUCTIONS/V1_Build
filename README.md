# Builder

A clean, well-structured foundation for AI project scaffolding. Centralized env, consistent tooling, and clear entry points.

## Quick start

```bash
# create and activate venv, install safe deps
make venv
make safe-install

# run health check
make health
```

## Layout

- `src/builder`: Typed Python package for scaffolding and orchestration
- `scripts/`: Operational scripts and automation entrypoints
- `toolkits/`: Symlinked, space-free pointers to external tool/resource dirs
- `.venv/`: Project virtual environment

## Environment

Paths are defined in `.env` and also exposed via `toolkits/` symlinks. Update `.env` if locations change.

## Coding standards

- Black, Ruff, Mypy configured via `pyproject.toml`
- Keep functions short, explicit names, early returns, handle edge cases first
- Add concise docstrings for non-trivial functions
