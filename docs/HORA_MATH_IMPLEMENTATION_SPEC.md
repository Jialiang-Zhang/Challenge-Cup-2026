# HORA-Math 执行级架构规范

> 版本：v2.1  
> 状态：目标实现规范  
> 入口约束：`ReasoningAgent.solve(problem: str, metadata: dict) -> dict`

HORA-Math 的完整名称为：

> **Heterogeneous Orthogonal Reasoning with Red-Team Attacks and Evidence Adjudication**

中文定义：

> **异构正交求解—红队对抗攻击—证据裁决数学智能体**

本规范将 README 中的目标架构进一步收敛成可编码、可测试、可消融的执行协议。

---

# 1. 系统目标

系统优化目标不是最大化 Agent 数量，而是在正式评测约束下最大化：

```text
正确答案率
-
误修率
-
超时率
-
无效输出率
```

必须同时满足：

1. 高价值候选之间具有方法级差异；
2. 理论高风险题受到主动红队攻击；
3. 能由代码验证的结论优先产生确定性证据；
4. 冲突定位到 Claim，而不是退化成整题投票；
5. Repair 保守、局部且最多一次；
6. 最终答案经过规范化、冻结和事务提交；
7. 所有高级模块都可以被单独关闭并进行消融。

---

# 2. 总体分层

```text
Layer 0  Runtime and Contract
Layer 1  Heterogeneous Blue Solvers
Layer 2  Canonicalization and Evidence
Layer 3  Orthogonality and Candidate Control
Layer 4  Red-Team Attack System
Layer 5  Dispute Resolution and Repair
Layer 6  Evidence Adjudication
Layer 7  Answer Transaction and Safe Trace
```

总体流程：

```text
Problem
  ↓
CanonicalProblem
  ↓
TaskContract + RiskMap + AmbiguityMap
  ↓
RoutePolicy
  ↓
Primary Blue Solver
  ↓
SolutionCapsule + ClaimGraph
  ↓
CertificateEngine
  ↓
低风险且证据充分？
  ├─ 是 → Freeze → Commit
  └─ 否
       ↓
Heterogeneous Strategy Compiler
       ↓
Orthogonal Blind Solver / Tool Solver / Enumeration Solver
       ↓
Orthogonality Gate
       ↓
Candidate Ledger
       ↓
Canonicalization + Equivalence Clustering
       ↓
Red-Team Attack Scheduler
       ↓
Challenge Ledger
       ↓
Deterministic Local Resolver
       ↓
仍有 Fatal Challenge？
  ├─ 否 → Evidence Adjudicator
  └─ 是
       ↓
One-shot Cross Examination
       ↓
仍成立？
  ├─ 否 → Evidence Adjudicator
  └─ 是 → One-shot Targeted Repair
                 ↓
              Reverify + Reattack
                 ↓
          Evidence Adjudicator
                 ↓
          Answer Normalizer
                 ↓
          Transaction Commit
```

---

# 3. 核心状态对象

## 3.1 CanonicalProblem

```python
@dataclass
class CanonicalProblem:
    raw_text: str
    normalized_text: str
    language: str
    parts: list["ProblemPart"]
    explicit_constraints: list[str]
    detected_symbols: list[str]
    normalization_warnings: list[str]
```

职责：

- 统一换行和异常 Unicode；
- 保留 LaTeX；
- 识别多小问；
- 识别证明、求值、构造、反例、所有解等目标；
- 不改变数学语义。

## 3.2 ProblemPart

```python
@dataclass
class ProblemPart:
    part_id: str
    text: str
    required: bool
    dependencies: list[str]
    answer_schema: str | None
```

多小问必须独立记录状态，禁止因为一个小问冲突而重跑全部小问。

## 3.3 TaskContract

```python
@dataclass
class TaskContract:
    primary_domain: str
    secondary_domains: list[str]
    problem_kind: str
    answer_schema: str
    requires_proof: bool
    requires_exact_answer: bool
    multipart_count: int
    risk_level: str
    verification_modes: list[str]
    mandatory_attacks: list[str]
    likely_failure_modes: list[str]
    route_hint: str
```

使用软路由：

```text
primary_domain = probability
secondary_domains = [combinatorics]
```

不能强制后续只能使用单一领域策略。

## 3.4 MethodFingerprint

