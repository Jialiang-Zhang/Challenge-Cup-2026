# HORA-Math hard3 review

> The reference answers are public benchmark data and were never passed to the agent.
> Automated relation checks are heuristic; inspect proof logic manually.

## idx 0 — 离散数学

- Status: `success`
- Route: `R2`
- Model calls: `3`
- Repair count: `0`
- Local reference relation: `unknown`

### Problem

设$m,n\ge 2$。利用矩阵树定理而不是递推或直接枚举，求完全二分图$K_{m,n}$的生成树总数，并严格说明拉普拉斯矩阵的非零特征值如何进入余子式行列式的计算。

### Agent final response

结论：完全二分图 $K_{m,n}$ 的生成树总数为 $m^{\,n-1}n^{\,m-1}$。

证明过程：
设 $K_{m,n}$ 的两部分顶点集为 $U=\{u_1,\dots,u_m\}$ 与 $V=\{v_1,\dots,v_n\}$。其拉普拉斯矩阵 $L$ 按分块写为
$$
L=\begin{pmatrix}
nI_m & -J_{m\times n}\\[2pt]
-J_{n\times m} & mI_n
\end{pmatrix},
$$
其中 $J$ 为全 1 矩阵。矩阵树定理要求计算 $L$ 的任意一个余子式（即删去一行一列后的行列式）。

**特征值分析。** 直接验证可得 $L$ 的特征值：
- 对任意满足 $\sum x_i=0$ 的向量 $(x,0)^\top$，有 $L(x,0)^\top=n(x,0)^\top$，故 $n$ 是特征值，重数至少 $m-1$；
- 对任意满足 $\sum y_j=0$ 的向量 $(0,y)^\top$，有 $L(0,y)^\top=m(0,y)^\top$，故 $m$ 是特征值，重数至少 $n-1$；
- 在由全 1 向量张成的二维子空间上，$L$ 的作用矩阵为 $\begin{pmatrix}n&-n\\-m&m\end{pmatrix}$，其特征值为 $0$ 与 $m+n$。

因此 $L$ 的全部特征值为
$$
0,\quad m+n,\quad n\ (\text{重数 }m-1),\quad m\ (\text{重数 }n-1).
$$

**余子式与特征值的关系。** 设 $L$ 的特征值为 $0=\lambda_1<\lambda_2\le\cdots\le\lambda_{m+n}$。伴随矩阵 $\operatorname{adj}(L)$ 在 $L$ 秩为 $N-1$ 时等于 $\prod_{i=2}^N\lambda_i\cdot \frac{1}{N}\mathbf{1}\mathbf{1}^\top$（其中 $\mathbf{1}$ 为全 1 向量），从而每个对角余子式 $M_{ii}$ 都等于 $\frac{1}{N}\prod_{i=2}^N\lambda_i$。对 $K_{m,n}$ 有 $N=m+n$，故
$$
\tau(K_{m,n})=\frac{1}{m+n}\cdot (m+n)\cdot n^{\,m-1}\cdot m^{\,n-1}=m^{\,n-1}n^{\,m-1}.
$$

这里非零特征值进入余子式的方式正是：余子式等于所有非零特征值之积除以顶点数 $m+n$，而 $m+n$ 恰好与唯一的非零大特征值相消，留下 $m^{n-1}n^{m-1}$。

### Public reference answer

设$K_{m,n}$的拉普拉斯矩阵为$L$。其谱为$0$（重数1）、$m$（重数$n-1$）、$n$（重数$m-1$）、$m+n$（重数1）。对任意$n+m$阶图拉普拉斯矩阵，矩阵树定理与非零谱给出$\tau(G)=\frac{1}{m+n}\prod_{\lambda_i\ne0}\lambda_i$。因此$\tau(K_{m,n})=\frac{1}{m+n}m^{n-1}n^{m-1}(m+n)=m^{n-1}n^{m-1}$。谱的求法可由分别考察两侧顶点和为零的子空间以及两侧常数向量张成的二维子空间得到。

## idx 40 — 测度积分

- Status: `success`
- Route: `R2`
- Model calls: `3`
- Repair count: `0`
- Local reference relation: `equivalent`

### Problem

