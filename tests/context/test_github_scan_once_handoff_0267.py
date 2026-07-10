from context.github_scan_once_handoff_0267 import GitHubScanOnceHandoffRequest, build_github_scan_once_handoff
CLOSED_FRAME={'valid':True,'sql_ref':'sql:inference_context:test','embedding_ref':'embedding:passage:test','projection_point_count':1,'recall_hit_count':1,'hydrated_count':1,'missing_count':0,'sql_remains_authority':True,'qdrant_projection_recall_refs_only':True,'executes_runtime':False,'starts_postgresql':False,'starts_openvino':False,'starts_qdrant':False}
PASSIVE_REPORT={'valid':True,'passive_supervisor_observation_only':True,'accepted_fact_count':3,'rejected_fact_count':0,'command_like_fact_count':0,'runtime_violation_count':0,'publishes_events':False,'findings':[{'finding_ref':'passive-supervisor-finding:0266:test','severity':'info','finding_kind':'observation_fact_accepted','command':False}]}
def test_github_scan_once_handoff_is_local_review_artifact():
    h=build_github_scan_once_handoff(closed_frame=CLOSED_FRAME,passive_report=PASSIVE_REPORT,request=GitHubScanOnceHandoffRequest(repository='newicody/autodoc'),source_reports={'closed_frame_report':'0264.json','passive_supervisor_report':'0266.json'}).to_mapping()
    assert h['valid'] is True; assert h['handoff_ref'].startswith('github-scan-once-handoff:'); assert h['local_authority'] is True; assert h['github_review_surface_only'] is True; assert h['remote_mutation_allowed'] is False; assert h['creates_issue'] is False; assert h['updates_project'] is False; assert h['pushes_commit'] is False; assert h['scan_once'] is True
def test_github_scan_once_handoff_rejects_remote_mutation():
    h=build_github_scan_once_handoff(closed_frame=CLOSED_FRAME,passive_report=PASSIVE_REPORT,request=GitHubScanOnceHandoffRequest(repository='newicody/autodoc',allow_remote_mutation=True),source_reports={})
    assert h.valid is False; assert 'remote mutation is forbidden in 0267' in h.issues
def test_github_scan_once_handoff_requires_passive_clean_report():
    h=build_github_scan_once_handoff(closed_frame=CLOSED_FRAME,passive_report={**PASSIVE_REPORT,'command_like_fact_count':1},request=GitHubScanOnceHandoffRequest(repository='newicody/autodoc'),source_reports={})
    assert h.valid is False; assert 'PassiveSupervisor report must have zero command-like facts' in h.issues
