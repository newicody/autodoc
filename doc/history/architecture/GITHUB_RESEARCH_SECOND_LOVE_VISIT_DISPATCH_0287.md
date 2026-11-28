# Seconde analyse spécialiste depuis la première visite GitHub

## But

Cette unité ferme la collaboration à deux spécialistes sans fusionner leurs
productions :

```text
première visite terminée
→ résultat de première analyse reconstruit et validé
→ `prepare_second_specialist_collaboration`
→ artefact de première analyse avec digest
→ tâche `love.relational_dynamics`
→ ajout append-only dans le résolveur existant
→ seconde `LABORATORY_VISIT_REQUEST`
→ Scheduler existant
→ second spécialiste
→ seconde analyse distincte
```

## Provenance

La seconde tâche transporte :

- la référence de la première analyse;
- l’artefact de cette analyse;
- son empreinte SHA-256;
- la visite parente;
- la même conversation;
- les références de contexte et de preuve déjà validées.

Le résolveur refuse une collision portant la même référence avec un contenu
différent.

## Deux visites distinctes

La première visite n’est pas rejouée. La seconde visite possède :

- son propre `visit_ref`;
- son propre `task_ref`;
- `parent_visit_ref` égal à la première visite;
- le spécialiste `love.relational-dynamics-analyst`;
- une nouvelle soumission au Scheduler.

Le spécialiste 1 ne lance donc jamais directement le spécialiste 2.

## Limites

Cette unité :

- ne construit aucun Scheduler, Dispatcher ou EventBus;
- ne démarre pas le Scheduler;
- n’appelle pas directement le provider;
- ne produit pas encore la synthèse de liaison;
- ne persiste pas encore les analyses dans SQL;
- ne projette rien dans Qdrant;
- ne publie rien vers GitHub.

La prochaine unité conservera les deux analyses comme productions distinctes
dans l’autorité durable avant leur projection et leur synthèse.
