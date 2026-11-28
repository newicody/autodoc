# Continuation PostgreSQL et runner transactionnel — 0287 r16-r65

## Objet

Cette unité fournit les deux fabriques laissées vides par r16-r64. Elles sont
construites sur la fondation OpenRC déjà ouverte et ne possèdent ni connexion,
ni Scheduler, ni processus.

## Continuation relationnelle

Le store conserve la définition du graphe dans des tables normalisées : ordre
des tâches, barrières, membres de barrières, portes de branche et règles. Les
objets `SchedulerTask` sont relus depuis `scheduler_tasks` ainsi que les tables
de dépendances, contextes et preuves déjà partagées avec les transactions r31
et r33.

La révision durable est calculée à partir des transactions effectivement
commises pour la commande :

- une promotion du graphe compte pour une révision ;
- un lancement SQL compte pour une révision ;
- une clôture SQL compte pour une révision.

Cette règle permet à une relecture effectuée après un redémarrage de reconstruire
le graphe courant sans cache local ni document sérialisé. `put_initial_graph`
enregistre une seule fois le graphe typé. `commit_promotion` compare la révision
et le digest relus, applique les mutations avec contrôle optimiste, insère les
transitions et écrit un reçu de promotion immuable.

## Runner transactionnel

Le runner reçoit un fournisseur typé pour une tâche déjà sélectionnée par le
Scheduler. Le fournisseur réhydrate la commande, le candidat, le plan
d'admission, le catalogue, la fabrique de handler et les ports de résultat,
échec, fermeture et observation.

Le runner appelle exclusivement la chaîne canonique existante :

1. `SchedulerTaskLaunchPreparationService.apply` ;
2. `SchedulerHandlerInstanceLifecycleService.create` ;
3. `SchedulerHandlerInstanceLifecycleService.start` ;
4. `SchedulerHandlerExecutionService.execute` ;
5. `SchedulerHandlerExecutionTransaction.commit_outcome`.

Il retourne l'`SchedulerHandlerExecutionOutcome` attendu par
`SchedulerCanonicalBoundedCycle`. Le reçu local `last_commit` relie le lancement,
l'outcome et la clôture, sans devenir une nouvelle autorité.

## Limite volontaire

La fabrique des quatre fournisseurs métier r16-r63 reste vide. Le service OpenRC
continue donc d'échouer fermé jusqu'à r16-r66. Cette unité ne déclenche aucune
publication distante et ne prétend pas encore fournir le smoke complet.

PostgreSQL reste l'autorité durable, Qdrant une projection/rappel, OpenVINO E5
reste à 384 dimensions et le Scheduler canonique reste unique.
