# CHANGELOG — Phase 1.8

## Objectif

Préparer la rejouabilité déterministe en ajoutant un `EventRecorder` minimal,
strictement passif, branché sur l’`EventBus`.

## Ajouts

- `contracts.replay.EventRecord`
- `contracts.replay.EventLogSnapshot`
- `observability.recorder.EventRecorder`
- tests du recorder en isolation
- test du recorder sur un roundtrip scheduler/proxy

## Décisions d'architecture

Le recorder observe uniquement. Il ne commande pas le scheduler, ne publie pas
d'événement, ne modifie pas les queues, et ne capture jamais les `Future`
contenus dans `Request.reply`.

Le replay effectif n’est pas implémenté en Phase 1.8. Cette étape enregistre
les événements dans une forme immuable afin de préparer un futur `ReplayEngine`.

## Validation

- `PYTHONPATH=src python3 -m compileall -q src tests`
- `PYTHONPATH=src pytest -q`
- `PYTHONPATH=src python3 src/main.py`
- syntaxe DOT validée avec Graphviz
