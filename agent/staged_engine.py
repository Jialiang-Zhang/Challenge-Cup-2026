from __future__ import annotations

from typing import Any

from .models import AuditResult, CaseState, EvidenceRecord, MethodFingerprint, SolutionCapsule
from .orchestrator import HORAEngine
from .parsing import parse_solution_capsule
from .prompt_overrides import blind_prompt_v2, primary_prompt_v2, repair_prompt_v2, rescue_prompt_v2
from .protocol_validation import sanitize_solution_capsule
from .runtime import RuntimeGuard


class StagedHORAEngine(HORAEngine):
    """Incremental HORA engine with compact validated solver protocols."""

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

    def _run_repair(
        self,
        problem: str,
        state: CaseState,
        guard: RuntimeGuard,
        trace: list[dict[str, Any]],
        audit: AuditResult,
    ) -> SolutionCapsule | None:
        if not self.config.allow_repair or state.repair_count >= 1:
            return None
        target_id = audit.target_candidate_id
        if target_id not in state.candidates or not guard.allow_model_call(state):
            return None

        parent = state.candidates[target_id].capsule
        text = self._call_model(
            state=state,
            guard=guard,
            trace=trace,
            step="targeted_repair_call",
            prompt=repair_prompt_v2(
                problem,
                state.contract,
                parent_answer=parent.answer_raw,
                parent_response=parent.final_response,
                challenge=audit.challenge,
                witness=audit.witness or "",
                resolver_hint=audit.resolver_hint or "",
            ),
            temperature=self.config.repair_temperature,
            max_tokens=min(self.config.repair_max_tokens, 2048),
            thinking_mode=False,
        )
        state.repair_count += 1
        capsule = parse_solution_capsule(
            text,
            candidate_id="C",
            source="targeted_repair",
            fallback_fingerprint=MethodFingerprint(
                paradigm=f"corrected-{parent.fingerprint.paradigm}",
                representation=parent.fingerprint.representation,
                theorem_family=parent.fingerprint.theorem_family,
                tool_channel=parent.fingerprint.tool_channel,
                interpretation_id=parent.fingerprint.interpretation_id,
                exposed_to_primary=True,
            ),
            requires_proof=state.contract.requires_proof,
            parent_candidate_id=parent.candidate_id,
        )
        capsule = sanitize_solution_capsule(
            capsule,
            requires_proof=state.contract.requires_proof,
        )
        state.add_candidate(capsule)
        self._apply_candidate_evidence(state, capsule)
        if capsule.challenge_resolution:
            state.add_evidence(
                EvidenceRecord(
                    evidence_id=f"E-repair-{state.repair_count}",
                    candidate_id=capsule.candidate_id,
                    evidence_type="challenge_resolution",
                    status="pass",
                    strength="semantic",
                    checker="targeted_repair_protocol",
                    target_claim_id=audit.target_claim_id,
                    detail_code="explicit_resolution_present",
                )
            )
        self._trace_candidate(trace, capsule)
        trace.append(
            {
                "step": "repair_result",
                "content": {
                    "candidate_id": capsule.candidate_id,
                    "parent_candidate_id": parent.candidate_id,
                    "challenge_resolution_present": bool(capsule.challenge_resolution),
                    "eligible": state.candidates[capsule.candidate_id].eligible,
                },
            }
        )
        return capsule

    def _run_rescue(
        self,
        problem: str,
        state: CaseState,
        guard: RuntimeGuard,
        trace: list[dict[str, Any]],
    ) -> SolutionCapsule | None:
        if not guard.allow_model_call(state):
            return None
        try:
            text = self._call_model(
                state=state,
                guard=guard,
                trace=trace,
                step="rescue_call",
                prompt=rescue_prompt_v2(problem, state.contract),
                temperature=0.0,
                max_tokens=min(1536, self.config.primary_max_tokens),
                thinking_mode=False,
            )
        except Exception:
            return None
        capsule = parse_solution_capsule(
            text,
            candidate_id="R",
            source="rescue",
            fallback_fingerprint=MethodFingerprint(
                paradigm="direct",
                representation="symbolic",
                theorem_family="none",
                tool_channel="none",
            ),
            requires_proof=state.contract.requires_proof,
        )
        capsule = sanitize_solution_capsule(
            capsule,
            requires_proof=state.contract.requires_proof,
        )
        state.add_candidate(capsule)
        self._apply_candidate_evidence(state, capsule)
        self._trace_candidate(trace, capsule)
        return capsule
