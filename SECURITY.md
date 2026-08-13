# Security Policy

## Reporting

Use GitHub Security Advisories on this repository.

## Guards

- Paths reject null bytes and `/etc`, `/proc`, `/sys`, `/dev`, `/root`, `/boot`.
- `maelstrom_run_pytest` runs `python -m pytest tests -q` only. Extra args are allow-listed. Timeout 60s. No `shell=True`.
- The pytest tool will execute tests in any non-blocked directory you point it at. Treat `path` as trusted operator input.

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | Yes |
| 1.0.x   | Best-effort |
