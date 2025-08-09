### Architecture overview

- **Core package**: `src/builder` contains typed modules for configuration, path resolution, and CLI.
- **Toolkits**: `toolkits/` holds symlinks to external resources; code resolves via env var or symlink.
- **Health**: `builder health` validates paths and core Python dependencies used by the toolboxes.
- **Standards**: Black, Ruff, and Mypy configured via `pyproject.toml`.

### Design principles
- **Explicit over implicit**: Typed settings and clear validation.
- **Stable paths**: Space-free symlink targets for reliability in scripts.
- **Separation of concerns**: Path resolution, config loading, and CLI separated.