```python
@dataclass(frozen=True)
class MethodFingerprint:
    paradigm: str
    representation: str
    theorem_family: str
    tool_channel: str
    interpretation_id: str
    exposed_to_primary: bool
```

可选值示例：

```text
paradigm:
direct / contradiction / constructive / induction / counting / optimization

representation:
symbolic / geometric / graph / event / operator / coordinate / generating_function

tool_channel:
none / sympy / numeric / brute_force / residual / matrix
```

## 3.5 ClaimRecord

```python
@dataclass
class ClaimRecord:
    claim_id: str
    statement: str
    dependencies: list[str]
    is_critical: bool
    status: str
    evidence_ids: list[str]
```

状态：

```text
PROPOSED
SUPPORTED
VERIFIED
CONTRADICTED
UNKNOWN
```

## 3.6 SolutionCapsule

```python
@dataclass
class SolutionCapsule:
    candidate_id: str
    source_role: str
    method: MethodFingerprint
    answer_raw: str
    answer_normalized: str | None
    claims: list[ClaimRecord]
    check_hints: list[str]
    risk_flags: list[str]
    complete: bool
    truncated: bool
    parent_candidate_id: str | None
```

## 3.7 EvidenceRecord

```python
@dataclass
class EvidenceRecord:
    evidence_id: str
    candidate_id: str
    target_claim_id: str | None
    evidence_type: str
    status: str
    strength: str
    checker: str
    detail_code: str | None
```

状态：

```text
PASS
FAIL
UNKNOWN
NOT_APPLICABLE
```

强度：

```text
HARD
STRUCTURAL
INDEPENDENT
SEMANTIC
FORMAT
```

## 3.8 Challenge

```python
@dataclass
class Challenge:
    challenge_id: str
    candidate_id: str
    target_claim_id: str
    attack_type: str
    severity: str
    statement: str
    witness: str | None
    resolver_hint: str | None
    status: str
```

状态：

```text
OPEN
SUSTAINED
REBUTTED
RESOLVED_BY_TOOL
NOT_APPLICABLE
```

## 3.9 CandidateRecord

```python
@dataclass
class CandidateRecord:
    capsule: SolutionCapsule
    evidence_ids: list[str]
    challenge_ids: list[str]
    eligible: bool
    frozen: bool
```

## 3.10 CaseState

```python
@dataclass
class CaseState:
    problem: CanonicalProblem
    contract: TaskContract
    candidates: dict[str, CandidateRecord]
    evidence: list[EvidenceRecord]
    challenges: list[Challenge]
    verified_facts: list[ClaimRecord]
    model_calls: int
    tool_calls: int
    repair_count: int
    elapsed_seconds: float
    route: str
    committed_candidate_id: str | None
```

---

# 4. Route Policy

## 4.1 R0：硬证书快速路线

适用：

- 明确数值计算；
- 标准方程；
- 简单矩阵；
- 可直接代回的 ODE/PDE；
- 可有限枚举的问题。

```text
Primary
→ CertificateEngine
→ BoundaryAttack
→ Commit
```

目标模型调用：1 次。

## 4.2 R1：中风险异构双路

适用：

- 概率计算；
- 较复杂积分；
- 复分析计算；
- 数值分析；
- 有工具但工具不能完全覆盖的题。

```text
Primary
→ Tool / Certificate
→ Orthogonal Blind
→ Equivalence Cluster
→ Targeted Attack
→ Commit
```

目标模型调用：1～2 次。

## 4.3 R2：高风险理论路线

适用：

- 测度论；
- 泛函分析；
- 拓扑；
- 抽象代数证明；
- 微分几何理论；
- 复杂离散证明。

```text
Structural Solver
+
Constructive Blind Solver
→ Orthogonality Gate
→ Theorem-Precondition Attack
→ Counterexample / Quantifier Attack
→ Evidence Adjudicator
```

目标模型调用：2～3 次。

## 4.4 R3：真实冲突路线

触发：

- 正交候选答案不等价；
- 工具产生 Hard Fail；
- Fatal Challenge 成立；
- 存在严重题意歧义；
- 多小问缺失。

```text
Dispute Mapper
→ Local Resolver
→ One-shot Cross Examination
→ Targeted Repair if necessary
→ Reverify + Reattack
→ Adjudicate
```

模型调用上限：4 次。

---

# 5. Blue Team Solver Portfolio

## 5.1 S1 Structural / Theorem Solver

职责：

