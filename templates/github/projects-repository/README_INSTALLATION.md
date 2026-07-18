# Installation cumulative — `newicody/projects`

## Publication du livrable final

Le plan r16-r17 est compatible avec l’adaptateur existant
`tools/publish_love_final_deliverable_0287.py`.

### Variables de sécurité

```bash
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_ISSUE_PUBLICATION_ALLOWED=true
export AUTODOC_PROJECT_PROJECTION_ALLOWED=true
```

Le jeton est lu par défaut dans :

```text
AUTODOC_PROJECT_TOKEN
```

Il doit permettre :

- la lecture et la création de commentaires sur l’Issue;
- la lecture du ProjectV2;
- `updateProjectV2ItemFieldValue` sur le champ ciblé.

### Prévisualisation obligatoire

```bash
python tools/publish_love_final_deliverable_0287.py \
  --plan /tmp/r16-r17-publication-plan.json \
  --operator-decision approve \
  --format json
```

Relever `plan_digest`, puis seulement ensuite exécuter :

```bash
python tools/publish_love_final_deliverable_0287.py \
  --plan /tmp/r16-r17-publication-plan.json \
  --operator-decision approve \
  --execute \
  --confirm-plan-digest '<PLAN_DIGEST_EXACT>' \
  --format json
```

La publication est valide uniquement si le commentaire Issue et la valeur du
champ ProjectV2 sont relus exactement.
