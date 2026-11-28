# Création et armement des handlers Scheduler — 0287 r16-r32

Cette unité transforme un `SchedulerHandlerLaunchTicket` déjà commité en une
instance réelle de handler, puis en un bail d’exécution typé. La fabrique est
injectée explicitement et ne choisit jamais le handler : le binding exact a
déjà été résolu par le Scheduler avec `command_type`, `capability_ref` et
`contract_version`.

```text
commit PostgreSQL du lancement
→ create()
→ instance réelle
→ notice CREATED issue des attributs avancés du handler
→ start()
→ notice STARTED
→ contexte d’exécution typé
→ arrêt avant handler.execute()
```

La métaclasse reste une abstraction de contrat et ne lance rien. La fabrique
ne contient aucun registre global et les builders sont assemblés explicitement
au bootstrap avec leurs dépendances injectées.

Les notices utilisent `HandlerInformation` et les attributs avancés du
descripteur. Une panne du sink informatif est enregistrée dans un reçu
observation-only mais ne modifie jamais la décision durable du Scheduler. Le
futur PassiveSupervisor/VisPy pourra rendre persistantes ou agréger les
apparitions et disparitions des instances; VisPy reste observation-only.

Cette unité n’appelle ni `execute()`, ni Dispatcher, ni EventBus, ni laboratoire,
ni SQL, ni Qdrant et ne crée aucun Scheduler. PostgreSQL reste l’autorité durable.
Aucune file JSON ou JSONL et aucun stockage JSON interne ne sont ajoutés.

Les notices `SUCCEEDED`, `FAILED`, `CANCELLED` et `CLOSED`, ainsi que la
libération des ressources et la transition durable de la tâche, appartiennent à
l’exécuteur contrôlé de l’unité suivante.
