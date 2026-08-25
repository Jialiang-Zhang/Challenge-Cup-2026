from __future__ import annotations

import time

from .models import AgentConfig, CaseState


class RuntimeGuard:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.started = time.monotonic()

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def allow_model_call(self, state: CaseState) -> bool:
        if state.model_calls >= self.config.max_model_calls:
            return False
        return self.elapsed < (
            self.config.soft_deadline_seconds
            - self.config.finalization_reserve_seconds
        )

    def mark_call(self, state: CaseState) -> None:
        state.model_calls += 1

    def should_finalize(self) -> bool:
        return self.elapsed >= (
            self.config.soft_deadline_seconds
            - self.config.finalization_reserve_seconds
        )
