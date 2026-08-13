"""Maelstrom oppositional gates for skills and plugins."""
from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

__version__ = "1.1.1"
PYTEST_TIMEOUT_S = 60
_BLOCKED_PREFIXES = ("/etc", "/proc", "/sys", "/dev", "/root", "/boot")

AI_TELLS = [
    r"in today's (?:rapidly changing )?world",
    r"in the ever-evolving",
    r"it is (?:important|crucial|vital) to note",
    r"delve into",
    r"landscape of",
    r"robust and comprehensive",
]


def _safe_path(path: str, *, must_exist: bool = False) -> Path:
    if not path or not isinstance(path, str) or "\x00" in path:
        raise ValueError("invalid path")
    p = Path(path).expanduser().resolve()
    s = str(p)
    if s == "/" or any(s == b or s.startswith(b + os.sep) for b in _BLOCKED_PREFIXES):
        raise ValueError("refusing path in protected filesystem area")
    if must_exist and not p.exists():
        raise FileNotFoundError(s)
    return p


def _load_yaml(text: str) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise RuntimeError("PyYAML is required for frontmatter/plugin.yaml parsing") from e
    return yaml.safe_load(text)


def _finding(code: str, detail: str, severity: str = "error") -> Dict[str, str]:
    return {"code": code, "detail": detail, "severity": severity}


def check_skill(path: str) -> Dict[str, Any]:
    root = _safe_path(path)
    findings: List[Dict[str, str]] = []
    skill = root / "SKILL.md" if root.is_dir() else root
    if skill.is_dir():
        skill = skill / "SKILL.md"
    if not skill.is_file():
        return {
            "ok": False,
            "version": __version__,
            "target": str(root),
            "findings": [_finding("missing_skill_md", "SKILL.md not found")],
            "status": "fail",
        }

    text = skill.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        findings.append(_finding("frontmatter_start", "SKILL.md must start with ---"))
    m = re.search(r"\n---\s*\n", text[3:])
    if not m:
        findings.append(_finding("frontmatter_close", "No closing frontmatter fence"))
        fm = {}
    else:
        try:
            fm = _load_yaml(text[3 : m.start() + 3]) or {}
        except Exception as e:
            fm = {}
            findings.append(_finding("frontmatter_yaml", f"YAML parse error: {e}"))

    if not isinstance(fm, dict):
        findings.append(_finding("frontmatter_yaml", "frontmatter must be a mapping"))
        fm = {}

    if not fm.get("name"):
        findings.append(_finding("missing_name", "frontmatter.name required"))
    if not fm.get("description"):
        findings.append(
            _finding("missing_description", "frontmatter.description required")
        )
    else:
        desc = str(fm["description"])
        if len(desc) > 1024:
            findings.append(
                _finding("description_too_long", f"description {len(desc)} > 1024")
            )
        if len(desc) > 57 and not desc.lower().startswith("use when"):
            findings.append(
                _finding(
                    "trigger_buried",
                    "description should front-load 'Use when' within 57 chars",
                    "warning",
                )
            )

    body = text[m.start() + 4 :] if m else text
    if len(body.strip()) < 80:
        findings.append(
            _finding("thin_body", "Body too thin to change agent behavior")
        )
    if len(text) > 100_000:
        findings.append(_finding("skill_too_large", "SKILL.md > 100k chars"))
    if len(text) > 20_000:
        findings.append(
            _finding(
                "skill_large", "SKILL.md > 20k — consider references/", "warning"
            )
        )

    for pat in AI_TELLS:
        if re.search(pat, body, re.I):
            findings.append(
                _finding("ai_tell", f"Possible AI-tell pattern: {pat}", "warning")
            )

    if (
        "Completion criteria" not in text
        and "completion criteria" not in text.lower()
        and "- [ ]" not in text
    ):
        findings.append(
            _finding(
                "no_completion_criteria",
                "No checklist/completion criteria found",
                "warning",
            )
        )

    if "Pitfall" not in text and "pitfall" not in text.lower():
        findings.append(_finding("no_pitfalls", "No pitfalls section", "warning"))

    errors = [f for f in findings if f["severity"] == "error"]
    status = "fail" if errors else ("pass_with_fixes" if findings else "pass")
    return {
        "ok": status != "fail",
        "version": __version__,
        "status": status,
        "target": str(skill),
        "findings": findings,
        "meta": {
            "name": fm.get("name"),
            "description_len": len(str(fm.get("description") or "")),
            "bytes": len(text.encode()),
        },
    }


