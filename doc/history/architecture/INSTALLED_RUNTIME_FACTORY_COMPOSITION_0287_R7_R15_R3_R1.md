# Installed runtime factory composition — 0287-r7-r15-r3-r1

```text
run_love_actions_closed_loop_0287.py
  -> context.love_installed_runtime_factory_0287:build_runtime
  -> .var/config/love_installed_runtime.ini
  -> provider de composition installé
  -> ports existants Scheduler / Dispatcher / SQL / OpenVINO-E5 / Qdrant
  -> ImportedActionsRuntimePorts validé
  -> r14 puis preview r15
```

La factory ne construit aucun de ces composants. Elle charge la composition
installée, construit ou vérifie l’attestation immuable, contrôle la dimension
384 et la collection Qdrant, puis remet les ports au consommateur existant.
