# Manual runtime configuration and canonical provider binding

```text
.var/config/love_installed_runtime.ini
  ├─ PostgreSQL coordinates + password environment name
  ├─ Qdrant alias/profile + optional API-key environment name
  └─ OpenVINO model/device/E5 profile
              │
              ▼
check_love_installed_runtime_0287.py
  ├─ PostgreSQL SELECT
  ├─ Qdrant GET readiness/readback
  └─ OpenVINO read/compile without inference
              │
              ▼
canonical server bootstrap (next unit)
  └─ register exact existing ImportedActionsRuntimePorts
              │
              ▼
love_manual_installed_runtime_provider_0287
  └─ validate readiness and return those exact ports
```

No Scheduler, SQL authority, OpenVINO executor, Qdrant client or laboratory is
constructed by this provider.
