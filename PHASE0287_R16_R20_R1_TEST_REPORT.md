# Rapport de test — 0287 r16-r20-r1

## Portée

- policy typed ref transmis au runtime tool-bounded;
- runtime INI réellement sélectionné;
- restauration de l’environnement après acquisition;
- projection et relecture Qdrant sur le même exécuteur;
- suppression de la fabrique externe de reader;
- aucune nouvelle connexion ou infrastructure.

## Vérifications du bundle

- syntaxe AST : réussie;
- contrôle des marqueurs architecturaux : réussi;
- `git apply --check` sur les fichiers complets : réussi;
- `git diff --check` : réussi;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
