# 0082 - Route notification eventfd primitive

## Added

- `runtime.route_notification`
- `RouteNotifier`
- eventfd backend through:
  - Python `os.eventfd` when available
  - libc `eventfd` through `ctypes` fallback
- non-blocking pipe fallback
- selector-friendly `fileno()`
- `notify()`, `drain()`, `wait_once()`
- tests integrating notification with mmap route write/drain

## Not added

- No daemon.
- No service.
- No OpenRC.
- No ControlFS watcher.
- No Scheduler wiring.
- No lease handoff.
- No live mmap resize.
- No CLI.
