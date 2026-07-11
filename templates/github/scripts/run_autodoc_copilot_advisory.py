#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os, subprocess

def canonical(p): return (json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
def parse(text):
 t=text.strip();
 if t.startswith("```"): t="\n".join(t.splitlines()[1:-1]); t=t.removeprefix("json").lstrip()
 p=json.loads(t)
 for k in ("summary","suggested_route","assumptions","questions","risks","confidence"):
  if k not in p: raise ValueError(f"Copilot response missing {k}")
 return p
def main():
 req_path=Path(os.environ.get("AUTODOC_REQUEST","out/authoritative_request.json")); req=json.loads(req_path.read_text())
 prompt=("Return one JSON object only with keys summary, suggested_route, assumptions, questions, risks, confidence. "
         "Treat the following GitHub request as authoritative. Do not modify it, do not call tools, do not authorize publication.\n"+json.dumps({"title":req["title"],"body":req["body"],"labels":req.get("labels",[])},ensure_ascii=False))
 command=os.environ.get("AUTODOC_COPILOT_COMMAND","copilot")
 proc=subprocess.run([command,"-p",prompt,"-s","--no-ask-user","--deny-tool=write","--deny-tool=shell"],capture_output=True,text=True,timeout=int(os.environ.get("AUTODOC_COPILOT_TIMEOUT","180")),check=True)
 parsed=parse(proc.stdout); response_digest=hashlib.sha256(proc.stdout.encode()).hexdigest(); prompt_digest=hashlib.sha256(prompt.encode()).hexdigest()
 ref="github-advisory:"+hashlib.sha256((req["artifact_ref"]+response_digest).encode()).hexdigest()[:16]
 payload={"schema":"missipy.github.copilot_advisory.v1","origin_frame_id":req["origin_frame_id"],"ticket_revision_id":req["ticket_revision_id"],"artifact_ref":ref,"request_artifact_ref":req["artifact_ref"],"prompt_digest":prompt_digest,"response_digest":response_digest,"summary":str(parsed["summary"]),"suggested_route":str(parsed["suggested_route"]),"assumptions":list(parsed["assumptions"]),"questions":list(parsed["questions"]),"risks":list(parsed["risks"]),"confidence":float(parsed["confidence"]),"producer_kind":"github_copilot_cli","trusted":False,"usable_as_hint":True,"usable_as_authority":False}
 out=Path(os.environ.get("AUTODOC_ADVISORY","out/copilot_advisory.json")); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(canonical(payload))
if __name__=="__main__": main()
