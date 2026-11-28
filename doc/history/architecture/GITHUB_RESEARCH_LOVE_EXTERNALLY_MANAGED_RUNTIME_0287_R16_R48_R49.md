# Runtime de recherche « amour » géré extérieurement — 0287 r16-r48-r49

OpenRC possède le processus, le Scheduler canonique et son redémarrage. Cette
unité n'ajoute ni daemon, ni thread, ni boucle autonome, ni second Scheduler.

Un tick borné suit la chaîne suivante :

```text
commande PostgreSQL pending
→ claim atomique par le Scheduler déjà running
→ cycle canonique borné
→ handlers du bootstrap complet (10 capacités)
→ commits métier PostgreSQL
→ flush des notices temporelles
```

Les notices `CREATED`, `STARTED`, `SUCCEEDED`, `FAILED`, `CANCELLED` et
`CLOSED` sont tamponnées pendant l'exécution, puis projetées dans la table
relationnelle `scheduler_handler_temporal_observations`. Cette table permet la
lecture individuelle et l'agrégation par période, handler, capacité, tâche,
commande ou phase.

La persistance d'observation se produit après le commit métier. Une panne de
cette projection est rapportée séparément et ne réécrit jamais le résultat de
la tâche. PassiveSupervisor et VisPy pourront lire ces traces, mais ne peuvent
ni réclamer une commande, ni choisir une tâche, ni lancer un handler.

VisPy reste observation-only.

Le cycle corrige aussi le préfixe du résultat d'exécution : l'exécuteur produit
`handler-outcome:` et la continuation canonique doit valider exactement ce
préfixe.
