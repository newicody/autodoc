# Phase 0287 r16-r6 — rapport de validation

## Objet

Vérifier l’admissibilité des recherches récupérées sans déclencher le
Scheduler ni le laboratoire.

## Fichiers

- `src/context/github_research_work_package_admissibility_0287.py`
- `tools/check_github_research_work_package_admissibility_0287.py`
- `tests/rules/test_github_research_work_package_admissibility_0287_rule.py`
- `doc/architecture/GITHUB_RESEARCH_WORK_PACKAGE_ADMISSIBILITY_0287.md`

## Verrous

- dépôt admis : `newicody/projects` uniquement ;
- statut explicite : `Recherche` ;
- modes : `initial` et `continuation` ;
- avis Copilot obligatoire mais consultatif ;
- réutilisation du paquet corrélé existant ;
- aucun accès réseau ;
- aucune écriture SQL ou Qdrant ;
- aucune mutation GitHub ;
- aucune commande Scheduler ;
- aucune exécution de laboratoire.
