#!/usr/bin/env python3
"""
installer.py — Install jlb-claude-skills into Claude Code (legacy method).

Preferred: /plugin marketplace add jlbionville/jlb-claude-skills

Usage:
    python installer.py                                        # All plugins, all components, symlink
    python installer.py --mode copy                            # Copy mode
    python installer.py --plugin jlb-python-toolkit            # One plugin only
    python installer.py --component agents                     # Only agents (skills|agents|all)
    python installer.py --project /path/to/repo                # Into a project's .claude/
    python installer.py --list                                 # Show plugins
    python installer.py --uninstall                            # Remove all
    python installer.py --dry-run                              # Preview without writing
    python installer.py --report-specifics                     # Report project-specific refs in agents
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from enum import StrEnum
from pathlib import Path

# ── Error codes ───────────────────────────────────────────────────────────────

class ErrorCode(StrEnum):
    OK = "OK"
    PLUGIN_NOT_FOUND = "PLUGIN_NOT_FOUND"
    TARGET_NOT_WRITABLE = "TARGET_NOT_WRITABLE"
    SKILL_INVALID = "SKILL_INVALID"
    AGENT_INVALID = "AGENT_INVALID"
    COMPONENT_UNKNOWN = "COMPONENT_UNKNOWN"

ERROR_CATALOG = {
    ErrorCode.PLUGIN_NOT_FOUND: "Plugin '{name}' not found in plugins/",
    ErrorCode.TARGET_NOT_WRITABLE: "Cannot write to target directory: {path}",
    ErrorCode.SKILL_INVALID: "Skill directory missing SKILL.md: {path}",
    ErrorCode.AGENT_INVALID: "Agent missing required frontmatter (name, description): {path}",
    ErrorCode.COMPONENT_UNKNOWN: "Unknown component: {name}. Expected: skills, agents, all.",
}

# ── Constants ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGINS_DIR = SCRIPT_DIR / "plugins"
CLAUDE_ROOT = Path.home() / ".claude"
DEFAULT_SKILLS_TARGET = CLAUDE_ROOT / "skills"
DEFAULT_AGENTS_TARGET = CLAUDE_ROOT / "agents"

# Keywords for --report-specifics: detect project-specific references in agents.
# PRODUCT_VISION.md, REQUIREMENTS.md, USER_STORIES.md are standard agile artifacts
# and NOT project-specific — they belong to the product-owner agent's generic role.
PROJECT_SPECIFIC_KEYWORDS = [
    "script4secrets",
    "test4secrets",
    "Dollar Universe",
    "Automic",
    "ops/file_transfer",
]

# ── Colors ────────────────────────────────────────────────────────────────────

class C:
    OK = "\033[32m✓\033[0m"
    WARN = "\033[33m⚠\033[0m"
    ERR = "\033[31m✗\033[0m"
    INFO = "\033[36mℹ\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    NC = "\033[0m"


def _supports_color() -> bool:
    return sys.stdout.isatty() and (os.name != "nt" or "WT_SESSION" in os.environ)


if not _supports_color():
    C.OK = "[OK]"
    C.WARN = "[!]"
    C.ERR = "[X]"
    C.INFO = "[i]"
    C.BOLD = ""
    C.CYAN = ""
    C.NC = ""

# ── Frontmatter validation ────────────────────────────────────────────────────

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def validate_agent_frontmatter(path: Path) -> tuple[bool, str]:
    """Return (is_valid, error_message). Checks name+description keys are present."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"read error: {exc}"

    match = FRONTMATTER_RE.match(content)
    if not match:
        return False, "no YAML frontmatter"

    block = match.group(1)
    has_name = re.search(r"^\s*name\s*:\s*\S+", block, re.MULTILINE) is not None
    has_desc = re.search(r"^\s*description\s*:\s*(\S+|>)", block, re.MULTILINE) is not None

    if not (has_name and has_desc):
        missing = [k for k, v in (("name", has_name), ("description", has_desc)) if not v]
        return False, f"missing keys: {', '.join(missing)}"
    return True, ""

# ── Discovery ─────────────────────────────────────────────────────────────────

def discover_plugins() -> dict[str, dict]:
    """Read plugin metadata and enumerate skills + agents for every plugin."""
    plugins: dict[str, dict] = {}
    if not PLUGINS_DIR.exists():
        return plugins

    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        manifest = plugin_dir / ".claude-plugin" / "plugin.json"
        if not manifest.exists():
            continue
        meta = json.loads(manifest.read_text(encoding="utf-8"))

        skills_dir = plugin_dir / "skills"
        skill_names = [
            d.name for d in sorted(skills_dir.iterdir())
            if d.is_dir() and (d / "SKILL.md").exists()
        ] if skills_dir.exists() else []

        agents_dir = plugin_dir / "agents"
        agent_paths: list[Path] = sorted(agents_dir.rglob("*.md")) if agents_dir.exists() else []

        plugins[meta["name"]] = {
            "description": meta.get("description", ""),
            "version": meta.get("version", "1.0.0"),
            "path": plugin_dir,
            "skills": skill_names,
            "agents": agent_paths,
        }
    return plugins

