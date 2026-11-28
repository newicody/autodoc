# 0293 — Contrat de cadrage scientifique Copilot–serveur

## Base
- Branche : `docs/unification-027x`
- Base : `89253f2fe1e470422cf5713d70b19ca9597c1dd9`

## Objectif
Définir et valider les artefacts corrélés du cadrage initial en un seul échange :
avis initial Copilot, réponse unique de cohérence du serveur, puis demande
reformulée par Copilot.

## Fichiers
- `src/contracts/copilot_scientific_framing.py`
- `tests/contracts/test_copilot_scientific_framing.py`
- `doc/architecture/COPILOT_SCIENTIFIC_FRAMING.md`

## Limites explicites
Ce patch ajoute un contrat pur. Il ne prétend pas fournir le producteur de la
réponse serveur ni le second appel Copilot. Il ne modifie pas le Scheduler,
les workflows GitHub, les permissions, les stockages ou les autorités
d'exécution. Les artefacts restent consultatifs ; aucun lancement de tâche
n'est autorisé par ce contrat.

## Validation
Tests définis pour corrélation, digest, statut de cohérence, provenance,
non-autorité et liaison de la reformulation. Non exécutés dans cet environnement.
