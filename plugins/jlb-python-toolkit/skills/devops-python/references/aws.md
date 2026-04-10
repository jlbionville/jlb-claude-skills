# Référence AWS / boto3

Doc officielle : https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

---

## Authentification & credentials

**Pattern recommandé** — ne jamais hardcoder les credentials :

```python
import boto3

# ✅ Bonne pratique : laisser boto3 résoudre via la chaîne de credentials
# (env vars > ~/.aws/credentials > IAM role > instance profile)
session = boto3.Session(region_name="eu-west-1")
client = session.client("s3")

# ✅ Pour du multi-compte : assumer un rôle IAM
sts = boto3.client("sts")
assumed = sts.assume_role(
    RoleArn="arn:aws:iam::123456789:role/MyRole",
    RoleSessionName="my-script-session",
)
creds = assumed["Credentials"]
cross_account_client = boto3.client(
    "s3",
    aws_access_key_id=creds["AccessKeyId"],
    aws_secret_access_key=creds["SecretAccessKey"],
    aws_session_token=creds["SessionToken"],
)

# ❌ À ne jamais faire
client = boto3.client("s3", aws_access_key_id="AKIA...", aws_secret_access_key="secret")
```

Alternatives : `aws-vault`, variables d'environnement CI/CD, AWS SSO.
Doc : https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html

---

## Pagination

AWS renvoie les résultats par pages. Toujours utiliser un paginator :

```python
# ✅ Avec paginator (récupère TOUS les résultats)
paginator = client.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket="my-bucket"):
    for obj in page.get("Contents", []):
        logger.info("Object: %s", obj["Key"])

# ❌ Sans paginator (rate les résultats au-delà de 1000)
response = client.list_objects_v2(Bucket="my-bucket")
```

Doc : https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html

---

## Gestion des erreurs boto3

```python
from botocore.exceptions import ClientError, NoCredentialsError

try:
    client.get_object(Bucket="my-bucket", Key="my-key")
except ClientError as e:
    error_code = e.response["Error"]["Code"]
    if error_code == "NoSuchKey":
        logger.warning("Objet introuvable : %s", e)
    elif error_code == "AccessDenied":
        logger.error("Accès refusé — vérifier les permissions IAM")
        raise
    else:
        logger.error("Erreur AWS inattendue : %s", e)
        raise
except NoCredentialsError:
    logger.error("Credentials AWS manquants ou invalides")
    sys.exit(1)
```

Doc : https://botocore.amazonaws.com/v1/documentation/api/latest/reference/services/index.html

---

## Retry avec back-off exponentiel

```python
from botocore.config import Config

# ✅ Configurer le retry au niveau du client
config = Config(
    retries={"max_attempts": 5, "mode": "adaptive"},  # "adaptive" > "standard" > "legacy"
    connect_timeout=5,
    read_timeout=30,
)
client = boto3.client("ec2", config=config)
```

Doc : https://boto3.amazonaws.com/v1/documentation/api/latest/guide/retries.html

---

## Secrets Manager (pas de secrets dans le code)

```python
import json
import boto3

def get_secret(secret_name: str, region: str = "eu-west-1") -> dict:
    """Récupère un secret depuis AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

# Usage
db_creds = get_secret("prod/myapp/database")
password = db_creds["password"]  # jamais hardcodé
```

Alternative : AWS Parameter Store (SSM) pour les configs non-sensibles.
Doc Secrets Manager : https://docs.aws.amazon.com/secretsmanager/latest/userguide/

---

## CloudWatch Logs depuis Python

```python
import boto3
import time

logs = boto3.client("logs", region_name="eu-west-1")
LOG_GROUP = "/myapp/scripts"
LOG_STREAM = f"run-{int(time.time())}"

# Créer le stream (idempotent avec try/except)
try:
    logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)
except logs.exceptions.ResourceAlreadyExistsException:
    pass

# Envoyer un log
logs.put_log_events(
    logGroupName=LOG_GROUP,
    logStreamName=LOG_STREAM,
    logEvents=[{"timestamp": int(time.time() * 1000), "message": "Script démarré"}],
)
```

Alternative : `watchtower` — handler logging Python natif vers CloudWatch.
Doc : https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/

---

## Bonnes pratiques IAM pour les scripts

- Principe du moindre privilège : créer un rôle IAM dédié par script
- Utiliser des rôles d'instance EC2 ou des IRSA (EKS) plutôt que des access keys
- Rotation automatique des credentials via AWS IAM Identity Center
- Doc : https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
