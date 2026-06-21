# Contributing

This is a personal portfolio project, but the workflow below keeps changes
reproducible if you fork it or want to extend the analysis.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

## Day-to-day commands

| Task | Command |
|---|---|
| Generate data + train + SQL | `make all` |
| Run the dashboard | `make app` |
| Lint | `make lint` |
| Auto-format | `make format` |
| Run tests | `make test` |
| Lint + tests (what CI runs) | `make check` |

## Conventions

- Code is formatted and linted with [ruff](https://docs.astral.sh/ruff/);
  configuration lives in `pyproject.toml`.
- Tests use `pytest`. The default suite runs against a small synthetic dataset
  and finishes in a couple of seconds. The full-scale check that guards the
  headline metrics in the README is marked `slow`:

  ```bash
  pytest            # fast suite
  pytest -m slow    # full-scale regression
  ```

- Pipeline scripts under `scripts/` are thin entrypoints; reusable logic lives
  in `src/customer_ai/` so it can be imported and tested directly.

## Before opening a pull request

Run `make check` and make sure both lint and tests pass. CI runs the same
checks on Python 3.9, 3.11, and 3.12.
