# Autodoc — Phase 5.4-r1

Correction ciblée du helper de test `tests/context/test_e5_local_context_runtime.py`.

`tmp_path` est déjà un dossier existant. Le helper `_write_artifacts()` doit donc accepter un répertoire déjà créé par pytest.

## Changement

```python
directory.mkdir(parents=True, exist_ok=True)
```

## Tests recommandés

```bash
PYTHONPATH=src pytest -q tests/context/test_e5_local_context_runtime.py
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.
