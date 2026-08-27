from __future__ import annotations

import re
from collections import OrderedDict

from .models import TaskContract
from .task_profile import analyze_task


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
            "linear_regression",
            ("线性回归", "最小二乘", "回归系数", "残差", "ols", "regression coefficient"),
        ),
        (
            "statistical_inference",
            ("统计推断", "似然", "估计量", "置信区间", "假设检验", "充分统计量", "置信水平"),
        ),
        (
            "probability",
            ("概率", "随机变量", "期望", "方差", "条件分布", "bayes", "贝叶斯"),
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
            "partial_differential_equations",
            ("偏微分", "pde", "热方程", "波动方程", "laplace方程", "泊松方程", "边值问题"),
        ),
        (
            "ordinary_differential_equations",
            ("常微分", "ode", "初值问题", "lane-emden", "lane--emden", "riccati", "bessel", "相平面", "微分方程组"),
        ),
        (
            "numerical_analysis",
            (
                "数值分析", "迭代", "误差界", "newton", "插值", "收敛阶", "数值积分",
                "bdf", "runge-kutta", "butcher", "局部截断误差", "零稳定", "a-稳定", "l-稳定", "稳定函数",
            ),
        ),
        (
            "discrete_combinatorics",
            ("离散", "组合", "图论", "生成树", "匹配", "染色", "递推", "排列", "计数", "sperner", "反链", "生成函数"),
        ),
        (
            "higher_algebra",
            ("高等代数", "矩阵", "特征值", "特征向量", "线性空间", "向量空间", "最小多项式", "特征多项式", "jordan", "交换子", "秩", "行列式", "二次型"),
        ),
        (
            "optimization_operations",
            ("运筹", "线性规划", "对偶", "最优化", "最优解", "单纯形", "运输问题"),
        ),
        (
            "mathematical_analysis",
            ("极限", "连续", "一致收敛", "级数", "可微", "积分", "数学分析", "inverse function", "derivative", "integral", "differentiable"),
        ),
        (
            "advanced_courses",
            ("非基础", "进阶课程", "代数拓扑", "代数几何", "表示论", "范畴论", "动力系统", "catalan", "p-adic", "legendre公式", "二进制展开"),
        ),
    ]
)


