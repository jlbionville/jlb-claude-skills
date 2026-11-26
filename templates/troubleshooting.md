# <Symptôme en une phrase, tel que l'utilisateur l'a vu>

<!--
Gabarit normalisé d'une fiche d'erreur. Un fichier par erreur :
docs/troubleshooting/YYYY-MM-DD-<slug>.md dans le projet concerné.
Toutes les sections restent présentes ; une section sans contenu dit « néant ».
Aucun secret, aucun chemin personnel (remplacer par ~ ou <projet>).
Langue : celle de la documentation du projet.
-->

| Champ | Valeur |
|---|---|
| Date | YYYY-MM-DD |
| Projet / composant | <dépôt, crate, module ou service> |
| Environnement | <OS, versions des outils et bibliothèques en cause> |
| Gravité | bloquant / gênant / cosmétique |
| Statut | résolu / contourné / ouvert |
| Commit de correction | <hash ou « aucun »> |

## Symptôme

Ce qui a été observé, dans l'ordre. Message exact dans un bloc de code. Comment reproduire
(commande, clics, conditions). Ce qui ne s'est **pas** produit alors qu'on l'attendait.

```text
<message d'erreur exact>
```

## Pourquoi (cause racine)

Le mécanisme, pas le symptôme : quel composant fait quoi, et pourquoi cela échoue. La
preuve (fichier, journal, numéro de ligne, horodatage) qui relie la cause au symptôme.
Si la cause est externe (bibliothèque, système, service), le dire et citer la référence.

## Hypothèses et tests

Toutes les hypothèses, y compris celles écartées, avec le test qui a tranché.

| # | Hypothèse | Test effectué | Résultat observé | Verdict |
|---|---|---|---|---|
| 1 | <ce que l'on pensait> | <commande ou vérification précise> | <sortie, mesure> | écartée / confirmée / probable |

## Résolution

Ce qui a été changé (fichiers, commandes, réglages) et pourquoi ce choix plutôt que les
alternatives envisagées. Si c'est un contournement, dire ce qu'une vraie correction
exigerait.

| Option envisagée | Effet | Coût | Risque | Retenue |
|---|---|---|---|---|

## Vérification

Commandes relancées après la correction et leurs résultats. Ce qui reste **non vérifié**,
et comment le vérifier à la main.

## Prévention

Ce qui empêche l'erreur de revenir ou de se rediscuter : test ajouté, règle, documentation,
contrôle de validation modifié.

## Sources

Liens vers les issues, documentations officielles, RFC ou pages consultées, avec la date
de consultation.
