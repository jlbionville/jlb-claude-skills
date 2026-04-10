---
name: aws-serverless
description: >
  Guide pour concevoir, coder et déployer des apps serverless AWS avec Terraform. Déclencher pour
  toute demande impliquant : Lambda, DynamoDB, API Gateway (REST/HTTP), S3, SQS, SNS, EventBridge,
  Step Functions, Cognito, Secrets Manager, SSM. Aussi pour : logs structurés, observabilité,
  X-Ray, CloudWatch, Lambda Powertools, métriques custom, cold start, alertes, dashboard, tagging,
  coûts par projet, modules Terraform réutilisables, infra as code serverless. Exemples : "crée
  une Lambda", "API REST sur AWS", "orchestrer des Lambdas", "auth Cognito", "gérer mes secrets",
  "monitorer mes Lambdas", "écrire le Terraform pour Lambda + DynamoDB". Exclut ECR et Fargate.
---

# AWS Serverless Skill (Terraform)

Guide pour concevoir et déployer des applications **serverless AWS** sans ECR ni Fargate.

Stack couverte : **Lambda · DynamoDB · API Gateway · S3 · EventBridge · SQS · SNS ·
Step Functions · Cognito · Secrets Manager · SSM Parameter Store**

Observabilité : **CloudWatch Logs · CloudWatch Metrics · CloudWatch Alarms · X-Ray · Lambda Powertools**

Outil IaC : **Terraform**

---

## Étape 0 — Collecte d'informations (si absentes)

Avant de générer quoi que ce soit, s'assurer d'avoir :

| Info | Exemple |
|------|---------|
| **Nom du projet** | `ecommerce-platform` |
| **Nom de l'application** | `orders-api` |
| **Environnement** | `dev` / `staging` / `prod` |
| **Région AWS** | `eu-west-1` |
| **Besoin fonctionnel** | "API REST pour gérer des commandes, stockées dans DynamoDB" |
| **Déclencheur Lambda** | API Gateway / SQS / EventBridge / S3 / Step Functions |
| **Livrable** | Code Lambda + Terraform, ou architecture seule, ou debug |

Si des infos manquent, poser **une seule question groupée**. Ne jamais bloquer sur une ambiguïté mineure — faire une hypothèse raisonnable et l'annoncer explicitement.

---

## Étape 1 — Charger la référence selon le besoin

Lire le fichier de référence **avant** de générer :

| Besoin principal | Référence à lire |
|-----------------|-----------------|
| Lambda + DynamoDB + API Gateway | `references/lambda-dynamodb.md` |
| Messaging : SQS, SNS, EventBridge | `references/messaging.md` |
| Orchestration : Step Functions | `references/step-functions.md` |
| Auth : Cognito + API Gateway | `references/cognito.md` |
| Secrets : Secrets Manager, SSM | `references/secrets.md` |
| Tagging & gestion des coûts | `references/tagging.md` |
| Logs, métriques, tracing, alarmes | `references/observability.md` |

Si le projet touche plusieurs domaines, lire tous les fichiers concernés.

**Toujours lire `references/tagging.md`** — le tagging est obligatoire sur chaque ressource.

**Toujours lire `references/observability.md`** — tout composant généré doit inclure logs, alarmes et tracing.

---

## Étape 2 — Conventions obligatoires

### 2.1 Nommage des ressources

```
{projet}-{application}-{composant}-{environnement}
```

Exemples :
- `ecommerce-orders-api-lambda-prod`
- `ecommerce-orders-orders-table-prod`
- `ecommerce-orders-events-queue-prod`

### 2.2 Tagging obligatoire sur **chaque** ressource Terraform

Tout bloc `resource` doit inclure ce bloc `tags` :

```hcl
tags = merge(local.common_tags, {
  Component = "orders-api-lambda"   # spécifique à la ressource
})
```

Avec dans `locals.tf` :

```hcl
locals {
  common_tags = {
    Project     = var.project      # ex: "ecommerce"
    Application = var.application  # ex: "orders-api"
    Environment = var.environment  # ex: "prod"
    ManagedBy   = "terraform"
    CostCenter  = var.cost_center  # ex: "backend-team"
  }
}
```

> ⚠️ **Aucune ressource sans tags.** Les tags `Project`, `Application`, `Environment` sont
> requis pour le calcul des coûts via AWS Cost Explorer (grouper par tag).

### 2.3 Variables Terraform minimales

```hcl
variable "project"     { type = string }
variable "application" { type = string }
variable "environment" { type = string }
variable "region"      { type = string  default = "eu-west-1" }
variable "cost_center" { type = string  default = "default" }
```

### 2.4 Structure de fichiers Terraform recommandée

```
infrastructure/
├── main.tf             # provider + backend
├── locals.tf           # common_tags + log_retention + metrics_namespace
├── variables.tf        # toutes les variables
├── outputs.tf          # ARNs, URLs, noms exposés
├── lambda.tf           # fonctions Lambda + IAM roles
├── dynamodb.tf         # tables DynamoDB
├── api_gateway.tf      # API Gateway REST/HTTP
├── messaging.tf        # SQS, SNS, EventBridge
├── storage.tf          # S3 buckets
├── auth.tf             # Cognito User/Identity Pools
├── secrets.tf          # Secrets Manager + SSM
├── observability.tf    # Log groups, alarmes, dashboard, metric filters
└── terraform.tfvars    # valeurs par environnement
```

