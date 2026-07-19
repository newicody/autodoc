from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_documents_lock_boundary():
    arch=(ROOT/'doc/architecture/SCHEDULER_HANDLER_EXECUTION_SQL_AUTHORITY_0287_R16_R33_R1.md').read_text()
    rule=(ROOT/'doc/code-rules/0287_r16_r33_r1_scheduler_handler_execution_sql_authority_rule.md').read_text()
    source=(ROOT/'src/context/scheduler_handler_execution_sql_authority_0287.py').read_text()
    for token in ('PostgreSQL reste l’autorité durable','Aucun JSON ou JSONL','VisPy reste observation-only'): assert token in arch
    for token in ('transaction atomique','rejeu exact idempotent','Ne pas choisir la tâche suivante'): assert token in rule
    assert 'json.loads' not in source and 'Dispatcher' not in source
