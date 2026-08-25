# HORA-Math 架构入口

本项目的目标架构为：

> **HORA-Math：异构正交求解—红队对抗攻击—证据裁决数学智能体**

完整名称：

> **Heterogeneous Orthogonal Reasoning with Red-Team Attacks and Evidence Adjudication**

---

## 文档导航

### 1. 前十方案综合

阅读：[`docs/TOP10_ARCHITECTURE_SYNTHESIS.md`](docs/TOP10_ARCHITECTURE_SYNTHESIS.md)

内容：

- 前十中哪些方案可以公开核验；
- 哪些队伍缺少可靠公开实现，因而不进行猜测；
- ChouCe、LemaMAV、JiuShao、ICMA、MathAgent 的高价值机制；
- 哪些机制被保留、改造或放弃；
- HORA-Math 的十五条架构不变量。

### 2. 执行级实现规范

阅读：[`docs/HORA_MATH_IMPLEMENTATION_SPEC.md`](docs/HORA_MATH_IMPLEMENTATION_SPEC.md)

内容：

- 分层状态图；
- `TaskContract`、`MethodFingerprint`、`SolutionCapsule`、`EvidenceRecord`、`Challenge`；
- 四级 Route Policy；
- 四类异构蓝队求解器；
- Orthogonality Gate；
- 数学答案规范化与等价归簇；
- Certificate Engine；
- 九类红队攻击；
- Claim Dependency Graph；
- Challenge Ledger；
- One-shot Cross Examination；
- One-shot Targeted Repair；
- Evidence Adjudicator；
- 十八学科策略矩阵；
- Runtime Guard、Safe Trace、Benchmark Telemetry；
- 目标目录、主流程伪代码和 Definition of Done。

### 3. 项目 README

阅读：[`README.md`](README.md)

README 记录赛事入口、目标架构概览、112 题运行方式、输出目录和分支管理规则。

---

## 核心架构

```text
Problem
  ↓
Task Contract + Risk Map
  ↓
Heterogeneous Blue Solvers
  ├─ Structural / Theorem
  ├─ Constructive / Definition Blind
  ├─ Tool-Integrated Symbolic
  └─ Numerical / Enumeration
  ↓
Orthogonality Gate
  ↓
Candidate Ledger + Claim Graph
  ↓
Canonicalization + Equivalence Clustering
  ↓
Certificate Engine
  ↓
Red-Team Attack Scheduler
  ├─ Assumption Attack
  ├─ Theorem-Precondition Attack
  ├─ Counterexample Attack
  ├─ Boundary / Degenerate Attack
  ├─ Transformation Attack
  ├─ Quantifier Attack
  ├─ Interpretation Attack
  ├─ Numerical Stress Attack
  └─ Completeness / Schema Attack
  ↓
Challenge Ledger
  ↓
Deterministic Local Resolver
  ↓
One-shot Cross Examination
  ↓
One-shot Targeted Repair if necessary
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

## 最高原则

1. **异构优先于数量**：不同候选必须使用不同推理范式、数学表示或工具通道。
2. **正交优先于投票**：同质重复不能伪装成独立支持。
3. **攻击必须具体**：红队必须攻击明确的 Candidate Claim。
4. **硬证据具有否决权**：一个可复现反例可以否决任意数量的软接受票。
5. **冲突局部化**：定位第一个分歧 Claim，而不是整题重做。
6. **Repair 保守且一次性**：保留 Verified Facts，修复后重验和重攻。
7. **证据足够立即停止**：低风险 Hard Pass 后 Early Stop。
8. **最终答案事务提交**：只有 Answer Normalizer 和 Transaction Commit 可以生成外部 `final_response`。

---

## 当前实现状态

当前 `user_agent.py` 仍是 generate–verify–select baseline。HORA-Math 需要按照以下阶段逐步落地：

```text
Phase 1
答案协议、数学等价、Candidate Ledger、Transaction Commit

Phase 2
符号、代回、residual、数值、枚举和多小问证书

Phase 3
MethodFingerprint、Orthogonality Gate、Blind Solver

Phase 4
Red-Team Attack Scheduler、Challenge Ledger、Local Resolver

Phase 5
Claim Graph、Cross Examination、Targeted Repair

Phase 6
112 题消融、静态 Route Policy 和正式版本冻结
```

任何阶段都必须通过独立功能分支、Pull Request 和 112 题消融进入 `main`。
