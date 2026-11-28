# 0295 — Raccordement runtime du transport Git Copilot–serveur

## Base
- Branche : `docs/unification-027x`
- Base : `6f99331c1600e97da4e3a474ac09ddcd50b2bf77`

## Objectif
Raccorder le transport Git défini en 0294 au workflow initial, au passage
Copilot unique de reformulation et à l'intake d'admissibilité existant, sans
ajouter d'orchestrateur ni contourner le Scheduler.

## Modifications
- Publication Git de l'avis Copilot v2 depuis le workflow `issues.opened`.
- Nouveau workflow `autodoc-copilot-refinement.yml`, déclenché uniquement
  par le push de `server-response.json`.
- Adaptateurs one-shot pour fetch, publication initiale, réponse serveur et
  reformulation Copilot.
- Le serveur peut produire sa réponse depuis une évaluation JSON structurée
  issue de ses propres observations ; l'adaptateur ne collecte pas lui-même
  l'état des composants.
- L'intake d'admissibilité peut exiger la chaîne Git complète et injecter la
  demande reformulée dans le work package comme indication non autoritative.
- Le work package conserve la demande GitHub initiale comme autorité.
- Documentation d'installation et manifest du bundle Projects mis à jour.

## Limites
Le producteur d'évaluation serveur doit encore être alimenté par les interfaces
réelles des composants et appelé par le traitement serveur vivant. L'option
d'intake Git n'est pas encore activée automatiquement dans le parcours
ProjectV2 `En cours`. Le bundle et le secret
`AUTODOC_EXCHANGE_GIT_TOKEN` doivent être installés dans `newicody/projects`
et le parcours doit être validé de bout en bout.

## Validation
Tests ajoutés pour les enveloppes et la reformulation. Non exécutés dans cet
environnement. Aucun dispatch Scheduler ni lancement de laboratoire ajouté.
