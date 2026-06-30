# Manifest — Phase 4.12-r2 E5 total code_rule-preserving realignment

## Fichiers modifiés

- `README.md`
- `MANIFEST_CHANGED_FILES.md`
- `PHASE4_12_TEST_REPORT.md`
- `PHASE4_12_CODE_STYLE_AUDIT.md`
- `doc/code_rule.md`
- `doc/CHANGELOG_PHASE4_12_E5_CODE_STYLE_REALIGNMENT.md`
- `doc/docs/architecture/inference/65_e5_search_report_file.dot`
- `doc/docs/architecture/inference/66_e5_code_style_alignment.dot`
- `src/inference/e5_cli_contracts.py`
- `src/inference/report_io.py`
- `src/inference/e5_corpus_cli.py`
- `src/inference/e5_rebuild_cli.py`
- `src/inference/e5_corpus_inspect_cli.py`
- `tests/inference/test_e5_cli_contracts.py`
- `tests/inference/test_report_io.py`
- `tests/rules/test_e5_code_rule_alignment.py`

## Nature de la correction r2

- Conservation de l'ancien `doc/code_rule.md` comme socle.
- Ajout d'un addendum court d'application aux phases E5.
- Suppression de la formulation trop permissive `Outillage CLI hors kernel`.
- Maintien du réalignement technique : commandes, politiques, résultats, IO isolée.

## Exclusions maintenues

- Aucun `.svg` livré.
- Aucun `__pycache__` livré.
- Aucun script de patch.
- Aucun Qdrant.
- Aucune modification Scheduler.
- Aucun changement de schéma corpus.
