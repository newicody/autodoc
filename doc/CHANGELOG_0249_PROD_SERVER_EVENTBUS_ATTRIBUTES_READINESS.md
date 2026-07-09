# Changelog 0249 - EventBus advanced attribute readiness

## r1

Added EventBus advanced attribute readiness for required envelope fields,
reference attributes, redacted fields, and refs-only payload policy.

The patch composes projection path readiness so future SQL/OpenVINO/Qdrant
projection events can expose references without placing large payloads on the
EventBus.
