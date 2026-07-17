# 0287-r7-r15-r3-r3-r1-runtime-lease-rule-alignment

Correctif cumulatif à appliquer sur le working tree où
`0287-r7-r15-r3-r3-tool-bounded-runtime-lease-boundary` est déjà appliqué mais
non commité.

## Corrige

- retire `os` du contrat de domaine ;
- injecte explicitement `current_process_id` depuis le tool ;
- rétablit `validate_imported_actions_runtime_ports` dans le chemin CLI ;
- conserve la lease process-local, les hooks inversés, l'exact-once et le replay ;
- adapte uniquement les nouveaux tests de r15-r3-r3 ;
- ne modifie aucun ancien test ou ancienne règle.

## Appliquer

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r3-r1-runtime-lease-rule-alignment \
  --dry-run \
  --allow-dirty
```

Puis :

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r3-r1-runtime-lease-rule-alignment \
  --commit \
  --push \
  --allow-dirty
```

Ne pas restaurer les deux fichiers déjà modifiés et ne pas réappliquer
`0287-r7-r15-r3-r3-tool-bounded-runtime-lease-boundary`.
