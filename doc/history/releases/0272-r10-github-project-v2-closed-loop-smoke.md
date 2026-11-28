# Release 0272-r10 — ProjectV2 closed-loop smoke

Cette release ferme la chaîne locale depuis un gate record r7 approuvé jusqu'à
la réhydratation SQL après recall Qdrant. Elle réutilise r8, 0261, r9, 0263 et
la membrane qdrant-client 0271. Le query embedding est validé avant la
projection, le replay SQL est idempotent et SQL reste l'autorité durable.

La release n'ouvre ni mutation GitHub, ni laboratoire, ni nouveau manager ou
orchestrateur. Elle prépare directement l'audit laboratoire 0273-r1.

The phase also makes the existing 0261 embedding surface role-aware for query embeddings; it does not add another embedding runtime.
