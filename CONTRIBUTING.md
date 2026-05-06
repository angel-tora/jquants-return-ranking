# Contributing

## Development

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

## Checks

Run these before opening a pull request:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/tmp/jrr-pycache python -m compileall src tests
python -m build
```

## Secrets

Do not commit real API keys, fetched market data, local config files, screenshots containing keys, or generated ranking CSVs. Tests must use fake keys only.
