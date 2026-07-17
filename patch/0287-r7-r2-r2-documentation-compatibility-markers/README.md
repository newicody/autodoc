# 0287-r7-r2-r2-documentation-compatibility-markers

## Objet

Correctif documentaire à appliquer après
`0287-r7-r2-r1-copilot-first-opinion-advisory-v2-rebase` lorsque ce dernier a
été appliqué mais que `tests/rules` a échoué sur cinq marqueurs historiques.

Le correctif :

- restaure les marqueurs cumulatifs attendus dans `INSTALLATION.md` ;
- conserve `0287-r7-r2` comme extension du contrat Copilot v2 ;
- restaure le texte historique Chalouf uniquement comme ancre de compatibilité ;
- indique explicitement que cette ancre est retirée de la roadmap active ;
- maintient la fermeture générique en `0287-r7-r10` et l'absence de phase 0288 ;
- ne modifie aucun code d'exécution.

## Application

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r2-r2-documentation-compatibility-markers \
  --dry-run \
  --allow-dirty
```

Puis :

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r2-r2-documentation-compatibility-markers \
  --commit \
  --push \
  --allow-dirty
```

Le patch précédent doit rester appliqué dans le working tree : ce correctif se
pose par-dessus avant le commit final.