DOMAIN_ANCHORS: dict[str, tuple[str, ...]] = {
    "measure_theory": (r"lebesgue|fubini|tonelli", r"可测|l\^?1", r"几乎处处|迭代积分", r"支配收敛|单调收敛|fatou"),
    "functional_analysis": (r"banach|hilbert", r"有界算子|闭图|弱收敛|强收敛|volterra|谱半径"),
    "topology": (r"hausdorff|同伦|基本群|torus knot", r"拓扑空间|开覆盖|结空间|阿贝尔化"),
    "differential_geometry": (r"黎曼|曲率|测地|联络", r"gauss.?bonnet|切空间"),
    "random_process": (r"markov|马尔可夫|布朗|brownian|cir扩散|fokker-+planck", r"鞅|停时|平稳分布|平稳密度|排队|扩散方程"),
    "linear_regression": (r"线性回归|least squares|ols|gls|2sls", r"回归系数|残差平方和|设计矩阵|工具变量"),
    "statistical_inference": (r"似然|置信区间|假设检验", r"估计量|充分统计量"),
    "probability": (r"概率|随机变量|\\mathbb\s*p|联合矩母函数", r"条件期望|条件特征函数|大偏差|chernoff|cram.r|l.vy刻画|分布函数|密度"),
    "abstract_algebra": (r"有限域|域扩张|galois|sylow", r"正规子群|群同态|环同态|理想"),
    "complex_analysis": (r"全纯|解析函数|留数|rouch|cauchy|jensen", r"极点|奇点|laurent|围道|单位圆盘"),
    "partial_differential_equations": (r"偏微分|pde|热方程|波动方程|hamilton.?jacobi|pohozaev", r"边值问题|dirichlet|neumann|\\delta\s*u|u_t|u_xx"),
    "ordinary_differential_equations": (r"常微分|ode|riccati|lane-+emden|单摆", r"初值问题|相平面|bessel方程|最小正周期"),
    "numerical_analysis": (
        r"bdf|runge-kutta|butcher|gmres|crank-+nicolson|peaceman-+rachford|共轭梯度|高斯求积|伪谱",
        r"局部截断误差|零稳定|a-稳定|l-稳定|稳定函数|中心差分|离散矩阵|网格|adi格式|krylov",
    ),
    "discrete_combinatorics": (r"sperner|反链|生成树|图论|完全图|euler回路|邻接矩阵|fisher不等式", r"匹配|染色|组合计数|关联矩阵|集合族|团数|临界群|砂堆群|顶点"),
    "higher_algebra": (r"最小多项式|特征多项式|jordan", r"向量空间|线性算子|二次型|交换子"),
    "optimization_operations": (r"线性规划|单纯形|对偶", r"可行解|运输问题|最优值"),
    "mathematical_analysis": (r"一致收敛|逐点收敛", r"数学分析|反函数|级数收敛"),
    "advanced_courses": (r"代数拓扑|代数几何|表示论|范畴论|理想类群", r"catalan|p-adic|legendre公式|minkowski界|整数环|判别式"),
}


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
    "probability": (
        "conditional-probability or distribution route",
        "combinatorial-counting or indicator route",
        ("assumption", "boundary", "completeness"),
        ("independence", "conditional_direction", "normalization", "double_counting"),
        ("range_check", "normalization_check", "small_case_enumeration"),
    ),
    "statistical_inference": (
        "likelihood and sampling-distribution route",
        "estimator property or pivotal-quantity route",
        ("assumption", "boundary", "completeness"),
        ("model_assumption", "tail_direction", "degrees_of_freedom", "coverage"),
        ("range_check", "normalization_check"),
    ),
    "linear_regression": (
        "projection and normal-equation route",
        "residual geometry or direct matrix route",
        ("assumption", "boundary", "completeness"),
        ("rank", "intercept", "degrees_of_freedom", "residual_definition"),
        ("matrix_check", "residual_check"),
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
    "partial_differential_equations": (
        "analytic transform or spectral route",
        "energy-residual or direct-substitution route",
        ("theorem_precondition", "boundary", "numerical_stress", "completeness"),
        ("residual", "initial_condition", "boundary_condition", "regularity"),
        ("residual_check", "boundary_check", "initial_check"),
    ),
    "ordinary_differential_equations": (
        "first-integral or qualitative phase route",
        "direct substitution or transformed-variable route",
        ("theorem_precondition", "boundary", "numerical_stress", "completeness"),
        ("initial_condition", "singular_branch", "domain", "regularity"),
        ("residual_check", "initial_check"),
    ),
    "higher_algebra": (
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
    "mathematical_analysis": (
        "analytic theorem and inequality route",
        "definition-limit or alternative inequality route",
        ("theorem_precondition", "boundary", "transformation", "quantifier"),
        ("domain", "uniform_pointwise", "limit_interchange", "boundary"),
        ("symbolic_check", "numerical_stress"),
    ),
    "advanced_courses": (
        "definition and structural-invariant route",
        "explicit example or local-computation route",
        ("theorem_precondition", "interpretation", "quantifier", "completeness"),
        ("definition_mismatch", "hidden_hypothesis", "local_global_confusion"),
        ("definition_check",),
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
        score += 3 * sum(
            len(re.findall(anchor, lowered, flags=re.IGNORECASE))
            for anchor in DOMAIN_ANCHORS.get(domain, ())
        )
        if score:
            hits.append((domain, score))
    hits.sort(key=lambda item: (-item[1], list(DOMAIN_PATTERNS).index(item[0])))
    if not hits:
        return "general", ()
    return hits[0][0], tuple(domain for domain, _ in hits[1:3])


def build_task_contract(problem: str) -> TaskContract:
    normalized = " ".join(problem.strip().split())
    lowered = normalized.lower()
    primary_domain, secondary_domains = _detect_domains(lowered)

    profile = analyze_task(problem)
    requires_proof = profile.requires_proof
    multipart_count = profile.part_count

    if profile.mode == "choice":
        answer_schema = "choice_letters"
        problem_kind = "choice"
    elif profile.mode == "fill":
        answer_schema = "fill_values"
        problem_kind = "fill"
    elif profile.mode == "true_false":
        answer_schema = "binary_verdict"
        problem_kind = "true_false"
    elif requires_proof:
        answer_schema = "proof"
        problem_kind = "proof"
    elif profile.mode == "multipart" or multipart_count > 1:
        answer_schema = "multipart"
        problem_kind = "multipart"
    elif profile.requires_all_solutions:
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
    elif profile.ambiguity_flags or profile.mode in {"multipart", "solve_all"}:
        risk_level = "medium"
        route_hint = "R1"
    elif len(normalized) < 230 and (
        _contains_any(lowered, COMPUTE_MARKERS)
        or profile.mode in {"choice", "fill", "true_false"}
    ):
        risk_level = "low"
        route_hint = "R0"
    else:
        risk_level = "medium"
        route_hint = "R1"

    primary_method, orthogonal_method, attacks, failures, checks = DOMAIN_POLICY.get(
        primary_domain, DOMAIN_POLICY["general"]
    )
    mandatory_attacks = tuple(attacks)
    if (
        multipart_count > 1
        or profile.requires_all_solutions
        or profile.blank_count > 1
        or (profile.choice_count is not None and profile.choice_count > 1)
    ) and "completeness" not in mandatory_attacks:
        mandatory_attacks += ("completeness",)

    return TaskContract(
        primary_domain=primary_domain,
        secondary_domains=secondary_domains,
        problem_kind=problem_kind,
        answer_schema=answer_schema,
        requires_proof=requires_proof,
        requires_exact_answer=not requires_proof,
        multipart_count=multipart_count,
        risk_level=risk_level,  # type: ignore[arg-type]
        verification_modes=tuple(checks),
        mandatory_attacks=mandatory_attacks,
        likely_failure_modes=tuple(failures),
        route_hint=route_hint,
        primary_method=primary_method,
        orthogonal_method=orthogonal_method,
        question_mode=profile.mode,
        mode_confidence=profile.confidence,
        alternate_modes=profile.alternate_modes,
        blank_count=profile.blank_count,
        choice_count=profile.choice_count,
        answer_obligations=profile.obligations,
        ambiguity_flags=profile.ambiguity_flags,
    )
