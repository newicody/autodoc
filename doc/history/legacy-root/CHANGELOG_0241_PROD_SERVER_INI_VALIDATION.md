# Changelog 0241 - production server INI validation

## r1

Added stdlib-only validation for the initial production server INI file.

The validation covers OpenRC launcher fields, component factories, PostgreSQL
sections, Qdrant collection shape, GitHub artifact exchange settings, and
EventBus attribute allowlists.
