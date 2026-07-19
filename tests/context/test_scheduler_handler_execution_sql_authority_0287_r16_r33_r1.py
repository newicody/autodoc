from types import SimpleNamespace
import sqlite3

from context.scheduler_handler_execution_sql_authority_0287 import DbApiSchedulerHandlerExecutionTransaction
from kernel.scheduler_task_model import SchedulerTaskState, SchedulerTaskAttemptState


def test_success_is_persisted_and_resources_are_released_atomically():
    c=sqlite3.connect(':memory:')
    c.executescript('''
    CREATE TABLE scheduler_task_launch_transactions (transaction_ref TEXT PRIMARY KEY,scheduler_ref TEXT,command_ref TEXT,task_ref TEXT,attempt_ref TEXT,reservation_ref TEXT);
    CREATE TABLE scheduler_task_attempts (attempt_ref TEXT PRIMARY KEY,state TEXT,finished_at TEXT,result_ref TEXT,failure_ref TEXT);
    CREATE TABLE scheduler_tasks (task_ref TEXT PRIMARY KEY,state TEXT,state_version INTEGER,updated_at TEXT,task_digest TEXT);
    CREATE TABLE scheduler_task_transitions (transition_ref TEXT PRIMARY KEY,task_ref TEXT,from_state TEXT,to_state TEXT,state_version INTEGER,occurred_at TEXT,actor_ref TEXT,cause_ref TEXT,transition_digest TEXT);
    CREATE TABLE scheduler_resource_inventory (resource_ref TEXT PRIMARY KEY,capacity INTEGER,reserved INTEGER,state_version INTEGER,updated_at TEXT);
    CREATE TABLE scheduler_resource_reservations (reservation_ref TEXT PRIMARY KEY,status TEXT);
    CREATE TABLE scheduler_resource_reservation_requirements (reservation_ref TEXT,ordinal INTEGER,resource_ref TEXT,amount INTEGER,exclusive BOOLEAN);
    CREATE TABLE scheduler_command_states (command_ref TEXT PRIMARY KEY,state TEXT,claimed_by TEXT,updated_at TEXT);
    ''')
    c.execute("INSERT INTO scheduler_task_launch_transactions VALUES (?,?,?,?,?,?)",('scheduler-launch-transaction:x','scheduler:canonical','scheduler-command:x','scheduler-task:x','scheduler-attempt:x','scheduler-reservation:x'))
    c.execute("INSERT INTO scheduler_task_attempts VALUES (?,?,?,?,?)",('scheduler-attempt:x','running','','',''))
    c.execute("INSERT INTO scheduler_tasks VALUES (?,?,?,?,?)",('scheduler-task:x','running',2,'2026-07-19T10:00:00Z','sha256:'+'a'*64))
    c.execute("INSERT INTO scheduler_resource_inventory VALUES (?,?,?,?,?)",('resource:cpu',2,1,1,'2026-07-19T10:00:00Z'))
    c.execute("INSERT INTO scheduler_resource_reservations VALUES (?,?)",('scheduler-reservation:x','active'))
    c.execute("INSERT INTO scheduler_resource_reservation_requirements VALUES (?,?,?,?,?)",('scheduler-reservation:x',0,'resource:cpu',1,0))
    c.execute("INSERT INTO scheduler_command_states VALUES (?,?,?,?)",('scheduler-command:x','running','scheduler:canonical','2026-07-19T10:00:00Z'))
    c.commit()
    tx=DbApiSchedulerHandlerExecutionTransaction(c,paramstyle='qmark'); tx.initialize_schema()
    task_before=SimpleNamespace(task_ref='scheduler-task:x',command_ref='scheduler-command:x',state=SchedulerTaskState.RUNNING,state_version=2,task_digest='sha256:'+'a'*64)
    task_after=SimpleNamespace(task_ref='scheduler-task:x',state=SchedulerTaskState.COMPLETED,state_version=3,updated_at='2026-07-19T10:01:00Z',task_digest='sha256:'+'b'*64)
    attempt=SimpleNamespace(attempt_ref='scheduler-attempt:x',state=SchedulerTaskAttemptState.SUCCEEDED,finished_at='2026-07-19T10:01:00Z',result_ref='scheduler-task-result:x',failure_ref='')
    result=SimpleNamespace(result_ref='scheduler-task-result:x',task_ref='scheduler-task:x',attempt_ref='scheduler-attempt:x',result_type_ref='result-type:x',completed_at='2026-07-19T10:01:00Z',result_digest='sha256:'+'c'*64,evidence_refs=('evidence:x',))
    transition=SimpleNamespace(transition_ref='scheduler-transition:x',task_ref='scheduler-task:x',from_state=SchedulerTaskState.RUNNING,to_state=SchedulerTaskState.COMPLETED,state_version=3,occurred_at='2026-07-19T10:01:00Z',actor_ref='scheduler:canonical',cause_ref='handler-execution:x',transition_digest='sha256:'+'d'*64)
    completion=SimpleNamespace(task=task_after,attempt=attempt,result=result,transition=transition)
    ticket=SimpleNamespace(scheduler_ref='scheduler:canonical',task_running=task_before,attempt=SimpleNamespace(attempt_ref='scheduler-attempt:x'),reservation=SimpleNamespace(reservation_ref='scheduler-reservation:x'),launch_commit=SimpleNamespace(transaction_ref='scheduler-launch-transaction:x'))
    outcome=SimpleNamespace(lease=SimpleNamespace(created=SimpleNamespace(ticket=ticket)),completion=completion,failure_outcome=None,interruption=None,outcome_ref='handler-outcome:x',outcome_digest='sha256:'+'e'*64,terminal_ref='scheduler-task-result:x',task_state=SchedulerTaskState.COMPLETED,close_receipt=SimpleNamespace(closed=True))
    receipt=tx.commit_outcome(outcome=outcome,released_at='2026-07-19T10:01:01Z')
    assert receipt.task_state == 'completed'
    assert c.execute('SELECT state FROM scheduler_tasks').fetchone() == ('completed',)
    assert c.execute('SELECT status FROM scheduler_resource_reservations').fetchone() == ('released',)
    assert c.execute('SELECT reserved FROM scheduler_resource_inventory').fetchone() == (0,)
    assert tx.commit_outcome(outcome=outcome,released_at='2026-07-19T10:01:01Z') == receipt
