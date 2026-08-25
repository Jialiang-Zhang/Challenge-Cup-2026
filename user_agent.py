from __future__ import annotations

from typing import Any

from agent.models import AgentConfig
from agent.staged_engine import StagedHORAEngine


class ReasoningAgent:
    """Competition entry point for the staged HORA-Math reasoning system."""

    def __init__(
        self,
        client: Any,
        config: AgentConfig | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        del args, kwargs
        # Low-risk R0 questions use Primary + adversarial audit by default.
        # Medium/high-risk routes still receive the orthogonal blind solution.
        self.config = config or AgentConfig(always_run_blind=False)
        self.engine = StagedHORAEngine(client=client, config=self.config)

    def solve(self, problem: str, metadata: dict) -> dict:
        return self.engine.solve(problem=problem, metadata=metadata)


__all__ = ["AgentConfig", "ReasoningAgent"]
