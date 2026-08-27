from __future__ import annotations

import re
from contextvars import ContextVar
from typing import Any

from .adjudication import has_irreversible_evidence_failure
from .models import AuditResult, CaseState, MethodFingerprint, SolutionCapsule
from .parsing import parse_solution_capsule
from .prompt_overrides import blind_prompt_v2, rescue_prompt_v2
from .prompts import primary_prompt
from .protocol_validation import sanitize_solution_capsule
from .staged_engine import StagedHORAEngine
from .submission import build_submission


_REQUIREMENTS: ContextVar[tuple[str, ...]] = ContextVar(
    "hora_explicit_requirements", default=()
)
_ACTIVE_TRACE: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "hora_active_trace", default=None
)

_REQUIREMENT_MARKERS = re.compile(
    r"(?:要求|必须|需(?:要)?|请|严格证明|进一步证明|并说明|说明为什么|解释|构造|验证|证明)",
    flags=re.IGNORECASE,
)
_NUMBERED_CLAUSE = re.compile(
    r"(?:^|[；;。\n])\s*(?:\(\d+\)|（\d+）|\d+[.)、])\s*([^；;。\n]{4,220})"
)
_DERIVATION_REQUIREMENT = re.compile(
    r"(?:证明|推导|说明为什么|解释为什么|说明理由|给出理由|验证(?:其)?关系|并验证|"
    r"严格说明|严格推导|prove|derive|explain\s+why|justify|verify)",
    flags=re.IGNORECASE,
)


def extract_explicit_requirements(problem: str, limit: int = 8) -> tuple[str, ...]:
    text = str(problem or "").strip()
    if not text:
        return ()

    candidates: list[str] = []
    for match in _NUMBERED_CLAUSE.finditer(text):
        clause = re.sub(r"\s+", " ", match.group(1)).strip(" ：:，,。.;；")
        if clause:
            candidates.append(clause)

    for part in re.split(r"[。；;\n]+", text):
        clause = re.sub(r"\s+", " ", part).strip(" ：:，,")
        if not clause or not _REQUIREMENT_MARKERS.search(clause):
            continue
        if len(clause) > 220:
            marker = _REQUIREMENT_MARKERS.search(clause)
            if marker:
                start = max(0, marker.start() - 40)
                clause = clause[start : start + 220]
        candidates.append(clause)

    unique: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        key = re.sub(r"\s+", "", item).casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
        if len(unique) >= limit:
            break
    return tuple(unique)


def _meaningful(value: str | None) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.lower() not in {"none", "null", "n/a", "unknown"}


