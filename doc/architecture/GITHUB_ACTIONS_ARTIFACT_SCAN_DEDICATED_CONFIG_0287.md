# Configuration dédiée au scan des artefacts GitHub Actions

## Problème résolu

La configuration ProjectV2 query-only utilise une commande de snapshot
ProjectV2. Le scan d’artefacts GitHub Actions utilise une surface différente.

Réutiliser le même fichier provoque :

```text
project scan_command is not an accepted scan-once surface
```

Le correctif ne modifie pas la configuration ProjectV2. Il génère un second
fichier local :

```text
.var/config/github_actions_artifact_scan.ini
```

## Génération

```bash
python tools/build_github_actions_artifact_scan_config_0287.py \
  --project-config .var/config/github_project_v2_query_only.ini \
  --fetch-config .var/config/github_artifact_server_fetch.ini \
  --output .var/config/github_actions_artifact_scan.ini \
  --working-directory /home/eric/projet/git/autodoc \
  --python-executable /home/eric/python/bin/python \
  --execute \
  --format summary
```

## Autorité des valeurs

Le fichier ProjectV2 fournit :

- owner et numéro du projet;
- options de contexte;
- paramètres opérateur de scan.

Le fichier server-fetch fournit :

- repository externe;
- workflow;
- préfixe des artefacts;
- `token_env`;
- API;
- allow-list;
- autorité du dataset.

Les identités communes doivent être strictement égales. Un mismatch bloque
l’écriture.

## Surface verrouillée

Le fichier généré contient exactement :

```text
scan_command = tools/run_github_actions_artifact_scan_once_live_0272.py
```

Les arguments `--execute` et `--policy-decision-id` sont fournis par le wrapper
de cycle, pas stockés dans cette configuration dédiée.

## Validation

Le générateur réutilise :

- `load_github_artifact_scan_config`;
- `load_github_artifact_server_fetch_config`;
- `build_github_actions_artifact_scan_plan`.

Il effectue une relecture exacte après écriture.

## Frontières

Le générateur :

- ne lit aucune valeur de jeton;
- ne contacte pas GitHub;
- ne modifie pas les deux fichiers sources;
- n’écrit ni SQL ni Qdrant;
- ne démarre ni Scheduler ni laboratoire;
- ne fait qu’une écriture locale atomique sous `--execute`.
