# 0079-r3-part12_18_controlproxy_rule_phrase_compat

Correctif minimal apres `0079-r2`.

## Probleme corrige

Deux tests de regles herites cherchent des phrases exactes dans les docstrings :

```text
It only writes desired route manifests
start RouteProxy
start a RouteProxy daemon
```

`0079-r2` avait change le vocabulaire vers `ControlProxy`, ce qui est correct
architecturalement, mais cassait ces regles textuelles.

## Changement

Aucun changement runtime.

Seulement docstrings :

```text
src/runtime/controlfs_manifest.py
src/context/baby_fork_controlfs.py
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0079-r3-part12_18_controlproxy_rule_phrase_compat

unzip -o /chemin/vers/${PATCH_ID}.zip -d .

python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules
```
