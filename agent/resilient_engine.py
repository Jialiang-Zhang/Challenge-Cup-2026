from __future__ import annotations

import re
from contextvars import ContextVar
from typing import Any

from .adjudication import has_irreversible_evidence_failure
from .models import AuditResult, CaseState, SolutionCapsule
from .staged_engine import StagedHORAEngine


_REQUIREMENTS: ContextVar[tuple[str, ...]] = ContextVar(
    "hora_explicit_requirements", default=()
)

_REQUIREMENT_MARKERS = re.compile(
    r"(?:要求|必须|需(?:要)?|请|严格证明|进一步证明|并说明|说明为什么|解释|构造|验证|证明)",
    flags=re.IGNORECASE,
)
_NUMBERED_CLAUSE = re.compile(
    r"(?:^|[；;。\n])\s*(?:\(\d+\)|（\d+）|\d+[.)、])\s*([^；;。\n]{4,220})"
)


def extract_explicit_requirements(problem: str, limit: int = 8) -> tuple[str, ...]:
    """Extract user-visible proof/derivation obligations without solving the problem.

    The extractor is deliberately lexical.  It does not invent mathematical facts;
    it only preserves explicit requests already present in the statement so every
    solver and auditor sees the same completion checklist.
    """

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
    """Staged HORA engine with evidence-authenticated vetoes and safe recovery.

    This layer keeps the strict path unchanged.  It only intervenes when a semantic
    red-team veto lacks concrete mathematical support, or when the strict path has
    exhausted rescue and a usable non-contradicted candidate would otherwise be
    discarded for presentation/protocol reasons.
    """

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
        token = _REQUIREMENTS.set(extract_explicit_requirements(problem))
        try:
            result = super().solve(problem=problem, metadata=metadata)
            requirements = _REQUIREMENTS.get()
            if requirements and isinstance(result.get("trace"), list):
                result["trace"].insert(
                    1,
                    {
                        "step": "explicit_requirements",
                        "content": {
                            "count": len(requirements),
                            "requirements": list(requirements),
                        },
                    },
                )
            return result
        finally:
            _REQUIREMENTS.reset(token)