- 识别数学结构；
- 选择主定理；
- 明确列出定理前提；
- 输出关键 Claim；
- 给出可验证提示。

禁止：

- 隐去定理条件；
- 用“显然”跳过决定性步骤；
- 将长推理直接作为外部最终答案。

## 5.2 S2 Constructive / Definition Blind Solver

职责：

- 完全隔离 Primary 内容；
- 从定义、构造、反证、逆否、局部计算或显式计数出发；
- 强制采用与 S1 不同的方法指纹；
- 独立理解题意。

输入中禁止出现：

```text
Primary answer
Primary reasoning
Primary claims
Primary risk flags
Verifier comments
```

## 5.3 S3 Tool-Integrated Symbolic Solver

职责：

```text
LLM 形成可执行表达式
→ 安全工具执行
→ 返回证书或反证
```

工具范围：

- SymPy 化简；
- 求导和积分反验；
- 方程代回；
- 矩阵计算；
- ODE/PDE residual；
- 多项式和特征值；
- 高精度表达式比较。

## 5.4 S4 Numerical / Enumeration Solver

职责：

- small-n 枚举；
- 有限图或有限结构遍历；
- 高精度多点测试；
- 极端参数测试；
- Monte Carlo 仅作为弱支持或错误发现；
- 数值误差和收敛性检查。

## 5.5 Solver Capability Registry

```python
SOLVER_CAPABILITIES = {
    "structural": {"proof", "theorem", "global_structure"},
    "constructive_blind": {"definition", "construction", "counterroute"},
    "symbolic": {"algebra", "calculus", "matrix", "residual"},
    "numerical_enum": {"finite", "stress", "small_instance"},
}
```

RoutePolicy 根据能力选择最少数量的求解器，不固定全部执行。

---

# 6. Orthogonality Gate

## 6.1 独立支持判定

候选 B 只有同时满足下列条件，才可以作为候选 A 的独立支持：

1. `exposed_to_primary == False`；
2. 方法指纹至少在两个实质维度上不同；
3. 不能仅靠 temperature、措辞或步骤顺序制造差异；
4. 不能共享同一个未验证的核心假设；
5. 若使用相同定理族，必须使用不同表示或不同工具证书补充。

规则示例：

```python
def is_orthogonal(a: MethodFingerprint, b: MethodFingerprint) -> bool:
    if b.exposed_to_primary:
        return False

    differences = sum(
        [
            a.paradigm != b.paradigm,
            a.representation != b.representation,
            a.theorem_family != b.theorem_family,
            a.tool_channel != b.tool_channel,
            a.interpretation_id != b.interpretation_id,
        ]
    )
    return differences >= 2
```

真实实现还要增加“共同核心假设”检测，不能只比较字符串。

## 6.2 独立性等级

```text
O0：同质重复，不计独立支持
O1：步骤不同但定理和表示相同，只记弱支持
O2：方法或表示显著不同，记独立支持
O3：自然语言方法与确定性工具证书互补，记强独立支持
```

## 6.3 新候选准入问题

生成新候选前，Controller 必须能够回答：

```text
当前缺少什么证据？
新候选将使用什么新的方法族？
它能解决哪个风险或 Challenge？
是否可能只是重复已有候选？
```

不能回答时，不生成新候选。

---

# 7. Mathematical Canonicalization and Equivalence

## 7.1 规范化层级

```text
C0：去除 Markdown 和答案前缀
C1：整数、有理数和小数标准化
C2：LaTeX 常见分式、根式和幂转换
C3：SymPy 表达式化简
C4：有限集合排序和去重
C5：区间标准化
C6：方程解集标准化
C7：矩阵逐项标准化
C8：多小问逐项匹配
```

## 7.2 等价状态

```text
EQUIVALENT
NOT_EQUIVALENT
UNKNOWN
```

不能把工具解析失败解释为不等价。

## 7.3 等价归簇

候选先按数学等价聚类，再分析方法多样性：

```text
Cluster 1: {A, B}
answer = -1/8
methods = {structural, symbolic}

Cluster 2: {C}
answer = 1/8
methods = {constructive}
```

“簇内人数”不是最终裁决依据；簇的证据质量和攻击存活情况更重要。

---

# 8. Certificate Engine

## 8.1 格式证书

检查：

- 非空字符串；
- 多小问完整；
- 答案类型匹配；
- 集合、矩阵、区间结构合法；
- JSON 可序列化；
- Candidate 与最终规范化答案一致。

