# Challenge-Cup-2026 数学推理智能体

本仓库用于开发和评测基于 Intern-S 系列模型的数学推理智能体。平台入口保持为：

```python
class ReasoningAgent:
    def __init__(self, client, *args, **kwargs):
        ...

    def solve(self, problem: str, metadata: dict) -> dict:
        ...
```

返回值必须至少包含非空字符串：

```python
{
    "final_response": "最终答案",
    "trace": []
}
```

> 当前 `user_agent.py` 仍是 generate–verify–select baseline。本 README 记录的是根据榜单前十公开可核验方案形成的**目标架构和实施决策**，后续将按消融实验逐阶段落地，不能把尚未实现的模块当作当前能力。

官方 baseline、接口约束与赛事说明以 [InternLM/Challenge-Cup-2026](https://github.com/InternLM/Challenge-Cup-2026) 为准。

---

## 1. 前十方案分析后的最终决策

榜单前十并非全部公开。对于无法读取代码或项目说明的队伍，本项目不推测其内部实现。最终架构主要吸收下列公开可核验方案中的高价值机制：

| 公开方案 | 保留的决策 |
|---|---|
| [筹策 ChouCe](https://gitcode.com/2401_88048876/chouce-math-reasoning-agent) | 数学方法级独立候选、Blind Solve、对抗式审查、领域风险检查 |
| [LemaMAV](https://gitcode.com/NUDTAIMP/mathcode) | 单题内 Verified Fact / Lemma Memory、验证、局部修复、证据选择 |
| [九韶 JiuShao](https://gitcode.com/zcyyyy/-Intern-S1-zcy) | Tool-Integrated Reasoning、数值裁判、数学等价归簇、动态预算与消融实验 |
| [ICMA](https://gitcode.com/CNZkeven/ICMA) | LLM 与 Python/SymPy 双路交叉验证、冲突协调 |
| [MathAgent](https://gitcode.com/SONGXIA_YEJI/math_agent) | 计算、证明和学科策略模块化 |

最终明确放弃把下列方向作为主架构：

- 固定执行大量 Agent；
- 同一 Prompt 的 8/16 路同质采样；
- 仅靠多数投票；
- 无限 Reflection；
- 把 SymPy 当万能数学 Judge；
- Verifier、Critic、Arbiter 每题全部调用；
- 多轮 Repair 循环；
- 模型自报 confidence 加权；
- 全量 Skill/RAG 注入；
- 用长推理正文直接充当 `final_response`。

---

# 2. 终极目标架构：OMEGA-Math

**OMEGA-Math** 表示：

- **O — Orthogonal Methods**：方法正交，而非随机重复采样；
- **M — Mathematical Equivalence & Memory**：数学等价判断与单题已验证事实记忆；
- **E — Evidence Engine**：确定性、反驳性和理论条件证据；
- **G — Gated Escalation Graph**：证据不足或出现冲突时才升级；
- **A — Answer Transaction & Adaptive Budget**：答案事务提交和自适应预算。

最高原则：

> 先生成一个强候选，立即寻找能够证明它正确或错误的证据；只有证据不足或出现冲突时，才增加模型调用。

## 2.1 总体流程

```text
Problem
  ↓
Runtime Guard
  ↓
Problem Canonicalizer
  ↓
Task Contract + Ambiguity Analyzer
  ↓
Strategy Portfolio
  ↓
Primary Solver
  ↓
Solution Capsule
  ↓
Certificate Engine
  ├─ 格式与完整性
  ├─ 数学归一化
  ├─ SymPy / Python
  ├─ 代回 / residual
  ├─ 数值与枚举
  └─ 定理前提检查
  ↓
证据是否充分？
  ├─ 是 → Candidate Freeze
  │        ↓
  │     Answer Normalizer
  │        ↓
  │     Transaction Commit
  │
  └─ 否 → Orthogonal Blind Solver
           ↓
        Mathematical Equivalence
           ↓
        答案等价？
           ├─ 是 → 高风险轻量审查 → 证据选择
           └─ 否/未知
                ↓
             Dispute Mapper
                ↓
             定位第一个分歧 Claim
                ↓
             Targeted Tool Check
                ↓
             仍不能解决？
                ├─ 否 → 证据选择
                └─ 是 → Dispute Auditor
                          ↓
                       Fatal Error?
                          ├─ 否 → 证据选择
                          └─ 是 → One-shot Targeted Repair
                                      ↓
                                   Reverify
                                      ↓
                                   证据选择
                                      ↓
                              Answer Normalizer
                                      ↓
                              Transaction Commit
```

这是动态状态图，不是固定流水线。

## 2.2 只保留四种模型调用角色

### Call 1：Primary Solver

每题执行一次，负责快速产生高质量、可验证的主候选。

### Call 2：Orthogonal Blind Solver

仅在主候选缺少证据、高风险、存在歧义或工具无法验证时执行。它：

- 看不到 Primary 的答案；
- 看不到 Primary 的推理；
- 必须采用不同方法族；
- 独立完成题意理解。

### Call 3：Dispute Auditor

仅在候选真实冲突或理论前提无法确定时执行。它只检查分歧 Claim、Fatal Error、定理条件和反例，不重写整道题。

### Call 4：Repair 或 Rescue

二选一：

- `Targeted Repair`：修复已定位的局部错误；
- `Rescue`：截断、格式失败或无有效候选时给出最短可靠答案。

每题最多一次 Repair，不允许循环修复。

## 2.3 四级动态路线

```text
Route A
Primary
→ Hard Certificate
→ Commit
```

适合可直接代回、化简、枚举或计算的题，通常只调用模型一次。

```text
Route B
Primary
→ Certificate
→ Orthogonal Blind
→ Equivalence
→ Commit
```

适合中风险计算题或证据不完整的题。

```text
Route C
Primary
→ Orthogonal Blind
→ Theorem Preconditions Audit
→ Commit
```

适合测度论、泛函分析、抽象代数证明、拓扑、微分几何等理论题。

```text
Route D
Primary
→ Blind
→ Dispute Mapper
→ Auditor
→ One-shot Repair / Rescue
→ Commit
```

只在存在真实冲突、硬反证或严重歧义时使用。

---

# 3. 核心数据协议

## 3.1 Task Contract

每题建立轻量契约：

```python
TaskContract(
    primary_domain="probability",
    secondary_domain="combinatorics",
    problem_kind="conditional_counting",
    answer_schema="exact_rational",
    requires_proof=False,
    requires_exact_answer=True,
    multipart_count=1,
    risk_level="medium",
    verification_modes=[
        "range_check",
        "normalization_check",
        "small_case_enumeration",
    ],
    likely_failure_modes=[
        "conditional_direction_reversal",
        "incorrect_independence",
        "double_counting",
    ],
    preferred_primary_method="conditional_probability",
    preferred_orthogonal_method="combinatorial_counting",
)
```

使用软路由而非硬路由。领域判断用于选择策略、工具和 Failure Skill，不能成为单点故障。

## 3.2 Solution Capsule

模型完整思考后必须提供高信息密度胶囊：

```text
<METHOD>
finite-field subfield exclusion
</METHOD>

<FINAL_CANDIDATE>
72
</FINAL_CANDIDATE>

<CRITICAL_CLAIMS>
1. [F_81:F_3] = 4
2. Proper subfields correspond to divisors of 4
3. The only nontrivial proper subfield is F_9
</CRITICAL_CLAIMS>

<CHECK_HINTS>
field_degree_divisibility
finite_count
</CHECK_HINTS>
```

下游优先处理胶囊，不反复传递完整长推理。

## 3.3 Candidate Ledger

所有候选都保留，不允许后一个 Agent 直接覆盖前一个候选：

```text
A：Primary
B：Orthogonal Blind
C：Targeted Repair
R：Rescue
```

每个候选记录：

- 来源；
- 方法族；
- 规范化答案；
- 关键 Claim；
- 证据；
- Fatal Error；
- 是否冻结；
- 是否有资格提交。

## 3.4 Verified Fact / Lemma Memory

只保存当前单题内已经验证的事实，不依赖跨题状态：

```text
F1: G is cyclic              VERIFIED
F2: |G| = 8                  VERIFIED
F3: every subgroup is cyclic VERIFIED
```

简单计算题不启用；长证明、多小问、测度论、抽象代数、泛函分析和微分几何按需启用。

---

# 4. Certificate Engine

证据优先级高于 LLM 自信度。

## 4.1 格式证据

- `final_response` 非空；
- 答案类型匹配；
- 多小问完整；
- 集合、区间、矩阵维度正确；
- 返回值可 JSON 序列化。

## 4.2 硬数学证据

- SymPy 恒等验证；
- 方程代回；
- 导数反验；
- 积分反微分；
- 矩阵等式；
- ODE/PDE residual；
- 初值和边界条件；
- 有限枚举；
- 概率归一化；
- 高精度数值和误差界。

## 4.3 反驳证据

- 找到反例；
- residual 非零；
- 边界或初值失败；
- 非法除零；
- small-n 枚举冲突；
- 概率不在 `[0,1]`；
- 定理必要条件不成立。

工具异常只能记为 `UNKNOWN`，不能直接判候选错误。

## 4.4 理论条件证据

重点检查：

- 可测性、可积性、支配条件；
- 一致收敛和极限交换；
- 完备、紧、闭、有界；
- 正规性、同态、核与像；
- 局部与全局条件；
- 量词、边界和定义域；
- 概率独立性和条件概率分母。

---

# 5. Mathematical Equivalence Engine

不能使用普通字符串相等判断数学答案。

分层判断：

```text
E0：清洗后字符串相同
E1：整数/有理数完全相等
E2：SymPy simplify(a-b) == 0
E3：方程解集标准化相同
E4：集合和区间标准化相同
E5：矩阵逐项等价
E6：多小问逐项等价
E7：高精度多点数值支持
E8：无法判断
```

返回值只能是：

```text
EQUIVALENT
NOT_EQUIVALENT
UNKNOWN
```

例如：

```text
-1/8
-\frac{1}{8}
-0.125
```

不应被误判为三个冲突答案。

---

# 6. Dispute Mapper 与局部修复

候选不一致时，先定位冲突，不立即调用 Judge：

```text
D1：表示形式不同
D2：题意解释不同
D3：定理选择不同
D4：第一个代数步骤不同
D5：边界或特殊情况不同
D6：多小问映射不同
D7：近似精度不同
D8：无法定位
```

优先用确定性工具解决第一个分歧 Claim。

Repair 规则：

- 只修复第一个 Fatal Error 及其后续结论；
- 已验证事实默认冻结；
- Repair 生成新候选，不能覆盖原候选；
- Repair 后必须重新运行原失败检查器；
- 每题最多一次 Repair。

---

# 7. 候选选择与 Early Stop

不使用未经数据校准的浮点权重。按字典序选择：

1. 输出契约合法；
2. 不存在 Hard Fail；
3. 关键结论有 Hard Pass；
4. 获得正交独立支持；
5. 不存在未解决 Fatal Error；
6. 关键 Claim 完整；
7. 稳定候选优先于证据不足的修复候选。

满足下列条件之一即可 Early Stop：

```text
Primary 完整
+ Hard Certificate PASS
+ 无高风险条件
```

```text
Primary 与 Blind 数学等价
+ 无 Fatal Error
+ 所有小问完整
```

```text
Candidate A HARD_PASS
+ Candidate B HARD_FAIL
```

达到阈值后冻结候选，除非出现新的硬反证，否则禁止继续修改。

---

# 8. 学科专属验证路线

| 学科 | 主要验证 |
|---|---|
| 离散数学 / 组合 | small-n 枚举、重复计数、递推初值、图结构检查 |
| 数值分析 | 高精度计算、误差界、收敛条件、迭代稳定性 |
| 测度积分 / 数学分析 | 可测、可积、支配、一致收敛、极限与积分交换 |
| 抽象代数 | 正规性、同态、核像、阶数整除、扩张次数、有限实例 |
| 概率统计 | 范围、归一化、条件概率分母、独立性、小规模枚举 |
| 随机过程 | 转移概率、Markov 条件、平稳分布、停时条件 |
| ODE / PDE | residual、初值、边界条件、定义域、正则性 |
| 复分析 | 解析性、奇点分类、留数、围道方向、支路选择 |
| 泛函分析 / 拓扑 | 完备、紧、闭、有界、Hausdorff、局部与全局、反例攻击 |

---

# 9. Runtime Guard

正式评测必须同时考虑：

- 单题独立进程硬时限；
- Agent 阶段总时限；
- 最多三题并发；
- 模型调用次数和 Token；
- 截断、异常与无效输出。

建议内部阶段：

```text
正常阶段：允许主解、工具和必要盲解
冲突阶段：只解决已有分歧，不再扩张候选
救援阶段：禁止长推理，只允许 Rescue 和答案提交
提交阶段：停止新增模型调用
```

`FINAL_CANDIDATE` 必须优先于长推理输出。发生截断时：

1. 已有完整候选：直接验证；
2. 没有候选：最多 Continuation 一次；
3. 再次失败：Rescue 一次；
4. 禁止无限续写。

---

# 10. 实施顺序与消融实验

按以下顺序开发，每次只增加一个主要变量：

```text
Phase 1
Answer Schema
→ Answer Normalizer
→ Mathematical Equivalence
→ Candidate Ledger
→ Transaction Commit
→ Runtime Guard
```

```text
Phase 2
SymPy
→ 代回
→ residual
→ numerical
→ brute force
→ multipart check
```

```text
Phase 3
Strategy Portfolio
→ Orthogonality Rules
→ Blind Context Isolation
```

```text
Phase 4
Dispute Mapper
→ Theorem Preconditions
→ Failure Skills
```

```text
Phase 5
Dispute Auditor
→ Fatal Error Locator
→ One-shot Repair
→ Reverification
```

每个模块必须记录：

```text
Wrong → Correct
Correct → Wrong
调用次数
输入/输出 Token
平均与 P95 耗时
超时率
异常率
无效输出率
```

模块净价值：

\[
\text{Module Value}
=
\text{Wrong}\rightarrow\text{Correct}
-
\text{Correct}\rightarrow\text{Wrong}
-
\lambda_1\text{Timeout}
-
\lambda_2\text{Invalid Output}
\]

救回题数小于误杀题数的模块应删除，而不是因为“架构高级”继续保留。

---

# 11. 112 题公开测试集

完整回归测试使用：

```text
https://github.com/Jialiang-Zhang/test-dataset-math/tree/main/112
```

该目录包含独立 JSON 文件。工作流会：

1. 检出本仓库 `main`；
2. 检出 `Jialiang-Zhang/test-dataset-math`；
3. 数字顺序读取 `112/*.json`；
4. 严格验证 `idx` 唯一和 `problem` 非空；
5. 生成只含 `idx`、`problem` 的临时 JSONL；
6. 调用 `main.py`；
7. 将结果保存到 `output/<UTC运行时间>/`；
8. 创建独立结果分支；
9. 提交结果并创建 Pull Request，不直接修改 `main`。

`answer`、`subject`、`source` 只用于本地数据清单与汇总，**不会传入 `ReasoningAgent.solve`**。

## 11.1 GitHub Actions 运行

先在仓库 Secret 中配置：

```text
INTERN_API_KEY
```

然后：

```text
Actions
→ Run 112 benchmark
→ Run workflow
```

推荐首次使用：

```text
concurrency = 3
dataset_ref = main
```

工作流是手动触发，不会在普通代码 push 时自动消耗 API 配额。

## 11.2 输出结构

```text
output/
├── README.md
└── 20260825T135011Z-run12/
    ├── 0.json
    ├── 1.json
    ├── ...
    ├── 111.json
    ├── run_metadata.json
    └── summary.json
```

目录名使用 UTC 运行时间，并附带 GitHub run number 以避免同秒冲突。

`run_metadata.json` 记录：

- 运行时间；
- 数据集仓库、ref 和 commit；
- 智能体仓库 commit；
- 模型；
- 并发数；
- 数据集摘要；
- runner 退出码和总耗时。

`summary.json` 记录：

- 成功、错误和缺失数量；
- 学科分布；
- 每题响应长度；
- Trace 步骤数；
- 错误类型。

该汇总只评估运行完整性，**不是官方数学 Judge 分数**。

## 11.3 本地运行

将数据集仓库放在相邻目录后：

```bash
export INTERN_API_KEY="sk-..."
export INTERN_MODEL="intern-s2-preview"

python scripts/run_112_benchmark.py \
  --dataset-dir ../test-dataset-math/112 \
  --output-root output \
  --concurrency 3
```

脚本自动创建 UTC 时间目录。也可以指定：

```bash
python scripts/run_112_benchmark.py \
  --dataset-dir ../test-dataset-math/112 \
  --output-root output \
  --run-id 20260825T135011Z-local \
  --concurrency 3
```

已有且非空的运行目录不会被覆盖。

---

# 12. 分支与结果管理规则

所有人工代码修改必须：

```text
main
→ 新建功能分支
→ 提交修改
→ Pull Request
→ 审查后合并
```

112 题工作流生成的结果同样遵守：

```text
main
→ benchmark/112-<运行时间>
→ output/<运行时间>/
→ 自动或手动创建 Pull Request
```

禁止：

- 直接将开发修改推入 `main`；
- 将 API Key 写入仓库；
- 在 Trace 或结果元数据中输出密钥；
- 覆盖旧运行目录；
- 用同一个输出目录混合多个 commit 的结果。

---

# 13. 当前项目结构

```text
.
├── user_agent.py
├── llm_client.py
├── main.py
├── requirements.txt
├── scripts/
│   └── run_112_benchmark.py
├── tests/
├── sample_data/
├── output/
│   └── README.md
└── .github/
    └── workflows/
        ├── run-dev.yml
        └── run-112-benchmark.yml
```

当前 baseline 仍用于接口和运行链路验证。OMEGA-Math 会按照上述阶段逐步替换内部实现，同时始终保持：

```python
ReasoningAgent(client=official_client)
agent.solve(problem, metadata)
```

接口稳定。
