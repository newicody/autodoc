# Actualisation documentaire — 027X

**Date : 2026-11-26**

- Réécriture de `README.md` racine comme entrée courte vers la documentation canonique.
- Actualisation de `doc/README_CURRENT.md` depuis l'archive examinée, avec distinction entre implémentation, tests ciblés et preuve d'exploitation.
- Ajout de `doc/027X_REUSE_AUDIT.md` pour inventorier les surfaces canoniques et les limites de preuve.
- Ajout de `doc/DOCUMENTATION_INDEX.md` pour établir une hiérarchie documentaire unique.
- Conservation des rapports, manifests, règles et bundles de patches historiques.
- Aucun code fonctionnel ni test du dépôt n'a été modifié par cette consolidation.
- Limite : `.git/` absent de l'archive ; branches, commits et statut exact d'application des bundles non certifiables.
- Vérifications de l'archive : compilation `src tests tools` réussie ; 19 tests ciblés réussis ; suite complète `tests/rules` interrompue par la limite de temps.
- 97 tests de règles documentaires/compatibilité ciblés : réussis après conservation des ancres historiques.


## Révision d'audit — 2026-11-26

- Correction de l'inventaire : 1 083 tests Python ; 4 426 occurrences de chemins dans les diffs (3 861 distincts) ; répartition recalculée par catégorie.
- Réconciliation r16 : le code et les tests r16-r66-r1 sont déjà présents dans l'archive ; le diff du bundle est reconnu comme déjà appliqué. r16-r67 reste la prochaine unité indiquée par le document d'architecture.
- Validation relancée : compilation réussie ; 43 tests ciblés réussis ; 1 863 tests de règles réussis en excluant le fichier dépendant de Git ; suite complète `tests/rules` terminée avec 1 863 réussis et 3 échecs dus à l'absence de `.git` pour les appels `git ls-files`.
- Ajout de la revue des règles de programmation/style issues de `doc/code-rules/code_rule.md` : typage, immutabilité, événements, frontières d'effets, CLI, dépendances et hygiène Git.
- Constat d'hygiène : le diff r16-r66-r1 embarque deux fichiers `__pycache__/*.pyc`, à retirer lors de la régénération du bundle.
- Limite supplémentaire : audit exécuté avec Python 3.13.5 alors que la règle canonique demande Python 3.14 ; aucune configuration de formatter/linter n'est définie dans le dépôt.
- Aucun code fonctionnel n'a été modifié ; seules les pages documentaires d'état/audit/index ont été actualisées.
