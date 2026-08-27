# HORA-Math hard3 review

> The reference answers are public benchmark data and were never passed to the agent.
> Automated relation checks are heuristic; inspect proof logic manually.

## idx 0 — 离散数学

- Status: `success`
- Route: `R2`
- Model calls: `4`
- Repair count: `1`
- Local reference relation: `unknown`

### Problem

设$m,n\ge 2$。利用矩阵树定理而不是递推或直接枚举，求完全二分图$K_{m,n}$的生成树总数，并严格说明拉普拉斯矩阵的非零特征值如何进入余子式行列式的计算。

### Agent final response

结论：完全二分图 $K_{m,n}$ 的生成树总数为 $m^{\,n-1}\,n^{\,m-1}$。

证明过程：
**结论**：完全二分图 $K_{m,n}$（$m,n\ge2$）的生成树总数为 $\tau(K_{m,n})=m^{\,n-1}n^{\,m-1}$。

**证明**：
1. **拉普拉斯矩阵的构造**。将 $K_{m,n}$ 的顶点分为两部 $U=\{u_1,\dots,u_m\}$ 与 $V=\{v_1,\dots,v_n\}$。每个 $u_i$ 的度为 $n$，每个 $v_j$ 的度为 $m$。于是拉普拉斯矩阵 $L$ 为
   $$
   L=\begin{pmatrix}nI_m&-J_{m\times n}\\-J_{n\times m}&mI_n\end{pmatrix},
   $$
   其中 $J$ 表示相应大小的全 1 矩阵。显然 $L$ 对称且行和为 0，故 $L\mathbf 1=0$，0 是特征值。

2. **求 $L$ 的谱**。考虑向量空间分解 $\mathbb R^{m+n}=\mathbb R^m\oplus\mathbb R^n$。
   - 对任意 $\mathbf x\in\mathbb R^m$ 满足 $\sum x_i=0$，取 $\mathbf y=\mathbf 0$，则 $L(\mathbf x,\mathbf 0)=(n\mathbf x,\mathbf 0)$，故 $n$ 是特征值，重数至少 $m-1$。
   - 同理，对 $\mathbf y\in\mathbb R^n$ 满足 $\sum y_j=0$，取 $\mathbf x=\mathbf 0$，得 $L(\mathbf 0,\mathbf y)=(\mathbf 0,m\mathbf y)$，故 $m$ 是特征值，重数至少 $n-1$。
   - 剩余二维子空间由 $(\mathbf 1_m,\mathbf 0)$ 与 $(\mathbf 0,\mathbf 1_n)$ 张成。在该基下，$L$ 的限制矩阵为
     $$
     \begin{pmatrix}n&-n\\-m&m\end{pmatrix},
     $$
     其特征值为 $0$ 与 $m+n$（对应特征向量 $(\mathbf 1_m,\mathbf 1_n)$）。
   - 综上，$L$ 的全部特征值为
     $$
     0\;(1\text{ 次}),\quad m\;(n-1\text{ 次}),\quad n\;(m-1\text{ 次}),\quad m+n\;(1\text{ 次}).
     $$

3. **矩阵树定理的应用**。矩阵树定理（Matrix-Tree Theorem）指出：对任意无向图 $G$，其生成树数 $\tau(G)$ 等于拉普拉斯矩阵 $L$ 的任意一个余子式，即
   $$
   \tau(G)=\det L_{ii},
   $$
   其中 $L_{ii}$ 为删除第 $i$ 行第 $i$ 列后的 $(N-1)\times(N-1)$ 矩阵（$N$ 为顶点数）。进一步，若 $L$ 的非零特征值为 $\lambda_2,\dots,\lambda_N$，则
   $$
   \det L_{ii}=\frac1N\prod_{k=2}^N\lambda_k.
   $$
   该式来源于 $L$ 的谱分解：$L$ 的伴随矩阵 $\operatorname{adj}(L)$ 等于 $\frac1N\prod_{k=2}^N\lambda_k\cdot \mathbf 1\mathbf 1^{\mathsf T}$，而 $\det L_{ii}$ 恰为 $\operatorname{adj}(L)$ 的对角元。

