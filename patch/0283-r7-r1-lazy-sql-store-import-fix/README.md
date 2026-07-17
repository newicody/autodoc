# 0283-r7-r1-lazy-sql-store-import-fix

Moves the existing SQL store import from CLI module loading to the authorized
recall execute store-opening boundary.

```text
sql_store_import_lazy: true
scheduler_modified: false
new_runtime_module_added: false
new_transport_added: false
```
