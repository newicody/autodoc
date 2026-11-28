# Changelog — 0165 Project push frame and fcron ConfigObj

0165 adds the project push frame contracts and ConfigObj/fcron table contract.

## Added

- ConfigObj-style example config
- project push frame artifact-family contracts
- config validation and idempotent fcron table rendering
- config-check tool
- tests
- rule tests
- architecture doc
- code rule
- runtime DOT source
- manifest
- phase test report

## Boundary

No GitHub API call, no fcron start, no OpenRC management, no SQL/Qdrant write,
no Scheduler/LLM/OpenVINO execution.