## 8.2 硬数学证书

```text
方程代回
符号恒等
导数反验
积分反微分
矩阵等式
特征方程
ODE/PDE residual
初值和边界条件
有限枚举
概率归一化
数值误差界
```

## 8.3 结构证书

用于工具不能完全处理的理论题：

- 定理前提逐项成立；
- 定义条件全部满足；
- 关键 Claim 依赖闭合；
- 必要性和充分性覆盖；
- 存在性和唯一性均已覆盖。

## 8.4 反驳证书

任一明确反驳证书应触发 Hard Fail：

- 反例；
- residual 非零；
- 边界条件失败；
- 代回不成立；
- small-n 枚举不一致；
- 定理必要条件明确不成立；
- 最终答案不满足题目。

## 8.5 工具安全

工具必须：

- 限时；
- 限制输入规模；
- 禁止任意文件和网络访问；
- 捕获异常；
- 异常返回 `UNKNOWN`；
- 记录 checker 名称和最小状态，不在 Trace 中泄露题目正文。

---

# 9. Red-Team Attack System

红队目标：

> 主动寻找能够推翻候选的最小、具体、可验证证据。

## 9.1 Attack Scheduler

输入：

```text
TaskContract
RiskMap
FailureSkills
Candidate Claims
Existing Evidence
Open Disputes
Remaining Budget
```

输出：

```python
AttackPlan(
    candidate_id="A",
    attacks=["theorem_precondition", "counterexample", "completeness"],
    target_claim_ids=["C2", "C4"],
)
```

## 9.2 九类攻击

### A1 Assumption Attack

攻击未声明的非零、可逆、独立、有限、正规、连续、紧性等假设。

### A2 Theorem-Precondition Attack

逐项核对定理前提，缺失关键前提时生成 Fatal Challenge。

### A3 Counterexample Attack

寻找最小、低维、有限、退化、极端参数或特殊结构反例。

### A4 Boundary / Degenerate Attack

检查零、一、空集、单点、端点、奇点、重根、秩退化和最小参数。

### A5 Transformation Attack

攻击非等价变形、除零、开平方符号、对数定义域、极限交换、积分交换、增根和漏解。

### A6 Quantifier Attack

检查任意/存在、处处/a.e.、局部/全局、至少/恰好、必要/充分。

### A7 Interpretation Attack

检查题意、符号作用域、多小问共享条件、精确值与近似值。

### A8 Numerical Stress Attack

使用高精度、多点、极端点、特殊点、residual 和枚举尝试击破表达式。

### A9 Completeness / Schema Attack

检查所有小问、全部解、存在性、唯一性、必要充分性和答案类型。

## 9.3 红队输出约束

红队必须输出：

```text
candidate_id
target_claim_id
attack_type
severity
minimal_reason
witness or resolver_hint
```

不满足结构的普通怀疑不进入 Challenge Ledger。

## 9.4 Attack Coverage Contract

```text
LOW:
A4 或 A9 至少一个轻量攻击

MEDIUM:
至少一个领域 Failure Attack
+ 一个确定性检查

HIGH:
A2 必选
A3/A6 至少一个
A9 必选

CONFLICT:
只攻击第一个分歧 Claim
必要时 A7
```

---

# 10. Claim Dependency Graph

## 10.1 支配 Claim

若最终答案依赖：

```text
C1 → C3 → FINAL
C2 → C3 → FINAL
```

则 C1、C2、C3 都是关键 Claim。红队优先攻击距离 FINAL 最近且尚未验证的支配 Claim。

## 10.2 攻击停止条件

一旦上游 Claim 被 `CONTRADICTED`：

```text
停止攻击其所有后继 Claim
```

避免无意义 Token 消耗。

## 10.3 Verified Fact Store

只有具有 `PASS` 或已解决支持证据的 Claim 才进入：

```text
VerifiedFactStore
```

Repair 和后续 Solver 默认不能修改这些事实，除非产生新的 Hard Contradiction。

---

# 11. Challenge Ledger and Dispute Resolution

## 11.1 Challenge 优先级

```text
FATAL
MAJOR
MINOR
INFO
```

只有 FATAL 或可能影响最终答案的 MAJOR Challenge 才能触发模型级 Cross Examination。

## 11.2 Deterministic Local Resolver

优先尝试：

