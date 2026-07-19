# Publication et clôture groupées — 0287 r16-r45/r16-r47

Cette unité complète le graphe Scheduler groupé avec trois capacités explicites :
préparer le plan de publication, publier sous contrôle, puis vérifier la fermeture.

Le plan est reconstruit depuis le livrable final et la synthèse réhydratés. La
mutation exige l'approbation opérateur, le digest exact et les trois verrous de
publication. Le publisher existant protège le rejeu par marqueurs et readback.

La publication distante et la persistance de sa preuve SQL sont exécutées dans
le même handler. Ce regroupement ferme la fenêtre de perte entre GitHub et SQL :
si le processus tombe après la mutation distante, le retry obtient un replay
idempotent puis termine la preuve SQL. La dernière tâche relit seulement cette
preuve et ne republie rien.

PostgreSQL demeure l'autorité durable. GitHub reste une surface de publication
et ProjectV2 une projection. Aucun nouveau client GitHub, store SQL, Scheduler,
Dispatcher, EventBus, laboratoire ou moteur de rappel n'est créé.

Le catalogue complet contient dix handlers correspondant exactement aux dix
tâches du graphe groupé. Le Scheduler reste seul propriétaire du choix de tâche,
des retries, des budgets, de l'arrêt et de la clôture de la commande.

VisPy reste observation-only. Il pourra afficher ou agréger les transitions de
publication et de fermeture sans les déclencher ni les modifier.
