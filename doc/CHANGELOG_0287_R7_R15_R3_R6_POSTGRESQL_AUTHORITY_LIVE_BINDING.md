# Changelog 0287-r7-r15-r3-r6

- Added a lazy, injectable psycopg DB-API connection boundary.
- Reused `DbApiContextRevisionAuthorityStore` with PostgreSQL format parameters.
- Added idempotent schema initialization and deterministic base-revision seed.
- Added sanitized public binding/seed receipts and an idempotent close surface.
- Added unit and cumulative rule tests.
