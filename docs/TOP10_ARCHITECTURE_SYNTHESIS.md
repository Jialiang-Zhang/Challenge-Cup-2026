# 前十方案架构综合与 HORA-Math 设计决策

> 状态：架构研究文档  
> 基准日期：2026-08-25  
> 适用项目：`Jialiang-Zhang/Challenge-Cup-2026`

本文只整理榜单前十中**能够公开核验**的仓库、README 或项目说明。无法读取源码或项目介绍的队伍只记录“未知”，不根据队名、分数或用户名猜测其内部设计。

---

## 1. 前十公开状态

| 排名 | 队伍 / 账号 | 分数 | 公开状态 | 本项目处理方式 |
|---:|---|---:|---|---|
| 1 | 梁子 / `clrh` | 88.39 | 存在公开仓库页面，但当前公开内容不足 | 不推测冠军内部架构，只记录其分数领先事实 |
| 2 | 中北大学 / `2401_88048876` | 83.93 | 可核验公开项目：ChouCe / 筹策 | 吸收方法级独立候选、Blind Solve、对抗审查、领域风险检查 |
| 3 | 不悲伤的折叠桌 / `weixin_72847500` | 80.36 | 未找到可可靠对应的公开实现 | 不推测 |
| 4 | NUDTAIMP / `zhoumuyan` | 73.21 | 可核验公开项目：LemaMAV | 吸收路由、引理记忆、验证、修复、选择和答案清洗 |
| 5 | 2123113231 的队伍 / `zcyyyy` | 72.32 | 可核验公开项目：JiuShao / 九韶 | 吸收 TIR、数值裁判、等价归簇、动态预算和消融实验思想 |
| 6 | 已读未回是在细品 / `whale-withme` | 72.32 | 未找到可可靠对应的公开实现 | 不推测 |
| 7 | 衡问 / `gcw_Pg97cPXk` | 70.54 | 未找到可可靠对应的公开实现 | 不推测 |
| 8 | `bur_xiaoz` 的队伍 | 68.75 | 未找到可可靠对应的公开实现 | 不推测 |
| 9 | CNZkeven | 66.96 | 可核验公开项目：ICMA | 吸收分类、LLM 与 SymPy 异构双路、交叉验证和冲突协调 |
| 10 | 陕西师范大学队伍 / `SONGXIA_YEJI` | 65.18 | 可核验公开项目：MathAgent | 吸收计算、证明和学科专家模块化 |

公开链接：

- ChouCe：<https://gitcode.com/2401_88048876/chouce-math-reasoning-agent>
- LemaMAV：<https://gitcode.com/NUDTAIMP/mathcode>
- JiuShao：<https://gitcode.com/zcyyyy/-Intern-S1-zcy>
- ICMA：<https://gitcode.com/CNZkeven/ICMA>
- MathAgent：<https://gitcode.com/SONGXIA_YEJI/math_agent>
- 冠军仓库页面：<https://gitcode.com/clrh/math-reasoning-agent>

---

## 2. 可核验方案的核心贡献

## 2.1 ChouCe：方法独立、盲解和对抗审查

高价值部分：

1. 不只是重复生成多个答案，而是要求候选采用不同数学方法；
2. Blind Solver 不读取主候选答案和推理，降低锚定偏差；
3. 使用对抗式审查主动寻找错误，而不是普通 Reflection；
4. 按学科和风险加载不同检查重点；
5. 将求解、验证和风险审查区分为不同职责。

HORA-Math 的落地：

```text
MethodFingerprint
Orthogonality Gate
Constructive Blind Solver
Red-Team Attack Scheduler
Domain Failure Skills
```

必须强化的地方：

- Blind 不仅要隔离上下文，还必须指定不同方法族；
- 对抗审查必须形成具体 `Challenge`，不能只输出“可能有问题”；
- 多候选一致只能作为支持证据，不能覆盖明确反例或 Hard Fail。

---

## 2.2 LemaMAV：引理记忆、验证、修复和选择

高价值部分：

1. 路由和规划决定解题路径；
2. 多个独立候选进入统一验证流程；
3. 将长推理压缩为可复用的 Lemma / Fact Memory；
4. 验证失败后进行 Repair；
5. 最后通过 Selector / Arbiter 选择候选；
6. 使用答案清洗或 Normalizer 保证提交格式。

HORA-Math 的落地：

```text
TaskContract
ClaimDependencyGraph
VerifiedFactStore
CandidateLedger
TargetedRepair
EvidenceAdjudicator
AnswerNormalizer
```

必须改进的地方：

- 不是所有题都需要 Planner；简单题应直接进入主解；
- Memory 只保存当前单题内已经验证的事实，不建立跨题状态；
- Repair 只能修复第一个 Fatal Claim 及后续，不允许无限循环；
- Repair 生成新候选，不能覆盖原候选；
- Repair 后必须重跑原攻击和原检查器。

---

## 2.3 JiuShao：TIR、数值裁判、等价归簇和消融

