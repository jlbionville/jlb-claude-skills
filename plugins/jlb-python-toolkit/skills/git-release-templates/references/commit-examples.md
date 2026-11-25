# Exemples de messages de commit

Bons :

```
feat(infrastructure): add KV v2 secrets engine adapter

Store identifier metadata in the KV v2 engine so configurations can be
versioned and rolled back.

Refs: #42
```

```
fix(cli): handle missing configuration file gracefully

Check that the configuration file exists before loading and print a
message with the expected path.

Fixes: #78
```

```
feat(domain)!: require a value object for identifiers

BREAKING CHANGE: Identifier now takes IdentifierId instead of a string.
Migration guide in docs/MIGRATION.md.
```

```
docs: describe the three-color palette in the README
test(domain): cover IdentifierBuilder edge cases
chore(deps): bump httpx from 0.27.0 to 0.27.2
```

Mauvais → corrigé :

| Mauvais | Pourquoi | Corrigé |
|---|---|---|
| `Update service` | pas de type, sujet vague | `refactor(application): split service into use cases` |
| `feat: added new feature` | passé, vague | `feat(cli): add --dry-run flag` |
| `fix: fix bug` | ne dit rien | `fix(cli): handle null configuration gracefully` |
| `feat: implement a comprehensive solution for managing credentials across partners` | > 50 caractères | `feat(domain): add multi-partner credentials` |
| `WIP`, `temp`, `test` | pas un changement nommé | scinder ou `fixup!` puis `rebase --autosquash` avant la PR |
