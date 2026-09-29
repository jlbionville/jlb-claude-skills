# =============================================================================
# Makefile — jlb-claude-skills installer (legacy method)
#
# Preferred: /plugin marketplace add jlbionville/jlb-claude-skills
#
# Legacy usage:
#   make install                 # Skills + agents (all plugins, symlink)
#   make install MODE=copy       # Copy mode
#   make install-skills          # Only skills (via install.sh)
#   make install-agents          # Only agents (via installer.py)
#   make install-aws             # Only jlb-aws-serverless
#   make install-python          # Only jlb-python-toolkit
#   make install-content         # Only jlb-content-publisher
#   make install-bourse          # Only jlb-bourse
#   make install-atlassian       # Only jlb-atlassian
#   make install-workflow        # Only jlb-workflow-toolkit
#   make project P=/path/to/repo # Install into a project's .claude/
#   make uninstall               # Remove all installed skills and agents
#   make list                    # Show plugins/skills/agents
#   make report-specifics        # Detect project-specific refs in agents
#   make dry-run                 # Preview install without writing
# =============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

MODE       ?= symlink
TARGET     ?= $(HOME)/.claude/skills
SCRIPT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
# Python >= 3.11 requis (StrEnum) : uv choisit la bonne version via l'en-tête
# PEP 723 d'installer.py ; repli sur python3 si uv est absent.
PY         ?= $(if $(shell command -v uv 2>/dev/null),uv run --script,python3)

# install.sh handles skills; installer.py handles both (skills + agents).
SH_INSTALL := bash $(SCRIPT_DIR)/install.sh --$(MODE) --target $(TARGET)
PY_INSTALL := $(PY) $(SCRIPT_DIR)/installer.py --mode $(MODE)

.PHONY: install install-skills install-agents
.PHONY: install-aws install-python install-content install-bourse install-atlassian install-workflow
.PHONY: project uninstall list report-specifics dry-run help

install: ## Install all (skills + agents, MODE=symlink|copy)
	@$(SH_INSTALL)
	@$(PY_INSTALL) --component agents

install-skills: ## Install skills only (all plugins)
	@$(SH_INSTALL)

install-agents: ## Install agents only (all plugins)
	@$(PY_INSTALL) --component agents

install-aws: ## Install jlb-aws-serverless only (skills + agents)
	@$(SH_INSTALL) --plugin jlb-aws-serverless
	@$(PY_INSTALL) --component agents --plugin jlb-aws-serverless

install-python: ## Install jlb-python-toolkit only (skills + agents)
	@$(SH_INSTALL) --plugin jlb-python-toolkit
	@$(PY_INSTALL) --component agents --plugin jlb-python-toolkit

install-content: ## Install jlb-content-publisher only
	@$(SH_INSTALL) --plugin jlb-content-publisher

install-bourse: ## Install jlb-bourse only
	@$(SH_INSTALL) --plugin jlb-bourse

install-atlassian: ## Install jlb-atlassian (agents only)
	@$(PY_INSTALL) --component agents --plugin jlb-atlassian

install-workflow: ## Install jlb-workflow-toolkit (agents only)
	@$(PY_INSTALL) --component agents --plugin jlb-workflow-toolkit

project: ## Install into a project (P=/path/to/repo)
ifndef P
	$(error P is required. Usage: make project P=/path/to/my-repo)
endif
	@bash $(SCRIPT_DIR)/install.sh --$(MODE) --project $(P)
	@$(PY_INSTALL) --project $(P) --component agents

uninstall: ## Remove all installed skills and agents
	@bash $(SCRIPT_DIR)/install.sh --uninstall --target $(TARGET)
	@$(PY_INSTALL) --uninstall --component agents

list: ## List plugins, skills, and agents
	@$(PY) $(SCRIPT_DIR)/installer.py --list

report-specifics: ## Detect project-specific references in agents
	@$(PY) $(SCRIPT_DIR)/installer.py --report-specifics

dry-run: ## Preview install without writing anything
	@$(PY_INSTALL) --dry-run

help: ## Show this help
	@echo ""
	@echo "jlb-claude-skills — Makefile (legacy installer)"
	@echo "Preferred: /plugin marketplace add jlbionville/jlb-claude-skills"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Variables: MODE=symlink|copy  TARGET=path  P=path  PY="uv run --script"|python3"
	@echo ""
