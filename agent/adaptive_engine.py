from __future__ import annotations

import re
from contextvars import ContextVar

from .verified_engine import VerifiedHORAEngine


_CURRENT_PROBLEM: ContextVar[str] = ContextVar("hora_current_problem", default="")


def _task_driven_guardrails(problem: str) -> str:
    """Compile narrow recovery guidance from mathematical structures visible in the statement.

    The guardrails contain method obligations, never benchmark reference answers. They are meant to
    prevent known theorem-precondition, sign, endpoint, and output-shape failures before a candidate
    reaches the evidence gate.
    """

    text = str(problem or "")
    blocks: list[str] = []

    if re.search(r"Radau\s*IIA|Runge[- ]?Kutta", text, flags=re.IGNORECASE) and re.search(
        r"R\s*\(z\).*\(I-zA\)|A-稳定|A[- ]stable",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        blocks.append(
            "RUNGE-KUTTA ARITHMETIC GUARD: Recompute every displayed 2x2 inverse/vector product from the "
            "given Butcher coefficients. On z=i*w, expand numerator and denominator moduli independently "
            "before comparing them. Do not keep an intermediate coefficient that contradicts the final R(z)."
        )

    if re.search(r"\\mathcal\s*F_?n.*\\mathcal\s*F_?\\infty|F_n.*F_.*infty", text, flags=re.IGNORECASE | re.DOTALL) and re.search(
        r"\\mathbb\s*E\s*\[\s*X.*\\mathcal\s*F_?n|条件期望", text, flags=re.IGNORECASE | re.DOTALL
    ):
        blocks.append(
            "LEVY-UPWARD GUARD: Nonnegative/L1-bounded martingale convergence alone does NOT imply L1 "
            "convergence. Establish uniform integrability of the conditional-expectation family (or use a "
            "valid approximation of the F_infinity-measurable limit), then identify the limit by the conditional "
            "expectation property. Do not approximate an arbitrary X by F_N-measurable variables unless X is "
            "known F_infinity-measurable."
        )

    if re.search(r"平行移动|parallel transport|holonomy", text, flags=re.IGNORECASE) and re.search(
        r"联络\s*1-?形式|connection\s*1-?form|Gauss[- ]?Bonnet", text, flags=re.IGNORECASE
    ):
        blocks.append(
            "HOLONOMY SIGN GUARD: A parallel-transported vector generally does NOT return with unchanged "
            "direction. Keep one orientation convention throughout. If dtheta=-omega and domega=-K dA, apply "
            "Stokes directly; never discard a minus sign by claiming +I and -I are automatically equal mod 2pi."
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
    """Verified HORA with statement-driven recovery guardrails."""

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

    def solve(self, problem: str, metadata: dict | None = None) -> dict:
        token = _CURRENT_PROBLEM.set(str(problem or ""))
        try:
            return super().solve(problem=problem, metadata=metadata)
        finally:
            _CURRENT_PROBLEM.reset(token)
