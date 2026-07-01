# Changelog — Phase 5.11 — ContextEngine contract lock

## Ajouté

- `doc/CONTEXT_ENGINE_CONTRACT.md`
- `doc/docs/architecture/context/35_context_engine_contract_lock.dot`
- `tests/context/test_context_engine_contract_lock.py`

## Mis à jour

- `doc/docs/architecture/00_global.dot`
- `doc/docs/architecture/context/34_e5_context_engine_intake_audit.dot`

## Contrats verrouillés

- `ContextEngine(registry, scheduler, event_bus)` reste compatible.
- `ContextEngine(inference_context)` reste accepté pour les usages locaux.
- `execute_tick()` retourne le snapshot historique.
- `current_inference_context` expose le dernier `InferenceContext` construit ou attaché.
- `attach_e5_artifact_dir()` et `attach_e5_runtime_context()` restent explicites.

## Frontières

- Pas de modification du Scheduler.
- Pas d'autoload E5.
- Pas de daemon.
- Pas de réseau.
- Pas d'API GitHub.
- Pas de Qdrant.
- Pas de LLM.
- Pas d'appel OpenVINO.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.11 verrouille des contrats existants par documentation et tests anti-régression ; aucune règle de programmation nouvelle n'est nécessaire.
```
