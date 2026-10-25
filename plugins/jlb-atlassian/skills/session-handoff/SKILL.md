---
name: session-handoff
description: Sauvegarde et reprise du contexte de travail dans Confluence : à utiliser quand jlb dit « clôture », « handoff », « sauvegarde le contexte », ou « reprise » en début de session.
---

# session-handoff

Objectif : qu'aucun contexte ni analyse ne soit perdu en changeant d'ordinateur. Confluence est le référentiel durable ; GitHub porte le code ; Jira porte les tâches.

## Paramètres (à modifier ici, jamais dans les étapes)

| Clé | Valeur |
|---|---|
| cloudId | mytechnoprojects.atlassian.net |
| espace | Devops (id 66224132) |
| page hub | Contexte Claude — hub de continuité (id 69468162) |
| page état | État courant — Devops (id 69206019) |
| page journal (parent) | Journal de sessions (id 69206046) |
| nommage journal | `Journal AAAA-Www` (semaine ISO) |

Si un id ne répond plus, retrouver la page par titre avec CQL (`space = "Devops" AND title = "..."`) avant de créer quoi que ce soit.

## Mode « reprise » (début de session)

1. Lire la page « État courant — Devops ».
2. Lire la page de journal de la semaine ISO courante (sinon la plus récente) et en retenir la dernière entrée.
3. Répondre en 5 lignes max : chantier concerné, dernier état, prochaine étape prévue, questions ouvertes. Demander sur quoi on travaille si ce n'est pas évident.

## Mode « clôture » (fin de session)

1. **Extraire de la conversation** : objectif, fait, décisions, fichiers produits, prochaines étapes, questions ouvertes, clés Jira.
   - Une décision n'est notée comme telle que si jlb l'a explicitement prise. Une suggestion de Claude non validée va dans « Prochaines étapes » ou « Questions ouvertes ».
   - Ne rien inventer ; marquer ⚠️ ce qui n'a pas été vérifié.
2. **Contrôle secrets** : aucun mot de passe, token, clé, numéro de compte ou IP privée sensible. Mentionner seulement le nom du secret et son emplacement (SOPS, GitHub Secrets, Vault). En cas de doute, retirer.
3. **Semaine ISO** : calculer avec `date +%G-W%V` (Bash) ou `datetime.date.today().isocalendar()`.
4. **Journal** : chercher `Journal AAAA-Www` sous la page journal. S'il n'existe pas, le créer avec la période (lundi–dimanche). Sinon, le lire puis ajouter l'entrée à la fin avec `updateConfluencePage` (lire `getContentFormatGuide` d'abord, conserver le contenu existant à l'identique).
   Format d'entrée :
   ```
   ### AAAA-MM-JJ — <titre court>
   - Conversation : <lien claude.ai si connu, sinon « projet <nom> »>
   - Objectif / Fait / Décisions / Fichiers produits / Prochaines étapes / Questions ouvertes / Jira
   ```
5. **État courant** : lire la page, ne modifier que les lignes des chantiers touchés (statut, prochaine étape, référence), ajouter les décisions prises, mettre à jour les questions ouvertes et la date. Ne jamais réécrire les autres chantiers.
6. **Fichiers produits** (le poste de travail de Claude est éphémère) :
   - code / config / Markdown technique → proposer un commit dans le dépôt GitHub concerné (confirmation obligatoire avant push) ;
   - binaires (docx, xlsx, pdf, images) → Google Drive, puis lien dans l'entrée ;
   - artifacts claude.ai → lien dans l'entrée.
7. **Jira** : proposer la création ou la mise à jour des tickets pour les prochaines étapes ; ne créer qu'après accord.
8. **Compte rendu** : 3 lignes maximum, avec les pages modifiées. Pas de récapitulatif de la session.

## Interdits

- Supprimer ou écraser une page Confluence.
- Copier une conversation brute dans le journal (une synthèse suffit ; une transcription seulement sur demande, en page enfant).
- Publier un secret.
