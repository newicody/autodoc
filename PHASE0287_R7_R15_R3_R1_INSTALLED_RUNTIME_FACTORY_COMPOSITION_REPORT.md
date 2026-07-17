# Phase 0287 R7 R15 R3 R1 — Installed runtime factory composition

## But

Fermer la frontière de factory demandée par `run_love_actions_closed_loop_0287.py`
sans exposer à l’opérateur un placeholder `module:function` à chaque lancement et
sans construire un second runtime.

## Audit de réutilisation

Le patch réutilise exclusivement :

- `ImportedActionsRuntimePorts` et son validateur ;
- `ImportedActionsRealBackendAttestation` ;
- le Scheduler et le Dispatcher fournis par la composition installée ;
- l’autorité SQL déjà installée ;
- les ports de projection OpenVINO/E5-384 et de recall Qdrant déjà installés.

Il ne crée ni Scheduler, ni laboratoire, ni client SQL, ni runtime OpenVINO, ni
client Qdrant, ni manager.

## Autorités préservées

- Le Scheduler reste l’unique autorité d’orchestration.
- SQL reste l’autorité durable des révisions et objets.
- Qdrant reste une projection et un recall de références.
- E5 reste verrouillé à 384 dimensions.
- Le provider installé ne devient pas une nouvelle autorité : il compose des
  ports déjà existants et les rend au contrat `r15-r2`.

## Configuration installée

`config/love_actions_closed_loop.example.ini` choisit désormais la factory
canonique :

`context.love_installed_runtime_factory_0287:build_runtime`.

La composition propre à la machine est déclarée une fois dans
`.var/config/love_installed_runtime.ini`, dérivé de
`config/love_installed_runtime.example.ini`. Cette configuration référence une
fonction de composition appartenant à l’installation serveur et atteste les
identités SQL, OpenVINO/E5 et Qdrant réellement utilisées.

Aucun fallback dummy, fake ou déterministe n’est sélectionné.

## Frontière de preuve

Ce patch ferme le contrat et le câblage par défaut. Il valide strictement les
ports et l’attestation fournis. Tant que la configuration locale et le provider
de la machine ne sont pas renseignés et qu’un vrai run n’a pas traversé la
chaîne, aucune preuve live n’est revendiquée.

La prochaine unité raccorde la composition serveur de l’installation de
référence, exécute le preview réel et archive ses références de preuve.