- SymPy；
- Python；
- 定义规则；
- 代回；
- residual；
- 有限枚举；
- 数值压力；
- 数学等价引擎。

工具可解决时，不调用 LLM Judge。

## 11.3 One-shot Cross Examination

只允许一次 Claim 级交叉质询。

Blue Defense 输出：

```text
DEFENDED
CONCEDED
REVISED_CLAIM
```

Dispute Auditor 在同一次审查调用内判断：

```text
Challenge 是否成立
哪项证据可复现
是否需要 Repair
```

禁止无限 Debate。

---

# 12. Targeted Repair

## 12.1 准入条件

```text
存在 SUSTAINED Fatal Challenge
+
错误 Claim 已定位
+
至少一个前置 Verified Fact 可保留
+
repair_count == 0
```

## 12.2 Repair 输入

```text
CanonicalProblem
TaskContract
父 Candidate Capsule
Verified Facts
Fatal Challenge
必须保留的前置 Claim
```

## 12.3 Repair 输出

生成新候选：

```python
SolutionCapsule(
    candidate_id="C",
    parent_candidate_id="A",
    ...
)
```

## 12.4 Repair 后操作

必须执行：

```text
原失败检查器
原攻击
答案规范化
多小问完整性
```

如果再次失败：

```text
不再 Repair
进入 Evidence Adjudicator
```

## 12.5 Fresh Restart

只有题意整体误读、核心方法完全失效或全部关键 Claim 不可保留时，允许一次短路重解。

---

# 13. Evidence Adjudicator

不使用普通多数投票，也不使用未经校准的浮点总分。

## 13.1 否决规则

候选出现任一项时原则上不可提交：

1. 输出契约非法；
2. 明确 Hard Fail；
3. Fatal Challenge `SUSTAINED` 且未修复；
4. 多小问缺失；
5. 核心 Claim 被反例推翻；
6. 最终答案无法规范化。

## 13.2 字典序优先级

1. 输出合法且完整；
2. 无 Hard Fail；
3. 关键 Claim 有 Hard / Structural Pass；
4. 经受住适用的 Fatal Attack；
5. 获得 O2/O3 正交独立支持；
6. Claim 覆盖完整；
7. 未解决 Challenge 更少；
8. 未经修复的稳定候选优于证据不足的 Repair 候选；
9. 最后才比较成本。

## 13.3 Evidence Veto

```text
Hard Counterexample
>
任意数量的 LLM 接受票
```

```text
Hard Pass
+
无强制攻击缺口
→ 允许 Freeze
```

```text
Generic Approval
→ 只能作为最低级软证据
```

---

# 14. Early Stop and Candidate Freeze

## 14.1 Early Stop 条件

### 条件 A

```text
Primary 完整
+ Hard Certificate PASS
+ 低风险
+ A4/A9 轻攻击通过
```

### 条件 B

```text
两个 O2/O3 候选数学等价
+ 强制攻击均未成立
+ 所有小问完整
```

### 条件 C

```text
Candidate A Hard Pass
+ Candidate B Hard Fail
```

## 14.2 Freeze

冻结后禁止普通 Reviewer、Repair 或 Formatter 修改数学答案。

只有新的 Hard Contradiction 可以解冻。

---

# 15. Answer Protocol

## 15.1 模型输出协议

每个 Solver 在完整推理后必须包含：

```text
<FINAL_CANDIDATE>
...
</FINAL_CANDIDATE>

<METHOD_FINGERPRINT>
...
</METHOD_FINGERPRINT>

<CRITICAL_CLAIMS>
...
</CRITICAL_CLAIMS>

<CHECK_HINTS>
...
</CHECK_HINTS>
```

## 15.2 Answer Normalizer

由确定性代码完成：

- 提取 final 标签；
- 去除多余 Markdown；
- 统一 LaTeX；
- 多小问排序；
- 检查答案类型；
- 检查空字符串；
- 检查候选与最终答案一致。

禁止再调用 LLM “美化”最终答案。

## 15.3 Transaction Commit

```text
PREPARE
→ Schema Check
→ Multipart Check
→ Candidate Consistency
→ JSON Serialization
→ FREEZE
→ COMMIT
```

外部返回只由 Transaction 模块产生：

```python
{
    "final_response": normalized_answer,
    "trace": safe_trace,
}
```

---

# 16. Runtime Guard

## 16.1 调用角色上限

