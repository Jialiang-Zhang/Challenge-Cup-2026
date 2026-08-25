from __future__ import annotations

from typing import Any

from agent.models import AgentConfig
from agent.orchestrator import HORAEngine


class ReasoningAgent:
    """Competition entry point for the HORA-Math reasoning system."""

    def __init__(
        self,
        client: Any,
        config: AgentConfig | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        del args, kwargs
        self.config = config or AgentConfig()
        self.engine = HORAEngine(client=client, config=self.config)

    def solve(self, problem: str, metadata: dict) -> dict:
        return self.engine.solve(problem=problem, metadata=metadata)


__all__ = ["AgentConfig", "ReasoningAgent"]
