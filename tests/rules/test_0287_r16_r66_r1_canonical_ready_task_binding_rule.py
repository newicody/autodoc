from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/github_research_love_canonical_ready_task_binding_0287.py"
RUNNER = ROOT / "src/context/github_research_love_transactional_step_runner_0287.py"


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_r16_r66_ne_cree_aucune_autorite_parallele() -> None:
    source = _source()

    for forbidden in (
        "SchedulerTaskAdmissionPlanner",
        "ExplicitSchedulerHandlerFactory(",
        "SchedulerHandlerCatalog(",
        "EventBus(",
        "Dispatcher(",
        "threading",
        "multiprocessing",
        "json.dumps",
        "jsonl",
    ):
        assert forbidden not in source


def test_r16_r66_ne_resout_ni_capacite_ni_handler() -> None:
    source = _source()

    for forbidden in (
        ".resolve(",
        ".resolve_for(",
        ".by_handler_ref(",
        "task.capability_ref",
        "candidate.task.capability_ref",
    ):
        assert forbidden not in source

    assert "catalog=self.bootstrap.catalog" in source
    assert "handler_factory=self.bootstrap.factory" in source


def test_r16_r66_relit_la_commande_et_l_admission_deja_decidee() -> None:
    source = _source()

    assert "self.command_store.get_command(task.command_ref)" in source
    assert "load_ready_task_admission(" in source
    assert "SchedulerAdmissionStatus.ADMITTED" in source
    assert '"ready_task_already_selected": True' in source
    assert '"admission_already_decided": True' in source


def test_r16_r66_valide_structurellement_le_sink_sans_modifier_le_contrat() -> None:
    provider_source = _source()
    runner_source = RUNNER.read_text(encoding="utf-8")

    marker = 'callable(getattr(self.information_sink, "publish", None))'
    assert marker in provider_source
    assert marker in runner_source
    assert "isinstance(self.information_sink, HandlerInformationSink)" not in provider_source
    assert "isinstance(self.information_sink, HandlerInformationSink)" not in runner_source
