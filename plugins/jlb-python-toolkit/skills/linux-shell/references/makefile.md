# Makefile — Task Runner DevOps / Python

## Table des matières
1. [Syntaxe fondamentale](#1-syntaxe-fondamentale)
2. [Variables et fonctions](#2-variables-et-fonctions)
3. [Targets et dépendances](#3-targets-et-dépendances)
4. [Patterns de conditionnels et d'OS](#4-patterns-de-conditionnels-et-dos)
5. [Template Python complet](#5-template-python-complet)
6. [Template DevOps / Infrastructure](#6-template-devops--infrastructure)
7. [Template multi-projets (includes)](#7-template-multi-projets-includes)
8. [Bonnes pratiques](#8-bonnes-pratiques)

---

## 1. Syntaxe fondamentale

```makefile
# ⚠️ CRITIQUE : les recettes doivent être indentées avec des TABS, jamais des espaces

# Structure d'une règle :
target: prerequisite1 prerequisite2
	commande1                    # tab obligatoire
	commande2                    # tab obligatoire

# Règles spéciales
.PHONY: clean test build        # targets qui ne sont pas des fichiers
.DEFAULT_GOAL := help           # target par défaut si 'make' sans argument
.SILENT:                        # supprimer l'affichage des commandes
.ONESHELL:                      # exécuter la recette dans un seul shell (GNU make 3.82+)

# Commentaires
# Ceci est un commentaire (ignoré par make)
```

---

## 2. Variables et fonctions

### Déclaration et types
```makefile
# Assignation récursive (évaluée à chaque usage)
VAR = valeur

# Assignation simple (évaluée une seule fois)
VAR := valeur

# Assignation conditionnelle (si non définie)
VAR ?= défaut

# Append
VAR += supplément

# Passage depuis la ligne de commande
# make VAR=valeur target → surcharge la valeur du Makefile

# Variables automatiques
# $@  : nom de la target
# $<  : première dépendance
# $^  : toutes les dépendances (sans doublons)
# $*  : stem du pattern (pour les règles pattern)
# $?  : dépendances plus récentes que la target
# $(@D): répertoire de $@
# $(@F): nom de fichier de $@
```

### Fonctions built-in utiles
```makefile
# Manipulation de chaînes
$(subst from,to,text)           # remplacer
$(patsubst %.c,%.o,$(SRCS))     # pattern substitution
$(strip string)                 # supprimer espaces
$(filter %.py,$(FILES))         # filtrer par pattern
$(filter-out %.pyc,$(FILES))    # exclure par pattern
$(sort list)                    # trier et dédupliquer
$(word n,text)                  # n-ème mot
$(words text)                   # compter les mots
$(firstword text)               # premier mot
$(lastword text)                # dernier mot

# Fichiers
$(wildcard *.py)                # expansion glob
$(dir path/to/file)             # → path/to/
$(notdir path/to/file)          # → file
$(basename file.txt)            # → file
$(suffix file.txt)              # → .txt
$(abspath rel/path)             # chemin absolu
$(realpath rel/path)            # chemin absolu résolu

# Shell
$(shell command)                # exécuter une commande shell
$(shell git rev-parse --short HEAD)   # exemple : hash git

# Conditions
$(if condition,then,else)
$(or val1,val2,val3)            # premier non vide
$(and val1,val2,val3)           # tous non vides → dernier
```

---

## 3. Targets et dépendances

### Patterns de targets
```makefile
# Règle pattern (pour compiler des fichiers)
%.o: %.c
	$(CC) -c -o $@ $<

# Double-colon rules (plusieurs recettes pour la même target)
clean::
	rm -f *.o
clean::
	rm -f *.pyc

# Targets multiples dans une règle
foo.txt bar.txt: source.txt
	split -d source.txt output_

# Ordre de dépendance uniquement (pas de rebuild si changé)
target: | directory_must_exist

# Règle pour créer des répertoires
$(BUILD_DIR):
	mkdir -p $@

artifacts: | $(BUILD_DIR)
```

### Dépendances dynamiques
```makefile
# Lire les dépendances depuis un fichier généré
-include $(patsubst %.py,$(DEP_DIR)/%.d,$(PY_SOURCES))

# Générer les dépendances
$(DEP_DIR)/%.d: %.py | $(DEP_DIR)
	$(PYTHON) -m modulegraph $< | sed 's|.*|$@: &|' > $@
```

---

## 4. Patterns de conditionnels et d'OS

```makefile
# Détecter l'OS
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
  OS_OPEN := xdg-open
endif
ifeq ($(UNAME_S),Darwin)
  OS_OPEN := open
endif

# Détecter si une commande est disponible
HAS_DOCKER := $(shell command -v docker 2>/dev/null)
HAS_COLIMA := $(shell command -v colima 2>/dev/null)

# Conditionnel sur variable
ifdef DEBUG
  VERBOSITY := --verbose
else
  VERBOSITY :=
endif

# Conditionnel inline dans une recette
check:
ifeq ($(ENV),prod)
	@echo "⚠️  Production — double confirmation requise"
	@read -p "Êtes-vous sûr ? [yes/no] " confirm && [ "$$confirm" = "yes" ]
endif
	./check.sh

# Variables d'environnement avec défaut
ENV ?= dev
REGION ?= eu-west-1
PROFILE ?= default

# Valider une variable obligatoire
check-env-%:
	@test -n "${$*}" || (echo "❌ Variable $* non définie" >&2; exit 1)

deploy: check-env-ENV check-env-REGION
	./deploy.sh --env $(ENV) --region $(REGION)
```

---

## 5. Template Python complet

```makefile
# =============================================================================
# Makefile — Task runner Python
# =============================================================================
.PHONY: help install install-dev lint format typecheck test test-cov \
        clean clean-all build publish docs run

.DEFAULT_GOAL := help

# ── Configuration ─────────────────────────────────────────────────────────────
PYTHON     := python3
UV         := uv
APP_NAME   := mon_app
SRC_DIR    := src
TEST_DIR   := tests
VENV_DIR   := .venv
COV_REPORT := htmlcov

# Détecter si on est dans le venv
PYTHON_BIN := $(VENV_DIR)/bin/python
PIP        := $(VENV_DIR)/bin/pip
PYTEST     := $(VENV_DIR)/bin/pytest
RUFF       := $(VENV_DIR)/bin/ruff
MYPY       := $(VENV_DIR)/bin/mypy

# Version depuis pyproject.toml
VERSION    := $(shell grep -m1 'version' pyproject.toml | sed 's/.*= "\(.*\)"/\1/')
GIT_HASH   := $(shell git rev-parse --short HEAD 2>/dev/null || echo "nogit")

# ── Couleurs ──────────────────────────────────────────────────────────────────
BOLD  := \033[1m
GREEN := \033[32m
CYAN  := \033[36m
RESET := \033[0m

# ── Aide ─────────────────────────────────────────────────────────────────────
help:   ## Afficher cette aide
	@echo "$(BOLD)$(APP_NAME) v$(VERSION)$(RESET) — Targets disponibles :"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ── Environnement ─────────────────────────────────────────────────────────────
$(VENV_DIR): pyproject.toml
	$(UV) venv $(VENV_DIR)
	touch $@

install: $(VENV_DIR)   ## Installer les dépendances de prod
	$(UV) pip install -e .

install-dev: $(VENV_DIR)   ## Installer les dépendances de dev
	$(UV) pip install -e ".[dev,test]"
	@echo "$(GREEN)✓ Environnement dev prêt$(RESET)"

# ── Qualité de code ───────────────────────────────────────────────────────────
lint:   ## Linter (ruff)
	$(RUFF) check $(SRC_DIR) $(TEST_DIR)

format:   ## Formater le code (ruff format)
	$(RUFF) format $(SRC_DIR) $(TEST_DIR)
	$(RUFF) check --fix $(SRC_DIR) $(TEST_DIR)

typecheck:   ## Vérification de types (mypy)
	$(MYPY) $(SRC_DIR)/$(APP_NAME)

check: lint typecheck   ## Lint + typecheck

# ── Tests ─────────────────────────────────────────────────────────────────────
test:   ## Lancer les tests
	$(PYTEST) $(TEST_DIR) -v --tb=short

test-cov:   ## Tests avec couverture de code
	$(PYTEST) $(TEST_DIR) \
	  --cov=$(SRC_DIR)/$(APP_NAME) \
	  --cov-report=term-missing \
	  --cov-report=html:$(COV_REPORT) \
	  --cov-fail-under=80
	@echo "$(GREEN)✓ Rapport HTML : $(COV_REPORT)/index.html$(RESET)"

test-fast:   ## Tests rapides (sans slow markers)
	$(PYTEST) $(TEST_DIR) -m "not slow" -v

test-watch:   ## Tests en mode watch (nécessite pytest-watch)
	$(VENV_DIR)/bin/ptw $(TEST_DIR) -- -v

# ── Build et publication ──────────────────────────────────────────────────────
build: clean   ## Builder le package
	$(UV) pip build
	@echo "$(GREEN)✓ Package v$(VERSION) buildé$(RESET)"

publish: build   ## Publier sur PyPI (confirmer la version !)
	@echo "Publication de $(APP_NAME) v$(VERSION) sur PyPI"
	@read -p "Confirmer [y/N] " ok && [ "$$ok" = "y" ]
	$(UV) pip publish

# ── Run ───────────────────────────────────────────────────────────────────────
run:   ## Lancer l'application
	$(PYTHON_BIN) -m $(APP_NAME)

run-dev:   ## Lancer en mode dev (reload)
	$(VENV_DIR)/bin/uvicorn $(APP_NAME).main:app --reload --port 8000

# ── Nettoyage ─────────────────────────────────────────────────────────────────
clean:   ## Supprimer les artefacts de build
	rm -rf dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

clean-all: clean   ## Supprimer aussi le venv et la couverture
	rm -rf $(VENV_DIR) $(COV_REPORT) .mypy_cache .ruff_cache .pytest_cache
	@echo "$(GREEN)✓ Tout nettoyé$(RESET)"

# ── Utilitaires ───────────────────────────────────────────────────────────────
info:   ## Afficher les infos de l'environnement
	@echo "App     : $(APP_NAME) v$(VERSION)"
	@echo "Git     : $(GIT_HASH)"
	@echo "Python  : $(shell $(PYTHON_BIN) --version 2>&1)"
	@echo "Venv    : $(VENV_DIR)"
```

---

## 6. Template DevOps / Infrastructure

```makefile
# =============================================================================
# Makefile — Task runner DevOps / Infra
# =============================================================================
.PHONY: help deploy rollback status logs health \
        tf-init tf-plan tf-apply tf-destroy \
        docker-build docker-push docker-run \
        k8s-apply k8s-rollout k8s-logs

.DEFAULT_GOAL := help

# ── Configuration ─────────────────────────────────────────────────────────────
APP        := mon-service
ENV        ?= dev
REGION     ?= eu-west-1
AWS_PROFILE ?= $(ENV)

IMAGE_NAME := $(APP)
IMAGE_TAG  := $(shell git rev-parse --short HEAD)
ECR_REPO   := 123456789.dkr.ecr.$(REGION).amazonaws.com/$(IMAGE_NAME)

TF_DIR     := infra/terraform/$(ENV)
TF_VARS    := -var-file=envs/$(ENV).tfvars

K8S_NS     := $(APP)-$(ENV)
K8S_CTX    := $(ENV)-cluster

# ── Couleurs ──────────────────────────────────────────────────────────────────
RED   := \033[31m
GREEN := \033[32m
CYAN  := \033[36m
BOLD  := \033[1m
RESET := \033[0m

# ── Aide ─────────────────────────────────────────────────────────────────────
help:
	@echo "$(BOLD)$(APP)$(RESET) — ENV=$(ENV) REGION=$(REGION)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; \
	         /##-/ {printf "\n$(BOLD)%s$(RESET)\n", substr($$2,2); next} \
	         {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'

# ── Validation ────────────────────────────────────────────────────────────────
guard-%:   ## Vérifier qu'une variable est définie
	@test -n "${$*}" || \
	  (echo "$(RED)❌ Variable $* non définie. Usage: make $@ $*=valeur$(RESET)"; exit 1)

confirm:
	@echo "$(RED)⚠️  ENV=$(ENV) — Confirmer l'action ?$(RESET)"
	@read -p "[yes/no] " ok && [ "$$ok" = "yes" ] || \
	  (echo "Annulé"; exit 1)

# ── Application ───────────────────────────────────────────────────────────────
## -- Application
deploy: docker-build docker-push k8s-apply   ## Builder, pusher, déployer
	@echo "$(GREEN)✓ Déployé $(IMAGE_TAG) sur $(ENV)$(RESET)"

rollback: guard-VERSION   ## Revenir à une version précédente (VERSION=xxxx)
	kubectl --context=$(K8S_CTX) -n $(K8S_NS) \
	  set image deployment/$(APP) $(APP)=$(ECR_REPO):$(VERSION)

status:   ## État du déploiement
	kubectl --context=$(K8S_CTX) -n $(K8S_NS) \
	  rollout status deployment/$(APP)

logs:   ## Suivre les logs
	kubectl --context=$(K8S_CTX) -n $(K8S_NS) \
	  logs -f deployment/$(APP) --tail=100

health:   ## Vérifier la santé du service
	@curl -sf https://$(ENV).api.example.com/health | jq .

# ── Docker ────────────────────────────────────────────────────────────────────
## -- Docker
docker-build:   ## Builder l'image Docker
	docker build \
	  --build-arg VERSION=$(IMAGE_TAG) \
	  --build-arg ENV=$(ENV) \
	  -t $(IMAGE_NAME):$(IMAGE_TAG) \
	  -t $(IMAGE_NAME):latest \
	  .
	@echo "$(GREEN)✓ Image buildée : $(IMAGE_NAME):$(IMAGE_TAG)$(RESET)"

docker-push:   ## Pousser l'image sur ECR
	aws ecr get-login-password --region $(REGION) --profile $(AWS_PROFILE) \
	  | docker login --username AWS --password-stdin $(ECR_REPO)
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(ECR_REPO):$(IMAGE_TAG)
	docker push $(ECR_REPO):$(IMAGE_TAG)

docker-run:   ## Lancer le conteneur localement
	docker run --rm -it \
	  -p 8080:8080 \
	  -e ENV=$(ENV) \
	  --env-file .env.$(ENV) \
	  $(IMAGE_NAME):latest

# ── Terraform ─────────────────────────────────────────────────────────────────
## -- Terraform
tf-init:   ## Initialiser Terraform
	cd $(TF_DIR) && terraform init -upgrade

tf-plan:   ## Plan Terraform
	cd $(TF_DIR) && terraform plan $(TF_VARS) -out=tfplan

tf-apply: tf-plan   ## Appliquer le plan Terraform
ifeq ($(ENV),prod)
	$(MAKE) confirm
endif
	cd $(TF_DIR) && terraform apply tfplan
	@echo "$(GREEN)✓ Infrastructure $(ENV) mise à jour$(RESET)"

tf-destroy:   ## ⚠️  Détruire l'infrastructure
	$(MAKE) confirm
	cd $(TF_DIR) && terraform destroy $(TF_VARS)

tf-output:   ## Afficher les outputs Terraform
	cd $(TF_DIR) && terraform output -json | jq .

# ── Kubernetes ────────────────────────────────────────────────────────────────
## -- Kubernetes
k8s-apply:   ## Appliquer les manifests K8s
	kubectl --context=$(K8S_CTX) apply -f k8s/$(ENV)/ -n $(K8S_NS)

k8s-rollout:   ## Attendre la fin du rollout
	kubectl --context=$(K8S_CTX) -n $(K8S_NS) \
	  rollout status deployment/$(APP) --timeout=5m

k8s-logs:   ## Logs en temps réel
	kubectl --context=$(K8S_CTX) -n $(K8S_NS) \
	  logs -f -l app=$(APP) --tail=50

k8s-exec:   ## Shell dans un pod
	kubectl --context=$(K8S_CTX) -n $(K8S_NS) \
	  exec -it deploy/$(APP) -- /bin/sh
```

---

## 7. Template multi-projets (includes)

```makefile
# common.mk — règles partagées entre projets
# Inclure avec : include ../../common.mk

# ── Macros réutilisables ──────────────────────────────────────────────────────
define log_success
  @echo "\033[32m✓ $(1)\033[0m"
endef

define log_error
  @echo "\033[31m✗ $(1)\033[0m" >&2
endef

define require_var
  $(if $($(1)),,$(error Variable $(1) non définie))
endef

# ── Targets communes ──────────────────────────────────────────────────────────
.PHONY: version git-status

version:
	@echo "$(APP) v$(shell git describe --tags --always)"

git-status:
	@git status --short
	@git log --oneline -5
```

```makefile
# Makefile du projet — utilisation de common.mk
APP    := mon-service
ENV    ?= dev

include ../../common.mk      # règles partagées
include envs/$(ENV).mk       # variables par environnement (auto-chargé)

# Règles spécifiques au projet
.PHONY: build

build:
	$(call log_success,Build démarré)
	$(call require_var,VERSION)
	./build.sh --version $(VERSION)
	$(call log_success,Build terminé — $(APP) v$(VERSION))
```

---

## 8. Bonnes pratiques

```makefile
# ── Toujours déclarer .PHONY ─────────────────────────────────────────────────
.PHONY: all clean test build deploy help

# ── Aide auto-générée ─────────────────────────────────────────────────────────
# Convention : ## après la target = documentation
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# ── Silencer sélectivement ────────────────────────────────────────────────────
quiet-target:
	@echo "Ce echo s'affiche"
	@some-command     # @ supprime l'affichage de la commande
	@@nested-silence  # double @ pour les $(MAKE) récursifs

# ── Eviter les problèmes de shell ────────────────────────────────────────────
# Chaque ligne de recette = nouveau shell → utiliser ; ou \ pour enchaîner
multi-step:
	cd /tmp && \
	ls -la && \
	echo "OK"

# Avec .ONESHELL (GNU make 3.82+)
.ONESHELL:
multi-step-clean:
	cd /tmp
	ls -la
	echo "OK"

# ── Variables d'environnement dans les recettes ───────────────────────────────
# $ doit être échappé en $$ dans les recettes
show-env:
	@echo "Shell PID : $$$$"
	@for f in *.txt; do echo "$$f"; done

# ── Targets qui produisent des fichiers ───────────────────────────────────────
# Nommer la target = le fichier produit → make ne re-buildra pas si à jour
dist/app.tar.gz: src/ requirements.txt
	mkdir -p dist/
	tar czf $@ src/

# ── Debugging ────────────────────────────────────────────────────────────────
debug:
	@echo "APP     = $(APP)"
	@echo "ENV     = $(ENV)"
	@echo "MAKEFLAGS = $(MAKEFLAGS)"
	$(info Variables chargées depuis $(MAKEFILE_LIST))

# make --dry-run (-n)  → afficher sans exécuter
# make --trace         → tracer les décisions
# make -p              → afficher toutes les règles et variables
```

### Anti-patterns à éviter
```makefile
# ❌ Espaces au lieu de tabs dans les recettes
target:
    echo "ERREUR : espaces"   # ← ne marchera pas

# ✅ Tab obligatoire
target:
	echo "OK : tab"

# ❌ Variable non définie utilisée dans un rm
clean:
	rm -rf $(BUILD)/   # si BUILD est vide → rm -rf /  !!!

# ✅ Vérifier avant
clean:
	@test -n "$(BUILD)" || (echo "BUILD non défini"; exit 1)
	rm -rf $(BUILD)/

# ❌ .PHONY oublié → make croit que "clean" est un fichier
clean:
	rm -rf dist/

# ✅
.PHONY: clean
clean:
	rm -rf dist/
```
