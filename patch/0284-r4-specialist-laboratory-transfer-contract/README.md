# 0284-r4 — Specialist/laboratory transfer contract

Base attendue :

```text
0284-r2-portable-specialist-contract
0284-r3-specialist-laboratory-message-contract
```

Le patch ajoute des contrats immuables pour :

- une visite temporaire dans un autre laboratoire ;
- un transfert durable vers un autre laboratoire ;
- la projection vers les champs du `LaboratoryVisitRequest` existant ;
- la continuité de `specialist_ref`, `conversation_ref`, `parent_visit_ref`,
  `context_refs`, `evidence_refs` et `return_route_ref`.

Il ne crée aucun transport, provider, registre, laboratoire, Scheduler,
LaboratoryManager ou autorité durable.

Commit proposé :

```text
add-specialist-laboratory-transfer-contract
```

Étape suivante :

```text
0284-r5-specialists-laboratories-existing-chain-smoke
```
