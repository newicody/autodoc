# CHANGELOG Phase 3.16 — E5 atomic corpus build

## Ajouté

- `E5CorpusJsonStore.write_atomic()` pour écrire un corpus dans un fichier temporaire voisin, valider le JSON, puis remplacer la cible uniquement après succès.
- `atomic_temp_path()` pour produire un chemin temporaire stable et déterministe.
- Tests de roundtrip atomique, overwrite contrôlé et non-remplacement de la cible quand la validation échoue.

## Modifié

- `build_e5_corpus.py` utilise maintenant l'écriture atomique via `run_build_async`.
- La sortie CLI de build contient `atomic_write: True`.
- Documentation Phase 3.16 et schéma DOT dédié.

## Non modifié

- Aucun changement Scheduler, Dispatcher, ComponentProxy ou PolicyEngine.
- Aucun Qdrant.
- Aucun changement de schéma JSON public : `missipy.e5.corpus.v1` reste utilisé.
