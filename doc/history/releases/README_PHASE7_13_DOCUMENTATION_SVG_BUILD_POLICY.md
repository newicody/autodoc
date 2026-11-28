# Phase 7.13 — Documentation SVG Build Policy

Phase 7.13 adds a local SVG build policy tool.

It allows operators to run the documentation `make` workflow and then clean
generated SVG files that violate the repository policy:

```text
doc/docs/architecture/context/*.svg
```

The phase does not modify the makefile. It adds a post-build cleanup/check step.
