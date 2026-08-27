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

结论：完全二分图 $K_{m,n}$ 的生成树总数为 $m^{n-1}n^{m-1}$。

证明过程：
设 $K_{m,n}$ 的顶点划分为 $U=\{u_1,\dots,u_m\}$ 与 $V=\{v_1,\dots,v_n\}$，总顶点数 $N=m+n$。其拉普拉斯矩阵 $L$ 按分块写为
$$
L=\begin{pmatrix}
n I_m & -J_{m\times n}\\[2pt]
-J_{n\times m} & m I_n
\end{pmatrix},
$$
其中 $J$ 为全 1 矩阵。

**Claim 1 (特征值分解)。** 向量 $\mathbf{1}_N$ 满足 $L\mathbf{1}_N=0$，故 $0$ 是 $L$ 的特征值。对任意与 $\mathbf{1}_N$ 正交的向量 $(x;y)$（即 $\sum x_i+\sum y_j=0$），由
$$
L\begin{pmatrix}x\\y\end{pmatrix}=\begin{pmatrix}nx-(\sum y_j)\mathbf{1}_m\\ my-(\sum x_i)\mathbf{1}_n\end{pmatrix}
=\begin{pmatrix}nx+(\sum x_i)\mathbf{1}_m\\ my+(\sum y_j)\mathbf{1}_n\end{pmatrix}
$$
可验证：若 $x$ 在 $U$ 上满足 $\sum x_i=0$ 且 $y=0$，则特征值为 $n$，此类向量有 $m-1$ 个；若 $y$ 在 $V$ 上满足 $\sum y_j=0$ 且 $x=0$，则特征值为 $m$，此类向量有 $n-1$ 个。最后，在由 $(\frac{1}{m}\mathbf{1}_m;-\frac{1}{n}\mathbf{1}_n)$ 张成的 1 维正交补上，直接计算得特征值 $m+n$。因此 $L$ 的非零特征值为
$$
\underbrace{n,\dots,n}_{m-1\text{ 次}},\quad \underbrace{m,\dots,m}_{n-1\text{ 次}},\quad m+n.
$$

**Claim 2 (矩阵树定理与余子式)。** 矩阵树定理指出生成树数 $\tau(G)$ 等于 $L$ 的任意一个余子式 $\det L(i|i)$。对对称矩阵，若 $0$ 为单特征值，则所有非零特征值的乘积等于 $N$ 乘以任意余子式（因为 $L$ 的特征多项式在 $\lambda=0$ 处的导数恰为各余子式之和，而所有余子式相等）。于是
$$
\tau(K_{m,n})=\frac{1}{m+n}\prod_{\lambda_i\neq 0}\lambda_i
=\frac{1}{m+n}\cdot n^{\,m-1}\cdot m^{\,n-1}\cdot (m+n)
=m^{\,n-1}n^{\,m-1}.
$$

**Claim 3 (严格说明非零特征值进入余子式)。** 设 $L=Q\operatorname{diag}(0,\lambda_2,\dots,\lambda_N)Q^T$ 为正交对角化。删去第 $i$ 行第 $i$ 列相当于在二次型中固定第 $i$ 个坐标为 0，对应于在特征基下投影到该坐标超平面。由 Cauchy–Binet 或矩阵行列式引理，$\det L(i|i)$ 等于 $\frac{1}{N}\prod_{j=2}^N\lambda_j$（因为 $L$ 的秩为 $N-1$ 且零特征值对应的特征向量为 $\mathbf{1}_N$，其在各坐标分量相同，故每个余子式获得相同的权重 $1/N$）。因此非零特征值以乘积形式完整进入余子式行列式，再除以 $N$ 即得生成树计数。

综上，$K_{m,n}$ 的生成树总数为 $m^{n-1}n^{m-1}$。

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
其中 $x_1,\dots,x_k$ 为各非中心共轭类的代表元。对任意 $x\notin Z(G)$，$C_G(x)$ 是 $G$ 的真子群，故 $[G:C_G(x)]$ 为 $p$ 的正整数次幂且 $>1$，即被 $p$ 整除。于是 $p\mid |G|$ 且 $p$ 整除所有非中心类的大小，故 $p\mid |Z(G)|$。因 $Z(G)\le G$，由 Lagrange 定理 $|Z(G)|$ 必为 $p^3$ 的因子，所以 $|Z(G)|\in\{p,p^2,p^3\}$，特别地 $Z(G)\neq 1$。

**(2) 若 $|Z(G)|\ge p^2$ 则 $G$ 为阿贝尔群**

- 若 $|Z(G)|=p^3$，则 $Z(G)=G$，显然 $G$ 阿贝尔。
- 若 $|Z(G)|=p^2$，则 $|G/Z(G)|=p$，故 $G/Z(G)$ 为循环群。设 $G/Z(G)=\langle gZ(G)\rangle$。对任意 $x,y\in G$，存在整数 $i,j$ 及 $a,b\in Z(G)$ 使 $x=g^i a,\ y=g^j b$。由于 $a,b$ 与所有元素可交换且 $g^i$ 与 $g^j$ 可交换，得
$$xy=g^i a\, g^j b=g^{i+j}ab=g^j b\, g^i a=yx.$$
故 $G$ 阿贝尔。此即"$G/Z(G)$ 循环迫使 $G$ 阿贝尔"的标准论证。

**(3) 非阿贝尔阶 $p^3$ 群的结构**

若 $G$ 非阿贝尔，则 $|Z(G)|\neq p^3$ 且由 (2) 知 $|Z(G)|\neq p^2$，故只能 $|Z(G)|=p$。此时 $|G/Z(G)|=p^2$。已知阶 $p^2$ 的群必阿贝尔，且只能是 $C_{p^2}$ 或 $C_p\times C_p$。若 $G/Z(G)\cong C_{p^2}$ 为循环，则由 (2) 的论证 $G$ 将为阿贝尔，矛盾。因此 $G/Z(G)\cong C_p\times C_p$。

综上，所有要求得证。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
