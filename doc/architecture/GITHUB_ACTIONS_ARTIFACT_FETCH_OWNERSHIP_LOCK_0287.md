# Verrou de propriété du premier avis Copilot — 0287 r16-r4-r3-r3-r1

## Décision

Le dépôt `newicody/projects` est l'unique propriétaire du premier commentaire
Copilot produit à partir d'une Issue. Le serveur Autodoc récupère ensuite les
artefacts du run, mais ne republie pas ce premier avis.

## Chemin canonique local

```text
workflow Projects
→ commentaire Copilot initial
→ authoritative_request + copilot_advisory + run_manifest
→ fetch local Autodoc
→ corrélation ready_run
→ contrôle d'admissibilité ultérieur
→ Scheduler existant
→ laboratoire
```

Le nouveau point d'entrée canonique est :

```text
tools/run_github_actions_artifact_fetch_once_0287.py
```

Il réutilise le scanner/fetcher existant
`run_github_actions_artifact_scan_once_live_0272.py` et n'appelle aucun éditeur
de commentaire d'Issue.

## Compatibilité

Le cycle historique
`run_github_actions_artifact_copilot_cycle_once_0287.py` reste versionné comme
preuve et outil de récupération manuelle. Il ne doit plus être utilisé dans le
chemin canonique ni dans la future installation fcron.

## Frontières conservées

- aucune mutation d'Issue ;
- aucune mutation ProjectV2 ;
- aucune écriture SQL ou Qdrant ;
- aucun lancement de Scheduler ou de laboratoire ;
- aucun nouveau poller ou daemon ;
- fcron reste l'autorité de déclenchement externe future.
