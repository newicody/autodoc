# Composition installée externally-managed — 0287 r16 r58

## But

Assembler une seule fois, au démarrage OpenRC, le Scheduler canonique unique,
le runtime de recherche GitHub borné et le catalogue complet des dix handlers.

Cette unité ne construit pas les backends elle-même. Elle reçoit une composition
process-local typée provenant de l'installation puis relie :

1. le Scheduler déjà construit ;
2. la réclamation atomique des commandes PostgreSQL ;
3. le store durable de continuation du graphe ;
4. le pipeline admission → handler → commit de fin ;
5. les quatre fournisseurs de réhydratation ;
6. les dix handlers du cycle groupé ;
7. les observations temporelles passives ;
8. le propriétaire de processus OpenRC introduit en r16-r57.

## Autorités

- OpenRC possède le processus et seulement son cycle de vie.
- Le Scheduler canonique unique reste l'autorité d'orchestration.
- PostgreSQL reste l'autorité durable des commandes, graphes, analyses et preuves.
- Qdrant reste une projection et une surface de rappel par références.
- OpenVINO E5 reste un composant d'embedding injecté.
- ControlFS et `/dev/shm` restent le plan rapide, jamais l'autorité durable.

## Frontière de sérialisation

Aucune file JSONL et aucun stockage interne JSON ne sont ajoutés. Les mappings
de reçus servent uniquement aux frontières CLI et d'observation.

## Échec fermé

La composition refuse :

- une configuration `tool-bounded` ;
- une identité Scheduler divergente ;
- un catalogue différent des dix handlers attendus ;
- un fournisseur ou un port incomplet ;
- l'absence d'une fabrique de composants explicitement configurée.

L'unité suivante fournira la liaison installée réelle des composants PostgreSQL,
Qdrant, OpenVINO et du pipeline d'exécution. Le service OpenRC ne doit pas être
activé avant cette liaison et son smoke test.
