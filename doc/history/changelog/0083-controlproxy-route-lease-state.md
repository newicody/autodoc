# 0083 - ControlProxy route lease state

## Added

- `runtime.controlproxy_route_lease`
- route lease schema:
  - `missipy.controlproxy.route_lease.v1`
- transition fact schema:
  - `missipy.controlproxy.route_lease_transition.v1`
- lease state files:
  - `active/routes/<route_id>/lease.json`
- status fields:
  - `lease_state`
  - `current_lease_id`
  - `current_lease_holder`
  - `current_lease_scope`
  - `current_lease_updated_at`
  - `previous_lease_state`
- allowed state machine:
  - `not_leased -> leased -> active -> draining -> closed`
  - `leased -> closed`

## Not added

- No daemon.
- No service.
- No OpenRC.
- No ControlFS watcher.
- No Scheduler wiring.
- No security policy decision.
- No mmap creation.
- No notification.
- No inter-process lock.
- No CLI.

## r2

Restores exact rule-test wording: `There is no daemon, no service and no CLI.`
