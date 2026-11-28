# Correlated fetched Actions run readiness

```text
completed newicody/projects runs
                |
                v
existing bounded Actions artifact fetch
                |
                v
existing local dataset sync + artifact dedup
                |
                v
group records by run_id
        |                       |
        v                       v
exact request+advisory+manifest missing/expired/duplicate
        |                       |
        v                       v
ready_runs                  deferred_runs
        |
        v
future local closed-loop consumer
```

No loop, service, Scheduler, laboratory or publication adapter is introduced.
