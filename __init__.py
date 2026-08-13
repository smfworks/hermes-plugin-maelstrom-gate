"""maelstrom-gate plugin."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

try:
    from . import gate
except ImportError:
    import gate

logger = logging.getLogger(__name__)

SKILL_SCHEMA = {
    "name": "maelstrom_check_skill",
    "description": (
        "Oppositionally lint a Hermes skill directory or SKILL.md: frontmatter, "
        "description length/trigger, body substance, AI-tell patterns, pitfalls."
    ),
    "parameters": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
}

PLUGIN_SCHEMA = {
    "name": "maelstrom_check_plugin",
    "description": (
        "Oppositionally lint a Hermes plugin directory: plugin.yaml, register(ctx), "
        "tests, README, bundled skills."
    ),
    "parameters": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
}

PYTEST_SCHEMA = {
    "name": "maelstrom_run_pytest",
    "description": "Run pytest -q on a package tests/ and return truncated output + ok flag.",
    "parameters": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
}


def _err(exc: Exception) -> str:
    return json.dumps({"ok": False, "error": str(exc), "version": gate.__version__})


def handle_skill(args: dict, **kwargs) -> str:
    del kwargs
    try:
        return json.dumps(gate.check_skill(args["path"]), indent=2)
    except Exception as e:
        return _err(e)


def handle_plugin(args: dict, **kwargs) -> str:
    del kwargs
    try:
        return json.dumps(gate.check_plugin(args["path"]), indent=2)
    except Exception as e:
        return _err(e)


def handle_pytest(args: dict, **kwargs) -> str:
    del kwargs
    try:
        return json.dumps(gate.run_pytest(args["path"]), indent=2)
    except Exception as e:
        return _err(e)


def _cli(argv: Any) -> None:
    import argparse
    import sys

    p = argparse.ArgumentParser(prog="hermes maelstrom")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("skill", "plugin", "gate", "pytest", "selftest", "version"):
        sp = sub.add_parser(name)
        if name not in {"selftest", "version"}:
            sp.add_argument("path")
    ns = p.parse_args(list(argv) if isinstance(argv, list) else [])
    try:
        if ns.cmd == "version":
            print(gate.__version__)
            return
        if ns.cmd == "skill":
            data = gate.check_skill(ns.path)
            print(json.dumps(data, indent=2))
            if data.get("status") == "fail":
                raise SystemExit(1)
        elif ns.cmd == "plugin":
            data = gate.check_plugin(ns.path)
            print(json.dumps(data, indent=2))
            if data.get("status") == "fail":
                raise SystemExit(1)
        elif ns.cmd == "gate":
            data = gate.full_gate(ns.path)
            print(json.dumps(data, indent=2))
            if data.get("status") == "fail":
                raise SystemExit(1)
        elif ns.cmd == "pytest":
            data = gate.run_pytest(ns.path)
            print(json.dumps(data, indent=2))
            if not data.get("ok"):
                raise SystemExit(1)
        elif ns.cmd == "selftest":
            r = __import__("subprocess").run(
                [sys.executable, "-m", "pytest", str(Path(__file__).parent / "tests"), "-q"]
            )
            raise SystemExit(r.returncode)
    except SystemExit:
        raise
    except Exception as e:
        print(_err(e), file=sys.stderr)
        raise SystemExit(1)


def _cli_setup(subparser: Any) -> None:
    subparser.add_argument("rest", nargs="*")


def _cli_handler(ns: Any) -> int:
    rest = list(getattr(ns, "rest", []) or [])
    try:
        _cli(rest)
        return 0
    except SystemExit as e:
        code = e.code
        if code is None:
            return 0
        return int(code) if not isinstance(code, int) else code


def register(ctx):
    ctx.register_tool(
        name="maelstrom_check_skill",
        toolset="maelstrom",
        schema=SKILL_SCHEMA,
        handler=handle_skill,
    )
    ctx.register_tool(
        name="maelstrom_check_plugin",
        toolset="maelstrom",
        schema=PLUGIN_SCHEMA,
        handler=handle_plugin,
    )
    ctx.register_tool(
        name="maelstrom_run_pytest",
        toolset="maelstrom",
        schema=PYTEST_SCHEMA,
        handler=handle_pytest,
    )
    ctx.register_command(
        name="maelstrom",
        handler=_slash,
        description="Maelstrom gate: skill|plugin|gate <path>",
    )
    try:
        ctx.register_cli_command(
            name="maelstrom",
            help="Oppositional ship gate",
            setup_fn=_cli_setup,
            handler_fn=_cli_handler,
            description="Break packages before ship",
        )
    except TypeError:
        try:
            ctx.register_cli_command("maelstrom", _cli)
        except Exception as e:
            logger.warning("%s", e)
    skill = Path(__file__).parent / "skills" / "maelstrom-oppose"
    if (skill / "SKILL.md").is_file():
        try:
            ctx.register_skill(name="maelstrom-oppose", path=skill / "SKILL.md")
        except TypeError:
            try:
                ctx.register_skill(str(skill))
            except Exception as e:
                logger.debug("%s", e)


def _slash(raw: str) -> str:
    parts = (raw or "").split()
    if parts and parts[0] == "version":
        return json.dumps({"ok": True, "version": gate.__version__})
    if len(parts) < 2:
        return json.dumps(
            {
                "ok": False,
                "error": "usage: /maelstrom skill|plugin|gate <path>",
                "version": gate.__version__,
            }
        )
    cmd, path = parts[0], parts[1]
    if cmd == "skill":
        return handle_skill({"path": path})
    if cmd == "plugin":
        return handle_plugin({"path": path})
    if cmd == "gate":
        try:
            return json.dumps(gate.full_gate(path), indent=2)
        except Exception as e:
            return _err(e)
    return json.dumps({"ok": False, "error": "unknown subcommand", "version": gate.__version__})
