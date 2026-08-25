import unittest

from agent.adjudication import select_best_candidate
from agent.evidence import challenge_from_audit, evaluate_candidate
from agent.models import CaseState, MethodFingerprint, SolutionCapsule, TaskContract
from agent.parsing import extract_asserted_answer, extract_tag, parse_audit_result, parse_solution_capsule


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
<FINAL_RESPONSE>42</FINAL_RESPONSE>
"""
        result = parse_solution_capsule(
            text,
            candidate_id="A",
            source="primary",
            fallback_fingerprint=MethodFingerprint(),
            requires_proof=False,
        )
        self.assertEqual(result.answer_raw, "42")
        self.assertEqual(result.claims[0].claim_id, "C7")
        self.assertFalse(result.truncated)

    def test_schema_echo_is_ignored_before_real_sections(self) -> None:
        text = r"""
The `<FINAL_CANDIDATE>` and `<FINAL_RESPONSE>` names are schema tokens.
<FINAL_CANDIDATE>-1/8</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: direct
representation: symbolic
theorem_family: residue
tool_channel: none
interpretation_id: I1
exposed_to_primary: false
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS><CLAIM id="C1">The pole is simple.</CLAIM></CRITICAL_CLAIMS>
<FINAL_RESPONSE>-1/8</FINAL_RESPONSE>
"""
        result = parse_solution_capsule(
            text,
            candidate_id="A",
            source="primary",
            fallback_fingerprint=MethodFingerprint(),
            requires_proof=False,
        )
        self.assertEqual(result.answer_raw, "-1/8")
        self.assertFalse(result.truncated)
        self.assertIsNone(
            extract_tag("Only discuss `<FINAL_CANDIDATE>` inline.", "FINAL_CANDIDATE")
        )

    def test_asserted_answer_extraction(self) -> None:
        self.assertEqual(extract_asserted_answer("The exact value is $-1$."), "-1")
        self.assertEqual(
            extract_asserted_answer("因此正确答案为 $-\\frac{1}{8}$。"),
            r"-\frac{1}{8}",
        )
        self.assertIsNone(extract_asserted_answer("The work mentions 1 and 635."))

    def test_audit_parser_rejects_unknown_verdict(self) -> None:
        audit = parse_audit_result("<VERDICT>MAYBE</VERDICT>")
        self.assertEqual(audit.verdict, "UNRESOLVED")

    def test_truncated_candidate_cannot_win(self) -> None:
        state = CaseState(contract=self.contract)
        bad = SolutionCapsule(
            candidate_id="A",
            source="primary",
            answer_raw="72",
            final_response="72",
            fingerprint=MethodFingerprint(paradigm="theorem"),
            complete=True,
            truncated=True,
        )
        good = SolutionCapsule(
            candidate_id="B",
            source="orthogonal_blind",
            answer_raw="54",
            final_response="54",
            fingerprint=MethodFingerprint(paradigm="constructive"),
        )
        state.add_candidate(bad)
        state.add_candidate(good)
        for item in (bad, good):
            for evidence in evaluate_candidate(item, self.contract):
                state.add_evidence(evidence)
        state.candidates["A"].eligible = False
        winner = select_best_candidate(state)
        self.assertIsNotNone(winner)
        self.assertEqual(winner.capsule.candidate_id, "B")

    def test_fatal_challenge_vetoes_candidate(self) -> None:
        state = CaseState(contract=self.contract)
        first = SolutionCapsule(
            candidate_id="A",
            source="primary",
            answer_raw="1",
            final_response="1",
            fingerprint=MethodFingerprint(paradigm="theorem"),
        )
        second = SolutionCapsule(
            candidate_id="B",
            source="orthogonal_blind",
            answer_raw="2",
            final_response="2",
            fingerprint=MethodFingerprint(paradigm="constructive"),
        )
        state.add_candidate(first)
        state.add_candidate(second)
        for item in (first, second):
            for evidence in evaluate_candidate(item, self.contract):
                state.add_evidence(evidence)
        state.add_challenge(
            challenge_from_audit(
                challenge_id="CH1",
                candidate_id="A",
                target_claim_id="C1",
                attack_type="boundary",
                severity="fatal",
                statement="A reproducible failure exists.",
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
