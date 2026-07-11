from pathlib import Path
import json, os, stat, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def test_scripts_build_three_separate_artifacts(tmp_path):
 event={"issue":{"number":7,"title":"Build it","body":"Details","html_url":"https://example/7","created_at":"2026-07-11T00:00:00Z","labels":[{"name":"feature"}]},"repository":{"full_name":"newicody/autodoc"},"sender":{"login":"eric"}}
 ep=tmp_path/"event.json"; ep.write_text(json.dumps(event)); out=tmp_path/"out"; fake=tmp_path/"copilot"; fake.write_text('#!/bin/sh\nprintf \'%s\\n\' \'{"summary":"S","suggested_route":"laboratory","assumptions":[],"questions":[],"risks":[],"confidence":0.7}\'\n'); fake.chmod(fake.stat().st_mode|stat.S_IEXEC)
 env=dict(os.environ,GITHUB_EVENT_PATH=str(ep),GITHUB_REPOSITORY="newicody/autodoc",GITHUB_RUN_ID="99",AUTODOC_OUTPUT=str(out/"authoritative_request.json"))
 subprocess.run([sys.executable,str(ROOT/"templates/github/scripts/build_autodoc_authoritative_request.py")],env=env,check=True)
 env.update(AUTODOC_REQUEST=str(out/"authoritative_request.json"),AUTODOC_ADVISORY=str(out/"copilot_advisory.json"),AUTODOC_COPILOT_COMMAND=str(fake))
 subprocess.run([sys.executable,str(ROOT/"templates/github/scripts/run_autodoc_copilot_advisory.py")],env=env,check=True)
 env.update(AUTODOC_MANIFEST=str(out/"dual_artifact_manifest.json")); subprocess.run([sys.executable,str(ROOT/"templates/github/scripts/build_autodoc_dual_manifest.py")],env=env,check=True)
 req=json.loads((out/"authoritative_request.json").read_text()); adv=json.loads((out/"copilot_advisory.json").read_text()); man=json.loads((out/"dual_artifact_manifest.json").read_text())
 assert req["authoritative"] is True and adv["usable_as_authority"] is False
 assert man["request_filename"]!=man["advisory_filename"]
