# Installed runtime provider default compatibility

```text
love_installed_runtime.ini
  [provider] factory =
        |
        v
DEFAULT_INSTALLED_RUNTIME_PROVIDER
        |
        v
love_manual_installed_runtime_provider_0287.build_installed_runtime_ports
```

The empty setting is not a fake fallback.  It selects the one canonical
provider introduced by r15-r3-r2.  Explicit non-empty providers remain subject
to the existing real-backend marker checks.
