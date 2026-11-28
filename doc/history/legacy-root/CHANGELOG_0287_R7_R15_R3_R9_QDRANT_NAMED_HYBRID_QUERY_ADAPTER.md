# Changelog 0287-r7-r15-r3-r9

- Extended the existing qdrant-client membrane with named dense queries.
- Added named sparse queries using the SDK sparse-vector model.
- Added a context adapter implementing dense/sparse hybrid-query methods.
- Preserved boolean and scalar canonical payload values.
- Rejected vectors and authoritative content in returned payloads.
- Kept the existing operator/policy search gate.
- Added no Qdrant writes or collection mutation.
