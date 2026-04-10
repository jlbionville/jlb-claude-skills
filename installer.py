#!/usr/bin/env python3
"""
installer.py — Install jlb-claude-skills into Claude Code (legacy method).

Preferred: /plugin marketplace add jlbionville/jlb-claude-skills

Usage:
    python installer.py                              # Install all, symlink
    python installer.py --mode copy                  # Install all, copy
    python installer.py --plugin jlb-aws-serverless  # One plugin only
    python installer.py --project /path/to/repo      # Into a project
    python installer.py --list                        # Show plugins
    python installer.py --uninstall                   # Remove all
"""

from __future__ import annotations

import argparse
import json
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

ERROR_CATALOG = {
    ErrorCode.PLUGIN_NOT_FOUND: "Plugin '{name}' not found in plugins/",
    ErrorCode.TARGET_NOT_WRITABLE: "Cannot write to target directory: {path}",
    ErrorCode.SKILL_INVALID: "Skill directory missing SKILL.md: {path}",
}

# ── Constants ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGINS_DIR = SCRIPT_DIR / "plugins"
DEFAULT_TARGET = Path.home() / ".claude" / "skills"

# ── Colors ────────────────────────────────────────────────────────────────────

class C:
    OK = "\033[32m✓\033[0m"
    WARN = "\033[33m⚠\033[0m"
    ERR = "\033[31m✗\033[0m"
    INFO = "\033[36mℹ\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    NC = "\033[0m"

# ── Discovery ─────────────────────────────────────────────────────────────────

def discover_plugins() -> dict[str, dict]:
    """Read plugin metadata from plugin.json files."""
    plugins = {}
    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        manifest = plugin_dir / ".claude-plugin" / "plugin.json"
        if not manifest.exists():
            continue
        meta = json.loads(manifest.read_text())
        skills_dir = plugin_dir / "skills"
        skill_names = [
            d.name for d in sorted(skills_dir.iterdir())
            if d.is_dir() and (d / "SKILL.md").exists()
        ] if skills_dir.exists() else []
        plugins[meta["name"]] = {
            "description": meta.get("description", ""),
            "version": meta.get("version", "1.0.0"),
            "path": plugin_dir,
            "skills": skill_names,
        }
    return plugins

# ── Core functions ────────────────────────────────────────────────────────────

def list_plugins() -> None:
    plugins = discover_plugins()
    print(f"\n{C.BOLD}Available plugins:{C.NC}\n")
    for name, meta in plugins.items():
        print(f"  {C.CYAN}{name}{C.NC} v{meta['version']} ({len(meta['skills'])} skills)")
        desc = meta["description"][:80]
        if desc:
            print(f"    {desc}...")
        for skill in meta["skills"]:
            print(f"    {C.OK} {skill}")
        print()
    print(f"  {C.BOLD}Plugin marketplace (preferred):{C.NC}")
    print(f"    /plugin marketplace add jlbionville/jlb-claude-skills")
    print(f"    /plugin install <name>@jlb-claude-skills\n")


def install_skill(skill_src: Path, target_dir: Path, mode: str) -> bool:
    skill_name = skill_src.name
    dest = target_dir / skill_name

    if not (skill_src / "SKILL.md").exists():
        print(f"  {C.WARN} Skipping {skill_name} (no SKILL.md)")
        return False

    if dest.is_symlink() or dest.exists():
        if dest.is_symlink():
            dest.unlink()
        else:
            shutil.rmtree(dest)

    if mode == "symlink":
        dest.symlink_to(skill_src.resolve())
    else:
        shutil.copytree(skill_src, dest)

    print(f"  {C.OK} {skill_name}")
    return True


def install(plugin_names: list[str], target: Path, mode: str) -> int:
    plugins = discover_plugins()
    target.mkdir(parents=True, exist_ok=True)
    count = 0

    for name in plugin_names:
        if name not in plugins:
            print(f"{C.ERR} {ERROR_CATALOG[ErrorCode.PLUGIN_NOT_FOUND].format(name=name)}")
            return 1

        meta = plugins[name]
        print(f"\n{C.INFO} Installing {C.BOLD}{name}{C.NC} ({mode} mode)")

        skills_dir = meta["path"] / "skills"
        for skill_name in meta["skills"]:
            if install_skill(skills_dir / skill_name, target, mode):
                count += 1

    print(f"\n{C.OK} {C.BOLD}Installed {count} skills into {target}{C.NC} ({mode} mode)\n")
    return 0


def uninstall(target: Path) -> int:
    plugins = discover_plugins()
    count = 0
    for meta in plugins.values():
        for skill_name in meta["skills"]:
            dest = target / skill_name
            if dest.is_symlink() or dest.exists():
                if dest.is_symlink():
                    dest.unlink()
                else:
                    shutil.rmtree(dest)
                print(f"  {C.OK} Removed {skill_name}")
                count += 1
    if count == 0:
        print(f"  {C.WARN} Nothing to uninstall.")
    else:
        print(f"\n{C.OK} Removed {count} skills.")
    return 0


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    plugins = discover_plugins()
    p = argparse.ArgumentParser(
        description="Install jlb-claude-skills into Claude Code (legacy method)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Preferred: /plugin marketplace add jlbionville/jlb-claude-skills",
    )
    p.add_argument("--mode", choices=["symlink", "copy"], default="symlink",
                   help="Installation mode (default: symlink)")
    p.add_argument("--plugin", "-p", action="append", dest="plugins",
                   choices=list(plugins.keys()),
                   help="Install specific plugin(s). Repeatable.")
    p.add_argument("--project", type=Path, metavar="PATH",
                   help="Install into a project's .claude/skills/")
    p.add_argument("--target", type=Path, default=None,
                   help=f"Custom target (default: {DEFAULT_TARGET})")
    p.add_argument("--list", "-l", action="store_true", help="List plugins")
    p.add_argument("--uninstall", "-u", action="store_true", help="Remove all")
    return p


def main() -> int:
    args = build_parser().parse_args()

    if args.list:
        list_plugins()
        return 0

    target = args.target or (
        args.project / ".claude" / "skills" if args.project else DEFAULT_TARGET
    )

    if args.uninstall:
        return uninstall(target)

    plugins = args.plugins or list(discover_plugins().keys())
    return install(plugins, target, args.mode)


if __name__ == "__main__":
    sys.exit(main())
