# 0124 — Server-oriented deliberation cycle

Added local contracts for the server/specialist deliberation loop:

- `ServerOrientation` from an imported GitHub artifact and SQL source candidate;
- `SpecialistPreliminaryOpinion` for first specialist answers;
- `RefinedSpecialistDemand` after server recomposition;
- `DeliberationRound` with local convergence state;
- `SpecialistBusStatistics` for passive supervision and future VisPy views;
- `FinalArtifactEnvelope` as a final-only exchange artifact.

The patch corrects the boundary: GitHub exchanges artifacts only; the local server performs orientation, navettes, recomposition, and convergence.
