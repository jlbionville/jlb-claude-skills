# Référence : Data & Traitement Python

## Pandas vs Polars — Quand choisir

| Critère | Pandas | Polars |
|---------|--------|--------|
| **Maturité / écosystème** | ✅ Très mature | 🔄 Rapide évolution |
| **Performance gros volumes** | ❌ Lent au-delà de 1M lignes | ✅ 5-100x plus rapide |
| **API** | Familière, omniprésente | Expressif, lazy evaluation |
| **Mémoire** | Élevée | Optimisée (Apache Arrow) |
| **SQL-like** | Limité | ✅ `filter`, `group_by`, `join` naturels |
| **Recommandation** | Scripts existants, équipe habituée | Nouveaux projets, gros volumes |

---

## Pandas — Patterns recommandés

### Lecture et validation

```python
import pandas as pd
from pathlib import Path

def load_and_validate(path: Path) -> pd.DataFrame:
    """Charger un CSV avec validation des colonnes requises."""
    required_cols = {"user_id", "email", "created_at"}

    df = pd.read_csv(
        path,
        dtype={"user_id": "int64", "email": "string"},  # types explicites
        parse_dates=["created_at"],
        encoding="utf-8",
    )

    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    return df
```

### Transformations idiomatiques

```python
# ✅ Chaînage de méthodes — lisible et efficace
result = (
    df
    .assign(
        email_domain=lambda x: x["email"].str.split("@").str[1],
        age_days=lambda x: (pd.Timestamp.now() - x["created_at"]).dt.days,
    )
    .query("age_days >= 30")
    .groupby("email_domain", as_index=False)
    .agg(count=("user_id", "count"), avg_age=("age_days", "mean"))
    .sort_values("count", ascending=False)
)

# ❌ Boucles for sur un DataFrame — très lent
for index, row in df.iterrows():  # à éviter absolument
    df.at[index, "domain"] = row["email"].split("@")[1]
```

### Gestion des valeurs manquantes

```python
# Inspecter
print(df.isnull().sum())
print(df.dtypes)

# Stratégies
df_clean = (
    df
    .dropna(subset=["user_id", "email"])  # colonnes critiques : supprimer
    .fillna({"country": "Unknown", "score": df["score"].median()})  # autres : imputer
)
```

### Export

```python
# CSV
df.to_csv(output_path, index=False, encoding="utf-8-sig")  # utf-8-sig pour Excel

# Excel
with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    df_summary.to_excel(writer, sheet_name="Résumé", index=False)
    df_detail.to_excel(writer, sheet_name="Détail", index=False)

# Parquet (recommandé pour stocker des DataFrames)
df.to_parquet(output_path, index=False)
```

---

## Polars — Patterns recommandés

### Lecture lazy (efficace pour gros fichiers)

```python
import polars as pl

# Lazy evaluation — ne lit que ce dont on a besoin
result = (
    pl.scan_csv("large_file.csv")  # lazy
    .filter(pl.col("status") == "active")
    .select(["user_id", "email", "created_at"])
    .with_columns([
        pl.col("created_at").str.to_datetime(),
        pl.col("email").str.split("@").list.get(1).alias("domain"),
    ])
    .group_by("domain")
    .agg(pl.count("user_id").alias("count"))
    .sort("count", descending=True)
    .collect()  # exécution réelle ici
)
```

### Expressions typées

```python
# ✅ Polars — expressions puissantes
df = df.with_columns([
    (pl.col("price") * pl.col("quantity")).alias("total"),
    pl.when(pl.col("total") > 1000).then("premium").otherwise("standard").alias("tier"),
])

# Jointures explicites
merged = customers.join(orders, on="customer_id", how="left")
```

---

## Pipeline de traitement — Pattern ETL

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import logging

logger = logging.getLogger(__name__)


class DataSource(Protocol):
    def extract(self) -> pd.DataFrame: ...

class DataTransformer(Protocol):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame: ...

class DataSink(Protocol):
    def load(self, df: pd.DataFrame) -> None: ...


@dataclass
class ETLPipeline:
    source: DataSource
    transformers: list[DataTransformer]
    sink: DataSink

    def run(self) -> dict[str, int]:
        logger.info("Extraction...")
        df = self.source.extract()
        initial_count = len(df)

        for transformer in self.transformers:
            df = transformer.transform(df)
            logger.debug("%s: %d lignes", type(transformer).__name__, len(df))

        logger.info("Chargement: %d lignes", len(df))
        self.sink.load(df)

        return {"input": initial_count, "output": len(df)}
```

---

## Validation de données — Pandera

```python
import pandera as pa
from pandera import Column, DataFrameSchema, Check

schema = DataFrameSchema(
    {
        "user_id": Column(int, Check.greater_than(0)),
        "email": Column(str, Check.str_matches(r"^[\w.-]+@[\w.-]+\.\w+$")),
        "age": Column(int, Check.in_range(0, 150), nullable=True),
        "status": Column(str, Check.isin(["active", "inactive", "pending"])),
    },
    index=pa.Index(int),
    strict=True,
)

# Validation (lève SchemaError si invalide)
validated_df = schema.validate(df)
```

---

## Bonnes pratiques données

**Toujours :**
- Spécifier les dtypes à la lecture (`dtype={"col": "int64"}`)
- Utiliser `parse_dates` pour les colonnes de dates
- Valider les données à l'entrée du pipeline
- Préférer Parquet pour stocker des DataFrames intermédiaires

**Jamais :**
- `iterrows()` ou `itertuples()` sur un grand DataFrame
- Concaténation dans une boucle : `df = pd.concat([df, new_row])` → accumuler dans une liste, concat une seule fois
- Ignorer les valeurs manquantes sans stratégie explicite

---

## Liens officiels

- Pandas : https://pandas.pydata.org/docs/
- Polars : https://docs.pola.rs/
- Pandera : https://pandera.readthedocs.io/
- openpyxl : https://openpyxl.readthedocs.io/
