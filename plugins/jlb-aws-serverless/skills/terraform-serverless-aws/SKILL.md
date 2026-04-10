---
name: terraform-serverless-aws
description: >
  Guide pour organiser, structurer et standardiser du code Terraform pour des applications
  serverless AWS multi-projets avec modules réutilisables. Utilise cette skill dès que
  l'utilisateur parle de structure Terraform, de modules réutilisables AWS, d'organisation
  de repo infra, de convention de nommage Terraform, de versioning de modules, de tags AWS
  étendus, de validation de variables Terraform, de gestion multi-environnements avec tfvars,
  de state S3 isolé par projet, ou de monorepo d'infrastructure. Déclencher aussi pour :
  "comment organiser mon Terraform", "je veux mutualiser mes modules AWS", "convention de
  tags AWS", "valider les tags Terraform", "créer un module Lambda réutilisable", "structure
  infra-platform", "comment versionner mes modules Terraform", "CreatedAt UpdatedAt sur mes
  ressources AWS", "tags Author Version GitRepo sur AWS". Complémentaire à la skill
  aws-serverless — toujours utiliser les deux ensemble pour des projets serverless complets.
---

# Terraform Serverless AWS — Structure & Modules

Guide pour organiser du Terraform **multi-projets** avec modules réutilisables,
tags étendus, validation et versioning.

Contexte : 6+ projets, monorepo platform, tfvars par environnement.

---

## Étape 0 — Collecte d'informations (si absentes)

| Info | Exemple |
|------|---------|
| **Nom du repo platform** | `infra-platform` |
| **Organisation Git** | `github.com/mon-org` |
| **Besoin** | Nouveau module / nouveau projet / review structure / tags |
| **Module concerné** | `lambda-function` / `dynamodb-table` / `observability` / ... |

---

## Étape 1 — Charger la référence selon le besoin

| Besoin | Référence à lire |
|--------|-----------------|
| Structure du monorepo | `references/repo-structure.md` |
| Convention de tags + validation | `references/tagging-extended.md` |
| Écrire un module réutilisable | `references/module-authoring.md` |
| Appeler un module depuis un projet | `references/module-consumer.md` |
| Versioning des modules | `references/versioning.md` |

**Toujours lire `references/tagging-extended.md`** — les tags sont obligatoires
sur chaque ressource de chaque module.

---

## Étape 2 — Règles fondamentales

### 2.1 Monorepo platform

```
infra-platform/
├── modules/          ← modules réutilisables versionnés par tag Git
└── projects/         ← un dossier par application, appelle les modules
```

Un module = un composant AWS cohérent (pas trop fin, pas trop large).
Un projet = une application métier complète.

### 2.2 Tags — ensemble complet obligatoire

Tout module doit exposer une variable `tags` et appliquer `merge(var.tags, local.module_tags)`.

Tags **obligatoires** (validés) :

| Tag | Type | Validation |
|-----|------|-----------|
| `Project` | string | libre |
| `Application` | string | libre |
| `Environment` | string | `dev\|staging\|prod` |
| `Team` | string | libre |
| `Criticality` | string | `high\|medium\|low` |
| `ManagedBy` | string | fixé à `terraform` |

Tags **obligatoires** (libres) :

| Tag | Exemple |
|-----|---------|
| `Author` | `john.doe@company.com` |
| `CostCenter` | `backend-team` |
| `GitRepo` | `infra-platform` |
| `Module` | `lambda-function` |
| `Version` | `lambda-function/1.2.0` |
| `TerraformWorkspace` | `prod` |

Tags **temporels** (stratégie hybride) :

| Tag | Stratégie | Détail |
|-----|-----------|--------|
| `CreatedAt` | CI/CD injecté à la création uniquement | `lifecycle { ignore_changes = [tags["CreatedAt"]] }` |
| `UpdatedAt` | AWS Config Rule automatique | Hors Terraform, mis à jour à chaque modification |