4. **代入计算**。对 $K_{m,n}$，顶点数 $N=m+n$，非零特征值乘积为
   $$
   (m+n)\cdot m^{\,n-1}\cdot n^{\,m-1}.
   $$
   因此
   $$
   \tau(K_{m,n})=\frac1{m+n}\cdot(m+n)\,m^{\,n-1}\,n^{\,m-1}=m^{\,n-1}n^{\,m-1}.
   $$

5. **验证小例**。当 $m=n=2$ 时，$K_{2,2}$ 为 4-环，生成树数为 $2^{1}2^{1}=4$，与直接删去任一边得到的 4 棵生成树一致。

故由矩阵树定理严格推导，$K_{m,n}$ 的生成树总数为 $m^{\,n-1}n^{\,m-1}$。证毕。

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

结论：对任意阶为 $p^3$ 的有限群 $G$（$p$ 为素数），有 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$；若 $|Z(G)|\ge p^2$ 则 $G$ 必为阿贝尔群；因此任意非阿贝尔阶 $p^3$ 群满足 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

证明过程：
**结论**：设 $|G|=p^3$（$p$ 素数），则 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$；若 $|Z(G)|\ge p^2$ 则 $G$ 必为阿贝尔群；故非阿贝尔的 $p^3$ 阶群必有 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

**证明**：

*Step 1（类方程论证）*。$G$ 的类方程为
$$|G|=|Z(G)|+\sum_{i} [G:C_G(x_i)],$$
其中 $x_i$ 取遍各非中心共轭类的代表元。因 $|G|=p^3$，每个 $[G:C_G(x_i)]$ 是 $p$ 的幂且 $>1$，故必被 $p$ 整除。于是
$$|Z(G)|\equiv |G|\equiv 0\pmod p,$$
得 $p\mid |Z(G)|$。又 $Z(G)\le G$，故 $|Z(G)|\in\{p,p^2,p^3\}$，且 $Z(G)\neq 1$。

*Step 2（$|Z(G)|\ge p^2$ 迫使 $G$ 阿贝尔）*。若 $|Z(G)|=p^3$，则 $G=Z(G)$ 显然阿贝尔。若 $|Z(G)|=p^2$，则商群 $G/Z(G)$ 的阶为 $p$，必为循环群 $C_p$。利用标准引理：

> **引理**：若 $G/Z(G)$ 循环，则 $G$ 为阿贝尔群。  
> *证明*：设 $G/Z(G)=\langle xZ(G)\rangle$。任取 $g,h\in G$，存在 $i,j\in\mathbb Z$ 及 $z_1,z_2\in Z(G)$ 使 $g=x^i z_1,\; h=x^j z_2$。则
> $$gh=x^i z_1 x^j z_2=x^{i+j}z_1z_2=x^j x^i z_2 z_1=hg,$$
> 因 $z_1,z_2$ 与一切元素可交换。故 $G$ 交换。

由此，$|Z(G)|=p^2$ 时 $G$ 必阿贝尔。综上，$|Z(G)|\ge p^2$ 均蕴含 $G$ 阿贝尔。

*Step 3（非阿贝尔情形）*。若 $G$ 非阿贝尔，则 $|Z(G)|\neq p^2,p^3$，结合 Step 1 只能有 $|Z(G)|=p$。此时 $|G/Z(G)|=p^2$。阶为 $p^2$ 的群只有两种：循环群 $C_{p^2}$ 与初等阿贝尔群 $C_p\times C_p$。若 $G/Z(G)\cong C_{p^2}$，则 $G/Z(G)$ 循环，由引理得 $G$ 阿贝尔，矛盾。故必有
$$G/Z(G)\cong C_p\times C_p.$$

至此，所有要求均已证毕。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
