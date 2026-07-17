# 0284-r6 — Portable specialist real-memory closure

Base attendue :

```text
0284-r2-portable-specialist-contract
0284-r3-specialist-laboratory-message-contract
0284-r4-specialist-laboratory-transfer-contract
0284-r5-specialists-laboratories-existing-chain-smoke
```

Le patch compose le spécialiste portable avec les surfaces existantes :

```text
Scheduler / fake laboratory
→ DbApiSqlContextStore
→ OpenVINO multilingual-E5-small (384)
→ Qdrant projection réelle
→ Qdrant recall de références
→ réhydratation SQL
```

Il ne crée aucun Scheduler, laboratoire, provider, exécuteur Qdrant, transport,
bus, registre, manager ou CLI.

L'application du patch et les tests n'effectuent aucun appel OpenVINO, SQL ou
Qdrant réel. L'exécution réelle exige deux autorisations explicites et conserve
les enregistrements SQL/points Qdrant jusqu'à une décision de nettoyage.

Commit proposé :

```text
add-portable-specialist-real-memory-closure
```

Étape suivante :

```text
0284-r7-projects-copilot-specialist-integrated-smoke
```
