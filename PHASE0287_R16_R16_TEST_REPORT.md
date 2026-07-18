# Rapport de test — 0287 r16-r16

## Unité

`construire-et-enregistrer-le-livrable-final`

## Portée

- validation de la lignée synthèse ↔ analyses SQL;
- réutilisation de `build_final_synthesis_packet`;
- création d’un objet final et d’un artefact final;
- création d’une révision enfant acceptée;
- inspection des collisions immuables;
- writes SQL idempotents et relecture exacte;
- aucune projection, exécution Scheduler ou mutation GitHub.

## Vérifications du bundle

- syntaxe Python analysée sans générer de `__pycache__`;
- contrôle statique de la construction et des contrats importés : réussi;
- contrôle statique des frontières : réussi;
- `git apply --check` sur une base vide : réussi;
- `git diff --check` : réussi.

La suite complète `tests/rules` est exécutée par `apply_patch_queue.py`.
