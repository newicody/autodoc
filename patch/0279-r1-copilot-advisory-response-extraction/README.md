# 0279-r1 — Copilot advisory response extraction

## Intention

Faire produire le troisième artefact `autodoc-copilot-advisory` en adaptant le
script existant au transport JSONL de GitHub Copilot CLI.

## Portée

- réutilise `run_autodoc_copilot_advisory.py` ;
- active `--output-format=json` et `--stream=off` ;
- extrait récursivement un avis depuis les événements JSONL ;
- conserve la compatibilité JSON direct, bloc Markdown et texte périphérique ;
- valide strictement le contrat métier ;
- calcule le digest sur le JSON métier canonique ;
- maintient `trusted=false` et `usable_as_authority=false` ;
- interdit les outils read/write/shell/url/memory ;
- n'ajoute aucune dépendance Python externe.

## Base visée

```text
6fd903e40421af932d607a51f2d917d03237c2ef
```

## Application

```bash
python apply_patch_queue.py \
  --patch 0279-r1-copilot-advisory-response-extraction \
  --dry-run \
  --allow-dirty
```

Puis, si le dry-run passe :

```bash
python apply_patch_queue.py \
  --patch 0279-r1-copilot-advisory-response-extraction \
  --commit \
  --push \
  --allow-dirty
```

## Tests ciblés

```bash
PYTHONPATH=src:. python -m compileall -q templates/github/scripts tests/tools
PYTHONPATH=src:. pytest -q \
  tests/tools/test_github_copilot_advisory_response_extraction_0279.py \
  tests/rules/test_copilot_advisory_response_extraction_0279_rule.py \
  tests/rules/test_github_dual_artifact_actions_workflow_0275_rule.py \
  tests/tools/test_github_copilot_advisory_optional_0277.py
```

## Limites

Aucune mutation distante, SQL, Qdrant, Scheduler ou `Scheduler.run()` n'est
introduite. Le test réel final reste un nouveau run GitHub Actions produisant
les trois artefacts.
