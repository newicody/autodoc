# Autodoc / MissiPy — architecture globale courante (0282-r4)

Ce schéma représente la **baseline opérationnelle actuelle**. Il ne remplace
pas la couche patrimoniale `doc/docs/architecture/00_global.dot`.

```mermaid
flowchart LR
    subgraph EXT[GitHub — workflow, review, synchronisation]
        ISSUE[Issue / ProjectV2]
        ACTIONS[GitHub Actions\nrequest + advisory + manifest]
        REVIEW[Publication contrôlée\nplan/preview, mutation différée]
    end

    subgraph DATASET[Dataset serveur configuré]
        FETCH[Fetcher 0168\nlecture seule]
        RAW[raw artifacts]
        INDEX[index / run-group / closed-loop]
        HISTORY[historique cycles ProjectV2\nappend-only 0282-r4]
    end

    subgraph ORCH[Autorité d'orchestration]
        SCHED[Scheduler unique]
        POLICY[PolicyEngine / gates]
        ROUTE[Handlers / adapters / RouteProxy]
    end

    subgraph LAB[Laboratoires et spécialistes]
        FAKE[Fake laboratory déterministe]
        PORTABLE[Spécialistes portables\nvisites/transferts prévus]
    end

    subgraph KNOW[Contexte et connaissance]
        SQL[(SQL\nautorité durable)]
        E5[OpenVINO / E5\nembeddings explicites]
        QDRANT[(Qdrant\nprojection / recall)]
        SHM[/dev/shm\ndata-plane rapide]
    end

    subgraph OBS[Observation passive]
        BUS[EventBus\nfacts only]
        SUP[PassiveSupervisor]
        VIS[VisPy / Cell Lens]
    end

    ISSUE --> ACTIONS --> FETCH --> RAW --> INDEX
    ISSUE -->|snapshot query-only| HISTORY
    INDEX -->|SourceCandidate / décision| SCHED
    HISTORY -->|intention typée future| SCHED
    SCHED --> POLICY --> ROUTE
    ROUTE --> FAKE
    FAKE -. future .-> PORTABLE
    ROUTE <--> SHM
    SCHED -->|travail planifié| E5
    E5 --> QDRANT
    QDRANT -->|sql_ref| SQL
    SQL -->|rehydrate| SCHED
    FAKE --> INDEX
    INDEX --> REVIEW
    REVIEW -. autorisation opérateur requise .-> ISSUE

    SCHED --> BUS
    ROUTE --> BUS
    FAKE --> BUS
    SQL --> BUS
    BUS --> SUP --> VIS
```

## Autorités verrouillées

| Surface | Autorité | Interdit |
|---|---|---|
| Scheduler | orchestration, politiques, priorités, cycle de vie des composants | logique métier, gestion de services externes |
| SQL | contexte durable et réhydratation | index vectoriel |
| Qdrant | projection et rappel reconstruisibles | autorité durable |
| OpenVINO/E5 | génération vectorielle explicite | backend caché du Scheduler |
| `/dev/shm` / RouteProxy | transport rapide | politique ou autorité durable |
| EventBus / PassiveSupervisor / VisPy | observation | commande ou autorisation |
| GitHub | workflow, review, synchronisation | autorité locale implicite |
| OpenRC / OS / administrateur | processus externes | orchestration applicative interne |

## État des axes

```text
0260..0269  SQL -> E5 -> Qdrant -> recall -> ResultFrame -> observation
0272..0281  ProjectV2/Issue -> artefacts -> dataset -> fake lab -> preview
0282-r1..r4 audit -> filiation -> normalisation -> historique append-only
0282-r5..r8 plans de mutation -> adapter autorisé -> smoke réel
0283         exécuteur Qdrant réel contrôlé
0284         spécialistes portables / visites / transferts
0285         VisPy / Cell Lens de la boucle complète
0286         démonstrateur Chalouf
```