```text
Call 1: Primary Solver
Call 2: Orthogonal Solver
Call 3: Dispute Auditor
Call 4: Repair 或 Rescue
```

工具调用不等于模型调用，但也必须限时和限规模。

## 16.2 阶段控制

```text
NORMAL:
允许生成主候选和必要正交候选

CONFLICT:
禁止新增无关候选，只解决现有 Challenge

RESCUE:
停止长推理，只允许最短可靠候选

FINALIZE:
禁止新增模型调用
```

## 16.3 截断

```text
已有 FINAL_CANDIDATE
→ 直接验证

无 FINAL_CANDIDATE
→ Continuation 最多一次

再次失败
→ Rescue 最多一次
```

---

# 17. 十八学科策略矩阵

| 学科 | 蓝队主路线 | 正交路线 | 强制红队攻击 | 主要工具 |
|---|---|---|---|---|
| 离散数学 | 结构/组合证明 | 递推、双计数或构造 | 重复计数、边界、反例 | brute force、图枚举 |
| 数值分析 | 误差和收敛推导 | 高精度实验 | 收敛条件、误差阶、极端初值 | mpmath、NumPy |
| 测度积分 | 定理结构证明 | 定义或另一收敛定理 | 可测、可积、支配、a.e./处处 | 局部数值仅作弱证据 |
| 微分几何 | 坐标/不变量路线 | 定义或局部构造 | 局部/全局、正则性、坐标退化 | SymPy 局部计算 |
| 概率论 | 条件概率/分布法 | 组合计数/指示变量 | 独立性、分母、范围、归一化 | 枚举、Monte Carlo 弱证据 |
| 抽象代数 | 结构定理 | 定义构造/阶数计数 | 正规性、同态、扩张次数、Sylow 前提 | 有限实例 |
| 随机过程 | 转移/鞅结构 | 递推或条件期望 | Markov 条件、停时、平稳/极限混淆 | 有限状态计算 |
| 复分析 | 留数/解析结构 | 直接 Laurent 或围道变形 | 支路、方向、奇点阶数、边界奇点 | SymPy 局部符号 |
| 常微分方程 | 解析求解 | 变换/能量/定性方法 | 定义域、初值、漏解 | residual |
| 统计推断 | 似然/充分统计量 | 枢轴量/决策路线 | 正则条件、参数边界、偏差 | NumPy、符号微分 |
| 泛函分析 | 定理结构 | 定义/反例 | 完备、闭、有界、紧、强弱收敛 | 有限维反例 |
| 线性回归 | 矩阵正规方程 | 几何投影/统计解释 | 满秩、可识别性、误差假设 | NumPy、矩阵检查 |
| 偏微分方程 | 分离变量/变换 | 能量法/谱方法 | PDE、初边值、正则性、唯一性 | residual、边界检查 |
| 非基础及进阶课程 | 通用结构求解 | 定义和小实例 | 题意、前提、边界、反例 | 按 TaskContract 选择 |
| 高等代数 | 结构/矩阵理论 | 坐标计算 | 秩、维数、特征空间、域条件 | SymPy/NumPy |
| 运筹学 | 优化模型/对偶 | 枚举/动态规划 | 可行性、边界、对偶条件、整数性 | SciPy、枚举 |
| 数学分析 | 定理/估计 | 定义/Taylor/反证 | 极限交换、一致性、边界、定义域 | SymPy、mpmath |
| 拓扑学 | 定义和结构定理 | 反例/构造 | Hausdorff、紧、连通、局部/全局 | 有限拓扑枚举 |

---

# 18. Skill System

每个 Skill 只包含高密度执行信息：

```yaml
name: dominated_convergence
domain: measure_theory
trigger:
  - limit
  - integral
required_conditions:
  - measurable
  - ae_convergence
  - dominating_function
  - dominating_function_integrable
failure_modes:
  - missing_dominator
  - integrability_not_checked
attacks:
  - theorem_precondition
  - counterexample
verification:
  - identify_g
  - check_abs_bound
  - check_integrability
orthogonal_methods:
  - uniform_convergence_if_available
  - fatou_based_route
```

每题只加载 1～3 个最相关 Skill。

优先级：

```text
Failure Skill
Verification Skill
Strategy Skill
Knowledge Skill
```

---

# 19. Safe Trace

Trace 只记录元数据：

