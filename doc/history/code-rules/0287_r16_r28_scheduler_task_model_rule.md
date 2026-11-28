# Règle — modèle des tâches Scheduler 0287 r16-r28

## Séparation commande / tâche / tentative

- Une commande est la mission durable.
- Une tâche est une unité exécutable créée par le Scheduler.
- Une tentative est l'exécution concrète d'un handler pour une tâche.
- Un handler ne crée pas directement la tâche suivante.

## Objets internes

Utiliser des classes immuables typées. Ne pas utiliser JSON, JSONL ou des dictionnaires comme autorité interne. PostgreSQL sera l'autorité durable des tâches, transitions, tentatives, résultats et échecs.

## Transitions

- Refuser toute transition depuis un état terminal.
- Incrémenter `state_version` à chaque mutation logique.
- Produire une `SchedulerTaskTransition` digestée.
- Exiger une tentative pour `ready → running`.
- Exiger un résultat corrélé pour `running → completed`.
- Exiger un échec corrélé pour `running → failed/retry-wait`.
- Ne planifier un retry que si l'échec est rejouable et que le budget de tentatives reste positif.

## Dépendances

- Refuser l'auto-dépendance et les doublons.
- Ne rendre une tâche `ready` que lorsque toutes les dépendances sont satisfaites.
- Distinguer dépendance de réussite et dépendance de terminaison.

## Effets de bord interdits

Le modèle ne doit :

- démarrer ou modifier aucun Scheduler ;
- appeler aucun Dispatcher ou handler ;
- publier aucun EventBus ;
- ouvrir aucune connexion SQL ou Qdrant ;
- manipuler `/dev/shm` ou ControlProxy ;
- exécuter aucun laboratoire ou spécialiste ;
- produire aucune mutation GitHub ;
- afficher aucun texte automatiquement.
