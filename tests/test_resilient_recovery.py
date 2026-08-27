import unittest

from agent.adjudication import freeze_candidate, select_best_candidate
from agent.models import (
    AuditResult,
    CaseState,
    EvidenceRecord,
    MethodFingerprint,
    SolutionCapsule,
    TaskContract,
)
from agent.prompt_overrides import primary_prompt_v2
from agent.requirement_checks import evaluate_explicit_requirement_coverage
from agent.resilient_engine import ResilientHORAEngine, extract_explicit_requirements


class ResilientRecoveryTest(unittest.TestCase):
    def _contract(self, *, proof=False, mode="open_response"):
        return TaskContract(
            primary_domain="general",
            secondary_domains=(),
            problem_kind="proof" if proof else "calculation",
            answer_schema="proof" if proof else "exact_expression",
            requires_proof=proof,
            requires_exact_answer=not proof,
            multipart_count=1,
            risk_level="high" if proof else "medium",
            verification_modes=("format_check",),
            mandatory_attacks=("completeness",),
            likely_failure_modes=("missing_case",),
            route_hint="R2" if proof else "R1",
            primary_method="direct",
            orthogonal_method="constructive",
            question_mode=mode,
        )

    @staticmethod
    def _capsule(candidate_id="A", source="primary", *, proof=False, truncated=True):
        response = (
            "由已知条件先得到关键等式。因为每一步都保持等价，所以可推出目标结论。"
            "再检查边界条件与定义域均满足，因此结论成立，证毕。"
            if proof
            else "42"
        )
        return SolutionCapsule(
            candidate_id=candidate_id,
            source=source,
            answer_raw="42",
            final_response=response,
            fingerprint=MethodFingerprint(paradigm="direct"),
            complete=True,
            truncated=truncated,
            protocol_complete=not truncated,
        )

    def _add_presentation_failure(self, state, capsule):
        state.add_candidate(capsule)
        state.add_evidence(
            EvidenceRecord(
                evidence_id=f"fmt-{capsule.candidate_id}",
                candidate_id=capsule.candidate_id,
                evidence_type="format_contract",
                status="pass",
                strength="structural",
                checker="test",
            )
        )
        state.add_evidence(
            EvidenceRecord(
                evidence_id=f"trunc-{capsule.candidate_id}",
                candidate_id=capsule.candidate_id,
                evidence_type="truncation",
                status="fail",
                strength="hard",
                checker="test",
            )
        )

    def test_degraded_commit_waits_until_rescue_exists(self):
        state = CaseState(contract=self._contract())
        self._add_presentation_failure(state, self._capsule())
        self.assertIsNone(select_best_candidate(state))

        self._add_presentation_failure(
            state,
            self._capsule(candidate_id="R", source="rescue"),
        )
        winner = select_best_candidate(state)
        self.assertIsNotNone(winner)
        self.assertEqual(winner.capsule.answer_raw, "42")
        freeze_candidate(state, winner.capsule.candidate_id)
        self.assertTrue(winner.frozen)

    def test_degraded_commit_rejects_mathematical_hard_failure(self):
        state = CaseState(contract=self._contract())
        rescue = self._capsule(candidate_id="R", source="rescue")
        self._add_presentation_failure(state, rescue)
        state.add_evidence(
            EvidenceRecord(
                evidence_id="bad-consistency",
                candidate_id="R",
                evidence_type="answer_response_consistency",
                status="fail",
                strength="hard",
                checker="test",
            )
        )
        self.assertIsNone(select_best_candidate(state))

    def test_proof_fallback_requires_a_real_chain(self):
        state = CaseState(contract=self._contract(proof=True))
        weak = self._capsule(candidate_id="R", source="rescue", proof=True)
        weak.final_response = "结论成立。"
        self._add_presentation_failure(state, weak)
        self.assertIsNone(select_best_candidate(state))

    def test_truncated_proof_is_never_safe_fallback(self):
        state = CaseState(contract=self._contract(proof=True))
        broken = self._capsule(candidate_id="R", source="rescue", proof=True)
        broken.final_response = (
            "由链式法则得到等式，因为条件越多条件熵越小，所以每一项可比较。"
            "继续整理得到关键不等式，最后需要代入 $H(Z_i\\mid"
        )
        self._add_presentation_failure(state, broken)
        self.assertIsNone(select_best_candidate(state))

    def test_high_risk_primary_needs_decisive_support(self):
        state = CaseState(contract=self._contract(proof=True))
        primary = self._capsule(proof=True, truncated=False)
        state.add_candidate(primary)
        state.add_evidence(
            EvidenceRecord(
                evidence_id="fmt-A",
                candidate_id="A",
                evidence_type="format_contract",
                status="pass",
                strength="structural",
                checker="test",
            )
        )
        self.assertIsNone(select_best_candidate(state))

        state.add_evidence(
            EvidenceRecord(
                evidence_id="audit-A",
                candidate_id="A",
                evidence_type="red_team_adjudication",
                status="pass",
                strength="semantic",
                checker="test",
            )
        )
        self.assertEqual(select_best_candidate(state).capsule.candidate_id, "A")

    def test_protocol_puts_submission_before_metadata(self):
        prompt = primary_prompt_v2("证明结论。", self._contract(proof=True))
        self.assertLess(prompt.index("<FINAL_CANDIDATE>"), prompt.index("<FINAL_RESPONSE>"))
        self.assertLess(prompt.index("<FINAL_RESPONSE>"), prompt.index("<METHOD_FINGERPRINT>"))

    def test_requirement_extraction_keeps_explicit_obligations(self):
        problem = (
            "证明结论成立。要求：(1) 验证边界条件；(2) 说明为什么该变换可逆；"
            "进一步证明解的唯一性。"
        )
        requirements = extract_explicit_requirements(problem)
        joined = " | ".join(requirements)
        self.assertIn("验证边界条件", joined)
        self.assertIn("变换可逆", joined)
        self.assertIn("唯一性", joined)

    def test_strict_gaussian_derivation_requires_visible_integral(self):
        requirements = (
            "请利用Markov性质、反射原理与高斯积分严格推导分布函数，并给出其密度",
        )
        summary_only = (
            "利用Markov性质和反射原理可得结论。经过高斯积分化简，"
            "所以分布函数为F(t)，密度为f(t)。"
        )
        checks = evaluate_explicit_requirement_coverage(summary_only, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["explicit_gaussian_derivation"].status, "fail")

        explicit = (
            "条件于B_t=x，由Markov性质和反射原理得不击中零的概率。"
            "因此F(t)=\\int_{\\mathbb R} q(x)p_t(x)\\,dx。"
            "由高斯积分可得F(t)=2\\pi^{-1}\\arcsin\\sqrt{t/T}，"
            "所以密度f(t)=1/(\\pi\\sqrt{t(T-t)})。"
        )
        checks = evaluate_explicit_requirement_coverage(explicit, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["explicit_gaussian_derivation"].status, "pass")

    def test_local_truncation_order_conflict_is_hard_failure(self):
        requirements = ("由局部截断误差验证二阶精度",)
        contradictory = (
            r"局部截断误差 $\tau_{n+2}=\frac h2 y'''(t_n)+O(h^2)=O(h)$。"
            r"经整理可知局部截断误差为 $O(h^2)$，故方法二阶。"
        )
        checks = evaluate_explicit_requirement_coverage(contradictory, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["local_truncation_order_consistency"].status, "fail")
        self.assertTrue(by_code["local_truncation_order_consistency"].hard_failure)

        consistent = (
            r"在 $t_{n+2}$ 展开可得差分商为 $y'-\frac13h^2y'''+O(h^3)$，"
            r"故局部截断误差为 $O(h^2)$，方法二阶。"
        )
        checks = evaluate_explicit_requirement_coverage(consistent, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["local_truncation_order_consistency"].status, "pass")

    def test_generator_requirement_needs_mappings_and_relations(self):
        requirements = ("要求写出两个生成自同构并验证其关系，而不能只给出群名",)
        short = "Galois群同构于D_4。"
        checks = evaluate_explicit_requirement_coverage(short, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["two_automorphisms"].status, "fail")
        self.assertEqual(by_code["generator_relations"].status, "fail")

        complete = (
            r"定义 r(α)\mapsto iα, r(i)\mapsto i；s(α)\mapsto α, s(i)\mapsto -i。"
            r"并验证 r^4=1, s^2=1, srs=r^{-1}。"
        )
        checks = evaluate_explicit_requirement_coverage(complete, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["two_automorphisms"].status, "pass")
        self.assertEqual(by_code["generator_relations"].status, "pass")

    def test_soft_fatal_label_without_basis_is_not_concrete(self):
        audit = AuditResult(
            verdict="REPAIR_A",
            target_candidate_id="A",
            target_claim_id=None,
            attack_type="none",
            severity="fatal",
            challenge="looks suspicious",
            witness=None,
            resolver_hint=None,
        )
        self.assertFalse(ResilientHORAEngine._attack_is_concrete(audit))

    def test_claim_localized_precondition_attack_is_concrete(self):
        audit = AuditResult(
            verdict="REPAIR_A",
            target_candidate_id="A",
            target_claim_id="C2",
            attack_type="theorem_precondition",
            severity="fatal",
            challenge="The theorem requires compactness, which was not established.",
            witness=None,
            resolver_hint=None,
        )
        self.assertTrue(ResilientHORAEngine._attack_is_concrete(audit))


if __name__ == "__main__":
    unittest.main()
