# Application transactionnelle de l’admission — 0287 r16-r31

Cette unité relie le plan pur `r16-r30` à une frontière transactionnelle
injectée. Le Scheduler vivant reste l’unique autorité qui applique une décision
`admitted`.

La séquence verrouillée est :

```text
SchedulerTaskAdmissionPlan
+ SchedulerTaskAdmissionCandidate
+ commande typée
+ SchedulerHandlerCatalog
        ↓
validation de la fenêtre, du budget et du contrat de capacité
        ↓
transition typée ready → running
+ tentative running
+ mutation bornée du budget
+ réservation de ressources
        ↓
transaction atomique injectée
        ↓
SchedulerHandlerLaunchTicket
```

PostgreSQL reste l’autorité durable. Le port transactionnel devra comparer les
versions attendues, enregistrer le budget, la réservation, la tâche, la
tentative, la transition et l’état `running` de la commande dans une seule
transaction, ou tout rollbacker.

Il n’existe aucune file JSON ou JSONL. Aucun handler n’est instancié ni exécuté.
Le Dispatcher n’est pas appelé. EventBus, PassiveSupervisor et VisPy restent des
surfaces d’observation ; VisPy reste observation-only.

Les notices `CREATED` et `STARTED` ne sont pas produites dans cette unité. Elles
seront publiées seulement après création réelle de l’instance du handler par
l’exécuteur contrôlé. Une trace informative ne doit jamais annoncer un objet ou
un démarrage qui n’existe pas encore.

Le ticket porte le type de handler résolu, la tâche `running`, la tentative, la
réservation, la mutation de budget et le reçu de commit. Il ne possède aucun
cycle de vie autonome et ne lance rien.
