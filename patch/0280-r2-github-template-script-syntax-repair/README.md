# 0280-r2 — GitHub template script syntax repair

## Correction par rapport à 0280-r1

`0280-r1` avait été produit depuis une reconstruction tronquée du fichier
`build_autodoc_ticket_artifact.py`. Le hunk visait donc la ligne 8 alors que le
défaut réel se trouve autour de la ligne 118 dans le fichier suivi.

`0280-r2` remplace intégralement `0280-r1` et recale le hunk sur le contenu réel
observé dans `HEAD` et `origin/master`.

## Portée

- répare le littéral `"\n"` cassé dans `write_json()` ;
- ajoute une gate `tests/rules` compilant récursivement tous les scripts Python
  de `templates/github/scripts/` ;
- ajoute un test fonctionnel du builder de ticket ;
- reste stdlib-only ;
- ne modifie ni Scheduler, ni SQL, ni Qdrant, ni les frontières de mutation
  distante.

## Application

Le dry-run de `0280-r1` n'a rien appliqué. Retirer son répertoire pour éviter
une sélection accidentelle, puis installer `0280-r2` :

```bash
cd /home/eric/projet/git/autodoc
rm -rf patch/0280-r1-github-template-script-syntax-repair
unzip -o /mnt/data/0280-r2-github-template-script-syntax-repair.zip
python apply_patch_queue.py \
  --patch 0280-r2-github-template-script-syntax-repair \
  --dry-run \
  --allow-dirty
```

Après validation :

```bash
python apply_patch_queue.py \
  --patch 0280-r2-github-template-script-syntax-repair \
  --allow-dirty
```

Faire ensuite un `git add` explicite des six fichiers puis un commit/push
manuel, afin d'éviter le défaut connu de l'auto-commit avec un arbre sale.
