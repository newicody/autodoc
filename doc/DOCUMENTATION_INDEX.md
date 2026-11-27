# Documentation Autodoc / MissiPy — index unifié

## Règle de priorité documentaire

En cas de divergence, lire les documents dans cet ordre :

1. `README_CURRENT.md` : état courant du dépôt et roadmap active.
2. `027X_REUSE_AUDIT.md` : surfaces réutilisables, statuts observés et limites de preuve.
3. Le document d'architecture ou le runbook explicitement cité par le point d'entrée courant.
4. Les rapports de phase et les manifests : preuves attachées à une unité.
5. `patch/<patch-id>/README.md`, `metadata.json`, `patch.diff` : historique de construction/application d'un patch.
6. Les documents plus anciens non référencés par le point d'entrée courant : historique, contexte et compatibilité.

Le `README.md` racine est un sommaire d'entrée. Il ne constitue pas une source d'état technique indépendante.

## Documents canoniques

| Document | Rôle |
|---|---|
| `README_CURRENT.md` | État courant, capacités, limites, prochaine étape |
| `027X_REUSE_AUDIT.md` | Audit de réutilisation, preuves, règles de programmation et limites |
| `code-rules/code_rule.md` | Référence normative de programmation et d'architecture |
| `DOCUMENTATION_INDEX.md` | Présent index et politique de lecture |
| `architecture/SCHEDULER_HANDLER_ROADMAP_0287_R16_R26_R1.md` | Roadmap historique Scheduler/handlers, à lire avec les unités r16 récentes |
| `architecture/GITHUB_RESEARCH_LOVE_CANONICAL_READY_TASK_BINDING_R16_R66_R1.md` | Raccord d'une tâche READY déjà décidée au runtime installé |
| `../patch/0288-hardware-contracts/README.md` | Contrats d'observation matérielle Phase 6.3 / 0288 |
| `architecture/GITHUB_RESEARCH_LOVE_END_TO_END_ACCEPTANCE_0287_R16_R50.md` | Contrat d'acceptation réelle |
| `runbooks/GITHUB_RESEARCH_LOVE_END_TO_END_ACCEPTANCE_0287_R16_R50.md` | Exécution et collecte des preuves |
| `architecture/GITHUB_RESEARCH_LOVE_POSTGRESQL_EXECUTION_CORE_0287_R16_R64.md` | Noyau d'exécution PostgreSQL |
| `architecture/GITHUB_RESEARCH_LOVE_POSTGRESQL_CONTINUATION_AND_TRANSACTIONAL_RUNNER_0287_R16_R65.md` | Continuité et runner transactionnel |
| `architecture/GITHUB_RESEARCH_LOVE_CANONICAL_READY_TASK_BINDING_R16_R66_R1.md` | Raccord d'une tâche déjà décidée |

## Répertoires spécialisés

| Répertoire | Contenu | Usage |
|---|---|---|
| `architecture/` | Architecture, décisions, contrats de flux | Comprendre les responsabilités et dépendances |
| `contracts/` | Contrats stables | Vérifier les formes de messages et données |
| `code-rules/` | Règles exécutables et leur documentation | Préserver les invariants |
| `manifests/` | Fichiers affectés par les phases | Traçabilité des changements |
| `reports/` et rapports `PHASE*` | Résultats de validations | Distinguer réussite locale et preuve réelle |
| `runbooks/` | Procédures opératoires | Exécuter et collecter les preuves |
| `operator/` | Configuration des connecteurs et déploiements | Configurer les surfaces GitHub/ProjectV2 contrôlées |
| `releases/` | Notes de livraison | Comprendre les unités livrées |
| `changelogs/` et `changelog/` | Historique | Conserver la chronologie fonctionnelle |
| `patch/<id>/` | README, metadata et diff | Examiner une unité de changement |

## Politique de consolidation

- Ne pas supprimer les documents historiques simplement parce qu'ils ne sont plus courants.
- Ne pas maintenir plusieurs fichiers « current state » concurrents.
- Toute actualisation de l'état courant doit modifier `README_CURRENT.md`.
- Les contrats matériels 0288 ne constituent pas un collecteur : ne pas documenter de polling, d'intégration Scheduler ou de visualisation comme déjà livrés.
- Toute modification des surfaces canoniques doit mettre à jour `027X_REUSE_AUDIT.md` si les décisions de réutilisation changent.
- Chaque nouveau domaine important doit être référencé ici plutôt que de créer un nouvel index parallèle.
- Les rapports doivent préciser le commit de base, la commande exacte, le code retour, le nombre de tests et si le résultat est local, mocké ou réel.
- Un patch proposé, un patch présent dans l'archive, un patch appliqué et un patch commité sont quatre états distincts.
- Une exécution réelle n'est considérée comme acceptée que si le runbook/contrat de phase et les preuves corrélées l'attestent.

## Références historiques conservées

- `architecture/GLOBAL_ARCHITECTURE_CURRENT_0282.md` — vue globale de l'architecture à la phase 0282 ; utile pour l'évolution, pas comme état complet de r16.
- `architecture/CURRENT_ARCHITECTURE_STATE_0154.md` et `ARCHITECTURE_LAYERS.md` — fondations et historique architectural.
- `operator/GITHUB_PROJECT_ACTIONS_CONFIGURATION_0272.md` — configuration du connecteur ProjectV2/Actions.
- `templates/github/projects-repository/INSTALLATION.md` — guide cumulatif du bundle déployé dans le dépôt externe `newicody/projects`.
