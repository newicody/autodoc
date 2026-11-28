# Phase 6.1-r1 — SourceCandidate live path alignment

## Objet

Cette phase reprend la Phase 6.1 après mise à jour de `code_rule.md`.

Le nouvel addendum Phase 6-r1 impose que les capacités durables convergent vers un chemin noyau vivant :

```text
Command dataclass
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
-> backend réel déclaré
-> résultat observable
```

La 6.1 initiale créait une `SourceCandidate` via CLI et use-case local direct.
La 6.1-r1 conserve la CLI, mais elle la transforme en adaptateur au-dessus d'un chemin Scheduler vivant.

## Capacité alignée

```text
source_candidate_intake_cli
-> SourceCandidateIntakeCommand
-> EventType.SOURCE_CANDIDATE_INTAKE
-> Scheduler
-> PolicyEngine
-> PriorityQueue
-> Dispatcher
-> SourceCandidateIntakeHandler
-> SourceCandidateStore JSON réel
-> EventType.SOURCE_CANDIDATE_INTAKE_RESULT observable
-> Request.reply
-> stdout text/json
```

## Backend réel déclaré

Le backend réel minimal de cette phase est le store JSON local `SourceCandidateStore`.

Il n'est pas dummy : il écrit réellement un fichier JSON atomique et produit un rapport optionnel.

## Pourquoi ce choix

Cette étape ne doit pas introduire OpenVINO, Qdrant, GitHub ou LLM.
Le premier chemin vivant Phase 6 doit donc porter la capacité locale la plus simple : création et stockage d'une `SourceCandidate`.

## Frontières

La phase ne modifie pas le Scheduler.
Elle ajoute seulement :

- un type d'événement d'intake SourceCandidate ;
- un type d'événement de résultat observable ;
- une destination de politique `source_candidate` ;
- un handler dédié ;
- un test d'intégration Scheduler.

## Plan vérifié

Le plan Phase 6 reste valide, mais les phases suivantes doivent suivre la même forme :

```text
6.2 SourceCandidate decision
-> décision via Scheduler + handler + store réel

6.3 SourceCandidate inspect
-> inspection via Scheduler + handler + snapshot réel

6.4 candidate <-> artifact-dir
-> liaison via Scheduler + handler + store réel
```

La CLI reste autorisée, mais elle ne doit plus devenir le chemin principal durable.
