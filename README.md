# Challenge-Cup-2026 数学推理智能体

本仓库用于开发、回归测试和提交基于 Intern-S 系列模型的数学推理智能体。平台入口保持为：

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

> 当前 `user_agent.py` 仍是 generate–verify–select baseline。本文档描述的是根据榜单前十公开可核验方案、现有 112 题分布以及本项目实测问题重新设计的**目标架构**。尚未实现的模块不会被描述成当前能力。

官方接口、赛事限制和 baseline 说明以 [InternLM/Challenge-Cup-2026](https://github.com/InternLM/Challenge-Cup-2026) 为准。

---

# 1. 最终架构决策

前十方案并非全部公开。本项目只吸收能够公开核验的设计，不推测未公开仓库的内部实现。

| 公开方案 | 吸收的高价值机制 |
|---|---|
| [筹策 ChouCe](https://gitcode.com/2401_88048876/chouce-math-reasoning-agent) | 数学方法级独立候选、Blind Solve、对抗式审查、领域风险检查 |
| [LemaMAV](https://gitcode.com/NUDTAIMP/mathcode) | 单题内 Verified Fact / Lemma Memory、验证、局部修复、证据选择 |
| [九韶 JiuShao](https://gitcode.com/zcyyyy/-Intern-S1-zcy) | Tool-Integrated Reasoning、数值裁判、等价归簇、动态预算和消融实验 |
| [ICMA](https://gitcode.com/CNZkeven/ICMA) | LLM 与 Python/SymPy 异构双路、交叉验证和冲突协调 |
| [MathAgent](https://gitcode.com/SONGXIA_YEJI/math_agent) | 计算、证明和学科策略模块化 |

最终架构必须同时具备：

1. **异构求解**：不同求解器使用不同推理范式、表示方式和工具通道；
2. **正交求解**：独立候选不能只是同一 Prompt 的随机复现；
3. **主动攻击**：红队审查器以推翻候选为目标，而不是礼貌地“再检查一次”；
4. **Claim 级争议定位**：冲突聚焦到第一个分歧 Claim，不把整题重新生成；
5. **证据裁决**：硬证据、攻击结果和独立支持优先于投票和模型自信度；
6. **动态升级**：简单题尽早提交，高风险题才启动异构求解和对抗攻击；
7. **一次性修复**：最多一次局部 Repair，Repair 后必须重新验证；
8. **事务提交**：最终答案规范化、冻结后再返回。

明确放弃将下列方向作为主架构：

- 固定执行大量 Agent；
- 同一 Prompt 的 8/16 路同质采样；
- 仅靠多数投票；
- 无限 Reflection；
- “你确定吗”式 Verifier；
- 让 Blind Solver 看到 Primary；
- 将 SymPy 当成万能数学 Judge；
- Verifier、Critic、Arbiter 每题全部调用；
- 多轮 Repair 循环；
- 模型自报 confidence 加权；
- 全量 Skill/RAG 注入；
- 用长推理正文直接充当 `final_response`。

---

# 2. 终极目标架构：HORA-Math

**HORA-Math** 表示：

- **H — Heterogeneous Solvers**：异构求解器；
- **O — Orthogonal Reasoning**：方法、表示、工具和上下文正交；
- **R — Red-Team Attacks**：红队对抗攻击与反例搜索；
- **A — Adjudicated Evidence**：基于证据的裁决、冻结和提交。

中文定义：

> **异构正交求解—红队对抗审查—证据裁决数学智能体**

最高原则：

> 先用异构方法产生少量高价值候选，再让红队主动攻击候选的假设、定理条件、边界和关键 Claim；只有经受攻击且得到证据支持的候选，才允许被冻结并提交。

## 2.1 总体状态图

```text
Problem
  ↓
Runtime Guard
  ↓
Problem Canonicalizer
  ↓
Task Contract + Risk Map + Ambiguity Map
  ↓
Heterogeneous Strategy Compiler
  ↓
Blue Team Solver Portfolio
  ├─ S1 Structural / Theorem Solver
  ├─ S2 Constructive / Definition Solver
  ├─ S3 Tool-Integrated Symbolic Solver
  └─ S4 Numerical / Enumeration Solver
  ↓
Orthogonality Gate
  ├─ 方法重复 → 不计为独立支持
  └─ 方法正交 → 进入 Candidate Ledger
  ↓
Solution Capsules
  ↓
Mathematical Canonicalization
  ↓
Equivalence Clustering
  ↓
Certificate Engine
  ├─ 格式与完整性证书
  ├─ 符号 / 代回 / residual
  ├─ 数值 / 枚举 / 极端测试
  └─ 定理前提与定义条件
  ↓
证据是否已充分？
  ├─ 是且风险低
  │    ↓
  │ Candidate Freeze
  │    ↓
  │ Answer Transaction
  │
  └─ 否或风险高
       ↓
Red-Team Attack Scheduler
       ↓
Adversarial Attack Factory
  ├─ Assumption Attack
  ├─ Theorem-Precondition Attack
  ├─ Counterexample Attack
  ├─ Boundary / Degenerate Attack
  ├─ Transformation / Quantifier Attack
  ├─ Interpretation Attack
  ├─ Numerical Stress Attack
  └─ Completeness / Format Attack
       ↓
Challenge Ledger
       ↓
Dispute Mapper
       ↓
定位第一个关键分歧 Claim
       ↓
Deterministic Local Resolver
       ↓
挑战是否解决？
  ├─ 已驳回攻击 → 增加 attack-survival 证据
  ├─ 攻击成立 → 候选降级或淘汰
  └─ 尚不确定
       ↓
One-shot Cross Examination
       ↓
Blue Defense / Red Rebuttal
       ↓
仍存在 Fatal Challenge？
  ├─ 否 → Evidence Adjudicator
  └─ 是 → One-shot Targeted Repair
                 ↓
              Reverify
                 ↓
        Evidence Adjudicator
                 ↓
        Answer Normalizer
                 ↓
        Transaction Commit
                 ↓
    final_response + safe trace
```

这是按风险和证据动态展开的图，不是每道题都执行全部节点。

---

# 3. 异构求解器设计

异构不是简单地给同一模型换几个角色名。每个求解器必须在至少两个维度上与其它求解器不同。

## 3.1 异构维度

```text
推理范式：
直接证明 / 反证 / 逆否 / 构造 / 归纳 / 极值 / 双计数

数学表示：
符号 / 几何 / 图结构 / 概率事件 / 算子 / 坐标 / 生成函数

工具通道：
纯 LLM / SymPy / Python 数值 / brute force / residual checker

知识路径：
定义展开 / 结构定理 / 局部计算 / 全局不变量 / 对偶性

目标函数：
求解 / 构造 / 验证 / 找反例 / 攻击条件

上下文暴露：
看主候选 / 不看主候选 / 只看分歧 Claim
```

## 3.2 Blue Team Solver Portfolio

### S1：Structural / Theorem Solver

适合：

- 抽象代数；
- 泛函分析；
- 拓扑；
- 测度论；
- 图论结构题；
- 需要调用标准定理的证明题。

职责：

```text
识别结构
选择定理
明确列出定理前提
给出关键 Claim
输出最终候选
```

### S2：Constructive / Definition Solver

禁止简单复述 S1 的定理路线，优先：

```text
从定义展开
直接构造
局部计算
反证或逆否
显式计数
```

它承担真正的正交盲解职责。

### S3：Tool-Integrated Symbolic Solver

适合：

- 代数恒等；
- 方程；
- 积分、导数；
- 矩阵；
- ODE/PDE 候选解；
- 部分复分析计算。

组合：

```text
LLM 生成可检查表达式
+
SymPy / Python 执行
+
返回证书或反证
```

### S4：Numerical / Enumeration Solver

适合：

- 组合与离散；
- 数值分析；
- 概率小规模事件；
- 递推；
- 有限结构；
- 极限和复杂表达式的 sanity check。

作用主要是：

```text
快速发现错误
```

而不是把有限数值测试伪装成一般性证明。

## 3.3 动态选择

每题不固定调用四个求解器。

```text
低风险计算题：
S1 或 S3

中风险题：
S1 + 一个正交求解器

高风险理论题：
S1 + S2 + 红队审查

工具可验证冲突题：
S1 + S3/S4 + 红队局部攻击
```

同一 base model 可以承担不同角色，但必须通过：

- 上下文隔离；
- 方法限制；
- 不同工具通道；
- 不同输出协议；
- Method Fingerprint；

实现功能异构。

---

# 4. 正交求解协议

## 4.1 Method Fingerprint

每个候选必须记录方法指纹：

```python
MethodFingerprint(
    paradigm="constructive",
    representation="combinatorial",
    theorem_family="none",
    tool_channel="brute_force",
    interpretation_id="I1",
    exposed_to_primary=False,
)
```

## 4.2 Orthogonality Gate

两个候选只有在关键维度确实不同，才算独立支持。

高价值正交：

```text
结构定理 ↔ 定义构造
条件概率 ↔ 组合计数
生成函数 ↔ 递推
解析求解 ↔ residual 检查
直接证明 ↔ 反证 / 反例攻击
自然语言证明 ↔ 确定性枚举
```

低价值重复：

```text
相同定理重新叙述
相同公式换符号
只改变 temperature
相同 Prompt 多次采样
看过 Primary 后再“独立”求解
```

低正交候选可以保留为调试记录，但：

```text
不能增加 independent-support 证据
不能参与多数票
不能触发“多候选一致即正确”
```

## 4.3 Blind Isolation

正交盲解器只能看到：

```text
原题
Task Contract
指定的正交方法族
必要的 1～3 个 Skill
```

禁止看到：

```text
Primary 答案
Primary 推理
Primary Claim
Verifier 结论
其它候选答案
```

---

# 5. Solution Capsule 与 Candidate Ledger

## 5.1 Solution Capsule

每个求解器在完整推理后输出高信息密度胶囊：

```text
<INTERPRETATION>
I1
</INTERPRETATION>

<METHOD_FINGERPRINT>
constructive | combinatorial | no_tool | blind
</METHOD_FINGERPRINT>

<FINAL_CANDIDATE>
...
</FINAL_CANDIDATE>

<CRITICAL_CLAIMS>
C1: ...
C2: ...
C3: ...
</CRITICAL_CLAIMS>

<PRECONDITIONS_USED>
P1: ...
P2: ...
</PRECONDITIONS_USED>

<CHECK_HINTS>
...
</CHECK_HINTS>

<RISK_FLAGS>
...
</RISK_FLAGS>
```

下游优先处理 Capsule，不反复传递完整长推理。

## 5.2 Candidate Ledger

```text
A：Primary
B：Orthogonal Blind
C：Tool-derived Candidate
D：Targeted Repair
R：Rescue
```

每个候选记录：

- 来源；
- 题意解释；
- Method Fingerprint；
- 规范化答案；
- 关键 Claim；
- 使用的定理前提；
- 硬证据；
- 红队挑战；
- 已解决和未解决的 Fatal Challenge；
- 是否冻结；
- 是否有资格提交。

后一个候选不得覆盖前一个候选。

---

# 6. 数学等价与候选归簇

不能使用普通字符串相等比较数学答案。

## 6.1 等价层级

```text
E0：清洗后的字符串相同
E1：整数 / 有理数完全相等
E2：SymPy simplify(a-b) == 0
E3：方程解集标准化相同
E4：集合 / 区间标准化相同
E5：矩阵逐项等价
E6：多小问逐项等价
E7：高精度多点数值支持
E8：无法判断
```

返回：

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

不能被误判为三个冲突答案。

## 6.2 Equivalence Cluster

候选先按数学等价归簇：

```text
Cluster K1:
A, B, C → answer equivalent

Cluster K2:
D → conflicting answer
```

簇的可信度不由成员数量直接决定，而由：

```text
方法正交性
硬证据覆盖
攻击存活情况
Fatal Challenge
```

共同决定。

---

# 7. Certificate Engine

证据优先级高于模型自信度和自然语言长度。

## 7.1 格式与完整性证书

- `final_response` 非空；
- 答案类型匹配；
- 多小问完整；
- 集合、区间、矩阵维度正确；
- 返回值可 JSON 序列化；
- Candidate 与最终规范化答案一致。

## 7.2 硬数学证书

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

## 7.3 反驳证书

- 明确反例；
- residual 非零；
- 边界或初值失败；
- 非法除零；
- small-n 枚举冲突；
- 概率超出 `[0,1]`；
- 定理必要条件不成立；
- 多小问缺失；
- 候选答案不满足原题。

工具异常只能记为：

```text
UNKNOWN
```

不能直接把候选判错。

## 7.4 理论条件证书

重点检查：

- 可测性、可积性、支配条件；
- 一致收敛和极限交换；
- 完备、紧、闭、有界；
- 正规性、同态、核与像；
- 局部与全局条件；
- 量词、边界和定义域；
- 概率独立性和条件概率分母；
- ODE/PDE 正则性与边界条件；
- 复分析围道、支路与奇点条件。

---

# 8. 红队对抗审查系统

红队不是普通 Verifier。它的目标是：

> 假设当前候选存在错误，主动寻找能够推翻它的最小证据。

红队只攻击候选，不负责写一篇新的完整解答。

## 8.1 Attack Scheduler

根据 Task Contract、Risk Map、Failure Skills 和候选状态选择攻击组合。

```text
低风险 + Hard Pass：
只做格式和边界轻攻击

理论高风险：
定理前提攻击 + 反例攻击 + 量词攻击

候选冲突：
只攻击第一个分歧 Claim

工具候选：
residual / numerical stress / domain attack

多小问：
只攻击未验证的小问
```

## 8.2 Attack Factory

### A1：Assumption Attack

寻找：

- 未声明假设；
- 把结论当条件；
- 隐含独立性；
- 隐含非零；
- 隐含可逆性；
- 隐含有限性。

### A2：Theorem-Precondition Attack

逐项核对：

```text
定理名称
必要条件
题面是否给出
候选是否已经证明
```

如果缺失条件，生成 Fatal Challenge。

### A3：Counterexample Attack

优先寻找：

- 最小反例；
- 有限低维反例；
- 退化结构；
- 极端参数；
- 非一般位置；
- 特殊分布；
- 非紧、非完备或非正规情形。

### A4：Boundary / Degenerate Attack

检查：

```text
0 / 1
空集
单点
端点
奇点
重根
秩退化
概率 0 或 1
参数最小允许值
无穷远行为
```

### A5：Transformation Attack

攻击：

- 非等价变形；
- 除零；
- 开平方丢符号；
- 取对数定义域；
- 极限交换；
- 积分交换；
- 非双向蕴含；
- 增根与漏解。

### A6：Quantifier Attack

检查：

```text
任意 ↔ 存在
几乎处处 ↔ 处处
局部 ↔ 全局
至少 ↔ 恰好
至多 ↔ 等于
充分 ↔ 必要
```

### A7：Interpretation Attack

从另一种合理题意解释出发，检查：

- 符号作用域；
- 多小问共享条件；
- 变量约束；
- 精确值与近似值；
- “所有”与“某个”；
- 题目是否存在两个自然解释。

### A8：Numerical Stress Attack

使用：

- 高精度；
- 多测试点；
- 极端点；
- 随机点；
- 特殊点；
- residual；
- small-instance brute force；

尝试发现候选表达式失败的位置。

### A9：Completeness / Answer-Schema Attack

检查：

- 是否回答所有小问；
- 是否只给必要条件却漏充分性；
- 是否只证明唯一性未证明存在性；
- 是否给一个解而题目要求全部解；
- 最终答案是否符合类型。

---

# 9. Challenge Ledger 与攻防协议

## 9.1 Challenge 对象

```python
Challenge(
    attack_id="A3-01",
    candidate_id="A",
    target_claim_id="C2",
    attack_type="counterexample",
    severity="fatal",
    statement="...",
    witness="...",
    required_resolver="finite_enumeration",
    status="open",
)
```

状态：

```text
OPEN
SUSTAINED
REBUTTED
RESOLVED_BY_TOOL
NOT_APPLICABLE
```

## 9.2 Claim 级攻击

红队必须优先输出：

```text
第一个可决定结论的错误 Claim
```

而不是：

```text
这篇解答似乎有问题。
```

只要上游 Claim 已被击破，不继续攻击其全部后续推导，避免重复 Token。

## 9.3 Deterministic Local Resolver

挑战生成后，优先使用：

- SymPy；
- Python；
- 代回；
- residual；
- 枚举；
- 定义检查；
- 静态规则；

解决争议。

能够由本地证据解决的冲突，不调用 LLM Arbiter。

## 9.4 One-shot Cross Examination

只有工具无法解决 Fatal Challenge 时，允许一次 Claim 级交叉质询。

### Red Team 输入

```text
原题摘要
Candidate Capsule
目标 Claim
已有证据
```

### Blue Defense 输入

```text
原题
已验证事实
目标 Challenge
自身 Candidate Capsule
```

Blue Defense 不能看到其它候选的长推理。

输出只允许：

```text
DEFENDED
CONCEDED
REVISED_CLAIM
```

并附最小必要理由。

### Red Rebuttal

如仍有必要，由同一个 Dispute Auditor 在一次调用内完成：

```text
挑战是否成立
哪一方证据更强
是否需要 Repair
```

不再创建无限辩论回合。

---

# 10. 对抗攻击后的修复规则

## 10.1 Targeted Repair

只有满足以下条件才允许：

```text
存在 Fatal Challenge
+
错误 Claim 已定位
+
其前置 Verified Facts 仍可保留
```

修复要求：

- 只修第一个 Fatal Claim 及其后续；
- 已验证事实默认冻结；
- Repair 生成新候选；
- 原候选不被覆盖；
- Repair 后重新执行原攻击和原检查器；
- 每题最多一次 Repair。

## 10.2 Fresh Restart

仅当：

- 题意整体误读；
- 方法核心完全失效；
- 所有关键 Claim 都不可保留；

才允许一次短路重解。

## 10.3 Repair 失败

```text
保留原 Ledger
淘汰有 Hard Fail 的候选
不再 Repair
进入最终 Evidence Adjudicator
```

---

# 11. Evidence Adjudicator

不使用未经数据校准的浮点加权，也不使用简单多数投票。

按字典序裁决。

## 11.1 淘汰条件

候选出现任意一项，原则上不可提交：

1. 输出契约非法；
2. 明确 Hard Fail；
3. Fatal Challenge 已成立且未修复；
4. 多小问缺失；
5. 最终答案无法规范化；
6. 使用了被反例推翻的核心 Claim。

## 11.2 候选优先级

1. 输出合法且完整；
2. 无 Hard Fail；
3. 关键结论有 Hard Pass；
4. 经受住 Fatal Attack；
5. 获得真正正交的独立支持；
6. 关键 Claim 覆盖完整；
7. 未解决 Challenge 更少；
8. 未经修复的稳定候选优先于证据不足的 Repair 候选；
9. 成本更低者作为最后 tie-breaker。

## 11.3 Attack Survival

攻击存活不能仅表示：

```text
红队没有说错
```

必须满足至少一种：

- Challenge 被工具反驳；
- Challenge 与题目不适用；
- Blue Defense 给出可验证证据；
- 独立正交候选支持同一 Claim；
- 红队无法提供具体 Fatal Claim，只给出泛化怀疑。

---

# 12. Dynamic Route Policy

## Route A：单解 + 硬证书

```text
Primary
→ Hard Certificate
→ Lightweight Boundary Attack
→ Commit
```

适合：

- 方程；
- 矩阵；
- 标准积分；
- 明确可代回的问题。

模型调用通常为 1 次。

## Route B：双解 + 正交攻击

```text
Primary
→ Orthogonal Blind
→ Equivalence Clustering
→ Targeted Red Attack
→ Commit
```

适合中风险计算题、概率题和工具不能完全验证的问题。

模型调用通常为 2～3 次。

## Route C：理论双解 + 强制红队

```text
Structural Solver
+
Definition / Constructive Blind Solver
→ Theorem-Precondition Attack
→ Counterexample / Quantifier Attack
→ Evidence Adjudication
```

适合：

- 测度论；
- 泛函分析；
- 抽象代数证明；
- 拓扑；
- 微分几何；
- 高风险离散证明。

模型调用通常为 3 次。

## Route D：真实冲突攻防

```text
Equivalence Conflict
→ Dispute Mapper
→ Claim-level Attack
→ Deterministic Resolver
→ One-shot Cross Examination
→ Targeted Repair
→ Reattack
→ Commit
```

只在存在真实冲突或 Hard Fail 时启用。

模型调用上限建议为 4 次。

---

# 13. 学科专属异构与攻击路线

| 学科 | 正交求解组合 | 红队重点攻击 |
|---|---|---|
| 离散数学 / 组合 | 双计数 ↔ 递推 / 生成函数 ↔ 枚举 | 重复计数、初值、极端小规模、连通性 |
| 数值分析 | 理论误差推导 ↔ 高精度实验 | 收敛条件、误差阶、稳定性、初值 |
| 测度积分 / 数学分析 | 定理法 ↔ 定义/逼近法 | 可测、可积、支配、极限交换、a.e. 与处处 |
| 抽象代数 | 结构定理 ↔ 定义构造 / 有限实例 | 正规性、阶数整除、扩张次数、核像、商结构 |
| 概率统计 | 条件概率 ↔ 组合计数 / 指示变量 | 独立性、条件方向、分母、归一化、重复计数 |
| 随机过程 | 转移结构 ↔ 条件期望 / 鞅方法 | Markov 条件、停时、平稳与极限分布 |
| ODE / PDE | 解析构造 ↔ residual / 数值检查 | 初值、边界、正则性、定义域、唯一性 |
| 复分析 | 留数/围道 ↔ 局部 Laurent / 直接极限 | 围道方向、支路、极点阶数、边界奇点 |
| 泛函分析 / 拓扑 | 定理法 ↔ 定义/反例法 | 完备、紧、闭、有界、Hausdorff、局部与全局 |
| 微分几何 | 坐标计算 ↔ 不变量/几何定义 | 坐标依赖、局部全局、正则点、符号约定 |

---

# 14. Multi-part 与 Verified Fact Memory

多小问按部分管理：

```python
PartState(
    part_id="b",
    candidates=[],
    verified_facts=[],
    challenges=[],
    status="unresolved",
)
```

允许：

```text
(a) 已冻结
(b) 发生 Fatal Challenge
(c) 已冻结
```

只对 `(b)` 启动额外求解和攻击。

Verified Fact / Lemma Memory 只保存当前单题内已经验证的事实：

```text
F1: G is cyclic              VERIFIED
F2: |G| = 8                  VERIFIED
F3: every subgroup is cyclic VERIFIED
```

Repair 和 Blue Defense 默认不能修改已冻结事实，除非红队提供新的硬反证。

---

# 15. Runtime Guard

正式评测必须同时考虑：

- 单题进程硬时限；
- Agent 阶段总时限；
- 最多三题并发；
- 模型调用次数；
- Token；
- 截断；
- 异常；
- 无效输出。

阶段建议：

```text
正常阶段：
允许 Primary、工具和必要的 Orthogonal Solver

攻击阶段：
只生成针对已有候选的 Challenge，不继续扩张普通候选

争议阶段：
只解决第一个 Fatal Dispute

救援阶段：
禁止长推理，只允许 Rescue 或选择已有候选

提交阶段：
停止所有新增模型调用
```

`FINAL_CANDIDATE` 必须优先于长推理输出。

发生截断：

1. 已有完整候选：直接验证；
2. 没有候选：最多 Continuation 一次；
3. 再次失败：Rescue 一次；
4. 禁止无限续写。

---

# 16. 安全 Trace

Trace 只记录结构化运行摘要，不记录题面、候选正文、最终答案、完整 Prompt 或密钥。

示例：

```json
[
  {
    "step": "strategy_compile",
    "content": {
      "route": "C",
      "solver_roles": ["structural", "constructive_blind"],
      "attack_plan": ["precondition", "counterexample"]
    }
  },
  {
    "step": "orthogonality_gate",
    "content": {
      "candidate_pair": ["A", "B"],
      "status": "accepted"
    }
  },
  {
    "step": "red_team_attack",
    "content": {
      "candidate_id": "A",
      "attack_type": "theorem_precondition",
      "status": "challenge_opened",
      "severity": "fatal"
    }
  },
  {
    "step": "challenge_resolution",
    "content": {
      "challenge_id": "A2-01",
      "status": "resolved_by_tool"
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

---

# 17. 目标工程结构

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
│   └── domain_routes.py
│
├── solvers/
│   ├── structural.py
│   ├── constructive_blind.py
│   ├── tool_integrated.py
│   ├── numerical_enum.py
│   └── rescue.py
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
├── evidence/
│   ├── candidate_ledger.py
│   ├── certificates.py
│   ├── equivalence.py
│   ├── verified_facts.py
│   └── adjudicator.py
│
├── repair/
│   ├── fatal_locator.py
│   ├── targeted.py
│   └── reverify.py
│
├── tools/
│   ├── registry.py
│   ├── safe_executor.py
│   ├── sympy_tool.py
│   ├── numeric.py
│   ├── brute_force.py
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
│   ├── strategies/
│   ├── verification/
│   └── failures/
│
└── trace/
    └── recorder.py
```

目录多不等于 Agent 多。大多数模块应为确定性 Python 逻辑。

---

# 18. 实施顺序与消融实验

每次只增加一个主要变量。

## Phase 1：答案与证据基础设施

```text
Answer Schema
→ Answer Normalizer
→ Mathematical Equivalence
→ Candidate Ledger
→ Transaction Commit
→ Runtime Guard
```

## Phase 2：异构工具求解

```text
SymPy / substitution
→ residual
→ numerical
→ brute force
→ Tool-Integrated Solver
```

## Phase 3：正交求解

```text
Method Fingerprint
→ Orthogonality Gate
→ Blind Context Isolation
→ Strategy Compiler
```

## Phase 4：红队攻击

```text
Attack Scheduler
→ Theorem-Precondition Attack
→ Counterexample Attack
→ Boundary / Transformation / Quantifier Attack
→ Challenge Ledger
```

## Phase 5：攻防与修复

```text
Dispute Mapper
→ Deterministic Local Resolver
→ One-shot Cross Examination
→ Fatal Error Locator
→ One-shot Targeted Repair
→ Reattack / Reverify
```

## Phase 6：动态策略

通过 112 题回归测试学习：

```text
哪些题只需要单解
哪些题需要一个正交盲解
哪些题必须红队攻击
哪些攻击误杀率过高
哪些 Repair 没有净收益
```

每个模块记录：

```text
Wrong → Correct
Correct → Wrong
攻击发现真实错误数
攻击制造假冲突数
Challenge 被工具解决比例
Repair 成功率
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
-
\lambda_3\text{False Challenge}
\]

救回题数小于误杀题数，或者制造大量假挑战的模块，应降级或删除。

---

# 19. 112 题公开测试集

完整回归测试使用：

```text
https://github.com/Jialiang-Zhang/test-dataset-math/tree/main/112
```

工作流会：

1. 检出本仓库 `main`；
2. 检出 `Jialiang-Zhang/test-dataset-math`；
3. 数字顺序读取 `112/*.json`；
4. 严格验证题目数量和 `idx=0..111`；
5. 生成只含 `idx`、`problem` 的临时 JSONL；
6. 调用 `main.py`；
7. 将结果保存到 `output/<UTC运行时间>/`；
8. 创建独立结果分支；
9. 提交结果并创建 Pull Request，不直接修改 `main`。

`answer`、`subject`、`source` 不会传入 `ReasoningAgent.solve`。

## 19.1 GitHub Actions 运行

仓库 Secret：

```text
INTERN_API_KEY
```

运行入口：

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

## 19.2 输出结构

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

该汇总只检查运行完整性，不是官方数学 Judge 分数。

## 19.3 本地运行

```bash
export INTERN_API_KEY="sk-..."
export INTERN_MODEL="intern-s2-preview"

python scripts/run_112_benchmark.py \
  --dataset-dir ../test-dataset-math/112 \
  --output-root output \
  --concurrency 3
```

也可指定运行目录：

```bash
python scripts/run_112_benchmark.py \
  --dataset-dir ../test-dataset-math/112 \
  --output-root output \
  --run-id 20260825T135011Z-local \
  --concurrency 3
```

已有且非空的运行目录不会被覆盖。

---

# 20. 分支与结果管理

所有人工代码修改：

```text
main
→ 新建功能分支
→ 提交修改
→ Pull Request
→ 审查后合并
```

112 题工作流结果：

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

# 21. 当前项目结构

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
        ├── tests.yml
        ├── run-dev.yml
        └── run-112-benchmark.yml
```

当前 baseline 仍用于接口和运行链路验证。HORA-Math 将按上述阶段逐步替换内部实现，同时保持：

```python
ReasoningAgent(client=official_client)
agent.solve(problem, metadata)
```

接口稳定。
