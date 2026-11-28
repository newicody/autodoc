# Phase 4.7 — Test report

## Scope

Phase 4.7 ajoute un mode gate optionnel aux diagnostics de corpus E5 locaux.

La phase reste hors Scheduler, hors Qdrant, en lecture seule, et conserve le format corpus existant.

## Commandes à exécuter

```bash
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

Validation DOT :

```bash
dot -Tsvg doc/docs/architecture/inference/60_e5_corpus_diagnostics.dot >/tmp/60_e5_corpus_diagnostics.svg
dot -Tsvg doc/docs/architecture/inference/61_e5_corpus_diagnostic_gate.dot >/tmp/61_e5_corpus_diagnostic_gate.svg
rm -f /tmp/60_e5_corpus_diagnostics.svg /tmp/61_e5_corpus_diagnostic_gate.svg
```

## Résultats attendus

- Tests inference : verts.
- Tests rules : verts.
- Suite complète : verte avec le skip OpenVINO local habituel si le modèle réel n'est pas activé.
- DOT : syntaxe valide.

## Couverture ajoutée

- Gate moteur qui passe quand les seuils sont respectés.
- Gate moteur qui échoue sur `min_chunks`.
- Gate moteur qui échoue avec `fail_on_warning`.
- Validation des seuils négatifs.
- Parser CLI avec options gate.
- Code retour `2` sur gate violé.
- Sortie JSON incluant `gate` quand un seuil est actif.

## Hors périmètre

- Aucun Scheduler.
- Aucun Qdrant.
- Aucun changement de format corpus.
- Aucune promotion automatique.
- Aucun SVG versionné.
- Aucun script de patch.
