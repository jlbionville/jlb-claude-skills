#!/usr/bin/env python3
"""Validate the YAML frontmatter and size of every agent and skill in the plugins tree.

Usage:
    python3 scripts/validate_components.py [--root plugins] [--max-agent-lines 300]
                                           [--max-skill-lines 300] [--json] [-v]
Exit codes: 0 when everything passes, 3 when at least one component fails.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constants import (  # noqa: E402
    AGENT_NAME_MAX,
    AGENT_NAME_MIN,
    AGENT_NAME_PATTERN,
    AGENTS_DIR,
    ALLOWED_COLORS,
    ALLOWED_MODELS,
    DEFAULT_MAX_AGENT_LINES,
    DEFAULT_MAX_SKILL_LINES,
    DEFAULT_ROOT,
    FRONTMATTER_DELIMITER,
    FULL_MODEL_ID_PREFIX,
    MAX_AGENT_BODY_CHARS,
    MAX_DESCRIPTION_CHARS,
    REQUIRED_AGENT_FIELDS,
    REQUIRED_SKILL_FIELDS,
    SKILL_FILE,
    SKILLS_DIR,
    TRIGGER_PREFIXES,
    ExitCode,
)

logger = logging.getLogger(__name__)


@dataclass
class Frontmatter:
    """A parsed Markdown component: frontmatter fields plus the body."""

    fields: dict[str, str] = field(default_factory=dict)
    body: str = ""
    present: bool = False

    @property
    def body_lines(self) -> int:
        return len(self.body.rstrip("\n").splitlines()) if self.body.strip() else 0

    @classmethod
    def parse(cls, text: str) -> "Frontmatter":
        """Parse a minimal YAML frontmatter: scalars, folded (`>`/`|`) blocks, inline lists."""
        lines = text.splitlines()
        if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
            return cls(body=text, present=False)
        fields: dict[str, str] = {}
        current_key: Optional[str] = None
        folded = False
        index = 1
        while index < len(lines):
            line = lines[index]
            if line.strip() == FRONTMATTER_DELIMITER:
                index += 1
                break
            match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
            if match and not line.startswith((" ", "\t")):
                current_key, value = match.group(1), match.group(2).strip()
                folded = value in (">", "|", ">-", "|-")
                fields[current_key] = "" if folded else value
            elif current_key is not None and (line.startswith((" ", "\t")) or not line.strip()):
                continuation = line.strip()
                if continuation.startswith("- "):
                    continuation = continuation[2:]
                separator = " " if folded or fields[current_key] else ""
                if continuation:
                    fields[current_key] = f"{fields[current_key]}{separator}{continuation}".strip()
            index += 1
        return cls(fields=fields, body="\n".join(lines[index:]), present=True)


@dataclass
class Issue:
    path: Path
    message: str

    def render(self) -> str:
        return f"{self.path}: {self.message}"


class AgentRule:
    """Rules for `plugins/<plugin>/agents/**/*.md`."""

    def __init__(self, max_lines: int) -> None:
        self.max_lines = max_lines

    def check(self, path: Path, component: Frontmatter) -> list[Issue]:
        issues: list[Issue] = []
        if not component.present:
            return [Issue(path, "missing frontmatter block")]
        for name in REQUIRED_AGENT_FIELDS:
            if not component.fields.get(name):
                issues.append(Issue(path, f"missing required field '{name}'"))
        issues.extend(self._check_name(path, component.fields.get("name", "")))
        issues.extend(check_description(path, component.fields.get("description", "")))
        color = component.fields.get("color")
        if color and color not in ALLOWED_COLORS:
            issues.append(
                Issue(path, f"color '{color}' not in {sorted(ALLOWED_COLORS)}")
            )
        model = component.fields.get("model")
        if model and model not in ALLOWED_MODELS and not model.startswith(FULL_MODEL_ID_PREFIX):
            issues.append(Issue(path, f"model '{model}' not in {sorted(ALLOWED_MODELS)}"))
        if component.body_lines > self.max_lines:
            issues.append(
                Issue(path, f"body has {component.body_lines} lines (max {self.max_lines})")
            )
        if len(component.body) > MAX_AGENT_BODY_CHARS:
            issues.append(
                Issue(path, f"body has {len(component.body)} chars (max {MAX_AGENT_BODY_CHARS})")
            )
        return issues

    @staticmethod
    def _check_name(path: Path, name: str) -> list[Issue]:
        if not name:
            return []
        if not (AGENT_NAME_MIN <= len(name) <= AGENT_NAME_MAX) or not re.match(
            AGENT_NAME_PATTERN, name
        ):
            return [Issue(path, f"name '{name}' must be 3-50 chars of [a-z0-9-], no edge hyphen")]
        if name != path.stem:
            return [Issue(path, f"name '{name}' differs from file stem '{path.stem}'")]
        return []


class SkillRule:
    """Rules for `plugins/<plugin>/skills/<skill>/SKILL.md`."""

    def __init__(self, max_lines: int) -> None:
        self.max_lines = max_lines

    def check(self, path: Path, component: Frontmatter) -> list[Issue]:
        if not component.present:
            return [Issue(path, "missing frontmatter block")]
        issues: list[Issue] = []
        for name in REQUIRED_SKILL_FIELDS:
            if not component.fields.get(name):
                issues.append(Issue(path, f"missing required field '{name}'"))
        issues.extend(check_description(path, component.fields.get("description", "")))
        skill_name = component.fields.get("name")
        if skill_name and skill_name != path.parent.name:
            issues.append(
                Issue(path, f"name '{skill_name}' differs from directory '{path.parent.name}'")
            )
        if component.body_lines > self.max_lines:
            issues.append(
                Issue(path, f"SKILL.md body has {component.body_lines} lines (max {self.max_lines})")
            )
        return issues


def check_description(path: Path, description: str) -> list[Issue]:
    issues: list[Issue] = []
    if not description:
        return issues
    if not description.startswith(TRIGGER_PREFIXES):
        issues.append(
            Issue(path, f"description must start with a trigger phrase {TRIGGER_PREFIXES}")
        )
    if len(description) > MAX_DESCRIPTION_CHARS:
        issues.append(
            Issue(path, f"description has {len(description)} chars (max {MAX_DESCRIPTION_CHARS})")
        )
    return issues


class ComponentValidator:
    """Walks the plugins tree and applies the rules."""

    def __init__(
        self,
        root: Path,
        max_agent_lines: int = DEFAULT_MAX_AGENT_LINES,
        max_skill_lines: int = DEFAULT_MAX_SKILL_LINES,
    ) -> None:
        self.root = root
        self.agent_rule = AgentRule(max_agent_lines)
        self.skill_rule = SkillRule(max_skill_lines)

    def agents(self) -> Iterator[Path]:
        yield from sorted(self.root.glob(f"*/{AGENTS_DIR}/**/*.md"))

    def skills(self) -> Iterator[Path]:
        yield from sorted(self.root.glob(f"*/{SKILLS_DIR}/*/{SKILL_FILE}"))

    def run(self) -> list[Issue]:
        issues: list[Issue] = []
        for path in self.agents():
            issues.extend(self.agent_rule.check(path, Frontmatter.parse(read(path))))
        for path in self.skills():
            issues.extend(self.skill_rule.check(path, Frontmatter.parse(read(path))))
        return issues


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ValidateComponents:
    """CLI entry point: parse arguments, configure logging, run, report."""

    def __init__(self) -> None:
        self.args: Optional[argparse.Namespace] = None

    def _parse_arguments(self, argv: Optional[list[str]]) -> int:
        parser = argparse.ArgumentParser(
            description="Validate agent and skill frontmatter in the plugins tree.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="Examples:\n  python3 scripts/validate_components.py\n"
            "  python3 scripts/validate_components.py --root plugins --json",
        )
        parser.add_argument("-r", "--root", type=Path, default=Path(DEFAULT_ROOT),
                            help="Plugins directory (default: %(default)s)")
        parser.add_argument("--max-agent-lines", type=int, default=DEFAULT_MAX_AGENT_LINES,
                            help="Maximum agent body lines (default: %(default)s)")
        parser.add_argument("--max-skill-lines", type=int, default=DEFAULT_MAX_SKILL_LINES,
                            help="Maximum SKILL.md body lines (default: %(default)s)")
        parser.add_argument("-j", "--json", action="store_true", help="JSON output")
        parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
        self.args = parser.parse_args(argv)
        return ExitCode.SUCCESS

    def _setup_logging(self) -> int:
        level = logging.DEBUG if self.args and self.args.verbose else logging.INFO
        logging.basicConfig(level=level, format="%(levelname)s %(message)s")
        return ExitCode.SUCCESS

    def _execute(self) -> int:
        assert self.args is not None
        if not self.args.root.is_dir():
            logger.error("Root directory not found: %s", self.args.root)
            return ExitCode.GENERAL_ERROR
        validator = ComponentValidator(
            self.args.root, self.args.max_agent_lines, self.args.max_skill_lines
        )
        issues = validator.run()
        counted = sum(1 for _ in validator.agents()) + sum(1 for _ in validator.skills())
        if self.args.json:
            print(json.dumps([{"path": str(i.path), "message": i.message} for i in issues],
                             ensure_ascii=False, indent=2))
        else:
            for issue in issues:
                print(issue.render())
            logger.info("%d component(s) checked, %d issue(s)", counted, len(issues))
        return ExitCode.VALIDATION_ERROR if issues else ExitCode.SUCCESS

    def run(self, argv: Optional[list[str]] = None) -> int:
        exit_code = self._parse_arguments(argv)
        if exit_code != ExitCode.SUCCESS:
            return exit_code
        for phase in (self._setup_logging, self._execute):
            exit_code = phase()
            if exit_code != ExitCode.SUCCESS:
                return exit_code
        return ExitCode.SUCCESS


def main() -> int:
    return ValidateComponents().run()


if __name__ == "__main__":
    sys.exit(main())