高价值部分：

1. Tool-Integrated Reasoning 将模型推理与数学工具连接；
2. 对数值或表达式结果构造 Judge / Certificate；
3. 对多种答案表示进行等价归簇；
4. 通过多链、单链、工具和 Judge 的实验比较真实收益；
5. 关注预算和不同 Profile 的成本效果。

HORA-Math 的落地：

```text
ToolRegistry
ComputationCertificate
MathematicalCanonicalizer
EquivalenceCluster
OfflineAblationPolicy
RuntimeBudget
```

必须吸取的教训：

- 多链不等于多方法；同质采样可能没有净增益；
- 投票前必须先做数学等价归一，否则等价答案会被拆散；
- 数值检查主要用于发现错误，不能自动替代理论证明；
- 所有工具异常只能标记为 `UNKNOWN`，不能直接判候选错误。

---

## 2.4 ICMA：LLM 与 SymPy 异构双路和冲突协调

公开项目说明给出的主流程是：

```text
分类
→ 双路并行求解
→ 交叉验证
→ 协调
```

并结合 LLM 推理和 Python/SymPy 符号计算。

HORA-Math 的落地：

```text
StructuralSolver
ToolIntegratedSolver
CertificateEngine
DisputeMapper
DeterministicLocalResolver
```

必须限制的地方：

- SymPy 只在其擅长的表达式、代数、微积分、矩阵和 residual 场景中作为强证据；
- 测度论、拓扑、抽象代数理论、泛函分析等题不能由 SymPy 统一裁决；
- 当 LLM 与工具冲突时，先定位具体 Claim，再决定哪一路失败；
- 不因工具解析失败而否决自然语言候选。

---

## 2.5 MathAgent：专家模块化

高价值部分：

1. 将分类、计算、证明等职责拆分；
2. 为不同数学问题维护专门 Prompt 和测试；
3. 工程目录清晰，便于增加专家能力。

HORA-Math 的落地：

```text
DomainPolicyRegistry
SolverCapabilityRegistry
AttackCapabilityRegistry
PromptTemplates
UnitTests
```

必须改进的地方：

- 专家模块不等于每个模块都调用一次模型；
- 大多数组件应是策略、规则、工具或 Prompt 模板；
- Router 使用软路由，不能成为单点故障；
- 混合学科题允许主领域和次领域同时存在。

---

## 3. 综合对比矩阵

| 能力 | ChouCe | LemaMAV | JiuShao | ICMA | MathAgent | HORA-Math 决策 |
|---|---|---|---|---|---|---|
| 方法多样性 | 强 | 多候选 | 多链实验 | 双路 | 专家分工 | 强制 MethodFingerprint 与 Orthogonality Gate |
| Blind 隔离 | 有 | 未作为唯一核心 | 非主要公开特征 | 无明确公开说明 | 无明确公开说明 | 高风险题默认使用上下文隔离的正交盲解 |
| 确定性工具 | 证书思想 | 可配验证器 | TIR / 数值 Judge | SymPy | SymPy / 专家工具 | Tool Registry + Certificate Engine |
| 对抗审查 | 强 | Verifier / Repair | Judge 反馈 | 交叉验证 | 专家检查 | 九类红队攻击 + Challenge Ledger |
| 引理记忆 | 非主要公开特征 | 核心 | 非主要公开特征 | 非主要公开特征 | 非主要公开特征 | 单题 VerifiedFactStore + Claim DAG |
| 数学等价 | 候选一致性 | 选择阶段 | 等价归簇 | 交叉验证 | 输出模块 | Canonicalizer + EquivalenceCluster |
| 冲突处理 | 对抗审查 | Repair / Arbiter | Judge 反馈 | Coordinator | 专家协调 | Dispute Mapper → Local Resolver → Cross Examination |
| 修复 | 有审查闭环 | 核心 | Judge 反馈 | Coordinator | 模块化处理 | One-shot Targeted Repair + Reattack |
| 动态预算 | 风险检查 | 预算允许时修复 | Profile / 实验 | 固定图较明显 | 专家路由 | Gated Escalation + Runtime Guard |
| 输出规范 | 风险与结果控制 | Answer Normalizer | 最终输出 | 格式化输出 | 输出模块 | Answer Schema + Transaction Commit |
| 消融实验 | 未完整公开 | 未完整公开 | 明确强调实验 | 未完整公开 | 测试目录 | 112 题离线消融和误杀率统计 |

---

## 4. 最终综合结论

前十公开方案共同说明，高分系统的关键不是“更多 Agent”，而是以下五类能力：

1. **候选错误尽量不相关**：使用不同数学方法、表示和工具；
2. **验证证据尽量硬**：代回、符号、数值、枚举、residual、反例和定理前提；
3. **冲突处理尽量局部**：定位第一个分歧 Claim，而不是整题重做；
4. **修复尽量保守**：保留 Verified Facts，修复后重新攻击；
5. **预算分配尽量自适应**：证据足够立即停止，高风险才进入深层攻防。

