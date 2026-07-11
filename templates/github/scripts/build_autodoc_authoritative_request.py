#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os

def canonical(p): return (json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
def main():
 event=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
 issue=event.get("issue") or {}; repo=os.environ.get("GITHUB_REPOSITORY",event.get("repository",{}).get("full_name",""))
 number=int(issue.get("number") or 0); updated=str(issue.get("updated_at") or issue.get("created_at") or "")
 origin=f"github-frame:{repo}:{number}:{os.environ.get('GITHUB_RUN_ID','local')}"
 revision=f"github-ticket-revision:{hashlib.sha256((repo+str(number)+updated+str(issue.get('title',''))+str(issue.get('body',''))).encode()).hexdigest()[:16]}"
 ref=f"github-request:{repo}:{number}:{revision.rsplit(':',1)[-1]}"
 payload={"schema":"missipy.github.authoritative_request.v1","origin_frame_id":origin,"ticket_revision_id":revision,"artifact_ref":ref,"repository":repo,"issue_number":number,"title":str(issue.get("title") or "Untitled GitHub request"),"body":str(issue.get("body") or "No description supplied."),"issue_url":str(issue.get("html_url") or ""),"labels":[str(x.get("name")) for x in issue.get("labels",[]) if x.get("name")],"actor":str((event.get("sender") or {}).get("login") or ""),"event_name":os.environ.get("GITHUB_EVENT_NAME","issues"),"metadata":{"github_sha":os.environ.get("GITHUB_SHA","")},"authoritative":True,"advisory_content_embedded":False,"remote_mutation_requested":False}
 out=Path(os.environ.get("AUTODOC_OUTPUT","out/authoritative_request.json")); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(canonical(payload))
if __name__=="__main__": main()
