# Changelog — Phase 4.17 — E5 prompt file CLI

## Ajouts

- Ajout de sorties optionnelles à `search` :
  - `--consumed-context-file FILE` ;
  - `--prompt-file FILE` ;
  - `--context-max-chars INT` ;
  - `--context-max-items INT` ;
  - `--context-include-scores` ;
  - `--prompt-system-instruction TEXT` ;
  - `--prompt-answer-instruction TEXT`.
- `search` peut maintenant produire en une passe :
  - rapport de recherche ;
  - bundle de contexte ;
  - contexte consommé ;
  - paquet de prompt.

## Règles

- Aucun LLM n'est appelé.
- Aucun Scheduler n'est modifié.
- Aucun Qdrant n'est introduit.
- Aucun format corpus `missipy.e5.corpus.v1` n'est modifié.
- L'écriture JSON reste centralisée dans `report_io.write_json_report_atomic()`.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.17 applique les règles Phase 4.12-r2 et la règle stdlib introduite en 4.14 ; aucune nouvelle guideline n'est nécessaire.
```
