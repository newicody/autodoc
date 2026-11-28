# 0287 r16-r4-r3-r2

- keeps the Projects workflow default Issue permission read-only;
- delegates only the advisory-comment mutation to a dedicated scoped secret;
- uploads all three correlated artifacts before publishing the comment;
- reuses the existing v2 preview builder and idempotent publisher;
- requires plan-digest confirmation and GitHub readback;
- does not mutate ProjectV2 or start Autodoc local execution.
