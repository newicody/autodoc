# Rapport de tests — 0287 r16-r65

## Périmètre

- store de continuation DB-API sur la connexion PostgreSQL partagée ;
- topologie du graphe en tables normalisées ;
- relecture des tâches partagées r31/r33 ;
- commit optimiste et idempotent des promotions ;
- runner lancement → handler → exécution → clôture ;
- installation des deux références `module:function` ;
- maintien de l'échec fermé pour les fournisseurs métier r16-r66.

## Validation de génération

- `python -m compileall -q src tests` : réussi ;
- tests de règles r16-r65 : `4 passed` ;
- contrôle syntaxique des deux nouveaux modules : réussi ;
- contrôle du diff : réussi.

La session de génération ne dispose pas du checkout local complet
`/home/eric/projet/git/autodoc`. Les deux tests fonctionnels ajoutés sont donc
fournis pour la suite réelle, mais leur réussite n'est pas revendiquée avant
l'application du bundle.

## Portes canoniques à l'application

```bash
PYTHONPATH=src:. /home/eric/python/bin/python -m compileall -q src tests tools
PYTHONPATH=src:. /home/eric/python/bin/python -m pytest -q tests/rules
PYTHONPATH=src:. /home/eric/python/bin/python -m pytest -q \
  tests/context/test_github_research_love_postgresql_continuation_store_0287.py \
  tests/context/test_github_research_love_transactional_step_runner_0287.py
PYTHONPATH=src:. /home/eric/python/bin/python -m pytest -q
```
