from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_intake_uses_existing_source_candidate_and_no_scheduler():
 t=(ROOT/"src/context/github_dual_artifact_source_candidate_intake_0275.py").read_text()
 for m in ("build_source_candidate","SourceCandidateOrigin(kind=\"github\"","advisory_content_copied\":False","scheduler_route_created:bool=False"):
  assert m in t
 for bad in ("Scheduler(","EventBus(","upsert_record","import qdrant","urllib.request"):
  assert bad not in t
