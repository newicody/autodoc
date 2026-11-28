# Changelog 0247 - Qdrant collection readiness

## r1

Added Qdrant collection readiness aligned with OpenVINO embedding readiness.

The patch checks vector dimension, distance, normalized-vector expectation, and
mandatory payload fields for SQL rehydration and embedding provenance without
calling Qdrant.