### 2.3 Versioning des modules

Convention : `{module}/{majeur}.{mineur}.{patch}`

```
lambda-function/1.0.0   ← stable initial
lambda-function/1.1.0   ← nouvelle variable avec default (non-breaking)
lambda-function/2.0.0   ← breaking change
```

Règle SemVer :
- `patch` → bugfix, tag manquant, doc
- `minor` → nouvelle variable **avec** `default` (rétrocompatible)
- `major` → variable renommée/supprimée, output retiré, comportement changé

### 2.4 State Terraform — isolé par projet

Chaque projet a son propre state S3 :
```
s3://mon-org-terraform-states/{projet}/{application}/{environnement}/terraform.tfstate
```

Jamais de state partagé entre projets → une erreur reste isolée.

---

## Étape 3 — Mode Génération

### Nouveau module
1. Lire `references/module-authoring.md`
2. Créer `modules/{nom}/` avec `main.tf`, `variables.tf`, `outputs.tf`, `README.md`
3. Toujours exposer `var.tags` et appliquer `merge(var.tags, local.module_tags)`
4. Inclure le bloc `CreatedAt` avec `ignore_changes`
5. Documenter les inputs/outputs dans `README.md`

### Nouveau projet
1. Lire `references/module-consumer.md`
2. Créer `projects/{projet}-{application}/` avec la structure standard
3. Créer `envs/dev.tfvars`, `envs/staging.tfvars`, `envs/prod.tfvars`
4. State backend S3 isolé dans `backend.tf`

### Ajout / modification de tags
1. Lire `references/tagging-extended.md`
2. Vérifier que la validation `variable` est en place pour les tags critiques
3. Appliquer la stratégie hybride pour `CreatedAt` / `UpdatedAt`

---

## Étape 4 — Mode Review

Signaler en priorité :
1. **Tags manquants** : ressource sans `merge(var.tags, ...)` → non-conforme
2. **Validation absente** sur `Environment` ou `Criticality`
3. **State partagé** entre plusieurs projets → risque de blast radius
4. **Module trop large** : un module qui crée Lambda + DynamoDB + API Gateway ensemble → difficile à réutiliser
5. **Version de module non fixée** : `ref=main` au lieu de `ref=lambda-function/1.2.0`
6. **CreatedAt avec `timestamp()`** → toujours en drift, à remplacer

---

## Étape 5 — Checklist avant livraison

**Structure :**
- [ ] `modules/{nom}/` contient `main.tf`, `variables.tf`, `outputs.tf`, `README.md`
- [ ] `projects/{projet}/` contient `backend.tf`, `envs/*.tfvars`
- [ ] State backend S3 isolé par projet + application + environnement

**Tags dans les modules :**
- [ ] Variable `tags` exposée avec `type = map(string)` et `default = {}`
- [ ] `local.module_tags` contient `Module` et `Version`
- [ ] Chaque `resource` utilise `tags = merge(var.tags, local.module_tags, {...})`
- [ ] Bloc `lifecycle { ignore_changes = [tags["CreatedAt"]] }` présent
- [ ] Validation sur `Environment` et `Criticality` dans le module racine

**Versioning :**
- [ ] Tag Git posé après chaque release (`lambda-function/x.y.z`)
- [ ] Les projets référencent une version fixe (`?ref=lambda-function/1.2.0`)
- [ ] `CHANGELOG.md` mis à jour dans le dossier du module

---

## Références

- `references/repo-structure.md` — Arborescence complète du monorepo, conventions de nommage
- `references/tagging-extended.md` — Tous les tags, validation Terraform, stratégie CreatedAt/UpdatedAt
- `references/module-authoring.md` — Écrire un module : structure, variables, outputs, patterns
- `references/module-consumer.md` — Appeler un module depuis un projet, tfvars, backend S3
- `references/versioning.md` — Convention de tags Git SemVer, CHANGELOG, procédure de release
