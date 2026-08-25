from __future__ import annotations

from textwrap import dedent

from .domain_checks import solver_obligations
from .models import TaskContract


def _contract_block(contract: TaskContract) -> str:
    secondary = ", ".join(contract.secondary_domains) or "none"
    return dedent(
        f"""
        Domain: {contract.primary_domain}
        Secondary domains: {secondary}
        Problem kind: {contract.problem_kind}
        Answer schema: {contract.answer_schema}
        Requires proof: {contract.requires_proof}
        Multipart count: {contract.multipart_count}
        Risk: {contract.risk_level}
        Likely failure modes: {', '.join(contract.likely_failure_modes)}
        """
    ).strip()


def _obligation_block(problem: str, contract: TaskContract) -> str:
    obligations = solver_obligations(problem, contract)
    if not obligations:
        return "No additional domain-specific obligations."
    return "\n".join(f"{index}. {item}" for index, item in enumerate(obligations, 1))


def _strict_protocol_block(response_requirement: str) -> str:
    return dedent(
        f"""
        OUTPUT CONTRACT
        - Start the response immediately with <FINAL_CANDIDATE>; do not write a preamble.
        - Put the actual computed value, expression, option set, or theorem conclusion inside it.
        - Close </FINAL_CANDIDATE> before opening any later protocol section.
        - Emit every section exactly once, in the order shown, and stop after </FINAL_RESPONSE>.
        - Never copy placeholders or instructions into a protocol field.
        - Do not nest FINAL_CANDIDATE inside FINAL_RESPONSE.

        <FINAL_CANDIDATE>
        actual compact mathematical answer or conclusion
        </FINAL_CANDIDATE>

        <METHOD_FINGERPRINT>
        paradigm: choose one of direct|contradiction|constructive|induction|counting|optimization|theorem
        representation: choose one of symbolic|geometric|graph|event|operator|coordinate|generating_function|other
        theorem_family: write the actual short theorem or method family, or none
        tool_channel: choose one of none|sympy|numeric|brute_force|residual|matrix
        interpretation_id: I1
        exposed_to_primary: false
        </METHOD_FINGERPRINT>

        <CRITICAL_CLAIMS>
        Write one to six actual decisive claims. Each claim must use
        <CLAIM id="C1">a concrete mathematical statement</CLAIM>.
        Include all theorem preconditions and every proof obligation that controls the conclusion.
        </CRITICAL_CLAIMS>

        <CHECK_HINTS>
        Write concrete substitutions, invariant checks, boundary cases, or theorem-condition checks
        that could falsify this route; otherwise write none.
        </CHECK_HINTS>

        <RISK_FLAGS>
        Write unresolved mathematical risks, or none.
        </RISK_FLAGS>

        <FINAL_RESPONSE>
        {response_requirement}
        Keep it submission-ready and compact, but do not omit a requested proof step.
        </FINAL_RESPONSE>
        """
    ).strip()


def primary_prompt_v2(problem: str, contract: TaskContract) -> str:
    response_requirement = (
        "State the conclusion first, then give a concise complete proof satisfying every domain obligation."
        if contract.requires_proof
        else "Write the exact answer first, followed by a short derivation checking sign, domain, and boundary conditions."
    )
    return dedent(
        f"""
        You are HORA-Math Blue Team Solver S1. Solve the mathematical problem with the shortest
        rigorous route using the assigned primary method family: {contract.primary_method}.
        Work out the mathematics before emitting the protocol. Do not use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        DOMAIN-SPECIFIC PROOF OBLIGATIONS
        {_obligation_block(problem, contract)}

        PROBLEM
        {problem}

        {_strict_protocol_block(response_requirement)}
        """
    ).strip()


def blind_prompt_v2(problem: str, contract: TaskContract) -> str:
    response_requirement = (
        "State the independent conclusion first, then give a concise complete proof satisfying every domain obligation."
        if contract.requires_proof
        else "Write the exact independent answer and a short derivation."
    )
    return dedent(
        f"""
        You are HORA-Math Blue Team Solver S2, an ORTHOGONAL BLIND solver.
        You have not seen another candidate. Solve independently with the assigned method family:
        {contract.orthogonal_method}.

        Use a genuinely different route: definitions, construction, contradiction, an alternative
        representation, local calculation, counting, or another theorem family. State all needed
        assumptions. Do not use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        DOMAIN-SPECIFIC PROOF OBLIGATIONS
        {_obligation_block(problem, contract)}

        PROBLEM
        {problem}

        {_strict_protocol_block(response_requirement)}
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
    response_requirement = (
        "Write the corrected conclusion and a concise complete proof addressing both the challenge and every domain obligation."
        if contract.requires_proof
        else "Write the corrected exact answer first and a short derivation that resolves the challenge."
    )
    return dedent(
        f"""
        You are HORA-Math Targeted Repair Solver. A red-team audit or deterministic checker found a
        localized fatal defect. Recompute the disputed point and preserve only mathematics that has
        been independently verified. Do not repeat an unverified witness from the audit.

        TASK CONTRACT
        {_contract_block(contract)}

        DOMAIN-SPECIFIC PROOF OBLIGATIONS
        {_obligation_block(problem, contract)}

        PROBLEM
        {problem}

        PARENT ANSWER
        {parent_answer}

        PARENT RESPONSE
        {parent_response[:2600]}

        CHALLENGE
        statement: {challenge or 'none'}
        alleged witness: {witness or 'none'}
        resolver hint: {resolver_hint or 'none'}

        Before using a counterexample or numerical witness, verify every hypothesis and the claimed
        failure. Start immediately with <FINAL_CANDIDATE> and emit the sections below in order.

        <FINAL_CANDIDATE>
        actual corrected mathematical answer or conclusion
        </FINAL_CANDIDATE>
        <METHOD_FINGERPRINT>
        paradigm: actual corrected method family
        representation: actual mathematical representation
        theorem_family: actual theorem or method family, or none
        tool_channel: choose one of none|sympy|numeric|brute_force|residual|matrix
        interpretation_id: I1
        exposed_to_primary: true
        </METHOD_FINGERPRINT>
        <CRITICAL_CLAIMS>
        Write one to six corrected decisive claims using
        <CLAIM id="C1">a concrete mathematical statement</CLAIM>.
        </CRITICAL_CLAIMS>
        <CHALLENGE_RESOLUTION>
        Explain exactly how the defect is resolved and how the witness was verified or replaced.
        </CHALLENGE_RESOLUTION>
        <CHECK_HINTS>
        Give one reproducible falsification check.
        </CHECK_HINTS>
        <RISK_FLAGS>
        Write remaining risks, or none.
        </RISK_FLAGS>
        <FINAL_RESPONSE>
        {response_requirement}
        </FINAL_RESPONSE>
        """
    ).strip()


def rescue_prompt_v2(problem: str, contract: TaskContract) -> str:
    response_requirement = (
        "State the conclusion first, then give a concise complete proof satisfying every domain obligation."
        if contract.requires_proof
        else "Write the exact answer and one decisive verification step."
    )
    return dedent(
        f"""
        You are HORA-Math Rescue Solver. Earlier candidates were invalid or unresolved. Recompute
        the problem from scratch using the shortest reliable route. Do not reuse an alleged answer
        or counterexample unless you independently verify it. Do not use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        DOMAIN-SPECIFIC PROOF OBLIGATIONS
        {_obligation_block(problem, contract)}

        PROBLEM
        {problem}

        {_strict_protocol_block(response_requirement)}
        """
    ).strip()
