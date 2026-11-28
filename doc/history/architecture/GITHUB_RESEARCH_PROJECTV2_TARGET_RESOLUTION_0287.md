# Résolution de la cible ProjectV2 du cycle de recherche GitHub

## But

La phase `prepare` r16-r20 a besoin de deux identités distantes :

- l’identifiant de l’item ProjectV2 portant l’Issue source;
- l’identifiant du champ `Résumé`.

Ces identités ne doivent pas être recopiées manuellement ni résolues par un
nouvel adaptateur.

## Réutilisation

L’outil :

```text
tools/resolve_github_research_project_target_0287.py
```

réutilise :

- `LoveProjectV2TargetRequest`;
- `resolve_love_projectv2_target`;
- `GitHubCliFinalDeliverablePublicationAdapter.resolve_project_target()`.

Le même GraphQL et le même contrat de résolution exacte sont donc employés par
la préparation et par la publication finale.

## Commande

```bash
python tools/resolve_github_research_project_target_0287.py \
  --repository newicody/projects \
  --issue-number 15 \
  --project-owner newicody \
  --project-number 3 \
  --field-name 'Résumé' \
  --output /tmp/github-love-project-target.json \
  --format summary
```

## Sortie shell

```bash
eval "$(
  python tools/resolve_github_research_project_target_0287.py \
    --repository newicody/projects \
    --issue-number 15 \
    --project-owner newicody \
    --project-number 3 \
    --field-name 'Résumé' \
    --format shell
)"
```

Les variables produites sont :

```text
PROJECT_ITEM_ID
RESUME_FIELD_ID
PROJECT_FIELD_NAME
```

## Résolution stricte

La commande bloque lorsque :

- l’Issue n’appartient pas exactement une fois au ProjectV2 configuré;
- le ProjectV2 n’existe pas pour l’owner demandé;
- plusieurs champs portent le même nom;
- le champ n’existe pas;
- un seul des deux overrides est fourni;
- les overrides diffèrent du readback.

## Frontières

La résolution :

- est strictement en lecture;
- ne crée aucun commentaire;
- ne modifie aucun champ;
- ne lance ni Scheduler ni laboratoire;
- n’écrit ni SQL ni Qdrant;
- ne sérialise jamais la valeur du token.
