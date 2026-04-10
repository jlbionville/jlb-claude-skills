# =============================================================================
# Makefile — jlb-claude-skills installer (legacy method)
#
# Preferred: /plugin marketplace add jlbionville/jlb-claude-skills
#
# Legacy usage:
#   make install                 # All plugins, symlink mode
#   make install MODE=copy       # All plugins, copy mode
#   make install-aws             # Only jlb-aws-serverless
#   make install-python          # Only jlb-python-toolkit
#   make install-content         # Only jlb-content-publisher
#   make install-bourse          # Only jlb-bourse
#   make project P=/path/to/repo # Install into a project's .claude/skills/
#   make uninstall               # Remove all installed skills
#   make list                    # Show available plugins and skills
# =============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

MODE       ?= symlink
TARGET     ?= $(HOME)/.claude/skills
SCRIPT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

.PHONY: install install-aws install-python install-content install-bourse
.PHONY: project uninstall list help

install: ## Install all plugins (MODE=symlink|copy)
	@bash $(SCRIPT_DIR)/install.sh --$(MODE) --target $(TARGET)

install-aws: ## Install jlb-aws-serverless only
	@bash $(SCRIPT_DIR)/install.sh --$(MODE) --target $(TARGET) --plugin jlb-aws-serverless

install-python: ## Install jlb-python-toolkit only
	@bash $(SCRIPT_DIR)/install.sh --$(MODE) --target $(TARGET) --plugin jlb-python-toolkit

install-content: ## Install jlb-content-publisher only
	@bash $(SCRIPT_DIR)/install.sh --$(MODE) --target $(TARGET) --plugin jlb-content-publisher

install-bourse: ## Install jlb-bourse only
	@bash $(SCRIPT_DIR)/install.sh --$(MODE) --target $(TARGET) --plugin jlb-bourse

project: ## Install into a project (P=/path/to/repo)
ifndef P
	$(error P is required. Usage: make project P=/path/to/my-repo)
endif
	@bash $(SCRIPT_DIR)/install.sh --$(MODE) --project $(P)

uninstall: ## Remove all installed skills
	@bash $(SCRIPT_DIR)/install.sh --uninstall --target $(TARGET)

list: ## List available plugins and skills
	@bash $(SCRIPT_DIR)/install.sh --list

help: ## Show this help
	@echo ""
	@echo "jlb-claude-skills — Makefile (legacy installer)"
	@echo "Preferred: /plugin marketplace add jlbionville/jlb-claude-skills"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Variables: MODE=symlink|copy  TARGET=path  P=path"
	@echo ""
