# Phase 4.13 — test report

## Objet

Réduction de surface CLI E5 par ajout d'une façade unique `tools/e5.py` et d'un dispatch typé `E5ToolCommand` / `E5ToolDispatchPolicy`.

## Vérifications effectuées dans l'environnement de génération

```text
python -m py_compile \
  src/inference/e5_tool_cli.py \
  tools/e5.py \
  tools/embed_e5.py \
  tools/rank_e5.py \
  tools/build_e5_corpus.py \
  tools/search_e5_corpus.py \
  tools/rebuild_e5_corpus.py \
  tools/inspect_e5_corpus.py \
  tests/inference/test_e5_tool_cli.py \
  tests/rules/test_e5_code_rule_alignment.py
```

Résultat : OK.

```text
PYTHONPATH=src pytest -q tests/inference/test_e5_tool_cli.py tests/rules/test_e5_code_rule_alignment.py
```

Résultat : `10 passed`.

## Tests complets attendus localement

```bash
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Validation DOT

```bash
dot -Tsvg doc/docs/architecture/inference/66_e5_code_style_alignment.dot >/tmp/66_e5_code_style_alignment.svg
dot -Tsvg doc/docs/architecture/inference/67_e5_unified_command_surface.dot >/tmp/67_e5_unified_command_surface.svg
rm -f /tmp/66_e5_code_style_alignment.svg /tmp/67_e5_unified_command_surface.svg
```

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: la règle de réduction de surface CLI existe déjà dans doc/code_rule.md depuis Phase 4.12-r2 ; 4.13 l'applique.
```

## Limite honnête

L'environnement de génération ne contient pas tout le dépôt Python importable. Les tests complets doivent être validés dans le dépôt local.
