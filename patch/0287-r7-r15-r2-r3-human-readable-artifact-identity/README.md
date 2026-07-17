# 0287-r7-r15-r2-r3 — human-readable artifact identity

## Intention

Rendre les artefacts GitHub Actions compréhensibles depuis leur nom, sans remplacer leurs références typées, leurs empreintes ni l'autorité du manifest.

## Noms produits

```text
autodoc-i<issue>-<titre-court>--authoritative-request-v1
autodoc-i<issue>-<titre-court>--copilot-advisory-v2
autodoc-i<issue>-<titre-court>--run-manifest-v1
```

Le fichier `artifact_identity.json`, rangé avec le manifest, conserve également le titre humain, le résumé du contenu, les sections, le nom historique et `artifact_ref`.

## Compatibilité

Les runs historiques utilisant les noms fixes restent acceptés. Le consommateur local accepte soit le nom historique exact, soit le suffixe canonique lisible. Deux artefacts représentant le même type dans un run provoquent un refus fermé.

## Scope

- contrat immuable stdlib-only ;
- adaptateur fin pour GitHub Actions ;
- workflow Projects avec noms dynamiques ;
- importeur r15-r2 rétrocompatible ;
- tests de contrat, outil, import et règles ;
- documentation, manifest, changelog et DOT source.

Aucun changement du Scheduler, du laboratoire, de SQL, OpenVINO/E5, Qdrant ou des autorisations de publication.

## Application

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r3-human-readable-artifact-identity \
  --dry-run \
  --allow-dirty
```

Puis :

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r3-human-readable-artifact-identity \
  --commit \
  --push \
  --allow-dirty
```

## Commit proposé

```text
add human-readable artifact identities
```
