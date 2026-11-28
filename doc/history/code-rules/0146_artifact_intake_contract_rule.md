# 0146 code rule — artifact intake contract first

Artifact intake must be represented by src/context/artifact_intake_contract.py before route refs or job refs are dynamically derived.

Rules:

- the intake contract must remain pure
- do not import OpenVINO or Qdrant clients from the artifact intake contract
- do not import Scheduler or RouteProxy runtime objects from the artifact intake contract
- do not derive dynamic RouteProxy refs in 0146
- use `artifact_ref`, `artifact_kind`, `artifact_path`, `text_kind`, `sql_ref`, `collection`, `dimension`, `route_root`, and `vector_indexing_job_ref` as explicit fields
- Scheduler remains the orchestrator
- SQLContextStore remains durable authority
- Qdrant remains projection/recall only

0147 may derive dynamic route refs from this contract, but 0146 only defines and serializes the intake envelope.
