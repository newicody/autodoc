# Manifest 0287-r7-r15-r3-r2

## Added

- `src/context/love_manual_runtime_configuration_0287.py`
- `src/context/love_manual_runtime_readiness_0287.py`
- `src/context/love_manual_installed_runtime_provider_0287.py`
- `tools/check_love_installed_runtime_0287.py`
- targeted context, tool and rule tests
- phase report, changelog and architecture documentation

## Modified

- `config/love_installed_runtime.example.ini`

## Boundaries

- no second Scheduler;
- no new backend implementation;
- no SQL or Qdrant write during readiness;
- no OpenVINO inference during readiness;
- no secret value serialized;
- SQL remains durable authority;
- Qdrant collection/alias is E5-384 Cosine.
