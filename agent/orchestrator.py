from __future__ import annotations

import time
from typing import Any

from .adjudication import freeze_candidate, select_best_candidate
from .canonicalize import normalize_answer_text
from .evidence import (
    add_audit_acceptance,
    add_equivalence_evidence,
    challenge_from_audit,
    evaluate_candidate,
    has_hard_fail,
)
from .models import (
    AgentConfig,
    AuditResult,
    CaseState,
    EvidenceRecord,
    MethodFingerprint,
    SolutionCapsule,
)
from .orthogonality import orthogonality_level
from .parsing import coerce_text, parse_audit_result, parse_solution_capsule, strip_protocol_tags
from .prompts import audit_prompt, blind_prompt, primary_prompt, repair_prompt, rescue_prompt
from .routing import build_task_contract
from .runtime import RuntimeGuard


class HORAEngine:
    """Heterogeneous orthogonal solver with red-team evidence adjudication."""

    def __init__(self, client: Any, config: AgentConfig | None = None) -> None:
        if not hasattr(client, "chat"):
            raise TypeError("client must provide a chat(messages, temperature, max_tokens) method")
        self.client = client
        self.config = config or AgentConfig()

    def _call_model(
        self,
        *,
        state: CaseState,
        guard: RuntimeGuard,
        trace: list[dict[str, Any]],
        step: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        thinking_mode: bool | None = None,
    ) -> str:
        if not guard.allow_model_call(state):
            raise RuntimeError("HORA-Math model-call budget or soft deadline reached")

        guard.mark_call(state)
        started = time.monotonic()
        call_id = state.model_calls
        try:
            call_kwargs = {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if thinking_mode is not None:
                call_kwargs["thinking_mode"] = thinking_mode
            try:
                response = self.client.chat(**call_kwargs)
            except TypeError as exc:
                if thinking_mode is None or "thinking_mode" not in str(exc):
                    raise
                call_kwargs.pop("thinking_mode", None)
                response = self.client.chat(**call_kwargs)
            text = coerce_text(response)
        except Exception as exc:
            trace.append(
                {
                    "step": step,
                    "content": {
                        "call_id": call_id,
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "elapsed_ms": round((time.monotonic() - started) * 1000),
                    },
                }
            )
            raise

        trace.append(
            {
                "step": step,
                "content": {
                    "call_id": call_id,
                    "status": "completed",
                    "response_chars": len(text),
                    "elapsed_ms": round((time.monotonic() - started) * 1000),
                },
            }
        )
        return text

    @staticmethod
    def _primary_fingerprint(method: str) -> MethodFingerprint:
        lowered = method.lower()
        if "count" in lowered:
            paradigm = "counting"
            representation = "graph"
        elif "construct" in lowered or "definition" in lowered:
            paradigm = "constructive"
            representation = "symbolic"
        else:
            paradigm = "theorem"
            representation = "symbolic"
        return MethodFingerprint(
            paradigm=paradigm,
            representation=representation,
            theorem_family=method,
            tool_channel="none",
            interpretation_id="I1",
            exposed_to_primary=False,
        )

    @staticmethod
    def _blind_fingerprint(method: str) -> MethodFingerprint:
        lowered = method.lower()
        if "count" in lowered or "recurrence" in lowered:
            paradigm = "counting"
            representation = "generating_function"
        elif "counterexample" in lowered or "contradiction" in lowered:
            paradigm = "contradiction"
            representation = "other"
        else:
            paradigm = "constructive"
            representation = "coordinate"
        tool_channel = "brute_force" if any(
            token in lowered for token in ("enumeration", "computational", "residual")
        ) else "none"
        return MethodFingerprint(
            paradigm=paradigm,
            representation=representation,
            theorem_family=method,
            tool_channel=tool_channel,
            interpretation_id="I1",
            exposed_to_primary=False,
        )

    @staticmethod
    def _trace_candidate(trace: list[dict[str, Any]], capsule: SolutionCapsule) -> None:
        trace.append(
            {
                "step": "candidate_parsed",
                "content": {
                    "candidate_id": capsule.candidate_id,
                    "source": capsule.source,
                    "complete": capsule.complete,
                    "truncated": capsule.truncated,
                    "response_chars": capsule.response_chars,
                    "claim_count": len(capsule.claims),
                    "method": capsule.fingerprint.paradigm,
                    "tool_channel": capsule.fingerprint.tool_channel,
                    "warning_count": len(capsule.parse_warnings),
                },
            }
        )

    @staticmethod
    def _apply_candidate_evidence(state: CaseState, capsule: SolutionCapsule) -> None:
        for record in evaluate_candidate(capsule, state.contract):
            state.add_evidence(record)
        if has_hard_fail(state, capsule.candidate_id):
            state.candidates[capsule.candidate_id].eligible = False

    def _run_primary(
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
            step="primary_call",
            prompt=primary_prompt(problem, state.contract),
            temperature=self.config.primary_temperature,
            max_tokens=self.config.primary_max_tokens,
            thinking_mode=True,
        )
        capsule = parse_solution_capsule(
            text,
            candidate_id="A",
            source="primary",
            fallback_fingerprint=self._primary_fingerprint(state.contract.primary_method),
            requires_proof=state.contract.requires_proof,
        )
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
            prompt=blind_prompt(problem, state.contract),
            temperature=self.config.blind_temperature,
            max_tokens=self.config.blind_max_tokens,
            thinking_mode=True,
        )
        planned_fingerprint = self._blind_fingerprint(state.contract.orthogonal_method)
        capsule = parse_solution_capsule(
            text,
            candidate_id="B",
            source="orthogonal_blind",
            fallback_fingerprint=planned_fingerprint,
            requires_proof=state.contract.requires_proof,
        )
        capsule.fingerprint = MethodFingerprint(
            paradigm=planned_fingerprint.paradigm,
            representation=planned_fingerprint.representation,
            theorem_family=planned_fingerprint.theorem_family,
            tool_channel=(
                capsule.fingerprint.tool_channel
                if capsule.fingerprint.tool_channel not in {"", "none", "unknown"}
                else planned_fingerprint.tool_channel
            ),
            interpretation_id=capsule.fingerprint.interpretation_id or "I1",
            exposed_to_primary=False,
        )
        state.add_candidate(capsule)
        self._apply_candidate_evidence(state, capsule)
        self._trace_candidate(trace, capsule)
        return capsule

    def _should_run_red_team(
        self,
        *,
        state: CaseState,
        relation: str,
        orthogonality: str,
    ) -> bool:
        if state.contract.risk_level in {"high", "critical"}:
            return self.config.red_team_for_high
        if relation != "equivalent":
            return True
        if orthogonality in {"O0", "O1"}:
            return True
        if any(has_hard_fail(state, candidate_id) for candidate_id in state.candidates):
            return True
        return state.contract.risk_level == "medium" and self.config.red_team_for_medium

    def _run_audit(
        self,
        problem: str,
        state: CaseState,
        guard: RuntimeGuard,
        trace: list[dict[str, Any]],
        candidate_a: SolutionCapsule,
        candidate_b: SolutionCapsule | None,
    ) -> AuditResult:
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
        result = parse_audit_result(text)
        trace.append(
            {
                "step": "red_team_result",
                "content": {
                    "verdict": result.verdict,
                    "target_candidate_id": result.target_candidate_id,
                    "target_claim_id": result.target_claim_id,
                    "attack_type": result.attack_type,
                    "severity": result.severity,
                },
            }
        )

        target_id = result.target_candidate_id
        sustained = (
            result.verdict.startswith("REPAIR_")
            or (result.verdict == "UNRESOLVED" and result.severity in {"fatal", "major"})
            or (
                result.verdict == "ACCEPT_A"
                and target_id == "B"
                and result.severity in {"fatal", "major"}
            )
            or (
                result.verdict == "ACCEPT_B"
                and target_id == "A"
                and result.severity in {"fatal", "major"}
            )
        )
        if result.challenge.lower() != "none" or result.severity != "none":
            state.add_challenge(
                challenge_from_audit(
                    challenge_id=f"CH{len(state.challenges) + 1}",
                    candidate_id=target_id,
                    target_claim_id=result.target_claim_id,
                    attack_type=result.attack_type,
                    severity=result.severity,
                    statement=result.challenge,
                    witness=result.witness,
                    resolver_hint=result.resolver_hint,
                    sustained=sustained,
                )
            )

        if result.verdict == "ACCEPT_A":
            add_audit_acceptance(state, "A", result.verdict)
        elif result.verdict == "ACCEPT_B" and "B" in state.candidates:
            add_audit_acceptance(state, "B", result.verdict)
        elif result.verdict == "EQUIVALENT":
            add_audit_acceptance(state, "A", result.verdict)
            if "B" in state.candidates:
                add_audit_acceptance(state, "B", result.verdict)

        if sustained and target_id and target_id in state.candidates:
            state.candidates[target_id].eligible = False

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
        if target_id not in state.candidates:
            return None
        if not guard.allow_model_call(state):
            return None

        parent = state.candidates[target_id].capsule
        text = self._call_model(
            state=state,
            guard=guard,
            trace=trace,
            step="targeted_repair_call",
            prompt=repair_prompt(problem, state.contract, parent, audit),
            temperature=self.config.repair_temperature,
            max_tokens=self.config.repair_max_tokens,
            thinking_mode=True,
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
                prompt=rescue_prompt(problem, state.contract),
                temperature=0.0,
                max_tokens=min(2048, self.config.primary_max_tokens),
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
        state.add_candidate(capsule)
        self._apply_candidate_evidence(state, capsule)
        self._trace_candidate(trace, capsule)
        return capsule

    def _submission_text(self, capsule: SolutionCapsule, state: CaseState) -> str:
        contract = state.contract
        if contract.requires_proof or contract.multipart_count > 1 or contract.answer_schema == "proof":
            value = capsule.final_response.strip() or capsule.answer_raw.strip()
        else:
            value = capsule.answer_raw.strip() or capsule.final_response.strip()

        value = strip_protocol_tags(value).strip()
        if not value:
            raise ValueError("selected candidate has an empty submission text")

        max_chars = self.config.max_submit_chars
        if len(value) > max_chars:
            answer = capsule.answer_raw.strip()
            prefix = f"{answer}\n\n" if answer and answer not in value[:500] else ""
            remaining = max(0, max_chars - len(prefix))
            value = prefix + value[:remaining].rstrip()

        if not normalize_answer_text(value):
            raise ValueError("selected candidate normalizes to an empty answer")
        return value

    def solve(self, problem: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
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

        run_blind = self.config.always_run_blind or contract.risk_level != "low"
        if run_blind and guard.allow_model_call(state):
            try:
                blind = self._run_blind(problem, state, guard, trace)
            except Exception:
                blind = None

        relation = "unknown"
        orthogonality = "O0"
        if primary is not None and blind is not None:
            orthogonality = orthogonality_level(
                primary.fingerprint, blind.fingerprint
            )
            state.candidates["A"].orthogonality_level = orthogonality
            state.candidates["B"].orthogonality_level = orthogonality
            relation = add_equivalence_evidence(
                state, primary, blind, orthogonality
            )
            trace.append(
                {
                    "step": "orthogonal_comparison",
                    "content": {
                        "candidate_ids": ["A", "B"],
                        "orthogonality": orthogonality,
                        "equivalence": relation,
                    },
                }
            )

        need_red_team = False
        if primary is not None:
            need_red_team = self._should_run_red_team(
                state=state,
                relation=relation,
                orthogonality=orthogonality,
            )
        if blind is None and contract.risk_level in {"high", "critical"}:
            need_red_team = True

        if need_red_team and primary is not None and guard.allow_model_call(state):
            try:
                audit = self._run_audit(
                    problem, state, guard, trace, primary, blind
                )
            except Exception:
                audit = None

        if audit is not None and audit.verdict in {"REPAIR_A", "REPAIR_B"}:
            self._run_repair(problem, state, guard, trace, audit)

        winner = select_best_candidate(state)
        if winner is None:
            self._run_rescue(problem, state, guard, trace)
            winner = select_best_candidate(state)

        if winner is None:
            raise RuntimeError("HORA-Math produced no valid candidate")

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
