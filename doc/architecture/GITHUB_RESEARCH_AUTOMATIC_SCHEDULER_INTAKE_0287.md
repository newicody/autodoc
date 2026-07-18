# Admission automatique d’une recherche dans l’intake Scheduler

## Objectif

Une recherche issue de `newicody/projects` et déjà déclarée admissible par le
verrou r16-r6 peut être transformée automatiquement en demande de route
autorisée pour le Scheduler existant.

```text
candidat de route admissible
→ politique automatique explicite
→ décision déterministe `approve`
→ intake Scheduler GitHub existant
→ SchedulerRouteRequest autorisé
```

Cette unité ne remet pas encore la demande au Scheduler.

## Pourquoi la décision est explicite

L’automatisation ne signifie pas l’absence de politique. La décision est
produite seulement lorsque le candidat possède déjà :

- le schéma d’admissibilité verrouillé;
- `repository = newicody/projects`;
- `requested_status = Recherche`;
- un mode `initial` ou `continuation` cohérent;
- un digest d’admissibilité SHA-256;
- les trois indicateurs d’exécution encore à `false`.

L’identifiant de décision est déterministe à partir de la politique et du
candidat. Un rejeu produit donc la même décision.

## Réutilisation

L’unité appelle
`build_github_artifact_scheduler_intake_plan(..., authorized=True)`.
Ce contrat existant construit le `SchedulerRouteRequest` à l’aide de
`scheduler_route_request_mapping(...)`.

Aucun second modèle de route ou de commande Scheduler n’est créé.

## Limites

Cette unité :

- ne modifie pas le Scheduler;
- ne démarre pas `Scheduler.run()`;
- n’appelle pas `Scheduler.emit()`;
- ne prépare pas directement le laboratoire;
- n’écrit pas dans SQL ou Qdrant;
- ne modifie pas GitHub;
- ne crée ni EventBus, ni Dispatcher, ni daemon.

L’unité suivante remettra ce `SchedulerRouteRequest` au handler déjà enregistré
derrière le Scheduler/Dispatcher.
