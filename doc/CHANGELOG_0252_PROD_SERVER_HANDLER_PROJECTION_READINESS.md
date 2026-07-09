# Changelog 0252 - handler projection readiness

## r1

Added handler projection readiness that derives a future Qdrant projection request
from the SQL controlled write handler frame.

The patch composes SQL handler readiness, OpenVINO embedding readiness, and
Qdrant collection readiness without running inference or writing Qdrant points.
