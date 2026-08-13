# Architecture — maelstrom-gate

```
register(ctx)
    tools: maelstrom_check_skill | maelstrom_check_plugin | maelstrom_run_pytest
gate.py
    check_skill / check_plugin / run_pytest / full_gate
```

`full_gate` is CLI/slash only (not a registered tool) so agents do not accidentally spawn unbounded pytest from a tool call unless they opt into `maelstrom_run_pytest`.

Statuses: `pass` | `pass_with_fixes` | `fail`.

Public tool names are stable. Handlers never raise.
