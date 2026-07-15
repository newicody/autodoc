# Multi-laboratory evidence digest deduplication

## Flow

```text
r2 aggregate
+ r3 provenance chains
→ validate exact provenance
→ group by evidence content SHA-256
→ deterministic canonical evidence_ref
→ preserve duplicate aliases and all source/provenance/laboratory refs
→ deduplication_digest
```

The original evidence items are never deleted. The result exposes both
`retained_evidence_items` and `canonical_evidence_items`.

## Source identity

The content digest remains the authority for equivalence. A separate SHA-256 of
the opaque `source_ref` records source identity. Same content observed through
multiple sources is counted as corroboration, not discarded.

## Claim variants

A duplicate content group can contain multiple claim signatures. Those member
references are retained in `claim_variant_evidence_refs` for r5 contradiction
detection.

R4 does not interpret which claim is correct and does not authorize selection.