# ── Listing ───────────────────────────────────────────────────────────────────

def list_plugins() -> int:
    plugins = discover_plugins()
    print(f"\n{C.BOLD}Available plugins:{C.NC}\n")
    for name, meta in plugins.items():
        n_skills = len(meta["skills"])
        n_agents = len(meta["agents"])
        print(f"  {C.CYAN}{name}{C.NC} v{meta['version']} "
              f"({n_skills} skills, {n_agents} agents)")
        desc = meta["description"][:80]
        if desc:
            print(f"    {desc}...")
        for skill in meta["skills"]:
            print(f"    {C.OK} skill:  {skill}")
        for agent in meta["agents"]:
            rel = agent.relative_to(meta["path"] / "agents")
            print(f"    {C.OK} agent:  {rel}")
        print()
    print(f"  {C.BOLD}Plugin marketplace (preferred):{C.NC}")
    print("    /plugin marketplace add jlbionville/jlb-claude-skills")
    print("    /plugin install <name>@jlb-claude-skills\n")
    return 0

# ── Install helpers ───────────────────────────────────────────────────────────

def _place(src: Path, dest: Path, mode: str) -> None:
    """Symlink or copy src → dest. Falls back to copy if symlink is unsupported."""
    if dest.is_symlink() or dest.exists():
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)

    dest.parent.mkdir(parents=True, exist_ok=True)

    if mode == "symlink":
        try:
            dest.symlink_to(src.resolve())
            return
        except OSError:
            pass

    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)


def install_skill(skill_src: Path, target_dir: Path, mode: str, dry_run: bool) -> bool:
    skill_name = skill_src.name
    dest = target_dir / skill_name

    if not (skill_src / "SKILL.md").exists():
        print(f"  {C.WARN} Skipping {skill_name} (no SKILL.md)")
        return False

    if dry_run:
        print(f"  {C.INFO} [dry-run] would install skill: {skill_name}")
        return True

    _place(skill_src, dest, mode)
    print(f"  {C.OK} skill: {skill_name}")
    return True


def install_agent(agent_src: Path, plugin_agents_root: Path, target_dir: Path,
                  mode: str, dry_run: bool) -> bool:
    """Install one agent .md, preserving its relative path (flat or nested)."""
    valid, err = validate_agent_frontmatter(agent_src)
    if not valid:
        rel = agent_src.relative_to(plugin_agents_root)
        print(f"  {C.ERR} {rel}: {err} ({ErrorCode.AGENT_INVALID})")
        return False

    rel = agent_src.relative_to(plugin_agents_root)
    dest = target_dir / rel

    if dry_run:
        print(f"  {C.INFO} [dry-run] would install agent: {rel}")
        return True

    _place(agent_src, dest, mode)
    print(f"  {C.OK} agent: {rel}")
    return True

# ── Install / uninstall ───────────────────────────────────────────────────────

def install(plugin_names: list[str], skills_target: Path, agents_target: Path,
            mode: str, component: str, dry_run: bool) -> int:
    plugins = discover_plugins()

    for name in plugin_names:
        if name not in plugins:
            print(f"{C.ERR} {ERROR_CATALOG[ErrorCode.PLUGIN_NOT_FOUND].format(name=name)}")
            return 1

    if not dry_run:
        if component in ("skills", "all"):
            skills_target.mkdir(parents=True, exist_ok=True)
        if component in ("agents", "all"):
            agents_target.mkdir(parents=True, exist_ok=True)

    n_skills = 0
    n_agents = 0

    for name in plugin_names:
        meta = plugins[name]
        print(f"\n{C.INFO} Installing {C.BOLD}{name}{C.NC} "
              f"(mode={mode}, component={component}{', dry-run' if dry_run else ''})")

        if component in ("skills", "all"):
            skills_dir = meta["path"] / "skills"
            for skill_name in meta["skills"]:
                if install_skill(skills_dir / skill_name, skills_target, mode, dry_run):
                    n_skills += 1

        if component in ("agents", "all"):
            agents_dir = meta["path"] / "agents"
            for agent_path in meta["agents"]:
                if install_agent(agent_path, agents_dir, agents_target, mode, dry_run):
                    n_agents += 1

    verb = "Would install" if dry_run else "Installed"
    print(f"\n{C.OK} {C.BOLD}{verb} {n_skills} skills → {skills_target}{C.NC}")
    print(f"{C.OK} {C.BOLD}{verb} {n_agents} agents → {agents_target}{C.NC}\n")
    return 0


