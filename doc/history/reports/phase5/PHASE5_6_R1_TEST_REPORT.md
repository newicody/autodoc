# Test report — Phase 5.6-r1 — ContextEngine compatibility

## Correction

La phase corrige la régression suivante :

```text
TypeError: ContextEngine.__init__() takes from 1 to 2 positional arguments but 4 were given
```

Le `Scheduler` conserve son contrat historique :

```python
ContextEngine(registry, self, event_bus)
```

## Vérifications effectuées dans le sandbox de packaging

```text
py_compile src/context/engine.py: OK
aucun SVG
aucun __pycache__ conservé
aucun script patch
archive .tar.gz
```

## Tests à lancer dans le dépôt utilisateur

```bash
PYTHONPATH=src pytest -q tests/context/test_context_engine.py::test_context_engine_uses_event_path_for_snapshot
PYTHONPATH=src pytest -q tests/context/test_e5_context_engine_intake.py
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.6-r1 restaure une compatibilité de constructeur ContextEngine sans nouvelle règle de programmation.
```
