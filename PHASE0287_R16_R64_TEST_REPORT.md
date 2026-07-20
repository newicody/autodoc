# Rapport de tests — 0287 r16-r64

## Périmètre

- noyau continuation + step runner construit sur le port PostgreSQL partagé ;
- réutilisation par identité des transactions r31 et r33 ;
- injection non remplaçable dans le constructeur du step runner ;
- alignement obligatoire avec la composition r16-r63 ;
- échec fermé sans fabriques explicites ;
- absence de nouveau backend, Scheduler et stockage JSON/JSONL.

## Validation réalisée lors de la génération

- compilation Python des sources et tests ajoutés : réussie ;
- test ciblé synthétique du partage de connexion et des identités : réussi ;
- contrôle du diff et de l'archive : réussi.

La génération n'avait pas accès au checkout local `/home/eric/projet/git/autodoc`.
Les portes canoniques ci-dessous doivent donc être exécutées par
`apply_patch_queue.py` sur le dépôt réel avant commit et push :

```bash
PYTHONPATH=src:. /home/eric/python/bin/python -m compileall -q src tests tools
PYTHONPATH=src:. /home/eric/python/bin/python -m pytest -q tests/rules
PYTHONPATH=src:. /home/eric/python/bin/python -m pytest -q
```

Aucune réussite de la suite complète locale n'est revendiquée avant cette
exécution.