因此 HORA-Math 不采用：

```text
固定 N 个 Solver
→ 固定 N 个 Verifier
→ 多数投票
→ 整题 Reflection
```

而采用：

```text
Primary
→ 证书检查
→ 需要时才编译正交异构路线
→ 红队攻击关键 Claim
→ 工具优先解决挑战
→ 一次性交叉质询
→ 最多一次局部修复
→ 证据裁决
→ 冻结与事务提交
```

---

## 5. HORA-Math 必须满足的架构不变量

以下规则属于强制约束，而不是建议。

### INV-01：独立支持必须通过正交门

两个候选只有在方法指纹足够不同且第二候选未读取第一候选内容时，才能被记为独立支持。

### INV-02：一个硬反例可以否决任意数量的软投票

```text
Hard Counterexample
>
N 个 LLM 接受票
```

### INV-03：工具错误不是数学反证

工具解析、超时或异常只能产生 `UNKNOWN`。

### INV-04：红队必须攻击具体 Claim

没有 `candidate_id`、`claim_id`、攻击类型和最小理由的普通怀疑，不进入 Challenge Ledger。

### INV-05：Blind Solver 不得读取 Primary

包括答案、推理、关键 Claim、Verifier 意见和候选账本。

### INV-06：Repair 不能覆盖父候选

Repair 必须生成新候选并记录 `parent_candidate_id`。

### INV-07：Repair 后必须重验和重攻

原失败检查器和原 Fatal Challenge 必须重新执行。

### INV-08：每题最多一次 Repair

防止无限纠错循环、超时和推理漂移。

### INV-09：高风险理论题不能只依赖工具

必须包含定理前提、量词、边界或反例攻击。

### INV-10：低风险硬证书通过后应 Early Stop

不能因为预算尚未用完继续调用模型。

### INV-11：数学等价必须先于答案冲突

`-1/8`、`-\frac{1}{8}` 与 `-0.125` 不应直接产生三方争议。

### INV-12：最终答案只能由提交协议产生

Solver、Repair 和 Auditor 都不能直接写入外部 `final_response`。

### INV-13：Trace 不得保存敏感正文

Trace 只记录步骤、角色、候选编号、状态、长度、耗时、攻击类型和证据状态。

### INV-14：参考答案不能进入 Agent

112 题测试中的 `answer`、`subject` 和 `source` 不得进入 `ReasoningAgent.solve()`。

### INV-15：所有高级模块必须通过净收益消融

```text
Wrong → Correct
-
Correct → Wrong
-
超时和无效输出惩罚
```

净收益为负的模块不得因“架构高级”而保留。

---

## 6. 从公开方案进一步推导出的增强设计

以下内容不是对某个单独仓库的照搬，而是对公开机制的工程化综合。

## 6.1 Claim Dependency Graph

每个 Solution Capsule 应把推理压缩成关键 Claim 和依赖：

```text
C1 → C3
C2 → C3
C3 → FINAL
```

红队优先攻击所有通向最终答案的支配 Claim。一个上游 Fatal Claim 被击破后，不再浪费 Token 攻击其后续结论。

## 6.2 Attack Coverage Contract

不同风险等级必须满足最低攻击覆盖：

```text
LOW:
格式 + 边界轻检查

MEDIUM:
至少一个领域失败模式攻击
+ 一个确定性检查

HIGH:
正交盲解
+ 定理前提或反例攻击
+ 完整性攻击

CONFLICT:
第一个分歧 Claim 攻击
+ 局部工具解析
+ 必要时一次性交叉质询
```

## 6.3 Evidence Veto Rules

证据不是简单加权平均，而是有否决关系：

```text
Hard Fail
→ 候选原则上淘汰

Fatal Challenge SUSTAINED
→ 候选不可提交

Hard Pass + 无高风险缺口
→ 允许冻结

Orthogonal Agreement
→ 增加支持，但不能覆盖 Hard Fail

Generic LLM Approval
→ 只作为最低级软证据
```

## 6.4 Diversity Before Quantity

新增候选前必须检查：

```text
当前候选缺少什么证据？
新路线能否提供新的方法族、表示或工具通道？
新路线是否会重复已有错误？
```

不能回答上述问题时，不应生成新候选。

## 6.5 Attack Before Repair

系统必须先形成可复现的 Challenge，再允许修复。禁止仅凭模糊“不确定”触发整题重写。

---

## 7. 公开信息边界

本文中的方案总结仅基于公开仓库页面、README 或可检索项目说明。以下内容未被当作事实：

- 冠军仓库未公开部分的具体代码；
- 第 3、6、7、8 名的内部 Agent 数量、Prompt 或工具；
- 分数差异与某个单一模块之间的因果关系；
- 任意公开 README 未明确说明的隐藏实现。

后续如有新仓库公开，应通过独立功能分支更新本文件，并注明：

```text
来源链接
读取日期
对应 commit / 页面状态
新增或修正的结论
```
