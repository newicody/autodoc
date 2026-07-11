from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_audit_locks_reuse_and_separation():
 text=(ROOT/"doc/architecture/GITHUB_DUAL_ARTIFACT_REUSE_AUDIT_0275.md").read_text()
 for marker in ("authoritative ticket artifact","advisory-only Copilot opinion","No global GitHub manager","0276-r4","advisory evidence only"):
  assert marker in text
def test_audit_graph_keeps_existing_path():
 text=(ROOT/"doc/docs/architecture/runtime/275_r1_github_dual_artifact_reuse_audit.dot").read_text()
 for marker in ("Manifest -> Scan","Scan -> Candidate","Candidate -> Laboratory","Review -> RemoteGate"):
  assert marker in text
