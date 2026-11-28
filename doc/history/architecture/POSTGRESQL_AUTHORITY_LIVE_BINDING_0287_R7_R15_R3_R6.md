# PostgreSQL authority live binding

```text
ManualInstalledRuntimeSettings
        |
        v
love_postgresql_authority_binding_0287
        |-- environment password (read only, never serialized)
        |-- psycopg.connect / injected DB-API connector
        |-- CREATE SCHEMA IF NOT EXISTS + search_path
        v
DbApiContextRevisionAuthorityStore
        |-- initialize_schema()
        |-- put_revision(context-revision:love-base)
        v
LovePostgreSqlAuthorityBinding
        |-- authority_store
        |-- public receipt
        `-- close hook for the future runtime lease
```

The module is an I/O composition boundary.  Domain contracts remain transport
neutral, SQL remains authoritative, and E5/Qdrant are not touched.
