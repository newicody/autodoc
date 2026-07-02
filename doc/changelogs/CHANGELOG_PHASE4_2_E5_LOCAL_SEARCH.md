# Changelog Phase 4.2 — E5 local search dev-ready

## Objectif

La Phase 4.2 fige l'usage développeur de la recherche E5 locale sur le corpus du dépôt.

Elle ne crée pas une nouvelle brique moteur. Elle documente et valide le flux déjà opérationnel :

```text
sources repo .md/.txt
-> rebuild_e5_corpus.py
-> staging
-> validation
-> promotion atomique
-> search_e5_corpus.py
-> rapport texte ou JSON
```

## Validé

- `rebuild_e5_corpus.py --help` fonctionne.
- Reconstruction du corpus repo vers `/tmp/autodoc_e5_corpus.json`.
- Corpus généré : 218 chunks.
- Promotion finale : `promoted: True`.
- Écriture atomique : `atomic_write: True`.
- Verrou actif : `lock_enabled: True`.
- Validation search active : `validation_search: True`.
- Recherche texte locale fonctionnelle.
- Recherche JSON locale fonctionnelle.
- Résultats avec score, id, source, lignes, chunk et extrait.
- Requêtes de validation pertinentes sur :
  - rebuild sûr ;
  - Scheduler / telemetry / code_rule ;
  - rapport avec source/lignes/extrait ;
  - OpenVINO multilingual-e5-small local.

## Non modifié

- Pas de Scheduler.
- Pas de Qdrant.
- Pas de format corpus.
- Pas de runtime OpenVINO supplémentaire.
- Pas de DOT.
- Pas de SVG.
- Pas de script de patch.

## Raison

Avant d'introduire une base vectorielle externe ou un service de recherche persistant, la recherche locale doit être exploitable, reproductible et lisible depuis le terminal.

La Phase 4.2 transforme donc le prototype E5 local en procédure de développement de référence.
