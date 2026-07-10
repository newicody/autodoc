import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_0267_tool_builds_local_handoff(tmp_path):
    closed=tmp_path/'closed.json'; passive=tmp_path/'passive.json'; output=tmp_path/'handoff.json'
    closed.write_text(json.dumps({'valid':True,'sql_ref':'sql:inference_context:tool','embedding_ref':'embedding:passage:tool','projection_point_count':1,'recall_hit_count':1,'hydrated_count':1,'missing_count':0,'sql_remains_authority':True,'qdrant_projection_recall_refs_only':True,'executes_runtime':False,'starts_postgresql':False,'starts_openvino':False,'starts_qdrant':False}),encoding='utf-8')
    passive.write_text(json.dumps({'valid':True,'passive_supervisor_observation_only':True,'accepted_fact_count':3,'rejected_fact_count':0,'command_like_fact_count':0,'runtime_violation_count':0,'publishes_events':False,'findings':[]}),encoding='utf-8')
    r=subprocess.run([sys.executable,'tools/build_github_scan_once_handoff_0267.py','--closed-frame-report',str(closed),'--passive-report',str(passive),'--repository','newicody/autodoc','--output',str(output),'--format','summary'],cwd=ROOT,text=True,capture_output=True,check=True)
    assert 'github_scan_once_handoff_valid=True' in r.stdout
    payload=json.loads(output.read_text(encoding='utf-8')); assert payload['schema']=='missipy.github_scan_once_handoff.v1'; assert payload['remote_mutation_allowed'] is False; assert payload['github_review_surface_only'] is True
