# Changelog — Part 8.2 Roadmap B Cell Lens Architecture Update

## Added

- `doc/maintenance/ROADMAP_B_CELL_LENS_INSERTION.md`
- `doc/docs/architecture/CELL_LENS_ARCHITECTURE.md`
- `doc/code-rules/CELL_LENS_OBSERVATION_RULES.md`
- Tests that guard the new visualisation direction.

## Clarified

- Visualization is a pure observation consumer.
- EventBus/recorder/replay are the observation path.
- Scheduler/typed commands are the only command path.
- `missipy.cell.v1` is the first required snapshot contract.
- VisPy belongs at the visualization boundary only.
- Mobile view belongs in Phase 10 as local SSE/browser window.
- Real-time optimization is out of scope.
