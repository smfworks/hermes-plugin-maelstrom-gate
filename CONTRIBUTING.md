# Contributing

1. Branch from the default branch (`feat/`, `fix/`, `docs/`, `test/`).
2. Keep public tool names and parameter schemas backward compatible.
3. Add or update a test for every behavior change.
4. Run `python -m pytest -q`.
5. Do not commit `__pycache__`, secrets, or live profile dumps.
6. Update `CHANGELOG.md` and version fields together.

PRs against the default branch. CI must be green.
