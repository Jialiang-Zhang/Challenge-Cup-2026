from __future__ import annotations

from typing import Any

from agent.adaptive_engine import AdaptiveVerifiedHORAEngine
from agent.models import AgentConfig


class ReasoningAgent:
    """Competition entry point for the adaptive verified HORA-Math system."""

    def __init__(
        self,
        client: Any,
        config: AgentConfig | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        del args, kwargs
        # Ordinary routes still stop early. The sixth slot is reserved for
        # decisive local confirmation plus one targeted repair/re-audit path.
        self.config = config or AgentConfig(always_run_blind=False, max_model_calls=6)
        self.engine = AdaptiveVerifiedHORAEngine(client=client, config=self.config)

    def solve(self, problem: str, metadata: dict) -> dict:
        return self.engine.solve(problem=problem, metadata=metadata)


__all__ = ["AgentConfig", "ReasoningAgent"]
