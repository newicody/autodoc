# 0062-part12_4_controlfs_shm_routeproxy_cluster_fabric_architecture

Patch documentaire pour verrouiller l'architecture runtime locale et la roadmap future.

## Contenu

- `doc/architecture/RUNTIME_CONTROLFS_SHM_CLUSTER_FABRIC_GRAPH.md`
- `doc/architecture/RUNTIME_CONTROLFS_SHM_PRIORITY_PLAN.md`
- `doc/architecture/ADR-0062-controlfs-shm-routeproxy-cluster-fabric.md`
- `doc/changelog/0062-controlfs-shm-routeproxy-cluster-fabric.md`
- `tests/rules/test_controlfs_shm_routeproxy_cluster_fabric_architecture_rule.py`

## Objectif

Verrouiller le modèle :

```text
SecurityFS -> Scheduler -> ControlFS -> RouteProxy passif -> SHM Runtime -> Workers
                                                  |
                                                  v
                                           Recorder -> ZFS -> Cell Lens
```

Et conserver en futur lointain :

```text
NetworkBridge
Hardware Cluster Fabric
PCIe FPGA/ASIC
DMA-backed routes
LVDS/direct machine bridge
distributed cluster dispatch
```

## Ce que le patch ne fait pas

- Pas de changement de Scheduler.
- Pas de daemon RouteProxy.
- Pas de vrai shm.
- Pas de sémaphores.
- Pas de réseau.
- Pas de FPGA/ASIC.
- Pas de cluster.

## Application

```bash
cd ~/projet/git/autodoc
python apply_patch_queue.py --patch 0062-part12_4_controlfs_shm_routeproxy_cluster_fabric_architecture --dry-run
python apply_patch_queue.py --patch 0062-part12_4_controlfs_shm_routeproxy_cluster_fabric_architecture --commit --push
```

## Gate conseillée

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules/test_controlfs_shm_routeproxy_cluster_fabric_architecture_rule.py
PYTHONPATH=src:. pytest -q tests/rules
```

## Patch suivant recommandé

Priorité 1 :

```text
Introduire le schéma ControlFS manifest + validateur/parser minimal.
Pas de shm réel.
Pas de Scheduler wiring.
Pas de daemon RouteProxy.
```
