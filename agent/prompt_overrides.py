from __future__ import annotations

from textwrap import dedent

from .models import TaskContract
from .prompts import answer_shape_instruction


def _contract_block(contract: TaskContract) -> str:
    secondary = ", ".join(contract.secondary_domains) or "none"
    alternates = ", ".join(contract.alternate_modes) or "none"
    obligations = ", ".join(contract.answer_obligations) or "explicit_final_answer"
    return dedent(
        f"""
        Domain: {contract.primary_domain}
        Secondary domains: {secondary}
        Problem kind: {contract.problem_kind}
        Question mode: {contract.question_mode} (confidence={contract.mode_confidence:.2f})
        Alternate modes: {alternates}
        Answer schema: {contract.answer_schema}
        Answer obligations: {obligations}
        Requires proof: {contract.requires_proof}
        Multipart count: {contract.multipart_count}
        Risk: {contract.risk_level}
        Likely failure modes: {', '.join(contract.likely_failure_modes)}
        """
    ).strip()


def _response_requirement(contract: TaskContract, *, independent: bool = False) -> str:
    qualifier = "independent " if independent else ""
    if contract.requires_proof or contract.answer_schema == "proof":
        return (
            f"Write a concise but complete {qualifier}proof. Cover every explicit requested step, "
            "state theorem preconditions where used, and stop once the requested conclusion is established. "
            "Do not add stronger classification/existence claims that the problem did not ask for."
        )
    if "derivation_chain" in contract.answer_obligations:
        return (
            f"Give the exact answer and the requested {qualifier}derivation. Show the decisive equations or "
            "conditional identities rather than merely naming a theorem or saying that a calculation simplifies."
        )
    if contract.multipart_count > 1:
        return (
            f"Answer all {contract.multipart_count} requested parts in order with a compact {qualifier}derivation "
            "for each part. Do not omit a requested stability, boundary, uniqueness, or equality-condition check."
        )
    return (
        f"Write the exact answer first, followed by one short {qualifier}derivation that checks the decisive "
        "sign, domain, boundary, or theorem condition when applicable."
    )


def _strict_protocol_block(response_requirement: str, contract: TaskContract) -> str:
    return dedent(
        f"""
        OUTPUT CONTRACT
        - Your FIRST characters must be <FINAL_CANDIDATE>. No thinking preamble is allowed.
        - Answer shape: {answer_shape_instruction(contract)}
        - Inside FINAL_CANDIDATE write the actual mathematical conclusion, never an instruction.
        - Keep FINAL_CANDIDATE compact; detailed reasoning belongs only in FINAL_RESPONSE.
        - Emit every remaining field in the exact order below and stop immediately after </FINAL_RESPONSE>.
        - Never copy template phrases such as "Exact answer", "First decisive claim", or "...".
        - Prefer equations and decisive implications over prose. Avoid repeating the same derivation.
        - Do not make optional stronger claims (classification, uniqueness, equality existence, historical facts)
          unless they are required for the requested conclusion.

        <METHOD_FINGERPRINT>
        paradigm: choose one of direct|contradiction|constructive|induction|counting|optimization|theorem
        representation: choose one of symbolic|geometric|graph|event|operator|coordinate|generating_function|other
        theorem_family: actual short theorem or method family, or none
        tool_channel: choose one of none|sympy|numeric|brute_force|residual|matrix
        interpretation_id: I1
        exposed_to_primary: false
        </METHOD_FINGERPRINT>

        <CRITICAL_CLAIMS>
        Write one to six actual decisive claims. Map the explicit requested steps into these claims.
        Each claim must use <CLAIM id="C1">a concrete mathematical statement</CLAIM>.
        </CRITICAL_CLAIMS>

        <CHECK_HINTS>
        Give concrete falsification checks for the decisive formulas or theorem conditions, or none.
        </CHECK_HINTS>

        <RISK_FLAGS>
        List genuinely unresolved mathematical risks, or none.
        </RISK_FLAGS>

        <FINAL_RESPONSE>
        {response_requirement}
        Keep the proof/derivation compact enough to finish the closing tag. Normally use at most about
        1400 Chinese characters or 900 English words unless the task has many explicit parts.
        </FINAL_RESPONSE>
        """
    ).strip()


