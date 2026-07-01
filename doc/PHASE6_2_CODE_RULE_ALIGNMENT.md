
# Phase 6.2 — Code rule alignment

## Décision

`doc/code_rule.md` a été relu avant la Phase 6.2.

Aucune mise à jour de règle n'est nécessaire : la phase applique l'addendum Phase 6-r1 en ajoutant une capacité minuscule mais réelle qui traverse le Scheduler.

## Chemin vivant ajouté

```text
SourceCandidateReviewCommand
-> EventType.SOURCE_CANDIDATE_REVIEW
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> SourceCandidateReviewHandler
-> SourceCandidateStore JSON réel en lecture seule
-> SourceCandidateReviewResult
-> EventType.SOURCE_CANDIDATE_REVIEW_RESULT
-> EventBus / Request.reply
```

## Frontières maintenues

- Le Scheduler ne contient aucune logique SourceCandidate.
- Le CLI de review est un adaptateur opérateur.
- Le store local reste la source autoritative.
- GitHub reste hors scope.
- Aucune dépendance externe n'est ajoutée.
