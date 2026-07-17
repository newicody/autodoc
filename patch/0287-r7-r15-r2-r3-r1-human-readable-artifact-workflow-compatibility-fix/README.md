# 0287-r7-r15-r2-r3-r1 — workflow compatibility fix

## Intention

Corriger l'unique règle historique en échec après l'introduction des noms
d'artefacts lisibles, sans rétablir les anciens noms fixes comme noms d'upload.

## Correction

Le workflow conserve près de l'étape d'identité les trois marqueurs historiques :

```text
autodoc-authoritative-request
autodoc-copilot-advisory
autodoc-dual-artifact-manifest
```

Ils documentent les noms enregistrés dans `artifact_identity.json` et acceptés
par l'importeur pour les anciens runs. Les trois étapes `upload-artifact`
continuent exclusivement à utiliser les sorties dynamiques :

```text
steps.artifact-identity.outputs.request_name
steps.artifact-identity.outputs.advisory_name
steps.artifact-identity.outputs.manifest_name
```

Aucun artefact en double n'est créé.

## Application

Le patch précédent est déjà appliqué dans l'arbre même si ses tests ont interrompu
la création du commit. Ne pas réinitialiser le dépôt.

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r3-r1-human-readable-artifact-workflow-compatibility-fix \
  --dry-run \
  --allow-dirty
```

Puis :

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r3-r1-human-readable-artifact-workflow-compatibility-fix \
  --commit \
  --push \
  --allow-dirty
```

## Commit proposé

```text
fix readable artifact workflow compatibility
```
