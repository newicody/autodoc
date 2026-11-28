# Pipeline groupé des deux spécialistes — 0287 r16-r39/r16-r41

Cette unité regroupe les effets qui disposent déjà d'une composition cohérente :

1. préparation de la première visite ;
2. exécution du premier spécialiste ;
3. préparation implicite et exécution du second spécialiste ;
4. persistance des deux analyses puis projection des deux analyses.

Le graphe v2 contient dix tâches au lieu de quatorze. La réduction ne fusionne
pas les objets métier : les deux analyses conservent des `object_ref`,
`artifact_ref`, `specialist_ref`, `visit_ref`, digests et points Qdrant distincts.
La persistance SQL précède toujours OpenVINO/E5 et Qdrant. L'embedding attendu
reste celui de multilingual-e5-small en 384 dimensions.

Les handlers réutilisent les fonctions existantes de première visite, seconde
visite, persistance SQL et double projection. Les entrées sont réhydratées par
un port injecté ; ce port ne choisit ni la priorité, ni le retry, ni la tâche
suivante.

Le Scheduler canonique reste l'unique autorité d'enchaînement. Aucun Scheduler,
Dispatcher, EventBus, laboratoire, connexion SQL, client Qdrant ou moteur
OpenVINO supplémentaire n'est construit. PostgreSQL reste l'autorité durable ;
Qdrant reste une projection et un index de rappel.

VisPy reste observation-only.
