# GitHub dual-artifact SourceCandidate intake — 0275-r4

The local intake verifies manifest SHA-256 values and request/advisory
correlation. It builds SourceCandidate title and body exclusively from the
authoritative request. Advisory content is not copied into the candidate; only
its ref and response digest are retained as hint provenance.

The result is unauthorized local material. It creates no Scheduler route,
performs no SQL/Qdrant write and makes no GitHub call.
