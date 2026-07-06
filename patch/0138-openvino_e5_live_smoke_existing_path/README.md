# 0138 — OpenVINO/E5 live smoke existing path

Adds an operator smoke command that reuses the existing OpenVINO/E5 CLI and inference membranes.

Default mode is dry-run. Backend execution requires `--execute`.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_openvino_e5_live_smoke_existing_path_0138.py tests/rules/test_openvino_e5_live_smoke_existing_path_0138_rule.py
```

Run the smoke plan:

```bash
python tools/run_openvino_e5_live_smoke.py . --format markdown
```

Run the real backend smoke:

```bash
python tools/run_openvino_e5_live_smoke.py . \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --execute
```
