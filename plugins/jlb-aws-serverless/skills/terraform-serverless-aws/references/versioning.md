# Référence : Versioning des modules — Git Tags SemVer

## Convention de tags Git

```
{module}/{majeur}.{mineur}.{patch}
```

**Exemples :**
```
lambda-function/1.0.0
lambda-function/1.1.0
lambda-function/2.0.0
dynamodb-table/1.0.0
observability/1.2.3
api-gateway-http/1.0.0
```

---

## Règles SemVer adaptées à Terraform

| Incrément | Quand l'utiliser | Exemple de changement |
|-----------|-----------------|----------------------|
| `patch` | Correction de bug, tag manquant, documentation | Ajout d'un tag `Component` oublié |
| `minor` | Nouvelle variable **avec** `default` (rétrocompatible) | `var.memory_size` ajouté avec `default = 256` |
| `major` | Variable renommée/supprimée, output retiré, type changé, comportement modifié | `var.function_name` → `var.name` |

> **Règle clé :** si un projet existant peut casser après mise à jour → c'est un `major`.

---

## Procédure de release

### 1. Développer et tester localement

```bash
# Dans un projet de test, pointer sur la branche en cours
module "api_lambda" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/lambda-function?ref=feat/add-memory-var"
  # ...
}
```

### 2. Mettre à jour le CHANGELOG

```markdown
## [1.1.0] — 2024-03-10
### Added
- Variable `memory_size` avec default 256
### Fixed
- Tag `Component` manquant sur le log group
```

### 3. Merger sur `main`

PR review obligatoire pour tout changement de module.

### 4. Poser le tag Git

```bash
git tag lambda-function/1.1.0
git push origin lambda-function/1.1.0
```

### 5. Mettre à jour les projets (si besoin)

Pour un `minor` ou `patch` : mise à jour optionnelle, les projets existants continuent de fonctionner.
Pour un `major` : ouvrir un ticket de migration pour chaque projet affecté.

---

## Référencer un module depuis un projet

```hcl
# ✅ Correct — version fixe et traçable
module "api_lambda" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/lambda-function?ref=lambda-function/1.2.0"
}

# ❌ Incorrect — ref flottante, risque de régression silencieuse
module "api_lambda" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/lambda-function?ref=main"
}
```

---

## Tag `Version` sur les ressources AWS

Le tag `Version` sur chaque ressource AWS reflète la version du module Terraform qui l'a créée.
Cela permet de savoir, depuis la console AWS ou Cost Explorer, quelle version du module
est en production pour chaque composant.

```hcl
# Dans le module — injecté via la variable module_version
locals {
  module_tags = {
    Module  = "lambda-function"
    Version = var.module_version   # ex: "lambda-function/1.2.0"
  }
}
```

```hcl
# Dans le projet — toujours aligner avec le ?ref=
module "api_lambda" {
  source         = "...?ref=lambda-function/1.2.0"
  module_version = "lambda-function/1.2.0"   # ← même valeur que le ref
}
```

---

## Matrice des modules et versions actives

Tenir à jour un fichier `MODULES.md` à la racine du repo :

```markdown
# Versions des modules en production

| Module | Dernière version stable | Utilisé par |
|--------|------------------------|-------------|
| lambda-function | 1.2.0 | orders-api, catalog-api, auth-api |
| dynamodb-table | 1.0.0 | orders-api, catalog-api |
| api-gateway-http | 1.1.0 | orders-api, catalog-api |
| observability | 1.1.0 | orders-api |
| sqs-with-dlq | 1.0.0 | orders-api |
| cognito-userpool | 1.0.0 | auth-api |
```
