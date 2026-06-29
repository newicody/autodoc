# Phase 3.10 — Test report — E5 query/passage

## Scope

Phase 3.10 ajoute :

- contrat `E5Text` pour `query:` / `passage:` ;
- mini-ranker local `E5LocalRanker` avant Qdrant ;
- option CLI `--role auto|query|passage` ;
- documentation et DOT de navigation.

## Validation sandbox

Depuis `/mnt/data/autodoc_phase3_10_work` :

```bash
python3 -m compileall -q src tests
pytest -q
python3 src/main.py
cd doc && make -f makefile
```

Résultat :

```text
compileall OK
147 passed, 1 skipped in 0.58s
main.py exit code: 0
DOT_OK
```

## Validation locale utilisateur avant phase

Le socle Phase 3.9 / 3.7b a été validé localement :

```text
122 passed, 1 skipped
MISSIPY_RUN_OPENVINO_LOCAL=1 ... test_openvino_e5_local.py -> 1 passed
```

## Notes

- Aucun `.svg` n'est inclus dans le lot.
- Aucun script de patch n'est inclus.
- Aucun changement Scheduler / Dispatcher / ComponentProxy.
- Aucun Qdrant.
- Aucun batch vectoriel optimisé.
