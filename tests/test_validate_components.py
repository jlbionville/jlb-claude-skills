"""Tests du validateur de frontmatter des agents et skills."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from constants import ExitCode  # noqa: E402
from validate_components import ComponentValidator  # noqa: E402

VALID_AGENT = """---
name: rust-reviewer
description: >
  À utiliser quand du code Rust vient d'être écrit ou modifié et qu'une relecture
  est demandée avant un commit.
tools: Read, Grep, Glob, Bash
model: inherit
color: blue
---

Tu relis du Rust.
"""

VALID_SKILL = """---
name: rust-dev
description: Use when writing Rust in a multi-crate workspace (cargo, clippy, fixtures).
---

# Rust dev
"""


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def agent_path(root: Path, name: str = "rust-reviewer") -> Path:
    return root / "plugins" / "p" / "agents" / f"{name}.md"


def skill_path(root: Path, name: str = "rust-dev") -> Path:
    return root / "plugins" / "p" / "skills" / name / "SKILL.md"


def problems(root: Path) -> list[str]:
    return [issue.message for issue in ComponentValidator(root / "plugins").run()]


def test_valid_agent_passes(tmp_path: Path) -> None:
    write(agent_path(tmp_path), VALID_AGENT)
    write(skill_path(tmp_path), VALID_SKILL)
    assert problems(tmp_path) == []


def test_agent_without_color_fails(tmp_path: Path) -> None:
    write(agent_path(tmp_path), VALID_AGENT.replace("color: blue\n", ""))
    assert any("color" in message for message in problems(tmp_path))


def test_agent_color_outside_list_fails(tmp_path: Path) -> None:
    write(agent_path(tmp_path), VALID_AGENT.replace("color: blue", "color: magenta"))
    assert any("magenta" in message for message in problems(tmp_path))


def test_agent_body_over_limit_fails(tmp_path: Path) -> None:
    body = "\n".join("ligne" for _ in range(301))
    write(agent_path(tmp_path), VALID_AGENT + body + "\n")
    assert any("lines" in message and "max 300" in message for message in problems(tmp_path))


def test_agent_description_without_trigger_fails(tmp_path: Path) -> None:
    text = VALID_AGENT.replace("À utiliser quand", "USE PROACTIVELY for")
    write(agent_path(tmp_path), text)
    assert any("trigger" in message for message in problems(tmp_path))


def test_skill_over_500_lines_fails(tmp_path: Path) -> None:
    body = "\n".join("ligne" for _ in range(501))
    write(skill_path(tmp_path), VALID_SKILL + body + "\n")
    assert any("SKILL.md" in message and "lines" in message for message in problems(tmp_path))


def test_skill_description_over_1024_fails(tmp_path: Path) -> None:
    long_description = "Use when " + "x" * 1030
    write(skill_path(tmp_path), VALID_SKILL.replace(
        "Use when writing Rust in a multi-crate workspace (cargo, clippy, fixtures).",
        long_description,
    ))
    assert any("1024" in message for message in problems(tmp_path))


def test_cli_returns_3_on_error_and_0_otherwise(tmp_path: Path) -> None:
    write(agent_path(tmp_path), VALID_AGENT)
    script = REPO_ROOT / "scripts" / "validate_components.py"
    ok = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path / "plugins")],
        capture_output=True, text=True, check=False,
    )
    assert ok.returncode == ExitCode.SUCCESS, ok.stdout + ok.stderr
    write(agent_path(tmp_path), VALID_AGENT.replace("color: blue", "color: magenta"))
    bad = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path / "plugins")],
        capture_output=True, text=True, check=False,
    )
    assert bad.returncode == ExitCode.VALIDATION_ERROR
    assert "magenta" in bad.stdout + bad.stderr


def test_plugin_filter_limits_the_scan(tmp_path: Path) -> None:
    write(agent_path(tmp_path), VALID_AGENT.replace("color: blue", "color: magenta"))
    other = tmp_path / "plugins" / "q" / "agents" / "rust-reviewer.md"
    write(other, VALID_AGENT)
    assert problems(tmp_path) != []
    assert [issue.message for issue in ComponentValidator(tmp_path / "plugins", plugin="q").run()] == []
    assert any(
        "magenta" in issue.message
        for issue in ComponentValidator(tmp_path / "plugins", plugin="p").run()
    )


def test_unknown_plugin_is_an_error(tmp_path: Path) -> None:
    write(agent_path(tmp_path), VALID_AGENT)
    script = REPO_ROOT / "scripts" / "validate_components.py"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path / "plugins"), "--plugin", "nope"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == ExitCode.GENERAL_ERROR
    assert "nope" in result.stdout + result.stderr


def test_preloaded_skill_must_exist_in_the_plugins_tree(tmp_path: Path) -> None:
    agent = VALID_AGENT.replace("color: blue\n", "color: blue\nskills:\n  - rust-dev\n  - missing-skill\n")
    write(agent_path(tmp_path), agent)
    write(skill_path(tmp_path), VALID_SKILL)
    messages = problems(tmp_path)
    assert any("missing-skill" in m for m in messages)
    assert not any("rust-dev" in m for m in messages)
