# Première visite du laboratoire amour depuis une recherche GitHub

## But

Cette unité déclenche la première analyse spécialisée à partir de la chaîne déjà
autorisée :

```text
paquet de recherche corrélé
+ demande Scheduler autorisée
+ réponse de route `ready`
→ étude amour typée
→ tâche du premier spécialiste
→ LABORATORY_VISIT_REQUEST
→ Scheduler existant
→ Dispatcher existant
→ laboratoire natif amour
→ analyse conceptuelle et affective
```

## Autorité du contenu

Le titre et le corps de la demande autoritative fournissent l’objectif et le
texte étudié. L’avis Copilot reste présent comme référence consultative mais
n’est jamais utilisé pour remplacer la demande.

## Plusieurs Issues

Un seul handler `LABORATORY_VISIT_REQUEST` est enregistré dans le Dispatcher.
Son résolveur est append-only :

- chaque `study_ref` peut être ajouté une fois;
- chaque `task_ref` peut être ajouté une fois;
- un rejeu identique est accepté;
- une collision avec un contenu différent est refusée.

Ainsi, deux Issues de recherche conservent deux études et deux tâches
distinctes sans remplacer le laboratoire ni son handler.

## Chemin Scheduler

L’exécution utilise exclusivement
`submit_native_love_collaboration_visit(...)`. Cette fonction crée l’événement
typé, appelle `scheduler.emit()` et attend la réponse coopérative du handler.

La nouvelle unité ne démarre pas le Scheduler. Il doit déjà être actif dans les
ports runtime injectés.

## Limites

Cette unité :

- exécute seulement le premier spécialiste;
- ne prépare pas encore le second spécialiste;
- ne produit aucune synthèse globale;
- n’écrit ni SQL ni Qdrant;
- ne publie rien vers GitHub;
- ne crée aucun Scheduler, Dispatcher, EventBus, manager ou daemon;
- n’appelle jamais directement la méthode d’exécution du spécialiste.

L’unité suivante préparera la seconde tâche depuis le résultat exact de la
première analyse, puis la remettra séparément au Scheduler.
