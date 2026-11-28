# 0294 — Transport Git du cadrage Copilot–serveur

## Base
- Branche : `docs/unification-027x`
- Base : `235be2feff069fca5a62c372b5acd4e0b22cf5b5`

## Objectif
Matérialiser le cadrage initial par trois artefacts append-only dans le dépôt
Git Projects, chacun publié par commit/push et consommé par l'autre côté.

## Fichiers
- `src/contracts/git_artifact_exchange.py`
- `tests/contracts/test_git_artifact_exchange.py`
- `doc/architecture/GIT_ARTIFACT_EXCHANGE.md`

## Limites
Ce patch ajoute le contrat pur de transport et sa validation. Il ne réalise
pas encore les commits/push runtime, le workflow déclenché par le push serveur,
ni la récupération serveur de l'artefact reformulé. Il n'autorise aucune
exécution et ne modifie pas le Scheduler.

## Validation
Tests définis pour chemins, filiation, digests, rejeu, collision et frontières.
Non exécutés dans cet environnement.
