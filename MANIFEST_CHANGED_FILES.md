# Manifest — Phase 4.13 unified E5 command surface

## Fichiers modifiés

- `README.md`
- `MANIFEST_CHANGED_FILES.md`
- `PHASE4_13_TEST_REPORT.md`
- `doc/CHANGELOG_PHASE4_13_E5_UNIFIED_COMMAND_SURFACE.md`
- `doc/docs/architecture/inference/66_e5_code_style_alignment.dot`
- `doc/docs/architecture/inference/67_e5_unified_command_surface.dot`
- `src/inference/e5_tool_cli.py`
- `tests/inference/test_e5_tool_cli.py`
- `tests/rules/test_e5_code_rule_alignment.py`
- `tools/e5.py`
- `tools/embed_e5.py`
- `tools/rank_e5.py`
- `tools/build_e5_corpus.py`
- `tools/search_e5_corpus.py`
- `tools/rebuild_e5_corpus.py`
- `tools/inspect_e5_corpus.py`

## Nature de la phase

- Ajout d'une façade unique `tools/e5.py` pour les sous-commandes E5.
- Conservation et normalisation des scripts existants comme wrappers de compatibilité.
- Dispatch typé via `E5ToolCommand`.
- Routage explicite via `E5ToolDispatchPolicy`.
- Aucun changement du format corpus.
- Aucune modification Scheduler.
- Aucun Qdrant.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: l'addendum Phase 4.12-r2 couvre déjà la réduction de surface CLI ; 4.13 applique cette règle sans en créer une nouvelle.
```

## Exclusions maintenues

- Aucun `.svg` livré.
- Aucun `__pycache__` livré.
- Aucun script de patch.
- Aucun fichier généré.
