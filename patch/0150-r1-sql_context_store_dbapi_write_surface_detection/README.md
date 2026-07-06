# 0150-r1 — SQLContextStore DB-API write surface detection

Fixes the 0150 audit to recognize the existing `DbApiSqlContextStore.upsert_record` method instead of requiring a class named exactly `SQLContextStore`.
