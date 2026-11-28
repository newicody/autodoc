# Manifest 0287-r7-r15-r3-r6

## Runtime source

- `src/context/love_postgresql_authority_binding_0287.py`

## Tests

- `tests/context/test_love_postgresql_authority_binding_0287_r7_r15_r3_r6.py`
- `tests/rules/test_love_postgresql_authority_binding_0287_r7_r15_r3_r6_rule.py`

## Documentation

- `PHASE0287_R7_R15_R3_R6_POSTGRESQL_AUTHORITY_LIVE_BINDING_REPORT.md`
- `doc/CHANGELOG_0287_R7_R15_R3_R6_POSTGRESQL_AUTHORITY_LIVE_BINDING.md`
- `doc/architecture/POSTGRESQL_AUTHORITY_LIVE_BINDING_0287_R7_R15_R3_R6.md`
- `doc/architecture/POSTGRESQL_AUTHORITY_LIVE_BINDING_0287_R7_R15_R3_R6.dot`
- `doc/manifests/MANIFEST_0287_R7_R15_R3_R6_POSTGRESQL_AUTHORITY_LIVE_BINDING.md`

## Locked boundaries

- Reuses the existing DB-API context revision authority.
- PostgreSQL driver import is lazy and isolated at the I/O boundary.
- Secrets are never serialized.
- No Scheduler, OpenVINO or Qdrant object is created.
