# Changelog — Phase 4.18 — E5 dry-run artifact directory

## Ajouts

- Ajout de `--artifact-dir DIR` à `search`.
- Ajout de `E5SearchArtifactDirectoryPolicy`.
- `--artifact-dir` produit par défaut :
  - `report.json` ;
  - `context.json` ;
  - `consumed_context.json` ;
  - `prompt.json`.
- Les chemins explicites (`--report-file`, `--context-file`, `--consumed-context-file`, `--prompt-file`) restent prioritaires sur les chemins dérivés.
- Le répertoire d'artefacts est préparé dans la bordure CLI avant les écritures atomiques.
- Le message historique `failed to write report` est conservé pour les échecs de `--report-file`.

## Règles

- Aucun nouveau script CLI.
- Pas de LLM.
- Pas de Scheduler.
- Pas de Qdrant.
- Pas d'écriture dans les modules domaine purs.
- Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.18 applique les règles Phase 4.12-r2 et la règle stdlib introduite en 4.14 ; aucune nouvelle guideline n'est nécessaire.
```
