from pathlib import Path
import gate


def test_bad_skill(tmp_path):
    s = tmp_path / "SKILL.md"
    s.write_text("no frontmatter\n")
    r = gate.check_skill(str(s))
    assert r["status"] == "fail"
    assert r["version"] == gate.__version__


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


def test_plugin_happy_path(tmp_path):
    (tmp_path / "plugin.yaml").write_text("name: demo\nversion: 1.0.0\n")
    (tmp_path / "__init__.py").write_text("def register(ctx):\n    return None\n")
    (tmp_path / "README.md").write_text("# demo\n")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    r = gate.check_plugin(str(tmp_path))
    assert r["ok"] is True
    assert r["meta"]["name"] == "demo"


def test_run_pytest_ok(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    r = gate.run_pytest(str(tmp_path))
    assert r["ok"] is True
    assert r["status"] == "pass"


def test_run_pytest_rejects_extra_args(tmp_path):
    (tmp_path / "tests").mkdir()
    r = gate.run_pytest(str(tmp_path), extra_args=["--maxfail=1", "-k", "evil"])
    assert r["ok"] is False
    assert "unapproved" in r["stderr"]


def test_full_gate_unrecognized(tmp_path):
    r = gate.full_gate(str(tmp_path))
    assert r["ok"] is False
    assert "Unrecognized" in r["error"]


def test_refuses_etc():
    r = None
    try:
        gate.check_plugin("/etc")
        assert False
    except ValueError:
        pass
