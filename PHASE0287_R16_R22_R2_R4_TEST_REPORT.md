# Rapport de test — 0287 r16-r22-r2-r4

## Unité

`rebaser-sur-fonction-suivante-reelle`

## Cause

Les variantes précédentes ne conservaient pas le contexte réel situé après
l'assertion résiduelle. `git apply` standard exige du contexte pour calculer
un décalage.

## Correction

La rustine utilise comme contexte :

- la fin de la boucle `for marker`;
- l'assertion historique;
- la fonction suivante réelle
  `test_artifact_identity_separates_issues_and_runs`.

Aucun workflow ni runtime n'est modifié.
