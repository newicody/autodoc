# 0284-r3 — Specialist/laboratory message contract

Base attendue : `0284-r2-portable-specialist-contract` déjà appliqué.

Ce patch ajoute un contrat immuable de message et de conversation reliant :

- `PortableSpecialistDescriptor`;
- `LaboratoryVisitRequest` / `LaboratoryVisitResult`;
- `SpecialistDemandFrame` / `SpecialistOpinionFrame`.

Il ne crée aucun transport, Scheduler, laboratoire, provider, manager, registre,
worker, bus ou autorité durable.

Commit proposé :

```text
add-specialist-laboratory-message-contract
```

Étape suivante verrouillée :

```text
0284-r4-specialist-laboratory-transfer-contract
```
