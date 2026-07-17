# 0272-r8-r1 — ProjectV2 durable consumer graph edge fix

Micro-correctif atomique du graphe runtime 0272-r8.

Le test de règle exige que la transition canonique d'autorisation durable soit
représentée explicitement par l'arête :

```text
GateR7 -> DurableR8
```

Le graphe initial représentait uniquement la validation interne intermédiaire :

```text
GateR7 -> Validate -> DurableR8
```

Le correctif conserve cette validation sous forme d'arêtes pointillées et ajoute
l'arête canonique directe, sans modifier le code runtime, les contrats, le
Scheduler, SQL, OpenVINO, Qdrant, GitHub ou les laboratoires.

Dépendances non-stdlib ajoutées : aucune.
