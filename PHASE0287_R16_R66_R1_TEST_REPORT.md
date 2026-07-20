# Rapport de tests — 0287 r16-r66-r1

## Périmètre

- réhydratation d'une tâche `ready` déjà choisie ;
- relecture de la commande SQL par `command_ref` ;
- relecture d'une admission déjà décidée ;
- réutilisation exacte du catalogue et de la fabrique des dix handlers ;
- absence de routeur de capacités et d'autorité parallèle ;
- correction du contrôle r16-r65 par vérification structurelle de la méthode
  `publish`, sans modifier le contrat canonique du handler.

## Validation de génération

- `python -m compileall -q` sur les nouveaux fichiers : réussi ;
- tests de règles exécutables sur le bundle synthétique : réussi ;
- contrôle statique d'absence de résolution de capacité : réussi ;
- suppression du hunk fragile sur `scheduler_handler_contract.py` : vérifiée ;
- `git diff --check` : réussi.

La session de génération ne possède pas le checkout local complet. Les tests
fonctionnels sont donc fournis pour l'exécution réelle par
`apply_patch_queue.py`, sans revendiquer leur résultat avant application.

## Portes canoniques à l'application

```bash
PYTHONPATH=src:. /home/eric/python/bin/python -m compileall -q src tests tools
PYTHONPATH=src:. /home/eric/python/bin/python -m pytest -q tests/rules
PYTHONPATH=src:. /home/eric/python/bin/python -m pytest -q \
  tests/context/test_github_research_love_canonical_ready_task_binding_0287.py
PYTHONPATH=src:. /home/eric/python/bin/python -m pytest -q
```