```json
[
  {
    "step": "route",
    "content": {
      "route": "R2",
      "risk": "high"
    }
  },
  {
    "step": "solver",
    "content": {
      "candidate_id": "A",
      "role": "structural",
      "status": "completed"
    }
  },
  {
    "step": "attack",
    "content": {
      "candidate_id": "A",
      "attack_type": "theorem_precondition",
      "status": "rebutted"
    }
  },
  {
    "step": "finalize",
    "content": {
      "candidate_id": "A",
      "status": "committed"
    }
  }
]
```

禁止写入：

- 题面；
- 完整 Prompt；
- 原始模型输出；
- 候选正文；
- 最终答案；
- API Key；
- 隐私信息。

---

# 20. Benchmark Telemetry

112 题离线测试应额外统计：

```text
route
solver_roles
method_fingerprints
orthogonality_level
certificate_types
attacks_scheduled
challenges_opened
challenges_sustained
challenges_rebutted
repair_triggered
repair_success
model_calls
tool_calls
response_chars
latency
```

参考答案只允许在 Agent 外部评估层使用，计算：

```text
Primary Correct
Final Correct
Wrong → Correct
Correct → Wrong
Red Team True Positive
Red Team False Positive
Repair Success
Repair Misrepair
```

核心净收益：

```text
NetGain
=
WrongToCorrect
-
CorrectToWrong
-
TimeoutPenalty
-
InvalidOutputPenalty
```

---

# 21. 必须具备的单元测试

## 21.1 输入隔离

- 参考答案不进入 Agent；
- Blind 不读取 Primary；
- Trace 不泄露题面和候选正文。

## 21.2 正交门

- 同 Prompt 换 temperature 被判 O0；
- 不同定理和工具路线被判 O2/O3；
- 读取 Primary 的候选不能算独立支持。

## 21.3 证据规则

- Hard Fail 否决多个软接受票；
- 工具异常产生 UNKNOWN；
- 数学等价先于冲突；
- `-1/8` 与 `-\frac{1}{8}` 归为同簇。

## 21.4 Challenge

- 无 target Claim 的普通怀疑不入账；
- 反例攻击生成 Fatal Challenge；
- Sustained Fatal Challenge 使候选不可提交。

## 21.5 Repair

- Repair 创建子候选；
- 不覆盖父候选；
- Repair 次数不超过 1；
- Repair 后重跑原攻击。

## 21.6 输出

- 多小问完整；
- final 非空；
- JSON 可序列化；
- Formatter 不能修改数学值。

---

# 22. 目标工程目录

```text
agent/
├── core.py
├── state.py
├── contracts.py
├── policies.py
│
├── profiler/
│   ├── canonicalizer.py
│   ├── task_contract.py
│   ├── risk_map.py
│   └── ambiguity.py
│
├── strategies/
│   ├── compiler.py
│   ├── method_fingerprint.py
│   ├── orthogonality.py
│   └── domain_registry.py
│
├── solvers/
│   ├── structural.py
│   ├── constructive_blind.py
│   ├── tool_integrated.py
│   ├── numerical_enum.py
│   └── rescue.py
│
├── evidence/
│   ├── candidate_ledger.py
│   ├── claim_graph.py
│   ├── certificates.py
│   ├── canonicalizer.py
│   ├── equivalence.py
│   ├── verified_facts.py
│   └── adjudicator.py
│
├── attacks/
│   ├── scheduler.py
│   ├── assumption.py
│   ├── theorem_precondition.py
│   ├── counterexample.py
│   ├── boundary.py
│   ├── transformation.py
│   ├── quantifier.py
│   ├── interpretation.py
│   ├── numerical_stress.py
│   └── completeness.py
│
├── challenges/
│   ├── ledger.py
│   ├── dispute_mapper.py
│   ├── local_resolver.py
│   └── cross_examination.py
│
├── repair/
│   ├── locator.py
│   └── targeted.py
│
├── tools/
│   ├── registry.py
│   ├── safe_executor.py
│   ├── sympy_tool.py
│   ├── numerical.py
│   ├── brute_force.py
│   ├── matrix.py
│   └── residual.py
│
├── protocols/
│   ├── solution_capsule.py
│   ├── answer_schema.py
│   ├── answer_normalizer.py
│   └── transaction.py
│
├── skills/
│   ├── router.py
│   ├── failures/
│   ├── verification/
│   └── strategies/
│
└── trace/
    └── recorder.py
```

