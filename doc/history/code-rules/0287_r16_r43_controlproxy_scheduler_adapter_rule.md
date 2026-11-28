# Règle 0287 r16 r43 — raccordement ControlProxy/Scheduler explicite

Une commande `SCHEDULER_ROUTE_REQUEST` déjà autorisée peut être raccordée au
ControlProxy uniquement par un adaptateur typé qui reçoit la commande du
Scheduler canonique unique. Cet adaptateur ne décide ni l'admission, ni la
sécurité, ni la priorité.

La racine ControlFS doit être explicite et absolue. Le plan de données de route
doit utiliser l'adaptateur `/dev/shm` existant sans fallback implicite. Un
manifeste déjà présent n'est réutilisé que si son identité de route, sa portée,
son TTL, son transport et son dimensionnement correspondent à la commande
autorisée. Le champ `created_at` conserve l'horodatage de la première
matérialisation et ne doit pas rendre invalide un replay ultérieur de la même
route. Toute autre collision échoue fermée.

Le JSON du manifeste ControlFS est une projection de frontière temporaire. Il
est interdit de l'utiliser comme stockage interne canonique, graphe durable,
file Scheduler, file JSONL ou journal JSONL. PostgreSQL reste l'autorité durable et les
objets métier internes restent typés.

Il est interdit à cette unité de construire ou démarrer un Scheduler,
Dispatcher, PriorityQueue, EventBus, thread, processus, daemon ou service
OpenRC. OpenRC reste uniquement l'autorité externe du futur processus Scheduler
`externally-managed`.
