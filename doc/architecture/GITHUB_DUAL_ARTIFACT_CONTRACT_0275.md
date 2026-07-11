# GitHub dual-artifact contract — 0275-r2

The request and Copilot advice are separate immutable files joined by a digest
manifest. The request is the only authority. Advice is untrusted, hint-only and
cannot replace title/body, make a SourceCandidate decision or permit mutation.

The manifest verifies origin frame, ticket revision, refs, filenames and SHA-256
digests. It can legally omit the optional advisory while retaining the request.

No Scheduler, network, GitHub client, SQL or Qdrant behavior exists here.
