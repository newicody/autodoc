# Réutilisation explicite d’un cycle de fetch déjà prêt

## Problème

Le fetch GitHub Actions est incrémental et append-only. Lorsqu’un run a
déjà été synchronisé, un nouveau cycle peut être valide avec le statut
`artifacts-fetched`, mais ne contenir aucun nouveau `ready_run`.

Le mode r16-r20-r5 transmettait uniquement ce nouveau cycle au chargeur.
Une relance pouvait donc produire :

```text
requested run_id not ready
expected exactly one selected ready_run, found 0
```

alors qu’un rapport antérieur contenait déjà les trois artefacts prêts.

## Correction

L’option suivante sélectionne explicitement un rapport antérieur :

```text
--existing-fetch-cycle-report <path>
```

Dans ce mode :

- aucun nouveau fetch GitHub Actions n’est lancé;
- le token d’artefacts n’est pas requis;
- le rapport choisi est transmis au chargeur r16-r20 existant;
- le chargeur valide toujours le schéma, le mode, le statut, le run,
  l’état durable et les trois contenus;
- le token ProjectV2 reste requis pour la résolution read-only;
- aucune recherche automatique dans l’historique n’est effectuée.

## Pourquoi pas un fallback automatique

Plusieurs rapports historiques peuvent référencer le même run. Choisir
silencieusement le plus récent ou le premier rendrait l’exécution
ambiguë. La sélection reste donc visible et contrôlée par l’opérateur.

## Exemple

```bash
FETCH_CYCLE_REPORT="$(
  jq -r '.reports.cycle' \
    /tmp/github-artifact-fetch-29622831972.json
)"

python tools/run_github_research_love_prepare_once_0287.py \
  --project-config .var/config/github_project_v2_query_only.ini \
  --fetch-config .var/config/github_artifact_server_fetch.ini \
  --runtime-config .var/config/love_installed_runtime.ini \
  --policy-decision-id policy:0287:issue-15-love \
  --run-id 29622831972 \
  --existing-fetch-cycle-report "$FETCH_CYCLE_REPORT" \
  --issue-number 15 \
  --project-owner newicody \
  --project-number 3 \
  --prepared-output /tmp/github-love-prepared.json \
  --output /tmp/github-love-prepare-once.json \
  --execute \
  --format summary
```
