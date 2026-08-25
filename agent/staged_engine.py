from __future__ import annotations

from typing import Any

from .models import CaseState, MethodFingerprint, SolutionCapsule
from .orchestrator import HORAEngine
from .parsing import parse_solution_capsule
from .prompt_overrides import blind_prompt_v2, primary_prompt_v2
from .protocol_validation import sanitize_solution_capsule
from .runtime import RuntimeGuard


class StagedHORAEngine(HORAEngine):
    """Incremental HORA engine with compact validated low-risk solver channels."""

    def _run_primary(
        self,
        problem: str,
        state: CaseState,
        guard: RuntimeGuard,
        trace: list[dict[str, Any]],
    ) -> SolutionCapsule:
        use_compact_protocol = (
            state.contract.risk_level == "low"
            and not state.contract.requires_proof
            and state.contract.multipart_count == 1
        )
        if not use_compact_protocol:
            return super()._run_primary(problem, state, guard, trace)

        text = self._call_model(
            state=state,
            guard=guard,
            trace=trace,
            step="primary_call",
            prompt=primary_prompt_v2(problem, state.contract),
            temperature=self.config.primary_temperature,
            max_tokens=min(self.config.primary_max_tokens, 2048),
            thinking_mode=False,
        )
        capsule = parse_solution_capsule(
            text,
            candidate_id="A",
            source="primary",
            fallback_fingerprint=self._primary_fingerprint(state.contract.primary_method),
            requires_proof=False,
        )
        capsule = sanitize_solution_capsule(capsule, requires_proof=False)
        state.add_candidate(capsule)
        self._apply_candidate_evidence(state, capsule)
        self._trace_candidate(trace, capsule)
        return capsule

    def _run_blind(
        self,
        problem: str,
        state: CaseState,
        guard: RuntimeGuard,
        trace: list[dict[str, Any]],
    ) -> SolutionCapsule:
        text = self._call_model(
            state=state,
            guard=guard,
            trace=trace,
            step="orthogonal_blind_call",
            prompt=blind_prompt_v2(problem, state.contract),
            temperature=self.config.blind_temperature,
            max_tokens=min(self.config.blind_max_tokens, 2048),
            # Functional heterogeneity: the primary high-risk route uses extended
            # thinking while the blind route returns a compact independent result.
            thinking_mode=False,
        )
        planned_fingerprint = self._blind_fingerprint(state.contract.orthogonal_method)
        capsule = parse_solution_capsule(
            text,
            candidate_id="B",
            source="orthogonal_blind",
            fallback_fingerprint=planned_fingerprint,
            requires_proof=state.contract.requires_proof,
        )
        capsule = sanitize_solution_capsule(
            capsule,
            requires_proof=state.contract.requires_proof,
        )
        capsule.fingerprint = MethodFingerprint(
            paradigm=planned_fingerprint.paradigm,
            representation=planned_fingerprint.representation,
            theorem_family=planned_fingerprint.theorem_family,
            tool_channel=(
                capsule.fingerprint.tool_channel
                if capsule.fingerprint.tool_channel not in {"", "none", "unknown", "..."}
                else planned_fingerprint.tool_channel
            ),
            interpretation_id=(
                capsule.fingerprint.interpretation_id
                if capsule.fingerprint.interpretation_id not in {"", "..."}
                else "I1"
            ),
            exposed_to_primary=False,
        )
        state.add_candidate(capsule)
        self._apply_candidate_evidence(state, capsule)
        self._trace_candidate(trace, capsule)
        return capsule
