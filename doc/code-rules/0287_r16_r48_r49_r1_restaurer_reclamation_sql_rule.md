# Règle 0287 r16-r48-r49-r1 — réclamation SQL obligatoire

1. Le runtime externe ne doit importer aucun module absent.
2. La réclamation appartient au Scheduler canonique déjà actif.
3. PostgreSQL sélectionne une commande `pending` avec `SKIP LOCKED`.
4. La sélection et la transition vers `claimed` restent atomiques.
5. La commande retournée est une classe typée, jamais un dictionnaire JSON.
6. Aucun second Scheduler, Dispatcher ou laboratoire n'est créé.
