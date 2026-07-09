# Changelog 0250 - Scheduler intention event emission

## r1

Added a read-only emission surface that derives immutable EventBus-shaped
envelopes from typed Scheduler intentions.

The patch validates required attributes, reference fields, redaction, and refs-only
payload policy without creating EventBus or publishing events.