def primary_prompt_v2(problem: str, contract: TaskContract) -> str:
    return dedent(
        f"""
        You are HORA-Math Blue Team Solver S1. Solve the mathematical problem rigorously using the assigned
        primary method family: {contract.primary_method}. Compute and verify the result before emitting the
        response. Do not use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        {_strict_protocol_block(_response_requirement(contract), contract)}
        """
    ).strip()


def blind_prompt_v2(problem: str, contract: TaskContract) -> str:
    return dedent(
        f"""
        You are HORA-Math Blue Team Solver S2, an ORTHOGONAL BLIND solver. You have not seen any other
        candidate. Solve independently with the assigned method family: {contract.orthogonal_method}.

        Use a genuinely different route: definitions, construction, contradiction, an alternative
        representation, local calculation, counting, or another theorem family. State all needed
        assumptions. Do not use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        {_strict_protocol_block(_response_requirement(contract, independent=True), contract)}
        """
    ).strip()


def repair_prompt_v2(
    problem: str,
    contract: TaskContract,
    *,
    parent_answer: str,
    parent_response: str,
    challenge: str,
    witness: str,
    resolver_hint: str,
) -> str:
    response_requirement = _response_requirement(contract)
    return dedent(
        f"""
        You are HORA-Math one-shot Targeted Repair Solver. A red-team audit found a localized mathematical
        defect. Recompute the disputed point from first principles, preserve only independently confirmed
        unaffected claims, and return a corrected submission. Do not defend a value merely because it
        appeared in the parent candidate.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        PARENT ANSWER
        {parent_answer}

        PARENT RESPONSE
        {parent_response[:2400]}

        RED-TEAM CHALLENGE
        challenge: {challenge or 'none'}
        witness: {witness or 'none'}
        resolver hint: {resolver_hint or 'none'}

        OUTPUT CONTRACT
        - Your FIRST characters must be <FINAL_CANDIDATE>.
        - Answer shape: {answer_shape_instruction(contract)}
        - Do not copy the parent conclusion unless your recomputation confirms it.
        - Address the challenged claim explicitly and cover every still-applicable task obligation.
        - Do not introduce stronger claims not requested by the problem.
        - Emit the fields below in order and stop after </FINAL_RESPONSE>.

        <METHOD_FINGERPRINT>
        paradigm: choose one actual corrected method family
        representation: choose one actual representation
        theorem_family: actual theorem or method family, or none
        tool_channel: choose one of none|sympy|numeric|brute_force|residual|matrix
        interpretation_id: I1
        exposed_to_primary: true
        </METHOD_FINGERPRINT>

        <CRITICAL_CLAIMS>
        Write one to five corrected decisive claims using
        <CLAIM id="C1">a concrete mathematical statement</CLAIM>.
        </CRITICAL_CLAIMS>

        <CHALLENGE_RESOLUTION>
        State the exact equation, condition, counterexample rejection, or implication that resolves the audit.
        </CHALLENGE_RESOLUTION>

        <CHECK_HINTS>
        Give one concrete falsification check.
        </CHECK_HINTS>

        <RISK_FLAGS>
        List remaining risks, or none.
        </RISK_FLAGS>

        <FINAL_RESPONSE>
        {response_requirement}
        Keep it concise and finish the closing tag.
        </FINAL_RESPONSE>
        """
    ).strip()


def rescue_prompt_v2(problem: str, contract: TaskContract) -> str:
    return dedent(
        f"""
        You are HORA-Math Rescue Solver. Earlier candidates were invalid or unresolved. Recompute the task
        from scratch using the shortest reliable route; do not inherit any alleged previous answer. Do not
        use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        {_strict_protocol_block(_response_requirement(contract), contract)}
        """
    ).strip()
