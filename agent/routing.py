from __future__ import annotations

import re
from collections import OrderedDict

from .models import TaskContract


DOMAIN_PATTERNS: "OrderedDict[str, tuple[str, ...]]" = OrderedDict(
    [
        (
            "measure_theory",
            (
                "测度",
                "可测",
                "lebesgue",
                "fatou",
                "支配收敛",
                "单调收敛",
                "几乎处处",
                "a.e.",
                "ae convergence",
            ),
        ),
        (
            "functional_analysis",
            ("banach", "hilbert", "泛函", "有界算子", "弱收敛", "强收敛", "闭图"),
        ),
        (
            "topology",
            ("拓扑", "hausdorff", "同伦", "基本群", "紧致", "连通", "开覆盖"),
        ),
        (
            "differential_geometry",
            ("微分几何", "流形", "黎曼", "曲率", "联络", "测地", "切空间"),
        ),
        (
            "random_process",
            ("随机过程", "markov", "马尔可夫", "布朗", "鞅", "停时", "平稳分布"),
        ),
        (
            "probability_statistics",
            ("概率", "随机变量", "期望", "方差", "分布", "似然", "估计量", "置信区间"),
        ),
        (
            "abstract_algebra",
            (
                "群",
                "环",
                "域",
                "同态",
                "正规子群",
                "sylow",
                "理想",
                "有限域",
                "galois",
                "扩张次数",
            ),
        ),
        (
            "complex_analysis",
            ("复分析", "留数", "全纯", "解析函数", "围道", "极点", "奇点", "cauchy"),
        ),
        (
            "ode_pde",
            ("偏微分", "常微分", "微分方程", "pde", "ode", "边界条件", "初值问题", "热方程"),
        ),
        (
            "numerical_analysis",
            ("数值分析", "迭代", "误差界", "newton", "插值", "收敛阶", "数值积分"),
        ),
        (
            "discrete_combinatorics",
            ("离散", "组合", "图论", "生成树", "匹配", "染色", "递推", "排列", "计数"),
        ),
        (
            "linear_algebra",
            ("矩阵", "特征值", "特征向量", "线性空间", "秩", "行列式", "二次型"),
        ),
        (
            "optimization_operations",
            ("运筹", "线性规划", "对偶", "最优化", "最优解", "单纯形", "运输问题"),
        ),
        (
            "real_analysis",
            ("极限", "连续", "一致收敛", "级数", "可微", "积分", "数学分析"),
        ),
    ]
)


PROOF_MARKERS = (
    "证明",
    "严格说明",
    "说明为什么",
    "show that",
    "prove",
    "demonstrate",
    "justify",
    "推导",
)

COMPUTE_MARKERS = (
    "求",
    "计算",
    "find",
    "compute",
    "numerical value",
    "留数",
    "个数",
    "总数",
)


DOMAIN_POLICY = {
    "measure_theory": (
        "theorem-with-explicit-preconditions",
        "definition-and-counterexample route",
        ("theorem_precondition", "quantifier", "completeness"),
        ("measurability", "integrability", "domination", "limit_interchange"),
        ("theorem_conditions", "definition_check"),
    ),
    "functional_analysis": (
        "operator-and-structure theorem route",
        "definition-or-counterexample route",
        ("theorem_precondition", "counterexample", "quantifier", "completeness"),
        ("completeness", "boundedness", "closedness", "weak_strong_confusion"),
        ("theorem_conditions",),
    ),
    "topology": (
        "global structural theorem route",
        "definition-and-explicit-cover route",
        ("theorem_precondition", "counterexample", "quantifier", "interpretation"),
        ("local_global_confusion", "compactness", "hausdorff", "connectedness"),
        ("definition_check",),
    ),
    "differential_geometry": (
        "intrinsic geometric structure route",
        "coordinate-computation route",
        ("theorem_precondition", "boundary", "quantifier", "completeness"),
        ("local_global_confusion", "regularity", "coordinate_invariance"),
        ("coordinate_check",),
    ),
    "abstract_algebra": (
        "structural theorem and invariant route",
        "definition-expansion and explicit construction route",
        ("theorem_precondition", "counterexample", "assumption", "completeness"),
        ("normality", "homomorphism", "order_divisibility", "extension_degree"),
        ("finite_structure_check", "definition_check"),
    ),
    "probability_statistics": (
        "conditional-probability or distribution route",
        "combinatorial-counting or indicator route",
        ("assumption", "boundary", "completeness"),
        ("independence", "conditional_direction", "normalization", "double_counting"),
        ("range_check", "normalization_check", "small_case_enumeration"),
    ),
    "random_process": (
        "transition-law or martingale route",
        "pathwise or conditioning route",
        ("theorem_precondition", "assumption", "boundary", "completeness"),
        ("markov_condition", "stopping_condition", "stationary_limit_confusion"),
        ("transition_check", "normalization_check"),
    ),
    "discrete_combinatorics": (
        "structural counting or invariant route",
        "constructive recurrence or double-counting route",
        ("counterexample", "boundary", "completeness"),
        ("double_counting", "initial_condition", "edge_case", "connectivity"),
        ("small_case_enumeration", "recurrence_check"),
    ),
    "numerical_analysis": (
        "analytic error and convergence route",
        "computational stress-test route",
        ("theorem_precondition", "numerical_stress", "boundary"),
        ("error_order", "convergence_condition", "stability", "initial_value"),
        ("high_precision", "error_bound"),
    ),
    "complex_analysis": (
        "analytic-structure and residue route",
        "local Laurent or direct-limit route",
        ("theorem_precondition", "boundary", "transformation", "completeness"),
        ("contour_orientation", "branch_choice", "pole_order", "singularity"),
        ("symbolic_check", "residue_check"),
    ),
    "ode_pde": (
        "analytic transform or spectral route",
        "energy-residual or direct-substitution route",
        ("theorem_precondition", "boundary", "numerical_stress", "completeness"),
        ("residual", "initial_condition", "boundary_condition", "regularity"),
        ("residual_check", "boundary_check", "initial_check"),
    ),
    "linear_algebra": (
        "structural linear-algebra route",
        "coordinate or direct-matrix route",
        ("assumption", "boundary", "completeness"),
        ("rank", "dimension", "invertibility", "eigenvalue_multiplicity"),
        ("matrix_check", "symbolic_check"),
    ),
    "optimization_operations": (
        "primal-dual structural route",
        "constructive feasible-solution route",
        ("theorem_precondition", "boundary", "completeness"),
        ("feasibility", "duality_gap", "constraint_qualification"),
        ("feasibility_check", "objective_check"),
    ),
    "real_analysis": (
        "analytic theorem and inequality route",
        "definition-limit or alternative inequality route",
        ("theorem_precondition", "boundary", "transformation", "quantifier"),
        ("domain", "uniform_pointwise", "limit_interchange", "boundary"),
        ("symbolic_check", "numerical_stress"),
    ),
    "general": (
        "direct structured reasoning route",
        "independent constructive or contradiction route",
        ("assumption", "boundary", "completeness"),
        ("misread_target", "missing_case", "invalid_transformation"),
        ("format_check",),
    ),
}


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _detect_domains(lowered: str) -> tuple[str, tuple[str, ...]]:
    hits: list[tuple[str, int]] = []
    for domain, patterns in DOMAIN_PATTERNS.items():
        score = sum(lowered.count(pattern) for pattern in patterns)
        if score:
            hits.append((domain, score))
    hits.sort(key=lambda item: (-item[1], list(DOMAIN_PATTERNS).index(item[0])))
    if not hits:
        return "general", ()
    return hits[0][0], tuple(domain for domain, _ in hits[1:3])


