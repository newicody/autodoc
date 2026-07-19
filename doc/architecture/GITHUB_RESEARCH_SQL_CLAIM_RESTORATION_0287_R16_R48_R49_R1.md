# Restauration de la réclamation SQL — 0287 r16-r48-r49-r1

Le runtime géré par OpenRC dépend de la frontière de réclamation atomique créée
pour r16-r26. Cette frontière avait disparu de l'état courant : le module
Python et la méthode SQL n'étaient plus présents.

La présente unité restaure ensemble :

```text
Scheduler canonique déjà running
→ claim PostgreSQL pending
→ FOR UPDATE OF s SKIP LOCKED
→ transition pending → claimed
→ reconstruction de la commande typée
→ cycle Scheduler borné
```

La branche SQLite `qmark` demeure une compatibilité de test. PostgreSQL reste
l'autorité installée. Aucun Scheduler, Dispatcher, handler ou laboratoire n'est
créé par cette frontière.
