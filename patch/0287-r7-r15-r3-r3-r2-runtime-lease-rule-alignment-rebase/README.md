# 0287-r7-r15-r3-r3-r2-runtime-lease-rule-alignment-rebase

Correctif rebasé à appliquer sur le working tree où
`0287-r7-r15-r3-r3-tool-bounded-runtime-lease-boundary` est déjà appliqué,
mais non commité à cause des deux échecs de règles cumulatives.

Le précédent correctif `r1` n'a pas modifié le working tree : son hunk principal
du tool n'était pas applicable. Ce bundle utilise des hunks plus petits et
n'altère pas la zone variable de construction du `runtime_context`.

## Corrige

- retire `os` du contrat de domaine ;
- injecte le PID depuis le tool via un helper local ;
- rétablit explicitement `validate_imported_actions_runtime_ports` ;
- conserve la lease process-local, la fermeture inversée, l'exact-once et le replay ;
- adapte uniquement les nouveaux tests de `r15-r3-r3` ;
- ne modifie aucun ancien test ni aucune ancienne règle.

## Vérification

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r3-r2-runtime-lease-rule-alignment-rebase \
  --dry-run \
  --allow-dirty
```

Puis :

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r3-r2-runtime-lease-rule-alignment-rebase \
  --commit \
  --push \
  --allow-dirty
```

Ne pas restaurer les fichiers déjà modifiés et ne pas réappliquer
`0287-r7-r15-r3-r3-tool-bounded-runtime-lease-boundary`.