---

## Étape 3 — Mode Génération

### 3.1 Code Lambda (Python)

Toujours générer avec :
- Handler décoré `@logger.inject_lambda_context` + `@tracer.capture_lambda_handler` + `@metrics.log_metrics`
- **Lambda Powertools** obligatoire : Logger (JSON structuré), Tracer (X-Ray), Metrics (EMF)
- `POWERTOOLS_SERVICE_NAME` = `{projet}-{application}` en variable d'environnement
- Variables d'environnement pour les ARNs/noms (jamais hardcodés)
- Réponse standardisée pour API Gateway
- Métriques custom : `SuccessCount`, `ErrorCount`, `ValidationErrorCount` au minimum

### 3.2 Code Terraform

Pour chaque ressource :
1. Bloc `resource` avec **tous les tags obligatoires** (via `merge`)
2. IAM role + policy attachée au principe du moindre privilège
3. Variables pour les valeurs changeantes par environnement
4. Output de l'ARN/URL de la ressource
5. **Log group dédié** avec rétention selon l'environnement (dev=7j, staging=14j, prod=90j)
6. **Alarme CloudWatch** sur les métriques critiques du composant

### 3.3 Décider du livrable

- Snippet court / illustration → **code inline**
- Module complet production-ready → **fichier(s) téléchargeables** via `bash_tool` + `present_files`

### 3.4 Bloc "Pourquoi ces choix ?" obligatoire

Après chaque génération, expliquer :
- Pourquoi ce service plutôt qu'un autre
- Les alternatives existantes (ex: API HTTP vs REST)
- Les liens vers la doc Terraform AWS Provider et AWS officielle

---

## Étape 4 — Mode Architecture

Quand l'utilisateur décrit un besoin fonctionnel sans préciser l'archi :

1. **Proposer un schéma textuel** des composants et leurs interactions
2. **Justifier chaque service choisi** (ex: "SQS plutôt que SNS car tu as un seul consommateur")
3. **Estimer les coûts** ordre de grandeur (voir `references/tagging.md` pour Cost Explorer)
4. **Lister les points d'attention** sécurité, limites de service, cold start Lambda
5. **Inclure systématiquement** les éléments d'observabilité : quels logs, quelles alarmes, quel dashboard

---

## Étape 5 — Mode Debug / Review

### Diagnostiquer un problème Terraform

```
## Problème identifié
[Cause racine : ex "le rôle IAM manque dynamodb:GetItem"]

## Correction
[bloc Terraform corrigé avec commentaires]

## Pourquoi ?
[explication + lien doc]

## À vérifier aussi
[effets de bord potentiels]
```

### Review de code Lambda

Signaler en priorité :
1. **Sécurité** : secrets hardcodés, permissions trop larges, input non validé
2. **Résilience** : pas de retry, timeout trop court, cold start non géré
3. **Observabilité** : pas de Powertools, logs non structurés, absence de métriques custom, X-Ray désactivé
4. **Coûts** : connexion DB non réutilisée, payload oversized, appels API inutiles

---

## Étape 6 — Checklist avant livraison

**Terraform :**
- [ ] `locals.tf` avec `common_tags`, `log_retention_days` et `metrics_namespace`
- [ ] Chaque `resource` a `tags = merge(local.common_tags, {...})`
- [ ] Tags `Project`, `Application`, `Environment`, `ManagedBy`, `CostCenter` présents
- [ ] Nommage `{projet}-{application}-{composant}-{env}`
- [ ] IAM policies au principe du moindre privilège
- [ ] Pas de valeurs hardcodées (région, ARN, compte) → variables ou `data`
- [ ] `outputs.tf` expose les ARNs/URLs utiles
- [ ] `observability.tf` créé avec log groups, alarmes et dashboard
- [ ] Rétention des log groups définie (pas d'infini)
- [ ] Alarme DLQ configurée si SQS présent
- [ ] Topic SNS d'alertes ops créé et abonné

**Lambda :**
- [ ] Powertools : `Logger`, `Tracer`, `Metrics` importés et décorateurs appliqués
- [ ] `POWERTOOLS_SERVICE_NAME` et `METRICS_NAMESPACE` en variables d'environnement
- [ ] Tracing X-Ray activé (`mode = "Active"`)
- [ ] Layer Powertools attaché à la fonction
- [ ] IAM : `AWSXRayDaemonWriteAccess` attaché au rôle Lambda
- [ ] `patch_all()` appelé pour instrumenter boto3
- [ ] Métriques custom : `SuccessCount`, `ErrorCount` au minimum
- [ ] Gestion des erreurs explicite avec log `.exception()` ou `.warning()`
- [ ] Handler retourne le format attendu par le déclencheur

---

## Références

- `references/lambda-dynamodb.md` — Lambda, DynamoDB, API Gateway REST/HTTP, patterns CRUD
- `references/messaging.md` — SQS, SNS, EventBridge : patterns, DLQ, filtrage
- `references/step-functions.md` — Orchestration, state machines, gestion d'erreurs
- `references/cognito.md` — User Pools, Identity Pools, autorisation API Gateway
- `references/secrets.md` — Secrets Manager, SSM Parameter Store, rotation
- `references/tagging.md` — Stratégie de tags, Cost Explorer, rapport par projet/application
- `references/observability.md` — Logs structurés (Powertools), X-Ray, alarmes CloudWatch, dashboards
