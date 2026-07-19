# Rappel, synthèse et livrable groupés — 0287 r16-r42/r16-r44

Cette unité adapte au Scheduler trois compositions existantes :

1. rappel hybride de deux projections et réhydratation SQL exacte ;
2. synthèse de liaison distincte, sans modifier les analyses sources ;
3. construction puis persistance PostgreSQL du livrable final local.

Les étapes restent trois tâches Scheduler distinctes. Le regroupement concerne
la rustine et le bootstrap, pas la transaction métier. Chaque handler reçoit une
commande typée réhydratée par un port injecté et vérifie la corrélation avec le
`work_package_ref` de la commande GitHub.

Le catalogue complet expose sept capacités : préparation de visite, deux
spécialistes, persistance/projection de la paire, rappel, synthèse et livrable.
Les trois capacités de publication et clôture restent volontairement absentes.

PostgreSQL demeure l'autorité durable. Qdrant reste un index de projection et de
rappel. OpenVINO/E5 produit une requête `query:` en 384 dimensions. Le livrable
est persisté localement avant toute préparation ou mutation GitHub.

Aucun Scheduler, Dispatcher, EventBus, laboratoire, connexion SQL, client
Qdrant ou moteur OpenVINO supplémentaire n'est construit. VisPy reste
observation-only.
