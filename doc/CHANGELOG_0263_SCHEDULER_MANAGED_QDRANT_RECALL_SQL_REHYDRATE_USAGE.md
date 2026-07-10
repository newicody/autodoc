# Changelog 0263 - Scheduler-managed Qdrant recall to SQL rehydrate usage

## r1

Adds the 0263 recall to SQL rehydrate usage path.

This patch reuses the existing Qdrant recall dataclasses and SQL context store
read surface. Qdrant remains reference-only; SQL remains the durable authority.
