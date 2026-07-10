# Changelog 0265 - Closed ResultFrame EventBus observation

## r1

Adds an observation-only EventBus surface for the 0264 closed ResultFrame.

The patch reuses `contracts.event.Event`, `contracts.event.EventType`, and
`kernel.event_bus.EventBus`. Events are fact-only and have no Request.
