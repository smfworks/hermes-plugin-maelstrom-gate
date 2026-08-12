from pathlib import Path
import gate


def test_bad_skill(tmp_path):
    s = tmp_path / "SKILL.md"
    s.write_text("no frontmatter\n")
    r = gate.check_skill(str(s))
    assert r["status"] == "fail"


def test_good_skill(tmp_path):
    d = tmp_path / "demo"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: demo\ndescription: \"Use when testing maelstrom. Short.\"\n---\n\n"
        "# Demo\n\n## Overview\nSomething substantial enough for the gate.\n\n## When to Use\n- x\n\n"
        "## Completion criteria\n- [ ] done\n\n## Pitfalls\n1. none\n"
    )
    r = gate.check_skill(str(d))
    assert r["ok"] is True


def test_plugin_missing_register(tmp_path):
    (tmp_path / "plugin.yaml").write_text("name: x\nversion: 0\n")
    (tmp_path / "__init__.py").write_text("# no register\n")
    r = gate.check_plugin(str(tmp_path))
    assert r["status"] == "fail"
    assert any(f["code"] == "no_register" for f in r["findings"])
