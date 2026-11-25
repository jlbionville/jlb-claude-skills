# Checklist de relecture d'une pull request

- **Commits** : format Conventional Commits, un changement par commit, scope juste, pas de
  « WIP », pas de mention d'assistant IA.
- **Périmètre** : la PR fait ce que son titre dit, rien de plus ; pas de fichier parasite
  (`.env`, artefacts de build, `target/`, `.venv/`).
- **Code** : conventions du `CLAUDE.md` du projet respectées (architecture, zéro valeur en
  dur, erreurs codifiées, logging) ; pas de duplication évidente ; complexité raisonnable.
- **Tests** : chaque comportement nouveau a un test ; les tests vérifient le code, pas un
  mock ; la suite passe (chiffres dans la description).
- **Sécurité** : aucun secret dans le code, les journaux, les fixtures, l'historique ;
  entrées validées ; messages d'erreur sans fuite (URL complète, corps brut).
- **Compatibilité** : anciens fichiers de configuration encore lus ; migration décrite ;
  version proposée cohérente avec la rupture éventuelle.
- **Documentation** : README / CHANGELOG / docs à jour ; exemples exacts.
- **Verdict** : `Prêt à fusionner` / `Avec corrections` / `Non`, avec `fichier:ligne` pour
  chaque point bloquant.
