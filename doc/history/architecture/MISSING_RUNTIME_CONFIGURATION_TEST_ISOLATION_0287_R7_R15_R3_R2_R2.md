# Missing runtime configuration test isolation

```text
production invocation without --config
  -> may read .var/config/love_actions_closed_loop.ini

test for missing runtime configuration
  -> explicit empty temporary love.ini
  -> explicit temporary project.ini
  -> deterministic operator-facing error
```

The production command must continue to discover a real installed local
configuration.  The negative-path test must not depend on whether an operator
has configured that file on the machine running the suite.
