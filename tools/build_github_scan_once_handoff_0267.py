#!/usr/bin/env python3
"""Build a local GitHub scan-once handoff from closed frame reports."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC_ROOT=ROOT/'src'
for p in (str(SRC_ROOT),str(ROOT)):
    if p not in sys.path: sys.path.insert(0,p)
from context.github_scan_once_handoff_0267 import GitHubScanOnceHandoffRequest, build_github_scan_once_handoff, load_json, write_handoff
DEFAULT_CLOSED_FRAME_REPORT=ROOT/'.var/reports/scheduler_managed_closed_result_frame_0264.json'
DEFAULT_PASSIVE_REPORT=ROOT/'.var/reports/passive_supervisor_closed_result_frame_observation_0266.json'
def parse_args():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--closed-frame-report',default=str(DEFAULT_CLOSED_FRAME_REPORT)); p.add_argument('--passive-report',default=str(DEFAULT_PASSIVE_REPORT)); p.add_argument('--repository',default='newicody/autodoc'); p.add_argument('--operator-intent',default='review_closed_result_frame'); p.add_argument('--target-surface',default='github_project_review'); p.add_argument('--policy-decision-id',default=''); p.add_argument('--allow-remote-mutation',action='store_true'); p.add_argument('--output',default=''); p.add_argument('--format',choices=('json','summary'),default='json'); return p.parse_args()
def main():
    a=parse_args(); closed=Path(a.closed_frame_report); passive=Path(a.passive_report)
    req=GitHubScanOnceHandoffRequest(repository=a.repository,operator_intent=a.operator_intent,target_surface=a.target_surface,policy_decision_id=a.policy_decision_id,allow_remote_mutation=a.allow_remote_mutation)
    handoff=build_github_scan_once_handoff(closed_frame=load_json(closed),passive_report=load_json(passive),request=req,source_reports={'closed_frame_report':str(closed),'passive_supervisor_report':str(passive)})
    payload=handoff.to_mapping()
    if a.output: write_handoff(Path(a.output),handoff)
    if a.format=='summary': print('github_scan_once_handoff_valid='+f"{payload['valid']} issues={len(payload['issues'])} handoff_ref={payload.get('handoff_ref') or '-'} repository={payload['request']['repository']} sql_ref={payload.get('sql_ref') or '-'} remote_mutation_allowed={payload['remote_mutation_allowed']} scan_once={payload['scan_once']}")
    else: print(json.dumps(payload,indent=2,sort_keys=True))
    return 0 if payload['valid'] else 2
if __name__=='__main__': raise SystemExit(main())
