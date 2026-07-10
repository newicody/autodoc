from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_0267_source_locks_github_scan_once_boundary():
    source=(ROOT/'src/context/github_scan_once_handoff_0267.py').read_text(encoding='utf-8')
    assert 'local/server remains the authority' in source; assert 'GitHub is a review/workflow surface, not the authority' in source; assert 'remote mutation is forbidden in 0267' in source; assert 'scan-once means one local artifact envelope' in source; assert 'requests.' not in source; assert 'urllib' not in source; assert 'subprocess.run' not in source; assert 'RuntimeManager(' not in source; assert 'Scheduler.run(' not in source
def test_0267_docs_lock_axis():
    doc=(ROOT/'doc/architecture/GITHUB_SCAN_ONCE_HANDOFF_0267.md').read_text(encoding='utf-8')
    assert 'GitHub scan-once handoff' in doc; assert 'local/server remains the authority' in doc; assert 'remote mutation is forbidden in 0267' in doc; assert 'GitHub is a review/workflow surface' in doc; assert '0268 can prepare OpenRC/launcher minimal' in doc
