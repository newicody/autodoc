# Graphe GitHub, bootstrap des capacités et première visite — 0287 r16-r36/r16-r38

Cette unité regroupe le bootstrap explicite des capacités, la construction du
graphe concret d’une recherche GitHub et la préparation de la première visite
du laboratoire amour.

Le graphe contient quatorze tâches corrélées à une seule commande : préparation
et exécution des deux spécialistes, persistance et projection séparées des deux
analyses, rappel, synthèse, livrable, publication et clôture. Les dépendances
sont linéaires et durables ; la première tâche seulement peut devenir `ready`
après promotion du graphe.

Le catalogue n’enregistre que la capacité réellement disponible dans cette
unité : préparer la première visite. Les capacités futures figurent dans le
graphe, mais restent non résolues jusqu’à l’installation de leurs handlers. Il
est donc impossible de simuler silencieusement une analyse ou une publication.

Le handler réutilise `build_first_love_visit_surface_from_github_research`. Il
construit les objets typés `LoveStudyRequest`, `SpecialistTaskRequest` et
`LaboratoryVisitRequest`, mais ne soumet pas la visite au laboratoire. La
soumission et l’analyse appartiennent au bloc suivant.

Le Scheduler reste l’unique autorité de sélection et d’enchaînement. Cette
unité ne crée aucun Scheduler parallèle, aucun Dispatcher applicatif, aucun
EventBus, aucune file JSON/JSONL et aucun gestionnaire de laboratoire.
PostgreSQL demeure l’autorité durable ; Qdrant n’est pas appelé ici.

L’EventBus, PassiveSupervisor et VisPy restent des surfaces d’observation.
VisPy reste observation-only.
