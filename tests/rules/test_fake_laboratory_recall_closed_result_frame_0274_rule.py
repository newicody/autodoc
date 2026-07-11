from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'src/context/fake_laboratory_recall_closed_result_frame_0274.py'
ARCH = ROOT / 'doc/architecture/FAKE_LABORATORY_RECALL_CLOSED_RESULT_FRAME_0274.md'
GRAPH = ROOT / 'doc/docs/architecture/runtime/274_r4_fake_laboratory_recall_closed_result_frame.dot'
MANIFEST = ROOT / 'doc/manifests/MANIFEST_0274_R4_FAKE_LABORATORY_RECALL_CLOSED_RESULT_FRAME_CHANGED_FILES.md'
REPORT = ROOT / 'PHASE0274_R4_FAKE_LABORATORY_RECALL_CLOSED_RESULT_FRAME_TEST_REPORT.md'


def test_r4_reuses_existing_0261_to_0266_surfaces() -> None:
    text = SOURCE.read_text(encoding='utf-8')
    for marker in (
        'run_scheduler_managed_sql_ref_openvino_embedding_usage',
        'run_scheduler_managed_qdrant_recall_sql_rehydrate_usage',
        'compose_scheduler_managed_closed_result_frame',
        'build_closed_result_frame_eventbus_observation_report',
        'publish_closed_result_frame_observation_facts',
        'build_passive_supervisor_closed_frame_observation_report',
        'build_visual_read_model',
        'build_passive_supervisor_visual_layout_model',
    ):
        assert marker in text


def test_r4_keeps_query_and_passage_roles_distinct() -> None:
    text = SOURCE.read_text(encoding='utf-8')
    for marker in (
        "role='query'",
        'passage_profile.role',
        'query_profile.role',
        'passage_embedding_ref',
        'query_embedding_ref',
        'query and passage profiles must share one vector space',
    ):
        assert marker in text


def test_r4_creates_no_scheduler_or_parallel_authority() -> None:
    text = SOURCE.read_text(encoding='utf-8')
    for forbidden in (
        'Scheduler(',
        'PriorityQueue(',
        'EventBus(',
        'Registry(',
        'LaboratoryManager',
        'LaboratoryOrchestrator',
        'create_task(scheduler.run',
        'await scheduler.run(',
        'import vispy',
        'import requests',
        'import httpx',
    ):
        assert forbidden not in text
    for marker in (
        'scheduler_created: bool = False',
        'scheduler_modified: bool = False',
        'parallel_orchestrator_created: bool = False',
        'parallel_eventbus_created: bool = False',
        'parallel_registry_created: bool = False',
        'sql_write_performed: bool = False',
        'qdrant_write_performed: bool = False',
        'github_mutation_performed: bool = False',
    ):
        assert marker in text


def test_r4_observation_and_visualization_are_passive() -> None:
    text = SOURCE.read_text(encoding='utf-8')
    assert 'publish_closed_result_frame_observation_facts' in text
    assert "'eventbus_observation_only': True" in text
    assert "'passive_supervisor_observation_only': True" in text
    assert "'vispy_passive': True" in text
    assert "'publication_gate_required': True" in text


def test_documentation_closes_recall_without_remote_mutation() -> None:
    architecture = ARCH.read_text(encoding='utf-8')
    graph = GRAPH.read_text(encoding='utf-8')
    for marker in (
        'one existing Scheduler',
        'query embedding',
        'passage embedding',
        'SQL remains durable authority',
        'Qdrant remains reference-only recall',
        'EventBus remains observation-only',
        'PassiveSupervisor',
        'VisPy',
        'publication gate',
        '0274-r5',
    ):
        assert marker in architecture
    for marker in (
        'R3Handoff -> QueryE5',
        'QueryE5 -> QueryProfile',
        'QueryProfile -> Recall0263',
        'Recall0263 -> SQLRehydrate',
        'SQLRehydrate -> Frame0264',
        'Frame0264 -> Facts0265',
        'Facts0265 -> Supervisor0266',
        'Supervisor0266 -> Visual',
    ):
        assert marker in graph


def test_manifest_and_report_keep_patch_clean() -> None:
    manifest = MANIFEST.read_text(encoding='utf-8')
    report = REPORT.read_text(encoding='utf-8')
    for marker in ('__pycache__', '.pyc', '.pyo', '.svg'):
        assert marker not in manifest
    for marker in (
        'scheduler_created: false',
        'scheduler_modified: false',
        'parallel_orchestrator_created: false',
        'external_dependencies_added: false',
        'sql_write_performed: false',
        'qdrant_write_performed: false',
        'qdrant_recall_refs_only: true',
        'github_mutation_performed: false',
    ):
        assert marker in report
