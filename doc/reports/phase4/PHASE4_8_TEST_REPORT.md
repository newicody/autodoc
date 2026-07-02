# Phase 4.8 — Test report

## Scope

Phase 4.8 ajoute un gate diagnostic optionnel au rebuild sûr du corpus E5.

La phase reste hors Scheduler, hors Qdrant et conserve le format corpus existant.

## Commandes à exécuter

```bash
PYTHONPATH=src pytest -q tests/inference
```

```bash
PYTHONPATH=src pytest -q tests/rules
```

```bash
PYTHONPATH=src pytest -q
```

```bash
dot -Tsvg doc/docs/architecture/inference/61_e5_corpus_diagnostic_gate.dot >/tmp/61_e5_corpus_diagnostic_gate.svg
dot -Tsvg doc/docs/architecture/inference/62_e5_rebuild_diagnostic_gate.dot >/tmp/62_e5_rebuild_diagnostic_gate.svg
rm -f /tmp/61_e5_corpus_diagnostic_gate.svg /tmp/62_e5_rebuild_diagnostic_gate.svg
```

## Validations attendues

- `rebuild_e5_corpus.py` accepte les options de gate diagnostic.
- `--min-chunks` bloque la promotion si le candidat contient trop peu de chunks.
- `--keep-staging` conserve un candidat qui échoue au gate.
- `--fail-on-warning` bloque un candidat contenant des avertissements diagnostic.
- La sortie JSON inclut `diagnostic_gate` quand un seuil est actif et passe.
- Les seuils négatifs sont rejetés avec le code retour `2`.
- Les tests d'inférence restent verts.
- Les règles d'architecture restent vertes.
- La suite complète reste verte.

## Hors périmètre

- Aucun Scheduler.
- Aucun Qdrant.
- Aucun changement de format corpus.
- Aucun SVG versionné.
- Aucun script de patch.
