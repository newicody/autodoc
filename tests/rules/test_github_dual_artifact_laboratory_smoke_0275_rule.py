from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_smoke_reuses_existing_0274_surface_and_gate():
 t=(ROOT/"src/context/github_dual_artifact_laboratory_smoke_0275.py").read_text()
 for m in ("run_github_dual_artifact_source_candidate_intake","SourceCandidateDecision","run_fake_laboratory_existing_scheduler_closed_loop_smoke","promote or merge","publication_gate_required"):
  assert m in t
 for bad in ("Scheduler(","PriorityQueue(","EventBus(","urllib.request"):
  assert bad not in t
