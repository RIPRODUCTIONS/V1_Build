### Temporal Worker (demo)

Quick start:

- Install deps: `pip install -r requirements.txt`
- Start local Temporal (via platform/infra): `make -C ../../ up`
- Run worker: `python worker.py`

Trigger a sample workflow (pseudo):

- Use Temporal CLI or a small Python client to start `HelloWorkflow` with an input name.
- Expected result: worker logs heartbeat activity and returns `hello,<name>`.
