# Référence : Tagging \& Gestion des Coûts AWS

> **Note :** Cette référence couvre les tags de base.
> Pour la convention complète (Author, Version, CreatedAt/UpdatedAt, Criticality,
> Team, GitRepo, Module, validation Terraform), voir la skill
> **`terraform-serverless-aws`** → `references/tagging-extended.md`.


## Stratégie de tags obligatoires

Chaque ressource Terraform **doit** porter ces 5 tags :

| Tag | Description | Exemple |
|-----|-------------|---------|
| `Project` | Nom du projet global | `ecommerce` |
| `Application` | Composant applicatif | `orders-api` |
| `Environment` | Environnement de déploiement | `prod` / `staging` / `dev` |
| `ManagedBy` | Toujours `terraform` | `terraform` |
| `CostCenter` | Équipe ou centre de coût | `backend-team` |

Tags optionnels recommandés :

| Tag | Description | Exemple |
|-----|-------------|---------|
| `Owner` | Responsable technique | `john.doe@company.com` |
| `Component` | Sous-composant spécifique | `orders-api-lambda` |
| `Version` | Version du module/service | `1.4.2` |

---

## locals.tf — Template de référence

```hcl
# locals.tf
locals {
  common_tags = {
    Project     = var.project
    Application = var.application
    Environment = var.environment
    ManagedBy   = "terraform"
    CostCenter  = var.cost_center
  }
}
```

## variables.tf — Variables de tagging

```hcl
variable "project" {
  type        = string
  description = "Nom du projet global (ex: ecommerce)"
}

variable "application" {
  type        = string
  description = "Nom de l'application (ex: orders-api)"
}

variable "environment" {
  type        = string
  description = "Environnement : dev / staging / prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "L'environnement doit être dev, staging ou prod."
  }
}

variable "cost_center" {
  type        = string
  description = "Centre de coût pour le suivi budgétaire"
  default     = "default"
}
```

## Appliquer les tags sur chaque ressource

```hcl
# ✅ Correct — toujours avec merge() pour permettre des tags additionnels
resource "aws_lambda_function" "api" {
  # ...
  tags = merge(local.common_tags, {
    Component = "${var.application}-lambda"
  })
}

resource "aws_dynamodb_table" "main" {
  # ...
  tags = merge(local.common_tags, {
    Component = "${var.application}-dynamodb"
  })
}

# ❌ Incorrect — tags fixes, pas extensibles
resource "aws_sqs_queue" "main" {
  tags = {
    Name = "my-queue"   # manque Project, Application, Environment...
  }
}
```

---

## AWS Cost Explorer — Activer le suivi par tag

### Étape 1 : Activer les tags comme clés de cost allocation

Dans AWS Console → Billing → Cost allocation tags → Activer :
- `Project`
- `Application`
- `Environment`
- `CostCenter`

> ⚠️ Il faut 24h après activation pour que les données apparaissent dans Cost Explorer.
> Les tags doivent exister sur les ressources **avant** la période de facturation mesurée.

### Étape 2 : Créer une vue Cost Explorer par projet/application

Dans AWS Cost Explorer :
1. Group by : Tag → `Project`
2. Filtrer par : Tag → `Environment` = `prod`
3. Sauvegarder comme "vue" nommée `{projet}-prod-costs`

### Automatiser avec un budget par projet (Terraform)

```hcl
resource "aws_budgets_budget" "project" {
  name         = "${var.project}-${var.environment}-monthly-budget"
  budget_type  = "COST"
  limit_amount = var.monthly_budget_usd
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "TagKeyValue"
    values = ["user:Project$${var.project}"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80   # alerte à 80% du budget
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.billing_alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.billing_alert_email]
  }
}
```

```hcl
variable "monthly_budget_usd" {
  type    = string
  default = "100"
}

variable "billing_alert_email" {
  type = string
}
```

---

## Checklist tagging avant `terraform apply`

- [ ] `locals.tf` contient `common_tags` avec les 5 tags obligatoires
- [ ] **Chaque** bloc `resource` utilise `tags = merge(local.common_tags, {...})`
- [ ] Le tag `Component` est spécifique à chaque ressource (pas le même pour Lambda et DynamoDB)
- [ ] Les tags sont en `PascalCase` (convention AWS)
- [ ] Un budget AWS est créé par projet/environnement en prod
- [ ] Les tags de cost allocation sont activés dans Billing

---

## Exemple : terraform.tfvars par environnement

```hcl
# terraform.tfvars (dev)
project             = "ecommerce"
application         = "orders-api"
environment         = "dev"
region              = "eu-west-1"
cost_center         = "backend-team"
monthly_budget_usd  = "20"
billing_alert_email = "team@company.com"
```

```hcl
# terraform.tfvars (prod)
project             = "ecommerce"
application         = "orders-api"
environment         = "prod"
region              = "eu-west-1"
cost_center         = "backend-team"
monthly_budget_usd  = "500"
billing_alert_email = "team@company.com"
```