class ResilientHORAEngine(StagedHORAEngine):
    """Staged HORA engine with evidence-authenticated vetoes and safe recovery."""

    @staticmethod
    def _attack_is_concrete(result: AuditResult) -> bool:
        if result.severity not in {"fatal", "major"}:
            return True
        if not _meaningful(result.challenge):
            return False
        if _meaningful(result.witness) or _meaningful(result.resolver_hint):
            return True
        return bool(
            result.target_claim_id
            and result.attack_type
            in {
                "assumption",
                "theorem_precondition",
                "counterexample",
                "boundary",
                "transformation",
                "quantifier",
                "completeness",
                "numerical_stress",
            }
        )

    @staticmethod
    def _requirements_prefix() -> str:
        requirements = _REQUIREMENTS.get()
        if not requirements:
            return ""
        lines = "\n".join(f"- R{i + 1}: {item}" for i, item in enumerate(requirements))
        return (
            "MANDATORY EXPLICIT REQUIREMENTS FROM THE PROBLEM\n"
            f"{lines}\n"
            "Treat every listed item as a completion obligation. Do not claim the solution is complete "
            "until each applicable obligation is addressed. During review, missing one is a completeness defect.\n\n"
        )

    def _call_model(
        self,
        *,
        state: CaseState,
        guard,
        trace: list[dict[str, Any]],
        step: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        thinking_mode: bool | None = None,
    ) -> str:
        _ACTIVE_TRACE.set(trace)
        prefix = self._requirements_prefix()
        if prefix:
            prompt = prefix + prompt
        return super()._call_model(
            state=state,
            guard=guard,
            trace=trace,
            step=step,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_mode=thinking_mode,
        )

    def _submission_text(self, capsule: SolutionCapsule, state: CaseState) -> str:
        return build_submission(
            capsule,
            state.contract,
            explicit_requirements=_REQUIREMENTS.get(),
            max_chars=self.config.max_submit_chars,
        )

    def _run_primary(self, problem, state, guard, trace):
        reasoning_heavy = state.contract.requires_proof or state.contract.multipart_count > 1
        if not reasoning_heavy:
            return super()._run_primary(problem, state, guard, trace)

        text = self._call_model(
            state=state,
            guard=guard,
            trace=trace,
            step="primary_call",
            prompt=primary_prompt(problem, state.contract),
            temperature=self.config.primary_temperature,
            max_tokens=min(self.config.primary_max_tokens, 3072),
            thinking_mode=False,
        )
        capsule = parse_solution_capsule(
            text,
            candidate_id="A",
            source="primary",
            fallback_fingerprint=self._primary_fingerprint(state.contract.primary_method),
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

    def _run_blind(self, problem, state, guard, trace):
        reasoning_heavy = (
            state.contract.requires_proof
            or state.contract.multipart_count > 1
            or "derivation_chain" in state.contract.answer_obligations
        )
        text = self._call_model(
            state=state,
            guard=guard,
            trace=trace,
            step="orthogonal_blind_call",
            prompt=blind_prompt_v2(problem, state.contract),
            temperature=self.config.blind_temperature,
            max_tokens=min(self.config.blind_max_tokens, 3072 if reasoning_heavy else 2048),
            thinking_mode=False,
        )
        planned = self._blind_fingerprint(state.contract.orthogonal_method)
        capsule = parse_solution_capsule(
            text,
            candidate_id="B",
            source="orthogonal_blind",
            fallback_fingerprint=planned,
            requires_proof=state.contract.requires_proof,
        )
        capsule = sanitize_solution_capsule(
            capsule,
            requires_proof=state.contract.requires_proof,
        )
        capsule.fingerprint = MethodFingerprint(
            paradigm=planned.paradigm,
            representation=planned.representation,
            theorem_family=planned.theorem_family,
            tool_channel=(
                capsule.fingerprint.tool_channel
                if capsule.fingerprint.tool_channel not in {"", "none", "unknown", "..."}
                else planned.tool_channel
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

    def _run_rescue(self, problem, state, guard, trace):
        if not guard.allow_model_call(state):
            return None
        reasoning_heavy = (
            state.contract.requires_proof
            or state.contract.multipart_count > 1
            or "derivation_chain" in state.contract.answer_obligations
        )
        try:
            text = self._call_model(
                state=state,
                guard=guard,
                trace=trace,
                step="rescue_call",
                prompt=rescue_prompt_v2(problem, state.contract),
                temperature=0.0,
                max_tokens=min(self.config.primary_max_tokens, 2304 if reasoning_heavy else 1536),
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

    def _run_audit(
        self,
        problem: str,
        state: CaseState,
        guard,
        trace: list[dict[str, Any]],
        candidate_a: SolutionCapsule,
        candidate_b: SolutionCapsule | None,
    ) -> AuditResult:
        result = super()._run_audit(
            problem,
            state,
            guard,
            trace,
            candidate_a,
            candidate_b,
        )
        if result.severity not in {"fatal", "major"} or self._attack_is_concrete(result):
            return result

        target_id = result.target_candidate_id
        if target_id:
            for challenge in reversed(state.challenges):
                if (
                    challenge.candidate_id == target_id
                    and challenge.status == "sustained"
                    and challenge.severity in {"fatal", "major"}
                ):
                    challenge.status = "open"
                    break
            record = state.candidates.get(target_id)
            if record is not None and not has_irreversible_evidence_failure(state, target_id):
                record.eligible = True

        downgraded_verdict = (
            "UNRESOLVED" if result.verdict in {"REPAIR_A", "REPAIR_B"} else result.verdict
        )
        trace.append(
            {
                "step": "red_team_evidence_gate",
                "content": {
                    "target_candidate_id": target_id,
                    "original_verdict": result.verdict,
                    "effective_verdict": downgraded_verdict,
                    "reason": "semantic_veto_lacked_concrete_basis",
                },
            }
        )
        return AuditResult(
            verdict=downgraded_verdict,
            target_candidate_id=target_id,
            target_claim_id=result.target_claim_id,
            attack_type=result.attack_type,
            severity="minor",
            challenge=result.challenge,
            witness=result.witness,
            resolver_hint=result.resolver_hint,
        )

    def solve(self, problem: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        requirements = extract_explicit_requirements(problem)
        requirements_token = _REQUIREMENTS.set(requirements)
        trace_token = _ACTIVE_TRACE.set([])
        try:
            result = super().solve(problem=problem, metadata=metadata)
            if isinstance(result.get("trace"), list):
                result["trace"].insert(
                    1,
                    {
                        "step": "explicit_requirements",
                        "content": {
                            "count": len(requirements),
                            "derivation_required": any(
                                _DERIVATION_REQUIREMENT.search(item or "")
                                for item in requirements
                            ),
                        },
                    },
                )
            return result
        except Exception as exc:
            trace = list(_ACTIVE_TRACE.get() or [])
            if trace:
                trace.insert(
                    1,
                    {
                        "step": "explicit_requirements",
                        "content": {
                            "count": len(requirements),
                            "derivation_required": any(
                                _DERIVATION_REQUIREMENT.search(item or "")
                                for item in requirements
                            ),
                        },
                    },
                )
                try:
                    setattr(exc, "trace", trace)
                except Exception:
                    pass
            raise
        finally:
            _ACTIVE_TRACE.reset(trace_token)
            _REQUIREMENTS.reset(requirements_token)
