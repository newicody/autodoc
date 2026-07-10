# Changelog 0261 - Scheduler-managed sql_ref to OpenVINO embedding usage

## r1

Adds the 0261 SQL rehydrate to OpenVINO/E5 passage embedding usage path.

This patch does not involve Qdrant. It reuses `DbApiSqlContextStore.get_record`
and the existing E5/OpenVINO pipeline surface.
