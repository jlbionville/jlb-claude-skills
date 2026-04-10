# Référence : Structure du monorepo infra-platform

## Arborescence complète

```
infra-platform/
│
├── modules/                              ← modules réutilisables
│   ├── lambda-function/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── CHANGELOG.md
│   │   └── README.md
│   ├── dynamodb-table/
│   ├── api-gateway-http/
│   ├── sqs-with-dlq/
│   ├── cognito-userpool/
│   ├── secrets/
│   └── observability/                   ← log groups + alarmes + dashboard
│
├── projects/                            ← une application = un dossier
│   ├── ecommerce-orders-api/
│   │   ├── main.tf                      ← appelle les modules
│   │   ├── variables.tf                 ← déclare toutes les variables
│   │   ├── outputs.tf                   ← expose ARNs, URLs
│   │   ├── backend.tf                   ← state S3 isolé
│   │   ├── locals.tf                    ← common_tags + calculs
│   │   └── envs/
│   │       ├── dev.tfvars
│   │       ├── staging.tfvars
│   │       └── prod.tfvars
│   │
│   └── ecommerce-catalog-api/
│       └── ...
│
├── bootstrap/                           ← à déployer une seule fois par compte AWS
│   ├── main.tf                          ← bucket S3 states, DynamoDB lock, Config Rules
│   └── README.md
│
├── .github/workflows/                   ← CI/CD Terraform
│   ├── terraform-plan.yml
│   └── terraform-apply.yml
│
└── README.md
```

---

## Convention de nommage des dossiers

| Niveau | Convention | Exemple |
|--------|-----------|---------|
| Module | `{composant-aws}` en kebab-case | `lambda-function`, `sqs-with-dlq` |
| Projet | `{projet}-{application}` | `ecommerce-orders-api` |
| Environnement | `{env}.tfvars` | `prod.tfvars` |

---

## Fichiers d'un projet — contenu minimal

### backend.tf

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "mon-org-terraform-states"
    key            = "ecommerce/orders-api/prod/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "mon-org-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      ManagedBy = "terraform"
      GitRepo   = var.git_repo
    }
  }
}
```

> **`default_tags`** dans le provider : les tags ici sont appliqués automatiquement
> sur toutes les ressources du projet, sans avoir à les passer explicitement à chaque module.
> Utiliser pour `ManagedBy` et `GitRepo` qui ne varient jamais.

### main.tf (exemple)

```hcl
# main.tf — ecommerce-orders-api

module "api_lambda" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/lambda-function?ref=lambda-function/1.2.0"

  name           = "${var.project}-${var.application}-handler-${var.environment}"
  module_version = "lambda-function/1.2.0"
  tags           = local.common_tags

  handler     = "handler.lambda_handler"
  runtime     = "python3.12"
  timeout     = 30
  memory_size = 256

  environment_variables = {
    TABLE_NAME        = module.orders_table.table_name
    EVENT_BUS_NAME    = module.event_bus.name
    METRICS_NAMESPACE = local.metrics_namespace
  }
}

module "orders_table" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/dynamodb-table?ref=dynamodb-table/1.0.0"

  name           = "${var.project}-${var.application}-orders-${var.environment}"
  module_version = "dynamodb-table/1.0.0"
  tags           = local.common_tags
}

module "observability" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/observability?ref=observability/1.1.0"

  project        = var.project
  application    = var.application
  environment    = var.environment
  module_version = "observability/1.1.0"
  tags           = local.common_tags

  lambda_function_name = module.api_lambda.function_name
  ops_alert_email      = var.ops_alert_email
}
```

---

## Bootstrap — à déployer une seule fois par compte

```hcl
# bootstrap/main.tf

resource "aws_s3_bucket" "terraform_states" {
  bucket = "mon-org-terraform-states"

  tags = {
    ManagedBy = "terraform"
    Component = "bootstrap-states"
  }
}

resource "aws_s3_bucket_versioning" "states" {
  bucket = aws_s3_bucket.terraform_states.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "states" {
  bucket = aws_s3_bucket.terraform_states.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "mon-org-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    ManagedBy = "terraform"
    Component = "bootstrap-locks"
  }
}
```

---

## CI/CD — GitHub Actions (structure)

```yaml
# .github/workflows/terraform-plan.yml
name: Terraform Plan
on:
  pull_request:
    paths: ['projects/**', 'modules/**']

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.7.0"

      - name: Terraform Init
        run: terraform init -backend-config="key=${{ env.PROJECT }}/${{ env.APPLICATION }}/${{ env.ENV }}/terraform.tfstate"
        working-directory: projects/${{ env.PROJECT }}-${{ env.APPLICATION }}

      - name: Terraform Plan
        run: |
          terraform plan \
            -var-file="envs/${{ env.ENV }}.tfvars" \
            -var="deployed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        working-directory: projects/${{ env.PROJECT }}-${{ env.APPLICATION }}
```
