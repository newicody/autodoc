# Changelog — Phase 4.12-r2 E5 code style realignment

## Correction r2

La première proposition 4.12 réécrivait trop largement `doc/code_rule.md`.
La version r2 conserve l'ancien fichier comme base et ajoute seulement un addendum court d'application aux phases E5.

## Ajout principal

- `doc/code_rule.md` conserve la philosophie micro-kernel initiale.
- Ajout d'un addendum `Phase 4.12-r2` : les CLI E5 sont des adaptateurs temporaires, pas des exceptions au noyau.
- Les fonctions E5 réalignées utilisent des `Command` dataclasses, des `Policy` dataclasses et un writer JSON centralisé.

## Fichiers techniques

- `src/inference/e5_cli_contracts.py` : commandes et politiques E5.
- `src/inference/report_io.py` : écriture atomique de rapports JSON.
- `src/inference/e5_corpus_cli.py` : build/search alignés sur commandes/politiques.
- `src/inference/e5_rebuild_cli.py` : rebuild aligné sur commandes/politiques.
- `src/inference/e5_corpus_inspect_cli.py` : inspect aligné sur commande/politique.

## Tests

- `tests/inference/test_e5_cli_contracts.py`
- `tests/inference/test_report_io.py`
- `tests/rules/test_e5_code_rule_alignment.py`

## code_rule

```text
code_rule_review: done
code_rule_update_required: true
reason: addendum court E5, sans remplacer la philosophie initiale
```
