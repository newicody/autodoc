# Rapport 0287 r16-r4-r3-r3-r1

## Objet

Créer le point d'entrée canonique de récupération des artefacts GitHub sans
republication locale du premier avis Copilot.

## Portée

- ajout d'une commande one-shot de fetch seul ;
- réutilisation du scanner/fetcher 0272 ;
- verrou local non bloquant ;
- rapport JSON explicite ;
- aucune mutation distante ;
- aucune exécution du laboratoire dans cette unité.

## Tests à exécuter

```bash
/home/eric/python/bin/python -m compileall -q src tools tests
/home/eric/python/bin/python -m pytest -q \
  tests/rules/test_github_actions_artifact_fetch_once_0287_rule.py
/home/eric/python/bin/python -m pytest -q tests/rules
```

## Critère de sortie

Une exécution `--execute` valide produit `status=artifacts-fetched`, expose les
`ready_runs` du scanner existant et fonctionne sans
`AUTODOC_REMOTE_MUTATION_ALLOWED` ni `AUTODOC_ISSUE_PUBLICATION_ALLOWED`.
