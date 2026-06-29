from __future__ import annotations

from types import MappingProxyType

from contracts.inference import InferenceRequest, InferenceResult


class DummyInferenceBackend:
    """Backend d'inférence déterministe pour valider le chemin kernel.

    Ce backend ne remplace pas OpenVINO. Il sert uniquement à prouver que
    ``InferenceRequest`` peut traverser le Scheduler, le Dispatcher et un
    handler sans introduire de dépendance IA dans le noyau.
    """

    name = "dummy"

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        prompt = request.prompt.strip()
        model = request.model or self.name
        context_size = len(request.context)
        text = f"dummy://{model}: {prompt}"
        return InferenceResult(
            text=text,
            confidence=1.0,
            backend=self.name,
            metadata=MappingProxyType(
                {
                    "model": model,
                    "context_size": context_size,
                    "prompt_length": len(prompt),
                }
            ),
        )
