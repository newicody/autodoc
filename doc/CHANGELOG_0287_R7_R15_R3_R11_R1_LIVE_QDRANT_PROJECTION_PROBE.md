# Changelog 0287-r7-r15-r3-r11-r1

- Added a preview-first single-object live projection plan and digest gate.
- Added exact Qdrant point readback through the existing executor membrane.
- Forced `with_vectors=False` during readback.
- Persisted reconstructible projection metadata in SQL after acknowledged upsert.
- Verified Qdrant references by rehydrating the source from SQL authority.
- Added a live CLI using the installed PostgreSQL, OpenVINO E5 and Qdrant ports.
- Added no Scheduler, collection mutation, deletion or alias switch.
