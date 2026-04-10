#!/usr/bin/env bash
# =============================================================================
# install.sh — Install jlb-claude-skills into Claude Code
#
# Usage:
#   ./install.sh                     # Install all plugins (symlink mode)
#   ./install.sh --copy              # Install all plugins (copy mode)
#   ./install.sh --plugin jlb-aws-serverless
#   ./install.sh --plugin jlb-python-toolkit --copy
#   ./install.sh --project /path/to/repo   # Install to .claude/skills/ in a project
#   ./install.sh --list              # List available plugins and skills
#   ./install.sh --uninstall         # Remove all installed skills
#
# Modes:
#   symlink (default): ln -s back to the cloned repo. One source of truth.
#   copy:              cp -r into the target. Independent of the repo.
#
# Note: For the native Claude Code plugin system, use instead:
#   /plugin marketplace add jlbionville/jlb-claude-skills
#   /plugin install jlb-python-toolkit@jlb-claude-skills
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="${SCRIPT_DIR}/plugins"
TARGET_DIR="${HOME}/.claude/skills"
MODE="symlink"
SELECTED_PLUGIN=""
ACTION="install"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log_info()    { echo -e "${CYAN}ℹ${NC}  $*"; }
log_success() { echo -e "${GREEN}✓${NC}  $*"; }
log_warn()    { echo -e "${YELLOW}⚠${NC}  $*"; }
log_error()   { echo -e "${RED}✗${NC}  $*" >&2; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --copy)           MODE="copy"; shift ;;
        --symlink)        MODE="symlink"; shift ;;
        --plugin|-p)      SELECTED_PLUGIN="$2"; shift 2 ;;
        --project)        TARGET_DIR="$2/.claude/skills"; shift 2 ;;
        --target)         TARGET_DIR="$2"; shift 2 ;;
        --list|-l)        ACTION="list"; shift ;;
        --uninstall|-u)   ACTION="uninstall"; shift ;;
        --help|-h)
            sed -n '2,/^# =====/{ /^# =====/d; s/^# \?//; p }' "$0"
            exit 0
            ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

# ── List ──────────────────────────────────────────────────────────────────────
list_plugins() {
    echo -e "\n${BOLD}Available plugins:${NC}\n"
    for plugin_dir in "${PLUGINS_DIR}"/*/; do
        plugin="$(basename "$plugin_dir")"
        skill_count=$(find "$plugin_dir/skills" -maxdepth 2 -name "SKILL.md" 2>/dev/null | wc -l)
        desc=$(python3 -c "import json; print(json.load(open('${plugin_dir}/.claude-plugin/plugin.json'))['description'][:80])" 2>/dev/null || echo "")
        echo -e "  ${CYAN}${plugin}${NC} (${skill_count} skills)"
        [[ -n "$desc" ]] && echo -e "    ${desc}..."
        for skill_dir in "${plugin_dir}"/skills/*/; do
            [[ -f "${skill_dir}/SKILL.md" ]] || continue
            echo "    → $(basename "$skill_dir")"
        done
        echo ""
    done
    echo -e "  ${BOLD}Plugin marketplace:${NC}"
    echo -e "    /plugin marketplace add jlbionville/jlb-claude-skills"
    echo -e "    /plugin install <plugin-name>@jlb-claude-skills"
    echo ""
}

# ── Uninstall ─────────────────────────────────────────────────────────────────
uninstall_skills() {
    log_info "Uninstalling jlb skills from ${TARGET_DIR}"
    local count=0
    for plugin_dir in "${PLUGINS_DIR}"/*/; do
        for skill_dir in "${plugin_dir}"/skills/*/; do
            [[ -f "${skill_dir}/SKILL.md" ]] || continue
            skill="$(basename "$skill_dir")"
            if [[ -e "${TARGET_DIR}/${skill}" ]]; then
                rm -rf "${TARGET_DIR}/${skill}"
                log_success "Removed ${skill}"
                ((count++))
            fi
        done
    done
    [[ $count -eq 0 ]] && log_warn "Nothing to uninstall." || log_success "Removed ${count} skills."
}

# ── Install ───────────────────────────────────────────────────────────────────
install_skills() {
    mkdir -p "$TARGET_DIR"

    local plugins_to_install=()
    if [[ -n "$SELECTED_PLUGIN" ]]; then
        if [[ ! -d "${PLUGINS_DIR}/${SELECTED_PLUGIN}" ]]; then
            log_error "Plugin not found: ${SELECTED_PLUGIN}"
            log_info "Use --list to see available plugins."
            exit 1
        fi
        plugins_to_install=("${PLUGINS_DIR}/${SELECTED_PLUGIN}")
    else
        for d in "${PLUGINS_DIR}"/*/; do plugins_to_install+=("$d"); done
    fi

    local count=0
    for plugin_dir in "${plugins_to_install[@]}"; do
        plugin="$(basename "$plugin_dir")"
        log_info "Installing plugin ${BOLD}${plugin}${NC} (${MODE} mode)"

        for skill_dir in "${plugin_dir}"/skills/*/; do
            [[ -f "${skill_dir}/SKILL.md" ]] || continue
            skill="$(basename "$skill_dir")"
            dest="${TARGET_DIR}/${skill}"

            [[ -e "$dest" || -L "$dest" ]] && rm -rf "$dest"

            if [[ "$MODE" == "symlink" ]]; then
                ln -s "$(cd "$skill_dir" && pwd)" "$dest"
            else
                cp -r "$skill_dir" "$dest"
            fi
            log_success "  ${skill}"
            ((count++))
        done
    done

    echo ""
    log_success "${BOLD}Installed ${count} skills into ${TARGET_DIR}${NC} (${MODE} mode)"
    echo ""
    log_info "Skills available as /skill-name in Claude Code."
}

# ── Main ──────────────────────────────────────────────────────────────────────
case "$ACTION" in
    list)       list_plugins ;;
    uninstall)  uninstall_skills ;;
    install)    install_skills ;;
esac
