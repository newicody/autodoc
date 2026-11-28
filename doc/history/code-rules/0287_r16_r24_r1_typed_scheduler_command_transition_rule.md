# Code rule — 0287 r16-r24-r1 — transition vers une commande typée

1. JSON est un format de frontière ; il ne constitue pas l’autorité interne.
2. La commande métier est une instance immuable de classe avant tout traitement.
3. L’héritage reste court et exprime une relation « est une » réelle.
4. L’autorisation, la corrélation, la charge de recherche, le budget et la route
   sont composés dans la commande.
5. Les références, corrélations, budgets et digests sont validés à la
   construction.
6. Le digest de commande ne dépend pas d’un dictionnaire JSON interne.
7. L’identité d’un rejeu ne dépend pas de l’heure d’exécution de la CLI.
8. Toute recherche porte un budget de ressources explicite et borné.
9. La persistance durable cible PostgreSQL par un port explicite.
10. `/dev/shm` et ControlProxy restent des surfaces rapides de signal/référence,
    pas l’autorité durable.
11. L’EventBus observe ; il ne commande pas le Scheduler.
12. Le chemin r16-r24 reste seulement une compatibilité transitoire, refusée par
    défaut et accessible uniquement par une option explicite.
13. Aucune métaclasse n’est ajoutée sans besoin réel de résolution dynamique ou
    de registre de schémas.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: application des règles existantes aux commandes typées, aux projections de frontière et aux recherches bornées
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: true
```
