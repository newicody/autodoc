# Manifest 0287-r7-r15-r3-r15

## Modified

- `src/context/love_installed_runtime_factory_0287.py`

## Added

- `src/context/love_tool_bounded_installed_runtime_composer_0287.py`
- focused composer and factory tests;
- architecture rule test;
- phase report, changelog, architecture and graph evidence.

## Locked boundaries

- one canonical Scheduler, owned by the tool invocation;
- no Scheduler run started inside the provider;
- SQL remains durable authority;
- Qdrant stores references and reconstructible vectors only;
- E5 dimension remains 384;
- named dense and sparse vectors are mandatory;
- separate explicit write/search gates;
- Qdrant closes before PostgreSQL;
- no remote mutation;
- no fallback backend or laboratory manager.
