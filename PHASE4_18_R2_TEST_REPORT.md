# Phase 4.18-r2 — Test report

## Portée

Intégration de la couche `GitHub Project Orchestrator / SourceCandidate` dans `doc/docs/architecture/00_global.dot`.

## Commandes exécutées ici

```bash
dot -Tsvg doc/docs/architecture/00_global.dot >/tmp/00_global.svg
dot -Tsvg doc/docs/architecture/integrations/90_github_project_orchestrator.dot >/tmp/90_github_project_orchestrator.svg
dot -Tsvg doc/docs/architecture/integrations/91_source_candidate_lifecycle.dot >/tmp/91_source_candidate_lifecycle.svg
rm -f /tmp/00_global.svg /tmp/90_github_project_orchestrator.svg /tmp/91_source_candidate_lifecycle.svg
```

## Résultat

```text
DOT 00 OK
DOT 90 OK
DOT 91 OK
```

Graphviz peut afficher l'avertissement historique sur `splines=ortho` et les labels d'arêtes du graphe global ; ce n'est pas une erreur de rendu.

## Hors périmètre

```text
pas d'API GitHub
pas de token
pas de polling réseau
pas de Copilot obligatoire
pas de Scheduler
pas de Qdrant
pas de LLM
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.18-r2 intègre une couche future dans le graphe global sans ajouter de code runtime ni de dépendance externe.
```
