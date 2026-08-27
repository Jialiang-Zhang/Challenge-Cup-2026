from __future__ import annotations

from textwrap import dedent

from .models import SolutionCapsule, TaskContract


def decisive_confirmation_prompt(
    problem: str,
    contract: TaskContract,
    candidate: SolutionCapsule,
    *,
    context_limit: int,
) -> str:
    response = candidate.final_response[:context_limit]
    claims = "\n".join(
        f"{claim.claim_id}: {claim.statement}" for claim in candidate.claims[:6]
    ) or "No parsed claims."
    return dedent(
        f"""
        You are HORA-Math Decisive Local Verifier. This is NOT a general review and NOT a request
        for a fresh long solution. Independently recompute the single most fragile mathematical
        step in Candidate A from first principles, then compare your recomputation with the text.

        TASK
        Domain: {contract.primary_domain}
        Requires proof: {contract.requires_proof}
        Answer obligations: {', '.join(contract.answer_obligations)}
        Multipart count: {contract.multipart_count}

        PROBLEM
        {problem}

        CANDIDATE A CLAIMS
        {claims}

        CANDIDATE A SUBMISSION
        {response}

        CHECK PRIORITY
        1. Arithmetic/Taylor/series coefficients and normalization constants.
        2. Inequality direction and the exact conditioning set in entropy/probability arguments.
        3. Theorem preconditions, signs, multiplicities, boundary cases, and quantifiers.
        4. Any sentence that retracts or corrects an earlier mathematical statement. A final answer
           does not become rigorous merely because a later paragraph repairs an earlier false assertion.
        5. If the problem requests a derivation, verify at least one decisive displayed equation by
           recomputing it, rather than accepting because the final formula looks familiar.

        VERDICT RULE
        - ACCEPT_A only if your independent recomputation agrees and WITNESS states the concrete
          checked equation/condition.
        - REPAIR_A if you find one localized false equality, coefficient, inequality direction,
          normalization, theorem condition, or contradictory proof step, even when the final conclusion is correct.
        - UNRESOLVED if you cannot complete a concrete check.

        Output ONLY these seven tags and stop:
        <VERDICT>ACCEPT_A|REPAIR_A|UNRESOLVED</VERDICT>
        <TARGET_CANDIDATE>A</TARGET_CANDIDATE>
        <TARGET_CLAIM>C1|C2|C3|C4|C5|C6|FINAL|none</TARGET_CLAIM>
        <ATTACK_TYPE>assumption|theorem_precondition|counterexample|boundary|transformation|quantifier|interpretation|numerical_stress|completeness|none</ATTACK_TYPE>
        <SEVERITY>fatal|major|minor|none</SEVERITY>
        <CHALLENGE>Smallest concrete defect, or none.</CHALLENGE>
        <WITNESS>Your independent recomputation/check, never a generic approval.</WITNESS>
        <RESOLVER_HINT>Shortest local repair/check, or none.</RESOLVER_HINT>
        """
    ).strip()
