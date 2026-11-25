"""Constants for the component validator (no literals elsewhere)."""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Process exit codes."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    VALIDATION_ERROR = 3


# Colors documented for file-based subagents (code.claude.com/docs/en/sub-agents.md).
ALLOWED_COLORS: frozenset[str] = frozenset(
    {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}
)
# Short model names accepted in agent frontmatter; a full model id is also accepted.
ALLOWED_MODELS: frozenset[str] = frozenset({"inherit", "sonnet", "opus", "haiku", "fable"})
FULL_MODEL_ID_PREFIX = "claude-"
# A description must say when to use the component, not summarize its workflow.
TRIGGER_PREFIXES: tuple[str, ...] = ("À utiliser", "Use this agent when", "Use when")

REQUIRED_AGENT_FIELDS: tuple[str, ...] = ("name", "description", "model", "color")
REQUIRED_SKILL_FIELDS: tuple[str, ...] = ("name", "description")

DEFAULT_MAX_AGENT_LINES = 300
DEFAULT_MAX_SKILL_LINES = 500  # documented hard limit; new skills aim for 300
MAX_AGENT_BODY_CHARS = 10_000
MAX_DESCRIPTION_CHARS = 1024
AGENT_NAME_MIN = 3
AGENT_NAME_MAX = 50
AGENT_NAME_PATTERN = r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"

DEFAULT_ROOT = "plugins"
AGENTS_DIR = "agents"
SKILLS_DIR = "skills"
SKILL_FILE = "SKILL.md"
FRONTMATTER_DELIMITER = "---"
