#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rp=Path(os.environ.get("AUTODOC_REQUEST","out/authoritative_request.json")); ap=Path(os.environ.get("AUTODOC_ADVISORY","out/copilot_advisory.json")); req=json.loads(rp.read_text())
 adv=json.loads(ap.read_text()) if ap.is_file() else None
 if adv and (adv["origin_frame_id"]!=req["origin_frame_id"] or adv["ticket_revision_id"]!=req["ticket_revision_id"] or adv["request_artifact_ref"]!=req["artifact_ref"]): raise ValueError("request/advisory correlation mismatch")
 ident=req["artifact_ref"]+sha(rp)+(sha(ap) if adv else "")
 payload={"schema":"missipy.github.dual_artifact_manifest.v1","manifest_ref":"github-dual-manifest:"+hashlib.sha256(ident.encode()).hexdigest()[:16],"origin_frame_id":req["origin_frame_id"],"ticket_revision_id":req["ticket_revision_id"],"request_artifact_ref":req["artifact_ref"],"request_filename":rp.name,"request_sha256":sha(rp),"advisory_artifact_ref":None if adv is None else adv["artifact_ref"],"advisory_filename":None if adv is None else ap.name,"advisory_sha256":None if adv is None else sha(ap),"request_is_authority":True,"advisory_is_authority":False}
 out=Path(os.environ.get("AUTODOC_MANIFEST","out/dual_artifact_manifest.json")); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
