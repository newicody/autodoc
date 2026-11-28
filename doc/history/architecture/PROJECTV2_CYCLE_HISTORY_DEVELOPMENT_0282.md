# Schéma du développement en cours — ProjectV2 cycle history 0282

```mermaid
flowchart LR
    R1[0282-r1\nAudit réutilisation\nGREEN]
    R2[0282-r2\nContrat filiation\nGREEN]
    R3[0282-r3\nParent / thème query-only\nGREEN]
    R4[0282-r4\nHistorique append-only\nCURRENT]
    R5[0282-r5\nPlan parent/sous-ticket\nNEXT]
    R6[0282-r6\nPlan champ Thème / groupes]
    R7[0282-r7\nAdapter autorisé]
    R8[0282-r8\nSmoke réel]

    R1 --> R2 --> R3 --> R4 --> R5 --> R6 --> R7 --> R8
```

## Flux fonctionnel visé

```mermaid
sequenceDiagram
    participant P as ProjectV2 snapshot
    participant N as Normaliseur r3
    participant L as Contrat lineage r2
    participant H as Projection history r4
    participant M as Mutation plan r5/r6
    participant A as Adapter autorisé r7

    P->>N: parent, subIssues, Theme, Status
    N->>L: références déterministes
    L->>H: cycle_ref + previous_cycle_ref
    H->>H: append / replay / collision
    H-->>M: historique validé (lecture seule)
    M-->>A: plan déterministe
    Note over A: aucune mutation sans décision opérateur
```

## Invariants r4

- un seul `root_issue_ref` par historique ;
- ordres de cycles contigus ;
- `previous_cycle_ref` pointe vers le dernier cycle ;
- replay identique accepté sans ajout ;
- même cycle avec contenu différent = collision ;
- digest d'entrée et digest global vérifiés ;
- aucune écriture GitHub, SQL, Qdrant ou fichier ;
- aucune modification du Scheduler.