def uninstall(skills_target: Path, agents_target: Path, component: str) -> int:
    plugins = discover_plugins()
    n_skills = 0
    n_agents = 0

    if component in ("skills", "all"):
        for meta in plugins.values():
            for skill_name in meta["skills"]:
                dest = skills_target / skill_name
                if dest.is_symlink() or dest.exists():
                    if dest.is_symlink() or dest.is_file():
                        dest.unlink()
                    else:
                        shutil.rmtree(dest)
                    print(f"  {C.OK} Removed skill: {skill_name}")
                    n_skills += 1

    if component in ("agents", "all"):
        for meta in plugins.values():
            plugin_agents_root = meta["path"] / "agents"
            for agent_path in meta["agents"]:
                rel = agent_path.relative_to(plugin_agents_root)
                dest = agents_target / rel
                if dest.is_symlink() or dest.exists():
                    if dest.is_symlink() or dest.is_file():
                        dest.unlink()
                    else:
                        shutil.rmtree(dest)
                    print(f"  {C.OK} Removed agent: {rel}")
                    n_agents += 1
            if agents_target.exists():
                for sub in sorted(agents_target.iterdir(), reverse=True):
                    if sub.is_dir() and not any(sub.iterdir()):
                        sub.rmdir()

    total = n_skills + n_agents
    if total == 0:
        print(f"  {C.WARN} Nothing to uninstall.")
    else:
        print(f"\n{C.OK} Removed {n_skills} skills and {n_agents} agents.")
    return 0

# ── Reporting ─────────────────────────────────────────────────────────────────

def report_specifics() -> int:
    """Scan installed agents for project-specific references and list them.
    Skips intentional mentions inside "e.g." example lists."""
    plugins = discover_plugins()
    hits: dict[Path, list[str]] = {}
    intentional = re.compile(r"e\.g\.\s+[^)\n]*")

    for meta in plugins.values():
        for agent_path in meta["agents"]:
            try:
                content = agent_path.read_text(encoding="utf-8")
            except OSError:
                continue
            # Strip "e.g. ..." fragments before scanning to avoid false positives
            scan_text = intentional.sub("", content)
            matched = [kw for kw in PROJECT_SPECIFIC_KEYWORDS if kw in scan_text]
            if matched:
                hits[agent_path] = matched

    if not hits:
        print(f"{C.OK} No project-specific references detected.")
        return 0

    print(f"\n{C.BOLD}Project-specific references detected in agents:{C.NC}\n")
    for path, keywords in hits.items():
        rel = path.relative_to(SCRIPT_DIR)
        print(f"  {C.WARN} {rel}")
        for kw in keywords:
            print(f"      · {kw}")
    print(f"\n{C.INFO} These agents may need generalization for reuse outside their origin project.\n")
    return 0

# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    plugins = discover_plugins()
    parser = argparse.ArgumentParser(
        description="Install jlb-claude-skills into Claude Code (skills + agents).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Preferred: /plugin marketplace add jlbionville/jlb-claude-skills",
    )
    parser.add_argument("--mode", choices=["symlink", "copy"], default="symlink",
                        help="Installation mode (default: %(default)s)")
    parser.add_argument("--component", choices=["skills", "agents", "all"], default="all",
                        help="Which component(s) to install (default: %(default)s)")
    parser.add_argument("--plugin", "-p", action="append", dest="plugins",
                        choices=list(plugins.keys()) or None,
                        help="Install specific plugin(s). Repeatable.")
    parser.add_argument("--project", type=Path, metavar="PATH",
                        help="Install into a project's .claude/ directory")
    parser.add_argument("--skills-target", type=Path, default=None,
                        help=f"Custom skills target (default: {DEFAULT_SKILLS_TARGET})")
    parser.add_argument("--agents-target", type=Path, default=None,
                        help=f"Custom agents target (default: {DEFAULT_AGENTS_TARGET})")
    parser.add_argument("--list", "-l", action="store_true", help="List plugins")
    parser.add_argument("--uninstall", "-u", action="store_true", help="Remove installed items")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview actions without writing")
    parser.add_argument("--report-specifics", action="store_true",
                        help="Scan agents for project-specific references")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.list:
        return list_plugins()

    if args.report_specifics:
        return report_specifics()

    if args.project:
        skills_target = args.skills_target or (args.project / ".claude" / "skills")
        agents_target = args.agents_target or (args.project / ".claude" / "agents")
    else:
        skills_target = args.skills_target or DEFAULT_SKILLS_TARGET
        agents_target = args.agents_target or DEFAULT_AGENTS_TARGET

    if args.uninstall:
        return uninstall(skills_target, agents_target, args.component)

    plugin_names = args.plugins or list(discover_plugins().keys())
    return install(plugin_names, skills_target, agents_target,
                   args.mode, args.component, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
