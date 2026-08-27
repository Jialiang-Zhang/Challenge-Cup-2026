from __future__ import annotations

from typing import Any

from .adjudication import freeze_candidate, select_best_candidate
from .canonicalize import compare_answers
from .evidence import (
    add_audit_acceptance,
    add_equivalence_evidence,
    challenge_from_audit,
    has_hard_fail,
)
from .models import AuditResult, CaseState, EvidenceRecord, MethodFingerprint, SolutionCapsule
from .orchestrator import HORAEngine
from .orthogonality import orthogonality_level
from .parsing import parse_audit_result, parse_solution_capsule
from .prompt_overrides import blind_prompt_v2, primary_prompt_v2, repair_prompt_v2, rescue_prompt_v2
from .prompts import audit_prompt
from .protocol_validation import sanitize_solution_capsule
from .routing import build_task_contract
from .runtime import RuntimeGuard


class StagedHORAEngine(HORAEngine):
    """HORA engine with hard candidate gates and evidence-vetoed red-team review."""

    @staticmethod
    def _candidate_is_valid(state: CaseState, candidate_id: str | None) -> bool:
        if candidate_id is None:
            return False
        record = state.candidates.get(candidate_id)
        if record is None:
            return False
        capsule = record.capsule
        return bool(
            record.eligible
            and capsule.answer_raw.strip()
            and capsule.final_response.strip()
            and capsule.complete
            and not capsule.truncated
            and not has_hard_fail(state, candidate_id)
        )

    def _run_primary(
        self,
        problem: str,
        state: CaseState,
        guard: RuntimeGuard,
        trace: list[dict[str, Any]],
    ) -> SolutionCapsule:
        # Objective single-part questions use a compact transaction protocol.
        # Extended thinking is reserved for proofs and multipart derivations.
        use_compact_protocol = (
            not state.contract.requires_proof
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

    def _run_audit(
        self,
        problem: str,
        state: CaseState,
        guard: RuntimeGuard,
        trace: list[dict[str, Any]],
        candidate_a: SolutionCapsule,
        candidate_b: SolutionCapsule | None,
    ) -> AuditResult:
        """Run red-team review without allowing soft verdicts to override hard evidence."""

        if not self._candidate_is_valid(state, candidate_a.candidate_id):
            raise ValueError("candidate A is not valid for red-team review")
        if candidate_b is not None and not self._candidate_is_valid(
            state, candidate_b.candidate_id
        ):
            candidate_b = None

        text = self._call_model(
            state=state,
            guard=guard,
            trace=trace,
            step="red_team_audit_call",
            prompt=audit_prompt(
                problem,
                state.contract,
                candidate_a,
                candidate_b,
                context_limit=self.config.max_candidate_context_chars,
            ),
            temperature=self.config.audit_temperature,
            max_tokens=self.config.audit_max_tokens,
            thinking_mode=False,
        )
        raw = parse_audit_result(text)
        positions = {"A": candidate_a.candidate_id}
        if candidate_b is not None:
            positions["B"] = candidate_b.candidate_id

        deterministic_relation = (
            compare_answers(candidate_a.answer_raw, candidate_b.answer_raw)
            if candidate_b is not None
            else "not_applicable"
        )
        verdict = raw.verdict

        if verdict in {"ACCEPT_B", "REPAIR_B"} and candidate_b is None:
            verdict = "UNRESOLVED"
        if verdict == "EQUIVALENT" and (
            candidate_b is None or deterministic_relation != "equivalent"
        ):
            verdict = "UNRESOLVED"

        selected_id: str | None = None
        if verdict == "ACCEPT_A":
            selected_id = candidate_a.candidate_id
        elif verdict == "ACCEPT_B" and candidate_b is not None:
            selected_id = candidate_b.candidate_id

        mapped_target = positions.get(raw.target_candidate_id or "")
        if verdict == "REPAIR_A":
            mapped_target = candidate_a.candidate_id
        elif verdict == "REPAIR_B" and candidate_b is not None:
            mapped_target = candidate_b.candidate_id

        # A verdict cannot accept the same candidate while simultaneously
        # sustaining a fatal/major attack against it.
        if (
            selected_id is not None
            and mapped_target == selected_id
            and raw.severity in {"fatal", "major"}
        ):
            verdict = "UNRESOLVED"
            selected_id = None

        sustained = False
        if verdict in {"REPAIR_A", "REPAIR_B"}:
            sustained = True
        elif (
            mapped_target is not None
            and raw.severity in {"fatal", "major"}
        ):
            if verdict == "UNRESOLVED":
                sustained = True
            elif verdict == "ACCEPT_A" and mapped_target != candidate_a.candidate_id:
                sustained = True
            elif (
                verdict == "ACCEPT_B"
                and candidate_b is not None
                and mapped_target != candidate_b.candidate_id
            ):
                sustained = True

        result = AuditResult(
            verdict=verdict,
            target_candidate_id=mapped_target,
            target_claim_id=raw.target_claim_id,
            attack_type=raw.attack_type,
            severity=raw.severity,
            challenge=raw.challenge,
            witness=raw.witness,
            resolver_hint=raw.resolver_hint,
        )
        trace.append(
            {
                "step": "red_team_result",
                "content": {
                    "raw_verdict": raw.verdict,
                    "verdict": verdict,
                    "target_candidate_id": mapped_target,
                    "target_claim_id": raw.target_claim_id,
                    "attack_type": raw.attack_type,
                    "severity": raw.severity,
                    "deterministic_relation": deterministic_relation,
                },
            }
        )

        if raw.challenge.lower() != "none" or raw.severity != "none":
            state.add_challenge(
                challenge_from_audit(
                    challenge_id=f"CH{len(state.challenges) + 1}",
                    candidate_id=mapped_target,
                    target_claim_id=raw.target_claim_id,
                    attack_type=raw.attack_type,
                    severity=raw.severity,
                    statement=raw.challenge,
                    witness=raw.witness,
                    resolver_hint=raw.resolver_hint,
                    sustained=sustained,
                )
            )

        if sustained and mapped_target in state.candidates:
            state.candidates[mapped_target].eligible = False

        if verdict == "ACCEPT_A" and self._candidate_is_valid(
            state, candidate_a.candidate_id
        ):
            add_audit_acceptance(state, candidate_a.candidate_id, verdict)
        elif (
            verdict == "ACCEPT_B"
            and candidate_b is not None
            and self._candidate_is_valid(state, candidate_b.candidate_id)
        ):
            add_audit_acceptance(state, candidate_b.candidate_id, verdict)
        elif verdict == "EQUIVALENT" and candidate_b is not None:
            if self._candidate_is_valid(state, candidate_a.candidate_id):
                add_audit_acceptance(state, candidate_a.candidate_id, verdict)
            if self._candidate_is_valid(state, candidate_b.candidate_id):
                add_audit_acceptance(state, candidate_b.candidate_id, verdict)

        return result

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

    def solve(self, problem: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        del metadata
        if not isinstance(problem, str) or not problem.strip():
            raise ValueError("problem must be a non-empty string")

        contract = build_task_contract(problem)
        state = CaseState(contract=contract, route=contract.route_hint)
        guard = RuntimeGuard(self.config)
        trace: list[dict[str, Any]] = [
            {
                "step": "profile",
                "content": {
                    "domain": contract.primary_domain,
                    "secondary_domain_count": len(contract.secondary_domains),
                    "risk": contract.risk_level,
                    "route": contract.route_hint,
                    "answer_schema": contract.answer_schema,
                    "multipart_count": contract.multipart_count,
                    "secondary_domains": list(contract.secondary_domains),
                    "question_mode": contract.question_mode,
                    "mode_confidence": contract.mode_confidence,
                    "alternate_modes": list(contract.alternate_modes),
                    "answer_obligations": list(contract.answer_obligations),
                    "ambiguity_flags": list(contract.ambiguity_flags),
                },
            }
        ]

        primary: SolutionCapsule | None = None
        blind: SolutionCapsule | None = None
        audit: AuditResult | None = None

        try:
            primary = self._run_primary(problem, state, guard, trace)
        except Exception:
            primary = None

        primary_valid = primary is not None and self._candidate_is_valid(
            state, primary.candidate_id
        )
        run_blind = (
            self.config.always_run_blind
            or contract.risk_level != "low"
            or not primary_valid
        )
        if run_blind and guard.allow_model_call(state):
            try:
                blind = self._run_blind(problem, state, guard, trace)
            except Exception:
                blind = None

        valid_capsules = [
            capsule
            for capsule in (primary, blind)
            if capsule is not None and self._candidate_is_valid(state, capsule.candidate_id)
        ]
        invalid_ids = [
            capsule.candidate_id
            for capsule in (primary, blind)
            if capsule is not None and not self._candidate_is_valid(state, capsule.candidate_id)
        ]
        trace.append(
            {
                "step": "candidate_gate",
                "content": {
                    "valid_candidate_ids": [item.candidate_id for item in valid_capsules],
                    "invalid_candidate_ids": invalid_ids,
                },
            }
        )

        relation = "unknown"
        orthogonality = "O0"
        if len(valid_capsules) == 2:
            candidate_a, candidate_b = valid_capsules
            orthogonality = orthogonality_level(
                candidate_a.fingerprint, candidate_b.fingerprint
            )
            state.candidates[candidate_a.candidate_id].orthogonality_level = orthogonality
            state.candidates[candidate_b.candidate_id].orthogonality_level = orthogonality
            relation = add_equivalence_evidence(
                state, candidate_a, candidate_b, orthogonality
            )
            trace.append(
                {
                    "step": "orthogonal_comparison",
                    "content": {
                        "candidate_ids": [
                            candidate_a.candidate_id,
                            candidate_b.candidate_id,
                        ],
                        "orthogonality": orthogonality,
                        "equivalence": relation,
                    },
                }
            )

        need_red_team = False
        if len(valid_capsules) == 1:
            need_red_team = True
        elif len(valid_capsules) == 2:
            need_red_team = self._should_run_red_team(
                state=state,
                relation=relation,
                orthogonality=orthogonality,
            )

        if need_red_team and guard.allow_model_call(state):
            try:
                audit = self._run_audit(
                    problem,
                    state,
                    guard,
                    trace,
                    valid_capsules[0],
                    valid_capsules[1] if len(valid_capsules) > 1 else None,
                )
            except Exception:
                audit = None

        repaired: SolutionCapsule | None = None
        if audit is not None and audit.verdict in {"REPAIR_A", "REPAIR_B"}:
            repaired = self._run_repair(problem, state, guard, trace, audit)

        if (
            repaired is not None
            and self._candidate_is_valid(state, repaired.candidate_id)
            and guard.allow_model_call(state)
        ):
            try:
                self._run_audit(
                    problem,
                    state,
                    guard,
                    trace,
                    repaired,
                    None,
                )
            except Exception:
                pass

        winner = select_best_candidate(state)
        if winner is None:
            self._run_rescue(problem, state, guard, trace)
            winner = select_best_candidate(state)

        if winner is None:
            raise RuntimeError("HORA-Math produced no complete, hard-valid candidate")

        freeze_candidate(state, winner.capsule.candidate_id)
        final_response = self._submission_text(winner.capsule, state)
        trace.append(
            {
                "step": "transaction_commit",
                "content": {
                    "candidate_id": winner.capsule.candidate_id,
                    "source": winner.capsule.source,
                    "model_calls": state.model_calls,
                    "tool_calls": state.tool_calls,
                    "repair_count": state.repair_count,
                    "status": "committed",
                    "final_response_chars": len(final_response),
                },
            }
        )
        return {"final_response": final_response, "trace": trace}
