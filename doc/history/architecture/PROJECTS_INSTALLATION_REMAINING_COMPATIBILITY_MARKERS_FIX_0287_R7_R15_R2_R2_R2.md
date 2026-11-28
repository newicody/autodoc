# Projects installation remaining compatibility markers fix — 0287-r7-r15-r2-r2-r2

## Boundary

This correction restores only historical strings consumed by cumulative rule
tests. It does not reopen or alter the readiness implementation.

```text
r15-r2-r2 readiness implementation
              |
              v
r15-r2-r2-r1 concise guide (375 lines)
              |
              v
restore four locked compatibility markers
              |
              v
INSTALLATION.md (379 lines)
              |
              v
full cumulative tests/rules compatibility
```

The executable digest path remains preview-first and uses the actual extracted
`$PLAN_DIGEST`. Legacy placeholders remain non-executable compatibility text.
