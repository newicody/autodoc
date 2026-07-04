import hashlib
import json

from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection


def _nested_report() -> dict:
    return {
        "ok": True,
        "retrieval": {
            "retrieved_ids": ["baby-silicone-fork", "rounded-stainless-soft-handle"],
            "rejected_ids": ["nasa-antenna"],
        },
        "variant_generator_stub": {
            "generated_variants": [
                {"variant_id": "variant-1", "label": "soft silicone baby fork", "score": 0.86},
                {"variant_id": "variant-2", "label": "rounded stainless with soft handle", "score": 0.74},
            ]
        },
        "final_context": {
            "context_id": "ctx-baby-fork-001",
            "context_version": 2,
            "selected_variant_id": "variant-1",
        },
    }


def test_projection_extracts_nested_variants_from_realistic_report_shape() -> None:
    projection = build_baby_fork_runtime_projection(_nested_report())

    variants_event = next(event for event in projection.events if event.topic == "variants.generated")

    assert variants_event.payload["variant_count"] == 2
    assert variants_event.payload["variant_ids"] == ["variant-1", "variant-2"]
    assert variants_event.payload["selected_variant_id"] == "variant-1"


def test_projection_adds_variant_ids_to_context_and_route_messages() -> None:
    projection = build_baby_fork_runtime_projection(_nested_report())

    assert projection.contexts[0].payload["variant_ids"] == ["variant-1", "variant-2"]

    variant_route = next(route for route in projection.routes if route.route_id == "baby_fork.variant_stub")
    context_patch = next(route for route in projection.routes if route.route_id == "baby_fork.context_gate")

    assert variant_route.payload["variant_ids"] == ["variant-1", "variant-2"]
    assert context_patch.payload["variant_ids"] == ["variant-1", "variant-2"]


def test_projection_uses_real_report_sha256_hash() -> None:
    report = _nested_report()
    projection = build_baby_fork_runtime_projection(report)

    expected = "sha256:" + hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    assert projection.data_handles[0].hash == expected
    assert projection.data_handles[0].hash != "sha256:projection"


def test_projection_falls_back_to_selected_variant_when_no_variant_list_exists() -> None:
    report = {
        "final_context": {
            "context_id": "ctx-baby-fork-001",
            "context_version": 2,
            "selected_variant_id": "variant-1",
        }
    }

    projection = build_baby_fork_runtime_projection(report)

    variants_event = next(event for event in projection.events if event.topic == "variants.generated")
    assert variants_event.payload["variant_count"] == 1
    assert variants_event.payload["variant_ids"] == ["variant-1"]
