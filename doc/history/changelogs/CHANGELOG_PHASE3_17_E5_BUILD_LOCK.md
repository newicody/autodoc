# CHANGELOG Phase 3.17 — E5 build lock

## Ajouté

- `src/inference/e5_corpus_lock.py`
  - `E5CorpusBuildLock`
  - `E5CorpusBuildLockInfo`
  - `E5CorpusBuildLockError`
  - `build_e5_corpus_lock_path()`
- Tests unitaires du verrou fichier exclusif.
- Tests CLI confirmant :
  - lock créé puis supprimé,
  - refus si lock existant,
  - option `--no-lock` disponible.
- Graphe `doc/docs/architecture/inference/55_e5_build_lock.dot`.

## Modifié

- `build_e5_corpus.py` utilise le verrou par défaut via `inference.e5_corpus_cli`.
- La sortie de build indique `lock_enabled` et `lock_path`.
- `README.md` et `ARCHITECTURE_LAYERS.md` documentent l'état Phase 3.17.
- Graphes DOT inference/tests mis à jour.

## Non changé

- Pas de changement Scheduler.
- Pas de Qdrant.
- Pas de SVG inclus.
- Pas de changement du schéma `missipy.e5.corpus.v1`.
- Pas de changement du modèle E5 ni du runtime OpenVINO.
