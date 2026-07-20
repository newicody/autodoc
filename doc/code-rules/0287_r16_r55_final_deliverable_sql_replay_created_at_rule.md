# Règle 0287 r16 r55 — rejeu immuable du livrable final SQL

Pour une référence déterministe de livrable final déjà matérialisée, une relance
ne doit pas remplacer l'horodatage initial par l'heure de la nouvelle tentative.

Le constructeur du plan doit relire l'artefact et la révision dans PostgreSQL,
conserver leur `created_at` commun, puis soumettre les objets reconstruits au
contrôle immuable exact déjà existant.

Une paire historique dont les horodatages divergent doit être refusée avant
toute écriture. Il est interdit de contourner ce contrôle en ignorant
`created_at`, en modifiant la comparaison des mappings, en supprimant les
entités, ou en utilisant un fichier JSON / une file JSONL comme autorité.

Cette règle ne change pas les responsabilités : Scheduler canonique unique,
PostgreSQL autorité durable, Qdrant projection, ControlFS plan rapide et GitHub
frontière externe contrôlée.
