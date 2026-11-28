# Changelog 0242 - production server component registry

## r1

Added a registry-only component table derived from the validated production
server INI file.

The registry validates factory reference syntax, computes dependency order, and
marks command/observation path components without importing or calling factories.
