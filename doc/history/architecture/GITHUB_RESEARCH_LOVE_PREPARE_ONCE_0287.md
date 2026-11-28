# Préparation opérationnelle du cycle en une commande

## Objectif

`run_github_research_love_prepare_once_0287.py` réduit la préparation réelle à
une seule surface opérateur, tout en conservant toutes les frontières
existantes.

Il ne remplace aucun composant métier. Il compose successivement :

1. `build_github_actions_artifact_scan_config_0287.py`;
2. `check_love_installed_runtime_0287.py`;
3. `run_github_actions_artifact_fetch_once_0287.py`;
4. `run_github_research_love_closed_loop_0287.py prepare`.

## Mode plan

Sans `--execute`, l’outil :

- valide l’alignement Project/fetch;
- construit le plan de configuration de scan sans écrire;
- vérifie PostgreSQL, Qdrant et OpenVINO;
- ne contacte pas GitHub;
- n’ouvre pas le runtime de production;
- n’écrit ni SQL ni Qdrant.

Le statut attendu est :

```text
ready-for-execute
```

## Mode execute

Avec `--execute`, l’outil :

- écrit la configuration scan dédiée;
- exige les deux gates Qdrant;
- exige les deux variables de token sans lire leur valeur dans le rapport;
- lance le fetch canonique;
- transmet le rapport de cycle au lanceur r16-r20;
- résout l’Issue et le champ ProjectV2 en lecture seule;
- ouvre le runtime tool-bounded;
- exécute les analyses, projections, rappel, synthèse et livrable final;
- écrit `prepared.json`;
- s’arrête au digest de publication.

Aucun commentaire Issue ni champ ProjectV2 n’est modifié.

## Commande plan

```bash
python tools/run_github_research_love_prepare_once_0287.py \
  --project-config .var/config/github_project_v2_query_only.ini \
  --fetch-config .var/config/github_artifact_server_fetch.ini \
  --runtime-config .var/config/love_installed_runtime.ini \
  --policy-decision-id policy:0287:issue-15-love \
  --run-id 29622831972 \
  --issue-number 15 \
  --project-owner newicody \
  --project-number 3 \
  --prepared-output /tmp/github-love-prepared.json \
  --output /tmp/github-love-prepare-once.json \
  --format summary
```

## Commande execute

```bash
export GITHUB_TOKEN="$(gh auth token)"
export AUTODOC_PROJECT_TOKEN="$GITHUB_TOKEN"
export AUTODOC_QDRANT_POINT_WRITE_ALLOWED=true
export AUTODOC_QDRANT_SEARCH_ALLOWED=true

python tools/run_github_research_love_prepare_once_0287.py \
  --project-config .var/config/github_project_v2_query_only.ini \
  --fetch-config .var/config/github_artifact_server_fetch.ini \
  --runtime-config .var/config/love_installed_runtime.ini \
  --policy-decision-id policy:0287:issue-15-love \
  --run-id 29622831972 \
  --issue-number 15 \
  --project-owner newicody \
  --project-number 3 \
  --prepared-output /tmp/github-love-prepared.json \
  --output /tmp/github-love-prepare-once.json \
  --execute \
  --format summary
```

## Résultat attendu

```text
valid=true
mode=execute
status=publication-confirmation-required
plan_digest=sha256:...
prepared_output=/tmp/github-love-prepared.json
```

## Frontières

- Scheduler existant uniquement;
- fetch read-only;
- résolution ProjectV2 read-only;
- SQL et Qdrant uniquement dans `prepare`;
- aucune publication distante;
- aucune valeur secrète sérialisée;
- confirmation humaine toujours obligatoire avant `complete`.
