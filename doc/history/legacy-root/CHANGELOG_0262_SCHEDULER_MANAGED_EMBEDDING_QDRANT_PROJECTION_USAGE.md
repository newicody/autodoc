# Changelog 0262 - Scheduler-managed embedding to Qdrant projection usage

## r1

Adds the 0262 embedding to Qdrant projection usage path.

This patch reuses the existing OpenVINO embedding vector/batch classes and the
existing Qdrant projection adapter. SQL remains the durable authority and Qdrant
points carry `payload.sql_ref`.