def _count_parts(problem: str) -> int:
    patterns = (
        r"(?:^|\n)\s*[（(]\s*(?:\d+|[一二三四五六七八九十]+)\s*[)）]",
        r"(?:^|\n)\s*[a-zA-Z]\s*[.)、]",
    )
    matches: set[str] = set()
    for pattern in patterns:
        matches.update(re.findall(pattern, problem, flags=re.MULTILINE))
    if len(matches) >= 2:
        return len(matches)
    if "分别" in problem and any(token in problem for token in ("(1)", "（1）", "①")):
        return max(2, len(re.findall(r"[①②③④⑤⑥⑦⑧⑨⑩]", problem)))
    return 1


def build_task_contract(problem: str) -> TaskContract:
    normalized = " ".join(problem.strip().split())
    lowered = normalized.lower()
    primary_domain, secondary_domains = _detect_domains(lowered)

    requires_proof = _contains_any(lowered, PROOF_MARKERS)
    multipart_count = _count_parts(problem)

    if requires_proof:
        answer_schema = "proof"
        problem_kind = "proof"
    elif multipart_count > 1:
        answer_schema = "multipart"
        problem_kind = "multipart"
    elif any(token in lowered for token in ("所有解", "解集", "区间", "set of all", "all solutions")):
        answer_schema = "set"
        problem_kind = "solve_all"
    elif any(token in lowered for token in ("个数", "总数", "多少种", "number of", "how many")):
        answer_schema = "integer"
        problem_kind = "counting"
    elif _contains_any(lowered, COMPUTE_MARKERS):
        answer_schema = "exact_expression"
        problem_kind = "calculation"
    else:
        answer_schema = "exact_expression"
        problem_kind = "reasoning"

    theoretical_domains = {
        "measure_theory",
        "functional_analysis",
        "topology",
        "differential_geometry",
        "abstract_algebra",
    }
    if requires_proof or primary_domain in theoretical_domains or len(normalized) > 520:
        risk_level = "high"
        route_hint = "R2"
    elif len(normalized) < 230 and _contains_any(lowered, COMPUTE_MARKERS):
        risk_level = "low"
        route_hint = "R0"
    else:
        risk_level = "medium"
        route_hint = "R1"

    primary_method, orthogonal_method, attacks, failures, checks = DOMAIN_POLICY.get(
        primary_domain, DOMAIN_POLICY["general"]
    )
    mandatory_attacks = tuple(attacks)
    if multipart_count > 1 and "completeness" not in mandatory_attacks:
        mandatory_attacks += ("completeness",)

    return TaskContract(
        primary_domain=primary_domain,
        secondary_domains=secondary_domains,
        problem_kind=problem_kind,
        answer_schema=answer_schema,
        requires_proof=requires_proof,
        requires_exact_answer=True,
        multipart_count=multipart_count,
        risk_level=risk_level,  # type: ignore[arg-type]
        verification_modes=tuple(checks),
        mandatory_attacks=mandatory_attacks,
        likely_failure_modes=tuple(failures),
        route_hint=route_hint,
        primary_method=primary_method,
        orthogonal_method=orthogonal_method,
    )