---

# 23. 主流程伪代码

```python
def solve(problem: str, metadata: dict) -> dict:
    guard = RuntimeGuard()
    trace = SafeTrace()

    canonical = canonicalize(problem)
    contract = build_task_contract(canonical)
    state = CaseState.create(canonical, contract)

    primary = run_primary_solver(canonical, contract)
    state.add_candidate(primary)
    normalize_candidate(primary)
    build_claim_graph(primary)
    certify(primary, state)
    run_mandatory_light_attacks(primary, state)

    if can_freeze(primary, state):
        return transaction_commit(primary, state, trace)

    strategy = compile_missing_evidence_strategy(state)

    if strategy.requires_orthogonal_solver and guard.allow_model_call():
        orthogonal = run_orthogonal_blind_solver(
            canonical,
            contract,
            forbidden_fingerprint=primary.method,
        )
        normalize_candidate(orthogonal)

        if orthogonality_gate(primary, orthogonal):
            state.add_candidate(orthogonal)
            certify(orthogonal, state)

    cluster_equivalent_answers(state)
    schedule_red_team_attacks(state)
    resolve_challenges_with_tools(state)

    winner = adjudicate(state)
    if winner is not None and can_freeze(winner, state):
        return transaction_commit(winner, state, trace)

    if state.has_unresolved_fatal_challenge() and guard.allow_model_call():
        run_one_shot_cross_examination(state)

    winner = adjudicate(state)
    if winner is not None and can_freeze(winner, state):
        return transaction_commit(winner, state, trace)

    if (
        state.has_sustained_repairable_fatal_challenge()
        and state.repair_count == 0
        and guard.allow_model_call()
    ):
        repaired = targeted_repair(state)
        state.add_candidate(repaired)
        state.repair_count += 1
        normalize_candidate(repaired)
        reverify_original_failures(repaired, state)
        reattack_original_challenges(repaired, state)

    winner = adjudicate(state)

    if winner is None and guard.allow_rescue():
        winner = run_rescue_solver(canonical, contract)
        normalize_candidate(winner)
        state.add_candidate(winner)

    if winner is None:
        winner = best_existing_valid_candidate(state)

    if winner is None:
        raise RuntimeError("No valid candidate produced")

    return transaction_commit(winner, state, trace)
```

---

# 24. 实施阶段

## Phase 0：接口与基线冻结

- 保存当前 Baseline commit；
- 固定 112 题运行器；
- 确认输出契约和 Trace 隐私测试。

## Phase 1：答案基础设施

- Solution Capsule；
- Answer Normalizer；
- Mathematical Equivalence；
- Candidate Ledger；
- Transaction Commit。

## Phase 2：证据引擎

- 格式检查；
- SymPy；
- 代回；
- residual；
- numerical；
- brute force；
- multipart check。

## Phase 3：异构正交求解

- MethodFingerprint；
- Orthogonality Gate；
- Constructive Blind；
- Tool-Integrated Solver；
- Strategy Compiler。

## Phase 4：红队攻击

- Attack Scheduler；
- A1/A2/A4/A5/A9；
- Challenge Ledger；
- Local Resolver。

先实现最常见且可测试的攻击，再扩展 A3/A6/A7/A8。

## Phase 5：Claim 图和局部修复

- ClaimDependencyGraph；
- VerifiedFactStore；
- Dispute Mapper；
- Cross Examination；
- One-shot Targeted Repair。

## Phase 6：离线路由优化

根据 112 题消融，冻结静态 Route Policy，不在正式评测中跨题在线学习。

---

# 25. Definition of Done

HORA-Math 不能仅因为目录和文档存在就被认为实现完成。必须满足：

1. 低风险题能在硬证书后 Early Stop；
2. Blind 隔离测试通过；
3. 正交门能拒绝同质采样；
4. 至少五类红队攻击可形成结构化 Challenge；
5. Hard Counterexample 能否决软投票；
6. 工具失败不会误杀候选；
7. Repair 后会自动重攻；
8. 多小问只重算冲突部分；
9. `final_response` 不再直接提交超长原始推理；
10. 112 题报告包含路线、攻击、证据、调用和耗时统计；
11. 每个新增模块具有 Wrong→Correct 与 Correct→Wrong 消融数据；
12. 所有代码修改仍通过功能分支和 Pull Request 进入 `main`。
