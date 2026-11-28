# OpenRC launcher minimal readiness - 0268

## Intent

0268 prepares a local OpenRC/launcher readiness envelope after the closed loop,
observation surfaces and GitHub scan-once handoff:

```text
0264 closed ResultFrame
+ 0265 EventBus observation-only report
+ 0266 PassiveSupervisor observation-only report
+ 0267 GitHub scan-once handoff
+ phase-0260 local SQLite file metadata
-> OpenRC launcher readiness
```

OpenRC/system/admin starts external services. Scheduler owns Autodoc runtime objects that use those services.

## r2 readiness inputs

0268-r2 verifies the local presence and validity of outputs 0264, 0265, 0266 and
0267. It also verifies, by filesystem metadata only, that the expected SQLite
file exists and is non-empty:

```text
.var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3
```

The SQLite file is not opened, queried or written. PostgreSQL, Qdrant and
OpenVINO are described as expected external capabilities whose process authority
belongs to OpenRC/OS/admin.

## Boundary

0268 does not install, enable, or start services. It renders an OpenRC service
file as text and emits a readiness report.

It does not call `rc-service`, `rc-update`, PostgreSQL, OpenVINO, Qdrant, GitHub,
or any runtime executor. It does not write SQL, modify Scheduler.run, or
introduce a RuntimeManager.

## Output

The readiness report contains:

```text
readiness_ref
service_spec
rendered_openrc_script
source_reports
closed_frame_summary
eventbus_observation_summary
passive_supervisor_summary
github_handoff_summary
sqlite_database_summary
checks
external_services_expected
external_process_authority
```

## Next step

0269 can run the prototype production smoke by composing the already validated
reports and readiness surfaces.
