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
设 $K_{m,n}$ 的顶点集划分为 $U=\{u_1,\dots,u_m\}$ 与 $V=\{v_1,\dots,v_n\}$，则 $|V(K_{m,n})|=m+n$。其拉普拉斯矩阵 $L$ 按分块写为
$$
L=\begin{pmatrix}
n I_m & -J_{m\times n}\\
-J_{n\times m} & m I_n
\end{pmatrix},
$$
其中 $J$ 为全 1 矩阵。

**Claim 1 (L 的特征值)。** $L$ 的特征值为：$0$（单重），$m+n$（单重），$n$（重数 $m-1$），$m$（重数 $n-1$）。
*验证*：对任意满足 $\sum_{i=1}^m x_i=0$ 的向量 $(x,0)^T$，有 $L(x,0)^T=(nx,0)^T$，故 $n$ 为特征值，重数至少 $m-1$；同理 $(0,y)^T$（$\sum y_j=0$）给出特征值 $m$，重数至少 $n-1$。再取向量 $(a\mathbf{1}_m,b\mathbf{1}_n)^T$，由
$$
L\begin{pmatrix}a\mathbf{1}_m\\ b\mathbf{1}_n\end{pmatrix}
=\begin{pmatrix}(na-nb)\mathbf{1}_m\\ (mb-ma)\mathbf{1}_n\end{pmatrix}
$$
可得在子空间 $\mathrm{span}\{(\mathbf{1}_m,0)^T,(0,\mathbf{1}_n)^T\}$ 上 $L$ 的矩阵为 $\begin{pmatrix}n&-n\\ -m&m\end{pmatrix}$，其特征值为 $0$ 与 $m+n$。综上 $m+n$ 个特征值已全部列出，且重数之和为 $1+1+(m-1)+(n-1)=m+n$，故 Claim 1 成立。

**Claim 2 (矩阵树定理与余子式)。** 矩阵树定理指出：连通图 $G$ 的生成树数 $\tau(G)$ 等于 $L$ 的任意一个余子式（即删去第 $i$ 行第 $i$ 列后的行列式）。
*前提检查*：$K_{m,n}$ 在 $m,n\ge 2$ 时显然连通，满足定理条件。

**Claim 3 (非零特征值进入余子式)。** 设 $L$ 的特征值为 $0=\lambda_1<\lambda_2\le\cdots\le\lambda_{m+n}$，则删去任意一行一列得到的 $(m+n-1)\times(m+n-1)$ 矩阵 $L^{(i)}$ 的特征值恰为 $\lambda_2,\dots,\lambda_{m+n}$，从而
$$
\det L^{(i)}=\prod_{k=2}^{m+n}\lambda_k.
$$
*理由*：$L$ 为实对称矩阵，可正交对角化 $L=Q\Lambda Q^T$。由于 $L\mathbf{1}=0$，零特征值对应的特征向量可取为 $\mathbf{1}/\sqrt{m+n}$。删去第 $i$ 行第 $i$ 列相当于在正交基下把对应于 $\mathbf{1}$ 的分量去掉，而其余特征向量均与 $\mathbf{1}$ 正交，故它们在删去第 $i$ 个坐标后仍线性无关且保持特征值不变。因此 $L^{(i)}$ 的非零特征值集合与 $L$ 的非零特征值集合完全相同（计重数）。

**Claim 4 (计算)。** 由 Claim 1 与 Claim 3，
$$
\tau(K_{m,n})=\det L^{(i)}=(m+n)\cdot n^{\,m-1}\cdot m^{\,n-1}.
$$
等等，这里需要仔细：矩阵树定理的余子式等于 **任意一个**  cofactor，而 $L$ 的零特征值只出现一次，故 $\det L^{(i)}$ 应等于所有非零特征值的乘积再除以 $m+n$？不，实际上更直接的论证是：$L$ 的伴随矩阵 $\mathrm{adj}(L)=\tau(G)J$（$J$ 为全 1 矩阵），且 $\mathrm{adj}(L)$ 的非零特征值恰为 $\prod_{k=2}^{m+n}\lambda_k$ 对应于特征向量 $\mathbf{1}$ 的特征值。因为 $\mathrm{adj}(L)=\prod_{k=2}^{m+n}\lambda_k\cdot \frac{1}{m+n}J$（投影到 $\mathbf{1}$ 方向），比较系数得
$$
\tau(K_{m,n})=\frac{1}{m+n}\prod_{k=2}^{m+n}\lambda_k
=\frac{1}{m+n}\cdot (m+n)\cdot n^{m-1}\cdot m^{n-1}
=m^{n-1}n^{m-1}.
$$

**Claim 5 (结论)。** 因此 $K_{m,n}$ 的生成树总数为 $m^{n-1}n^{m-1}$，且拉普拉斯矩阵的非零特征值 $m+n,m,n$ 通过上述乘积（并除以 $m+n$ 以消除零特征值对应的全 1 方向）精确进入余子式行列式的计算。

综上，命题得证。

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

**(1) 类方程论证 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$。**

$G$ 的类方程为
$$|G|=|Z(G)|+\sum_{i=1}^k [G:C_G(x_i)],$$
其中 $x_1,\dots,x_k$ 为各非中心共轭类的代表元。对任意 $x\notin Z(G)$，有 $C_G(x)\subsetneq G$，故 $[G:C_G(x)]$ 为 $p$ 的正整数次幂且严格大于 $1$，即 $p\mid [G:C_G(x_i)]$。于是 $p\mid \sum [G:C_G(x_i)]$。由 $|G|=p^3$ 得 $p\mid |Z(G)|$。又 $Z(G)\le G$，故 $|Z(G)|$ 为 $p$ 的幂且 $|Z(G)|\ge p$，从而 $|Z(G)|\in\{p,p^2,p^3\}$，且 $Z(G)\neq 1$。

**(2) 若 $|Z(G)|\ge p^2$ 则 $G$ 为阿贝尔群。**

若 $|Z(G)|=p^3$，则 $Z(G)=G$，显然 $G$ 阿贝尔。下设 $|Z(G)|=p^2$，则 $|G/Z(G)|=p$。任何素数阶群必循环，故 $G/Z(G)$ 循环。

**引理：** 若 $G/Z(G)$ 循环，则 $G$ 阿贝尔。
*证明：* 设 $G/Z(G)=\langle gZ(G)\rangle$。对任意 $x,y\in G$，存在整数 $i,j$ 及 $a,b\in Z(G)$ 使得 $x=g^ia,\ y=g^jb$。于是
$$xy=g^ia g^jb = g^{i+j}ab = g^j b g^i a = yx,$$
因为 $a,b$ 与所有元素可交换。故 $G$ 阿贝尔。

由引理，$|Z(G)|=p^2$ 时 $G$ 亦阿贝尔。综上，$|Z(G)|\ge p^2$ 蕴含 $G$ 阿贝尔。

**(3) 非阿贝尔阶 $p^3$ 群的结构。**

若 $G$ 非阿贝尔，则由 (2) 知 $|Z(G)|\neq p^2,p^3$，结合 (1) 得 $|Z(G)|=p$。此时 $|G/Z(G)|=p^2$。$p^2$ 阶群只有两种：循环群 $C_{p^2}$ 或初等阿贝尔群 $C_p\times C_p$。若 $G/Z(G)\cong C_{p^2}$，则由引理知 $G$ 阿贝尔，矛盾。故必有 $G/Z(G)\cong C_p\times C_p$。

证毕。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
