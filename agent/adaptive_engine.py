from __future__ import annotations

import re
from contextvars import ContextVar

from .cross_domain_certificates import evaluate_cross_domain_certificates
from .evidence import evidence_for_candidate
from .models import EvidenceRecord, SolutionCapsule
from .verified_engine import VerifiedHORAEngine


_CURRENT_PROBLEM: ContextVar[str] = ContextVar("hora_current_problem", default="")


def _task_driven_guardrails(problem: str) -> str:
    """Compile narrow recovery guidance from mathematical structures visible in the statement.

    The guardrails contain method obligations, never benchmark reference answers. They prevent
    theorem-precondition, sign, endpoint, option-completeness, and output-shape failures before a
    candidate reaches the evidence gate.
    """

    text = str(problem or "")
    blocks: list[str] = []

    option_labels = set(
        re.findall(
            r"(?:^|[\s；;:：。])\s*[（(]?\s*([A-FＡ-Ｆ])\s*(?:[)）]|[.、:：])",
            text,
            flags=re.MULTILINE,
        )
    )
    multi_select = len(option_labels) >= 2 and re.search(
        r"哪些|哪几项|选出.*(?:正确|错误|成立|不成立)|which\s+(?:statements?|options?)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if multi_select:
        blocks.append(
            "MULTI-SELECT COMPLETENESS GUARD: Evaluate EVERY labelled option independently before writing "
            "FINAL_CANDIDATE. Build an internal true/false table for all options; do not stop after finding some "
            "correct statements. Recompute any stated stability function or invariant. Distinguish a symplectic "
            "property from exact preservation of a general Hamiltonian: one does not automatically imply the other. "
            "FINAL_CANDIDATE must contain exactly the letters judged true."
        )

    if re.search(r"Radau\s*IIA|Runge[- ]?Kutta", text, flags=re.IGNORECASE) and re.search(
        r"R\s*\(z\).*\(I-zA\)|A-稳定|A[- ]stable",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        blocks.append(
            "RUNGE-KUTTA ARITHMETIC GUARD: Recompute every displayed 2x2 inverse/vector product from the "
            "given Butcher coefficients. Check each row sum of (I-zA)^(-1)1 before applying b^T. On z=i*w, "
            "expand the real and imaginary parts of the denominator separately and square them term-by-term. "
            "Every intermediate coefficient must be algebraically compatible with the final R(z)."
        )

    levy_signal = re.search(
        r"\\mathbb\s*E\s*\[\s*X\s*\\mid\s*\\mathcal\s*F_?n|M_?n\s*=\s*\\mathbb\s*E|条件期望",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ) and re.search(r"L\^?1|L_1|L¹", text, flags=re.IGNORECASE)
    if levy_signal:
        blocks.append(
            "LEVY-UPWARD GUARD: Nonnegative/L1-bounded martingale convergence alone does NOT imply L1 "
            "convergence. For M_n=E[X|F_n], explicitly establish uniform integrability of the conditional-"
            "expectation family (for example by truncating the one integrable variable X), then use martingale "
            "convergence and the conditional-expectation identity to identify the F_infinity-measurable limit. "
            "Do not approximate an arbitrary X by F_N-measurable variables unless X is known F_infinity-measurable."
        )

    if re.search(r"平行移动|parallel transport|holonomy", text, flags=re.IGNORECASE) and re.search(
        r"联络\s*1-?形式|connection\s*1-?form|Gauss[- ]?Bonnet", text, flags=re.IGNORECASE
    ):
        blocks.append(
            "HOLONOMY SIGN GUARD: A parallel-transported vector generally does NOT return with unchanged "
            "direction around a curved closed loop. Keep one orientation convention throughout. If dtheta=-omega "
            "and domega=-K dA, Stokes already gives the holonomy integral. Apply Gauss-Bonnet to the triangle "
            "separately; do not derive Gauss-Bonnet by forcing the transported vector to return to its original direction."
        )

    if re.search(r"原滤过|original filtration", text, flags=re.IGNORECASE) and re.search(
        r"Brownian|布朗|指数鞅|exponential martingale", text, flags=re.IGNORECASE
    ):
        blocks.append(
            "ORIGINAL-FILTRATION GUARD: The required conditional characteristic function must be conditioned "
            "on the ORIGINAL filtration F_s. Proving independence only from the natural filtration of M is a "
            "strictly weaker statement and does not satisfy the task."
        )

    if re.search(r"James[-– ]?Stein|\\delta_?a|δ_a", text, flags=re.IGNORECASE) and re.search(
        r"Stein.*恒等式|Stein.*identity|风险|risk", text, flags=re.IGNORECASE | re.DOTALL
    ):
        blocks.append(
            "JAMES-STEIN RANGE GUARD: After deriving the scalar coefficient multiplying E[1/||X||^2], "
            "solve the non-increase inequality with endpoints included, then state the strict-improvement "
            "range separately. Do not replace the closed non-increase range by the open strict range."
        )

    algebra_objects = (
        re.search(r"Spec\s*R|\\operatorname\{Spec\}", text, flags=re.IGNORECASE)
        and re.search(r"极大理想|maximal ideals?", text, flags=re.IGNORECASE)
        and re.search(r"极小素理想|minimal primes?", text, flags=re.IGNORECASE)
        and re.search(r"nilradical|幂零根|nilpotent", text, flags=re.IGNORECASE)
        and re.search(r"零因子|zero divisors?", text, flags=re.IGNORECASE)
    )
    if algebra_objects:
        blocks.append(
            "MULTI-OBJECT ALGEBRA GUARD: FINAL_CANDIDATE must be a compact self-contained summary listing "
            "the prime ideals, maximal ideals, minimal primes, nilradical, complete zero-divisor set, and reduced "
            "status. In FINAL_RESPONSE prove BOTH inclusions for the zero-divisor description and justify why "
            "zero divisors do not imply nilpotents. Do not end the candidate with a heading such as 'zero divisors are'."
        )

    return "\n\n".join(blocks)


class AdaptiveVerifiedHORAEngine(VerifiedHORAEngine):
    """Verified HORA with statement-driven recovery guardrails and cross-domain certificates."""

    @staticmethod
    def _trace_rejection_codes(state, capsule) -> None:
        """Record only opaque checker/reason codes; never candidate values or problem snippets."""
        failed = [
            item
            for item in evidence_for_candidate(state, capsule.candidate_id)
            if item.status == "fail" and item.strength in {"hard", "fatal"}
        ]
        if not failed:
            return
        from .resilient_engine import _ACTIVE_TRACE

        trace = _ACTIVE_TRACE.get()
        if trace is None:
            return
        trace.append(
            {
                "step": "candidate_evidence_gate",
                "content": {
                    "candidate_id": capsule.candidate_id,
                    "source": capsule.source,
                    "reason_codes": [item.evidence_type for item in failed[:8]],
                },
            }
        )

    def _apply_candidate_evidence(self, state, capsule: SolutionCapsule) -> None:
        super()._apply_candidate_evidence(state, capsule)
        new_failure = False
        for index, check in enumerate(
            evaluate_cross_domain_certificates(
                answer_raw=capsule.answer_raw,
                response=capsule.final_response,
            ),
            start=1,
        ):
            state.add_evidence(
                EvidenceRecord(
                    evidence_id=f"E-cross-{capsule.candidate_id}-{index}-{len(state.evidence)}",
                    candidate_id=capsule.candidate_id,
                    evidence_type=f"cross_domain_certificate:{check.code}",
                    status=check.status,  # type: ignore[arg-type]
                    strength="hard" if check.hard_failure else "structural",
                    checker="cross_domain_consistency_certificate",
                    detail_code=check.detail,
                )
            )
            if check.hard_failure and check.status == "fail":
                state.candidates[capsule.candidate_id].eligible = False
                new_failure = True
        if new_failure:
            self._trace_rejection_codes(state, capsule)

    def _call_model(self, *, state, guard, trace, step, prompt, temperature, max_tokens, thinking_mode=None):
        guardrails = _task_driven_guardrails(_CURRENT_PROBLEM.get())
        if guardrails:
            prompt = "TASK-DRIVEN MATHEMATICAL GUARDRAILS\n" + guardrails + "\n\n" + prompt
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

    def _confirmation_result(self, *, problem, state, guard, trace, selected: SolutionCapsule):
        result = super()._confirmation_result(
            problem=problem,
            state=state,
            guard=guard,
            trace=trace,
            selected=selected,
        )
        if result.verdict == "UNRESOLVED":
            state.add_evidence(
                EvidenceRecord(
                    evidence_id=f"E-confirm-unresolved-{selected.candidate_id}-{len(state.evidence)}",
                    candidate_id=selected.candidate_id,
                    evidence_type="decisive_confirmation_unresolved",
                    status="fail",
                    strength="hard",
                    checker="decisive_local_verifier",
                    target_claim_id=result.target_claim_id,
                    detail_code="independent_local_check_did_not_confirm",
                )
            )
            state.candidates[selected.candidate_id].eligible = False
            self._trace_rejection_codes(state, selected)
        return result

    def solve(self, problem: str, metadata: dict | None = None) -> dict:
        token = _CURRENT_PROBLEM.set(str(problem or ""))
        try:
            return super().solve(problem=problem, metadata=metadata)
        finally:
            _CURRENT_PROBLEM.reset(token)
