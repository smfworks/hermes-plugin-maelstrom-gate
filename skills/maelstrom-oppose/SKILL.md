---
name: maelstrom-oppose
description: "Use when shipping skills/plugins. Oppositional gate before publish."
version: 1.0.0
author: SMF Works / Team Maelstrom
license: MIT
metadata:
  hermes:
    tags: [qa, oppositional, ship-gate, hermes, maelstrom]
    related_skills: [requesting-code-review, hermes-agent-skill-authoring, dogfood]
---

# Maelstrom Oppose

## Overview

Before a skill or plugin leaves harbor, run it through the Moskstraumen. The Lofoten maelstrom is a real tidal current system that punishes casual seamanship. This skill is the same discipline for packages.

## When to Use

- Immediately before GitHub publish of a skill or plugin
- After tests pass but before claiming done
- Lookout role in crew challenges

## Procedure

1. `maelstrom_check_skill` or `maelstrom_check_plugin` on the path.
2. Require status pass or pass_with_fixes with all error severity fixed.
3. `maelstrom_run_pytest` when tests/ exists — green required.
4. Manually try to break: empty inputs, huge inputs, missing files, duplicate IDs.
5. Write OPPOSITION.md scars (first failure kept).
6. Only then tag/push/install.

## Completion criteria

- [ ] Static gate not fail
- [ ] Pytest green (if applicable)
- [ ] At least one scar documented
- [ ] Install path verified

## Pitfalls

1. Treating warnings as optional forever.
2. Checking only the happy-path demo.
3. No OPPOSITION.md (crew challenge incomplete).
