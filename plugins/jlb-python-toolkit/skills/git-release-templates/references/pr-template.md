# Gabarit de description de pull request

```markdown
## Résumé
Ce que fait la PR, en une à trois phrases.

## Changements
- …
- …

## Type
- [ ] Fonctionnalité (feat)   - [ ] Correctif (fix)   - [ ] Refactorisation (refactor)
- [ ] Documentation (docs)    - [ ] Tests (test)      - [ ] Outillage (chore)
- [ ] Rupture de compatibilité (!)

## Tests exécutés
- Commande(s) et résultat constaté (ex. `cargo test --workspace --locked` → 252 réussis).
- [ ] Tests ajoutés ou mis à jour pour chaque comportement nouveau.
- Ce qui n'a **pas** été vérifié (clics, appels réels…).

## Configuration et secrets
- [ ] Aucun changement de configuration
- [ ] Nouveau champ / nouveau fichier de configuration (décrire, valeur par défaut, compatibilité des anciens fichiers)
- [ ] Nouveau secret ou droit requis (décrire ; jamais la valeur)

## Rupture de compatibilité
- [ ] Aucune
- [ ] Oui : étapes de migration, compatibilité descendante, documentation mise à jour.

## Documentation
- [ ] README   - [ ] CHANGELOG   - [ ] docs/   - [ ] CLAUDE.md (si conventions touchées)

## Points à relire en priorité
- …

## Tickets
Refs: #…  /  Fixes: #…
```

Règles : aucune mention d'un assistant IA ; aucun secret ; les chiffres de tests sont ceux
réellement constatés.
