from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_contract_is_immutable_and_authority_locked():
 t=(ROOT/"src/context/github_dual_artifact_contract_0275.py").read_text()
 for m in ("@dataclass(frozen=True,slots=True)","request_is_authority:bool=True","advisory_is_authority:bool=False","usable_as_authority:bool=False","request and advisory must be physically distinct"):
  assert m in t
def test_no_runtime_or_network_imports():
 t=(ROOT/"src/context/github_dual_artifact_contract_0275.py").read_text()
 for m in ("Scheduler(","EventBus(","requests","urllib.request","openvino","qdrant"):
  assert m not in t
