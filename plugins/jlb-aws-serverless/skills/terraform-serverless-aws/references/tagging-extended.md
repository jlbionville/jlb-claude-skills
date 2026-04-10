# Référence : Tags étendus — Convention complète

## Tableau complet des tags

### Tags obligatoires avec validation Terraform

```hcl
# variables.tf — dans chaque module ET dans chaque projet

variable "environment" {
  type        = string
  description = "Environnement de déploiement"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment doit être : dev, staging ou prod."
  }
}

variable "criticality" {
  type        = string
  description = "Niveau de criticité métier de la ressource"
  validation {
    condition     = contains(["high", "medium", "low"], var.criticality)
    error_message = "criticality doit être : high, medium ou low."
  }
}
```

### Tags obligatoires libres (pas de validation stricte)

```hcl
variable "project"     { type = string; description = "Nom du projet global ex: ecommerce" }
variable "application" { type = string; description = "Nom de l'application ex: orders-api" }
variable "team"        { type = string; description = "Équipe responsable ex: backend" }
variable "author"      { type = string; description = "Créateur de la ressource ex: john.doe@company.com" }
variable "cost_center" { type = string; description = "Centre de coût ex: backend-team" }
variable "git_repo"    { type = string; description = "Repo Git source ex: infra-platform" }
```

### Tags injectés par la CI/CD (pas de variable Terraform)

```hcl
variable "deployed_at" {
  type        = string
  description = "Date/heure du déploiement, injectée par la CI — format ISO 8601"
  default     = ""
}
```

En CI/CD (GitHub Actions, GitLab CI) :
```bash
terraform apply \
  -var="deployed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -var-file="envs/prod.tfvars"
```

---

## locals.tf — Bloc de référence complet

```hcl
# locals.tf — dans chaque projet
locals {
  # ── Tags communs passés à tous les modules ──────────────────────────────────
  common_tags = {
    # Identification
    Project         = var.project
    Application     = var.application
    Environment     = var.environment
    Team            = var.team

    # Responsabilité
    Author          = var.author
    CostCenter      = var.cost_center

    # Traçabilité infra
    ManagedBy       = "terraform"
    GitRepo         = var.git_repo
    TerraformWorkspace = terraform.workspace

    # Criticité
    Criticality     = var.criticality

    # Temporel — CreatedAt injecté CI, UpdatedAt géré par AWS Config
    CreatedAt       = var.deployed_at   # figé à la création via ignore_changes
    UpdatedAt       = ""                # laissé vide : géré par AWS Config Rule
  }

  # Rétention logs selon environnement
  log_retention_days = {
    dev     = 7
    staging = 14
    prod    = 90
  }[var.environment]

  # Namespace métriques CloudWatch
  metrics_namespace = "${var.project}/${var.application}"
}
```

---

## Pattern dans un module réutilisable

```hcl
# modules/lambda-function/variables.tf

variable "tags" {
  type        = map(string)
  description = "Tags communs passés depuis le projet (local.common_tags)"
  default     = {}
}

variable "module_version" {
  type        = string
  description = "Version du module ex: lambda-function/1.2.0"
  default     = "lambda-function/unknown"
}
```

```hcl
# modules/lambda-function/main.tf

locals {
  # Tags propres au module — fusionnés PAR DESSUS les tags du projet
  module_tags = {
    Module    = "lambda-function"
    Version   = var.module_version
    Component = "${var.name}-lambda"   # spécifique à l'instance
  }
}

resource "aws_lambda_function" "this" {
  function_name = var.name
  # ...

  tags = merge(var.tags, local.module_tags)

  lifecycle {
    # CreatedAt est injecté une seule fois à la création
    # On évite que terraform plan le modifie à chaque apply
    ignore_changes = [tags["CreatedAt"]]
  }
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = lookup(var.tags, "Environment", "dev") == "prod" ? 90 : 14

  tags = merge(var.tags, local.module_tags, {
    Component = "${var.name}-logs"
  })

  lifecycle {
    ignore_changes = [tags["CreatedAt"]]
  }
}
```

---

## Stratégie hybride CreatedAt / UpdatedAt

### CreatedAt — Variable CI/CD + ignore_changes

