# Dépendances

Le dépôt ne fournit pas à sa racine un manifeste Python standard unique permettant d'énumérer et verrouiller toutes les dépendances. Les versions doivent être établies à partir des environnements déployés et des configurations dédiées.

| Composant | Rôle | État |
|---|---|---|
| Python | Runtime | Présent |
| PostgreSQL | Autorité durable | Utilisé par les chemins de contexte/recherche concernés |
| Qdrant | Projection vectorielle et rappel | Adaptateurs et chemins présents |
| OpenVINO | Inférence locale / embeddings | Adaptateurs présents |
| multilingual-e5-small | Embeddings E5 384-D | Profil canonique |
| GitHub API, Actions, Projects v2 | Workflow, revue et projection externes | Intégrations présentes selon configuration |
| ControlFS / POSIX SHM | Transport local explicite | Adaptateurs présents, environnement requis |
| Graphviz | Rendu des graphes .dot | Dépendance documentaire |
| VisPy | Visualisation | Ne pas présumer un renderer runtime complet |

Le dépôt contient `config/requirements-qdrant-client-0271.txt`, qui n'est pas un manifeste global. Les bibliothèques Python runtime, test et développement doivent être inventoriées depuis les imports et compositions réellement utilisées avant de créer un verrou. Les services externes ne sont pas des packages Python.

Règles : dépendances rattachées à leur unité ; extras optionnels séparés ; versions verrouillées dans un manifeste maintenu ; profil E5 384-D contractuel ; aucune dépendance d'observation ne doit introduire une autorité de commande parallèle.
