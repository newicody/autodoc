from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTION = ROOT / "tools/run_scheduler_managed_embedding_qdrant_projection_0262.py"
RECALL = ROOT / "tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py"
CORE = ROOT / "src/context/production_prototype_smoke_composition_0269.py"
CLI = ROOT / "tools/run_production_prototype_smoke_composition_0269.py"
RULE = ROOT / "doc/code-rules/0271_qdrant_client_live_projection_recall_binding_rule.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0271_QDRANT_CLIENT_LIVE_PROJECTION_RECALL_BINDING_CHANGED_FILES.md"


def test_existing_0262_and_0263_tools_inject_the_0271_executor() -> None:
    projection = PROJECTION.read_text(encoding="utf-8")
    recall = RECALL.read_text(encoding="utf-8")
    assert "build_qdrant_client_projection_executor" in projection
    assert "allow_write=True" in projection
    assert "allow_search=False" in projection
    assert "build_qdrant_client_projection_executor" in recall
    assert "allow_write=False" in recall
    assert "allow_search=True" in recall
    assert "--live-qdrant" in projection
    assert "--live-qdrant" in recall


def test_live_binding_keeps_service_and_shm_boundaries() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in (PROJECTION, RECALL, CORE, CLI))
    forbidden = (
        "rc-service",
        "rc-update",
        "subprocess.Popen",
        "RuntimeManager",
        "Scheduler.run(",
        "multiprocessing.shared_memory",
        "mmap.mmap",
    )
    for phrase in forbidden:
        assert phrase not in combined
    assert 'payload["touches_shm"] = False' in PROJECTION.read_text(encoding="utf-8")
    assert 'payload["touches_shm"] = False' in RECALL.read_text(encoding="utf-8")


def test_api_key_value_is_not_serialized_or_forwarded_in_0269_argv() -> None:
    projection = PROJECTION.read_text(encoding="utf-8")
    recall = RECALL.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8")
    assert "os.environ.get(args.qdrant_api_key_env)" in projection
    assert "os.environ.get(args.qdrant_api_key_env)" in recall
    assert '"--qdrant-api-key",' not in core
    assert "--qdrant-api-key-env" in core


def test_rule_and_manifest_lock_reuse_and_live_opt_in() -> None:
    rule = RULE.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "existing QdrantProjectionExecutor" in rule
    assert "live opt-in" in rule
    assert "SQL remains the durable authority" in rule
    assert "tools/run_scheduler_managed_embedding_qdrant_projection_0262.py" in manifest
    assert "tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py" in manifest
    assert "src/context/production_prototype_smoke_composition_0269.py" in manifest