def check_plugin(path: str) -> Dict[str, Any]:
    root = _safe_path(path)
    findings: List[Dict[str, str]] = []
    if not root.is_dir():
        return {
            "ok": False,
            "version": __version__,
            "status": "fail",
            "target": str(root),
            "findings": [_finding("not_dir", "plugin path must be directory")],
        }

    yml = root / "plugin.yaml"
    init = root / "__init__.py"
    meta: Dict[str, Any] = {}
    if not yml.is_file():
        findings.append(_finding("missing_plugin_yaml", "plugin.yaml required"))
    else:
        try:
            loaded = _load_yaml(yml.read_text(encoding="utf-8")) or {}
            if not isinstance(loaded, dict):
                findings.append(_finding("plugin_yaml_parse", "plugin.yaml must be a mapping"))
            else:
                meta = loaded
        except Exception as e:
            findings.append(_finding("plugin_yaml_parse", str(e)))
    if not meta.get("name"):
        findings.append(_finding("plugin_name", "plugin.yaml name required"))
    if not meta.get("version"):
        findings.append(
            _finding("plugin_version", "version recommended", "warning")
        )
    if not init.is_file():
        findings.append(
            _finding("missing_init", "__init__.py required for native plugins")
        )
    else:
        src = init.read_text(encoding="utf-8", errors="replace")
        if "def register" not in src:
            findings.append(_finding("no_register", "register(ctx) not found"))
        try:
            ast.parse(src)
        except SyntaxError as e:
            findings.append(_finding("init_syntax", f"SyntaxError: {e}"))

    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        findings.append(_finding("no_tests", "No tests/ directory", "warning"))
    else:
        if not list(tests_dir.glob("test_*.py")):
            findings.append(
                _finding("no_test_files", "tests/ has no test_*.py", "warning")
            )

    if not (root / "README.md").is_file():
        findings.append(_finding("no_readme", "README.md missing", "warning"))

    skills = root / "skills"
    skill_results = []
    if skills.is_dir():
        for child in skills.iterdir():
            if child.is_dir() and (child / "SKILL.md").is_file():
                skill_results.append(check_skill(str(child)))

    errors = [f for f in findings if f["severity"] == "error"]
    skill_fails = [s for s in skill_results if s.get("status") == "fail"]
    status = (
        "fail"
        if errors or skill_fails
        else (
            "pass_with_fixes"
            if findings or any(s.get("findings") for s in skill_results)
            else "pass"
        )
    )
    return {
        "ok": status != "fail",
        "version": __version__,
        "status": status,
        "target": str(root),
        "findings": findings,
        "skills": skill_results,
        "meta": {"name": meta.get("name"), "version": meta.get("version")},
    }


def run_pytest(path: str, extra_args: Optional[List[str]] = None) -> Dict[str, Any]:
    root = _safe_path(path)
    tests = root / "tests"
    if not tests.is_dir():
        return {
            "ok": False,
            "version": __version__,
            "returncode": 2,
            "stdout": "",
            "stderr": "no tests/",
            "status": "fail",
        }
    extra = extra_args or []
    if any(a.startswith("-") and a not in {"-q", "-v", "--tb=short", "--tb=line"} for a in extra):
        return {
            "ok": False,
            "version": __version__,
            "returncode": 2,
            "stdout": "",
            "stderr": "refusing unapproved pytest extra args",
            "status": "fail",
        }
    cmd = [sys.executable, "-m", "pytest", str(tests), "-q"] + extra
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=PYTEST_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "version": __version__,
            "returncode": 124,
            "stdout": "",
            "stderr": f"pytest timed out after {PYTEST_TIMEOUT_S}s",
            "status": "fail",
        }
    return {
        "ok": proc.returncode == 0,
        "version": __version__,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-4000:],
        "status": "pass" if proc.returncode == 0 else "fail",
        "cmd": ["python", "-m", "pytest", "tests", "-q"],
    }


def full_gate(path: str) -> Dict[str, Any]:
    root = _safe_path(path)
    if (root / "plugin.yaml").is_file():
        static = check_plugin(str(root))
        tests = run_pytest(str(root))
    elif (root / "SKILL.md").is_file() or root.name == "SKILL.md":
        static = check_skill(str(root))
        tests = {"ok": True, "status": "skip", "detail": "skill-only package"}
    else:
        return {
            "ok": False,
            "version": __version__,
            "status": "fail",
            "error": "Unrecognized package (need plugin.yaml or SKILL.md)",
        }

    ok = static.get("ok") and tests.get("ok", True)
    if not ok or static.get("status") == "fail" or tests.get("status") == "fail":
        status = "fail"
    elif static.get("status") == "pass" and tests.get("status") in ("pass", "skip"):
        status = "pass"
    else:
        status = "pass_with_fixes"
    return {
        "ok": status != "fail",
        "version": __version__,
        "status": status,
        "static": static,
        "tests": tests,
        "metaphor": {
            "name": "maelstrom",
            "note": "Moskstraumen: respect the current before you commit the longship.",
        },
    }