```hcl
# 1. Injecté par la CI uniquement au premier apply
variable "deployed_at" { type = string; default = "" }

# 2. Appliqué dans les tags
tags = merge(var.tags, { CreatedAt = var.deployed_at })

# 3. Figé après la création — Terraform ne le modifie plus jamais
lifecycle {
  ignore_changes = [tags["CreatedAt"]]
}
```

**Résultat :** `CreatedAt` = date du premier `terraform apply` sur la ressource.
Les `apply` suivants ne le modifient pas → pas de bruit dans les plans.

### UpdatedAt — AWS Config Rule (hors Terraform)

Déployer cette Config Rule une fois par compte AWS :

```hcl
# infrastructure/config-rules.tf (déployé une seule fois au niveau du compte)

resource "aws_config_config_rule" "auto_tag_updated_at" {
  name = "auto-tag-updated-at"

  source {
    owner             = "AWS"
    source_identifier = "REQUIRED_TAGS"
  }

  # Alternative : Lambda Config Rule custom qui écrit UpdatedAt
  # à chaque changement de ressource détecté par CloudTrail
}
```

Pour une implémentation plus précise, utiliser une **Lambda EventBridge** :

```hcl
# Déclencher sur chaque événement CloudTrail de création/modification de ressource
resource "aws_cloudwatch_event_rule" "resource_changes" {
  name        = "tag-updated-at-on-change"
  description = "Met à jour le tag UpdatedAt sur chaque modification de ressource AWS"

  event_pattern = jsonencode({
    source      = ["aws.lambda", "aws.dynamodb", "aws.sqs", "aws.apigateway"]
    detail-type = ["AWS API Call via CloudTrail"]
    detail = {
      eventName = ["UpdateFunctionConfiguration", "UpdateTable", "TagResource"]
    }
  })

  tags = {
    ManagedBy = "terraform"
    Component = "auto-tagging"
  }
}
```

> **En pratique** : `UpdatedAt` via AWS Config/EventBridge est complexe à maintenir.
> Une alternative pragmatique : utiliser `deployed_at` pour les deux tags,
> avec `ignore_changes` sur `CreatedAt` seulement.
> `UpdatedAt` sera alors la date du dernier `terraform apply` — suffisant pour la plupart des cas.

---

## terraform.tfvars — Template complet par environnement

```hcl
# envs/prod.tfvars
project      = "ecommerce"
application  = "orders-api"
environment  = "prod"
team         = "backend"
author       = "john.doe@company.com"
cost_center  = "backend-team"
git_repo     = "infra-platform"
criticality  = "high"

# Observabilité
ops_alert_email    = "oncall@company.com"
monthly_budget_usd = "500"
```

```hcl
# envs/dev.tfvars
project      = "ecommerce"
application  = "orders-api"
environment  = "dev"
team         = "backend"
author       = "john.doe@company.com"
cost_center  = "backend-team"
git_repo     = "infra-platform"
criticality  = "low"

ops_alert_email    = "dev-team@company.com"
monthly_budget_usd = "20"
```

---

## Résultat final sur une ressource AWS

Une Lambda déployée en prod aura ces tags :

```json
{
  "Project":             "ecommerce",
  "Application":         "orders-api",
  "Environment":         "prod",
  "Team":                "backend",
  "Author":              "john.doe@company.com",
  "CostCenter":          "backend-team",
  "ManagedBy":           "terraform",
  "GitRepo":             "infra-platform",
  "TerraformWorkspace":  "prod",
  "Criticality":         "high",
  "CreatedAt":           "2024-01-15T09:32:00Z",
  "UpdatedAt":           "2024-03-10T14:21:00Z",
  "Module":              "lambda-function",
  "Version":             "lambda-function/1.2.0",
  "Component":           "orders-api-handler-lambda"
}
```

---

## Checklist tags avant `terraform apply`

- [ ] `local.common_tags` contient les 13 tags définis ci-dessus
- [ ] `var.environment` et `var.criticality` ont un bloc `validation`
- [ ] `deployed_at` est injecté par la CI (`-var="deployed_at=..."`)
- [ ] Chaque module reçoit `tags = local.common_tags`
- [ ] Chaque `resource` dans les modules utilise `merge(var.tags, local.module_tags, {...})`
- [ ] `lifecycle { ignore_changes = [tags["CreatedAt"]] }` présent sur chaque resource
- [ ] Tags activés comme Cost Allocation Keys dans AWS Billing
