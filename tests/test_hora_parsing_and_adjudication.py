import unittest

from agent.adjudication import select_best_candidate
from agent.evidence import challenge_from_audit, evaluate_candidate
from agent.models import (
    CaseState,
    MethodFingerprint,
    SolutionCapsule,
    TaskContract,
)
from agent.parsing import parse_audit_result, parse_solution_capsule


class ParsingAdjudicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = TaskContract(
            primary_domain="general",
            secondary_domains=(),
            problem_kind="calculation",
            answer_schema="exact_expression",
            requires_proof=False,
            requires_exact_answer=True,
            multipart_count=1,
            risk_level="medium",
            verification_modes=("format_check",),
            mandatory_attacks=("boundary",),
            likely_failure_modes=("missing_case",),
            route_hint="R1",
            primary_method="direct",
            orthogonal_method="constructive",
        )

    def test_solution_capsule_parser(self) -> None:
        text = """
<FINAL_CANDIDATE>42</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: constructive
representation: symbolic
theorem_family: definition
tool_channel: none
interpretation_id: I1
exposed_to_primary: false
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS><CLAIM id="C7">A decisive fact.</CLAIM></CRITICAL_CLAIMS>
<FINAL_RESPONSE>The result is 42.</FINAL_RESPONSE>
"""
        capsule = parse_solution_capsule(
            text,
            candidate_id="A",
            source="primary",
            fallback_fingerprint=MethodFingerprint(),
            requires_proof=False,
        )
        self.assertEqual(capsule.answer_raw, "42")
        self.assertEqual(capsule.claims[0].claim_id, "C7")
        self.assertEqual(capsule.fingerprint.paradigm, "constructive")

    def test_audit_parser_rejects_unknown_verdict(self) -> None:
        audit = parse_audit_result("<VERDICT>MAYBE</VERDICT>")
        self.assertEqual(audit.verdict, "UNRESOLVED")

    def test_fatal_counterexample_vetoes_soft_candidate(self) -> None:
        state = CaseState(contract=self.contract)
        a = SolutionCapsule(
            candidate_id="A",
            source="primary",
            answer_raw="1",
            final_response="1",
            fingerprint=MethodFingerprint(paradigm="theorem"),
        )
        b = SolutionCapsule(
            candidate_id="B",
            source="orthogonal_blind",
            answer_raw="2",
            final_response="2",
            fingerprint=MethodFingerprint(paradigm="constructive"),
        )
        state.add_candidate(a)
        state.add_candidate(b)
        for candidate in (a, b):
            for evidence in evaluate_candidate(candidate, self.contract):
                state.add_evidence(evidence)

        state.add_challenge(
            challenge_from_audit(
                challenge_id="CH1",
                candidate_id="A",
                target_claim_id="C1",
                attack_type="counterexample",
                severity="fatal",
                statement="A reproducible counterexample exists.",
                witness="n=1",
                resolver_hint="substitute",
                sustained=True,
            )
        )
        state.candidates["A"].eligible = False

        winner = select_best_candidate(state)
        self.assertIsNotNone(winner)
        self.assertEqual(winner.capsule.candidate_id, "B")


if __name__ == "__main__":
    unittest.main()
