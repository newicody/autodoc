from __future__ import annotations

import asyncio
from types import SimpleNamespace

import context.love_full_deterministic_local_smoke_0287 as module


class _Continuation:
    def __init__(self, binding):
        self.binding = binding
        self.analysis_reprojected = False
        self.synthesis = SimpleNamespace()


def test_live_synthesis_path_runs_r12_then_r13_once(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []
    binding = SimpleNamespace()
    continuation = _Continuation(binding)

    async def fake_bind(command, *, authority_store, projection_port):
        calls.append(("r12", command))
        assert authority_store == "sql"
        assert projection_port == "projector"
        return binding

    async def fake_recall(
        command,
        *,
        binding,
        collection,
        embedder,
        executor,
        authority_store,
    ):
        calls.append(("r13", command))
        assert binding is globals_binding
        assert collection == "collection"
        assert embedder == "embedder"
        assert executor == "executor"
        assert authority_store == "sql"
        return continuation

    globals_binding = binding
    monkeypatch.setattr(module, "bind_love_specialist_analyses_live", fake_bind)
    monkeypatch.setattr(
        module,
        "run_love_async_hybrid_recall_liaison_synthesis",
        fake_recall,
    )
    command = SimpleNamespace(command_ref="love-synthesis-command:test")

    result = asyncio.run(
        module._run_live_synthesis_path(
            command,
            authority_store="sql",
            projection_port="projector",
            collection="collection",
            embedder="embedder",
            executor="executor",
        )
    )

    assert result == (binding, continuation)
    assert calls == [("r12", command), ("r13", command)]


def test_live_wrapper_selects_explicit_async_mode(monkeypatch) -> None:
    captured = {}
    expected = SimpleNamespace(live_path_used=True)

    async def fake_run(command, **kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(
        module,
        "run_love_full_deterministic_local_smoke",
        fake_run,
    )
    result = asyncio.run(
        module.run_love_full_live_local_smoke(
            SimpleNamespace(),
            scheduler="scheduler",
            dispatcher="dispatcher",
            authority_store="sql",
            projection_port="projector",
            collection="collection",
            embedder="embedder",
            executor="executor",
        )
    )

    assert result is expected
    assert captured["live_async"] is True
