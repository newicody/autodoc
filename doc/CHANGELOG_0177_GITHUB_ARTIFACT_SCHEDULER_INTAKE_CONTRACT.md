# Changelog — 0177 GitHub artifact scheduler intake contract

## Added

- Pure scheduler intake candidate contract for GitHub artifact/server dataset
  observations.
- Optional authorized route request mapping using existing
  `scheduler_route_request_mapping(...)`.
- Tests and rules locking that no Scheduler, EventBus, Dispatcher, PriorityQueue,
  GitHub API, network, conversion, inference, SQL, Qdrant, VisPy, or route
  handler execution is introduced.

## Not changed

- No Scheduler modification.
- No route execution.
- No bus publication.
- No GitHub API.
