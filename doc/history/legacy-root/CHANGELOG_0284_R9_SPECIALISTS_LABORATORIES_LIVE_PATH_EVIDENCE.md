# Changelog — 0284-r9 specialists/laboratories live-path evidence

- added an immutable, effect-free live-path evidence command and result;
- correlated repository, run, policy decision, SourceCandidate, SQL and
  embedding references from one r7 result;
- enforced exact E5/Qdrant dimension `384` and rejected dimension `385`;
- converted verified r7 evidence into the existing r8 operational evidence;
- reused the existing r8 closure audit for the final decision;
- added deterministic SHA-256 result and evidence digests;
- added a thin local verifier with atomic report writing and no execute mode;
- refreshed `doc/README_CURRENT.md` to the actual 0284 state and 0285 roadmap;
- reviewed and updated the cumulative `newicody/projects` installation guide;
- added context tests, architecture-rule tests, architecture docs and report;
- added no external dependency and no parallel runtime.
