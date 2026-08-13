# hermes-plugin-maelstrom-gate

Oppositional ship gate for Hermes skills and plugins.

Named for Moskstraumen (the Maelstrom) off Lofoten.

Current version: **1.1.0**.

## Install

`install` is not `enable`.

```bash
hermes plugins install smfworks/hermes-plugin-maelstrom-gate
hermes plugins enable maelstrom-gate
```

Runtime dependency: **PyYAML**.

## Usage

```bash
hermes maelstrom skill path/to/skill
hermes maelstrom plugin path/to/plugin
hermes maelstrom gate path/to/package
hermes maelstrom pytest path/to/package
hermes maelstrom version
```

Agent tools: `maelstrom_check_skill`, `maelstrom_check_plugin`, `maelstrom_run_pytest`.

`path` is trusted operator input. Pytest is time-boxed (60s) and extra flags are allow-listed.

## Develop

```bash
pip install pytest PyYAML
python -m pytest -q
```

## License

MIT — SMF Works
