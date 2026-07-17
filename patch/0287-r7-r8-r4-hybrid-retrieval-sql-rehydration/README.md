# 0287-r7-r8-r4 — hybrid retrieval and SQL rehydration

Apply after `0287-r7-r8-r3-qdrant-canonical-profile`.

This patch adds dense E5 plus sparse lexical retrieval composition, RRF,
diversity grouping and SQL-authoritative rehydration. It performs no Qdrant
write and does not modify Scheduler, EventBus, ControlProxy or installation.
