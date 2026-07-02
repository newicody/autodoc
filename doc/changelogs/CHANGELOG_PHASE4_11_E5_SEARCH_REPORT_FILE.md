# Changelog Phase 4.11 — E5 search report file

## Objectif

La Phase 4.11 ajoute un rapport JSON optionnel à la recherche E5 locale.

Elle complète le rapport de rebuild Phase 4.10 avec l'artefact équivalent côté requête utilisateur.

## Ajouté

- Option CLI `search_e5_corpus.py --report-file FILE`.
- Écriture JSON stable du résultat de recherche.
- Écriture atomique via fichier temporaire voisin puis remplacement final.
- Validation de `--report-file` avant lecture du corpus et construction du modèle.
- Gestion d'erreur explicite si le rapport ne peut pas être écrit.

## Comportement

Le rapport contient la projection JSON existante du `E5SearchReport` :

```text
query
prefixed_query
index
model
backend
tokenizer
dimension
hit_count
hits
```

Le rapport est écrit uniquement si la recherche réussit.

## Non modifié

- Pas de Scheduler.
- Pas de Qdrant.
- Pas de changement du format corpus.
- Pas de modification de ranking.
- Pas de changement du contrat `query:` / `passage:`.
- Pas de SVG versionné.

## Raison

Le prototype doit pouvoir conserver une recherche locale comme artefact stable pour audit, debug, future interface HTML ou workflow question -> contexte.
