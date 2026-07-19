# Validation locale du triplet fetché avant intake Scheduler

## Position dans la chaîne

La validation intervient exclusivement côté serveur Autodoc :

```text
GitHub Projects / Actions
→ fetch local existant
→ ready_run local
→ validation r16-r23
→ intake contrôlé par le Scheduler
```

Elle n’intervient pas dans le workflow GitHub et ne modifie pas la création
technique des artefacts Actions.

## Entrée

L’outil :

```text
tools/validate_fetched_github_research_triplet_0287.py
```

exige :

```text
fetch_cycle_report
run_id explicite
état durable du fetch, si nécessaire
```

Il sélectionne exactement un `ready_run` et charge de manière bornée :

```text
authoritative_request.json
copilot_advisory.json
dual_artifact_manifest.json
```

## Réutilisation

Aucune nouvelle logique de corrélation n’est inventée. L’outil réutilise :

- le sélecteur `ready_run` du fetch;
- le chargeur local borné et protégé contre les symlinks;
- l’assemblage dual-artifact existant;
- la validation existante des digests du manifeste;
- le constructeur existant du work package corrélé;
- la politique d’admissibilité existante.

## Verrou automatique initial

Après la chaîne existante, le wrapper exige en plus :

```text
repository = newicody/projects
requested_status = Recherche
request_mode = initial
parent_event_ref = ""
```

Une continuation n’est pas acceptée par cette surface dédiée au premier cycle
automatique.

## Sortie

Le rapport contient :

```text
status = validated-before-scheduler-intake
validated_ready_runs = [ready_run]
validation
route_candidate
validation_digest
```

Le digest lie :

- le rapport de fetch source;
- le dépôt, le run et l’Issue;
- le handoff;
- les trois identifiants et noms d’artefacts;
- la route candidate et son digest d’admissibilité.

## Frontières

La validation :

- ne contacte pas GitHub;
- ne modifie aucun workflow;
- ne crée aucun artefact Actions;
- ne publie aucun résultat vers Projects;
- n’écrit ni SQL ni Qdrant;
- ne crée ni ne distribue de commande Scheduler;
- n’exécute aucun laboratoire.

La seule écriture est le rapport JSON local demandé par l’opérateur.
