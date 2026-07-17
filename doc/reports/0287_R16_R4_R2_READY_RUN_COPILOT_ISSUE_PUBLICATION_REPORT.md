# Report — ready-run Copilot Issue publication r16-r4-r2

## Audit conclusion

The advisory artifact was already produced correctly, fetched locally, and
correlated into `ready_runs`.  The missing link was a local composition from one
ready run to the existing controlled Issue-comment adapter.

Moving publication into GitHub Actions was rejected because established rules
require `issues: read` and prohibit workflow self-authorization.  This unit
therefore adds only a bounded local connector.

## Operational behavior

- newest uncompleted ready runs are selected;
- all three artifact ids must belong to the same run;
- local files are resolved below the raw dataset;
- the existing preview builder validates schemas, references, and SHA-256;
- the existing publisher plans against current Issue comments;
- execute mode confirms that exact plan digest;
- state is persisted only after `created` or `replay-noop` with verified
  readback.

## Known deferred work

- periodic chaining of fetch then publication;
- ProjectV2 `Avis Copilot` field projection;
- durable SQL intake;
- operator decision and laboratory execution;
- final specialist result publication.
