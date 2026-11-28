# Règle r16-r66-r1 — aucun routeur après la décision du Scheduler

Une frontière recevant `snapshot` et `task_ref` depuis
`SchedulerCanonicalBoundedCycle` traite une tâche déjà choisie.

Elle peut relire les objets durables nécessaires à cette tâche et injecter le
bootstrap existant. Elle ne doit jamais :

- parcourir les capacités afin de choisir un fournisseur ;
- résoudre ou choisir un handler ;
- construire un catalogue ou une fabrique de handlers ;
- recalculer un plan d'admission ;
- créer un Scheduler, Dispatcher, EventBus ou registre parallèle ;
- modifier le graphe durable.

La résolution du handler reste exclusivement dans
`SchedulerTaskLaunchPreparationService` à partir du catalogue canonique. La
fabrique explicite ne fait qu'instancier le binding déjà résolu.

Un port d'observation structurel est validé par ses opérations requises. Une
frontière d'intégration ne modifie pas le contrat canonique uniquement pour
rendre possible un contrôle nominal à l'exécution.
