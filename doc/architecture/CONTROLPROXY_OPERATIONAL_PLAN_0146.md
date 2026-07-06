# 0146 operational plan — artifact intake contract

0146 adds a typed input contract to the local artifact vector indexing runner.

```text
artifact text
-> artifact_intake_contract.json
-> existing Scheduler vector indexing smoke
-> existing RouteProxyRuntime frames
-> existing OpenVINO/Qdrant smoke tools
-> local artifact report
```

The contract does not change the authority model: Scheduler stays in control, RouteProxyRuntime handles frame IO, SQL remains durable authority, and Qdrant remains projection/recall.