设$(X,\mathcal M,\mu)$为有限测度空间，$1\le p<\infty$，且$f_n,f\in L^p(X)$。关于“弱收敛与范数收敛是否推出强收敛”，下列说法哪些正确？（多选）\nA. 若$1<p<\infty$，$f_n\rightharpoonup f$于$L^p$且$\|f_n\|_p\to\|f\|_p$，则$\|f_n-f\|_p\to0$。\nB. A的结论本质上利用了$L^p$在$1<p<\infty$时的一致凸性。\nC. 当$p=1$时同样成立。\nD. 在$L^1(0,1)$中可构造$f_n\rightharpoonup1$且$\|f_n\|_1=\|1\|_1=1$，但$\|f_n-1\|_1$不趋于0。

### Agent final response

最终答案：A,B,D

### Public reference answer

A,B,D

## idx 70 — 抽象代数

- Status: `success`
- Route: `R2`
- Model calls: `3`
- Repair count: `0`
- Local reference relation: `unknown`

### Problem

设$G$为阶$p^3$的有限群，$p$为素数。证明$Z(G)\neq1$且$|Z(G)|\in\{p,p^2,p^3\}$；进一步证明若$|Z(G)|\ge p^2$则$G$必为阿贝尔群；因此任意非阿贝尔阶$p^3$群都有$|Z(G)|=p$且$G/Z(G)\cong C_p\times C_p$。要求给出类方程论证，并说明为什么$G/Z(G)$循环会迫使$G$阿贝尔。

### Agent final response

结论：设 $G$ 为阶 $p^3$ 的有限群，$p$ 为素数。则 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$；若 $|Z(G)|\ge p^2$ 则 $G$ 必为阿贝尔群；因此任意非阿贝尔阶 $p^3$ 群都有 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

证明过程：
**证明：**

**(1) $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$（类方程论证）**

$G$ 的类方程为
$$|G|=|Z(G)|+\sum_{i=1}^k [G:C_G(x_i)],$$
其中 $x_1,\dots,x_k$ 为各非平凡共轭类的代表元，$C_G(x_i)$ 为 $x_i$ 的中心化子。因为 $x_i\notin Z(G)$，故 $C_G(x_i)\subsetneq G$，从而 $[G:C_G(x_i)]$ 是 $|G|=p^3$ 的真因子且大于 $1$，必为 $p$ 或 $p^2$。于是 $p\mid [G:C_G(x_i)]$ 对所有 $i$ 成立。由类方程得
$$p^3=|Z(G)|+\sum_{i=1}^k [G:C_G(x_i)],$$
右端求和项被 $p$ 整除，故 $p\mid |Z(G)|$。又 $Z(G)\le G$，由 Lagrange 定理 $|Z(G)|$ 整除 $p^3$，所以 $|Z(G)|\in\{p,p^2,p^3\}$，且 $|Z(G)|\ge p$，即 $Z(G)\neq 1$。

**(2) 若 $|Z(G)|\ge p^2$ 则 $G$ 为阿贝尔群**

- 若 $|Z(G)|=p^3$，则 $Z(G)=G$，显然 $G$ 阿贝尔。
- 若 $|Z(G)|=p^2$，则 $|G/Z(G)|=p$。任何素数阶群必循环，故 $G/Z(G)$ 循环。

**引理：** 若 $G/Z(G)$ 循环，则 $G$ 阿贝尔。  
*证明：* 设 $G/Z(G)=\langle gZ(G)\rangle$。任取 $x,y\in G$，可写 $x=g^a z_1$，$y=g^b z_2$，其中 $z_1,z_2\in Z(G)$。则
$$xy=g^a z_1 g^b z_2=g^{a+b}z_1z_2=g^b z_2 g^a z_1=yx,$$$
因为 $z_1,z_2$ 与所有元素可换且 $g$ 的幂次可交换。故 $G$ 阿贝尔。

由此，$|Z(G)|=p^2$ 时 $G$ 亦阿贝尔。综上，$|Z(G)|\ge p^2$ 蕴含 $G$ 阿贝尔。

**(3) 非阿贝尔阶 $p^3$ 群的结构**

若 $G$ 非阿贝尔，则由 (2) 知 $|Z(G)|\neq p^2$ 且 $|Z(G)|\neq p^3$，结合 (1) 得 $|Z(G)|=p$。此时 $|G/Z(G)|=p^2$。$p^2$ 阶群只有两种：循环群 $C_{p^2}$ 或初等阿贝尔群 $C_p\times C_p$。若 $G/Z(G)\cong C_{p^2}$，则由引理知 $G$ 阿贝尔，矛盾。故 $G/Z(G)\cong C_p\times C_p$。

**结论：** 任意非阿贝尔阶 $p^3$ 群满足 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
