from __future__ import annotations

from typing import Any

from agent.models import AgentConfig
from agent.resilient_engine import ResilientHORAEngine


class ReasoningAgent:
    """Competition entry point for the resilient staged HORA-Math system."""

    def __init__(
        self,
        client: Any,
        config: AgentConfig | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        del args, kwargs
        self.config = config or AgentConfig(always_run_blind=False)
        self.engine = ResilientHORAEngine(client=client, config=self.config)

    def solve(self, problem: str, metadata: dict) -> dict:
        return self.engine.solve(problem=problem, metadata=metadata)


__all__ = ["AgentConfig", "ReasoningAgent"]
