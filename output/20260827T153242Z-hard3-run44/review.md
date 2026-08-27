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
设 $K_{m,n}$ 的两部分顶点集为 $U=\{u_1,\dots,u_m\}$ 与 $V=\{v_1,\dots,v_n\}$。其拉普拉斯矩阵 $L$ 在按 $U$ 先、$V$ 后的分块下为
$$
L=\begin{pmatrix}
nI_m & -J_{m\times n}\\[2pt]
-J_{n\times m} & mI_n
\end{pmatrix},
$$
其中 $J$ 为全 1 矩阵。矩阵树定理要求计算 $L$ 的任意一个余子式，即删去一行一列后所得 $(m+n-1)\times(m+n-1)$ 矩阵的行列式。

**特征值分析。** 直接验证 $L$ 的特征向量：
- 对任意与 $\mathbf{1}_m$ 正交的 $x\in\mathbb{R}^m$，向量 $(x,0)^{\mathsf T}$ 满足 $L(x,0)^{\mathsf T}=n(x,0)^{\mathsf T}$，故 $n$ 是特征值，重数至少 $m-1$。
- 对任意与 $\mathbf{1}_n$ 正交的 $y\in\mathbb{R}^n$，向量 $(0,y)^{\mathsf T}$ 满足 $L(0,y)^{\mathsf T}=m(0,y)^{\mathsf T}$，故 $m$ 是特征值，重数至少 $n-1$。
- 在由 $(\mathbf{1}_m,0)^{\mathsf T}$ 与 $(0,\mathbf{1}_n)^{\mathsf T}$ 张成的二维子空间上，$L$ 的矩阵表示为 $\begin{pmatrix}n&-m\\-n&m\end{pmatrix}$，其特征值为 $0$ 与 $m+n$。

因此 $L$ 的全部特征值为
$$
0,\quad m+n,\quad n\ (\text{重数 }m-1),\quad m\ (\text{重数 }n-1).
$$

**余子式与特征值的关系。** 设 $L$ 的特征值为 $0=\lambda_1<\lambda_2\le\cdots\le\lambda_{m+n}$。对拉普拉斯矩阵，所有余子式相等，且等于 $\frac{1}{m+n}\prod_{i=2}^{m+n}\lambda_i$（即伪行列式的 $\frac1{m+n}$）。更直接地，若删去对应于全 1 特征向量的一行一列，则所得矩阵的特征值恰为 $\lambda_2,\dots,\lambda_{m+n}$，故其行列式为
$$
\prod_{i=2}^{m+n}\lambda_i=(m+n)\cdot n^{\,m-1}\cdot m^{\,n-1}.
$$
再除以顶点总数 $m+n$（因为每个生成树在 $m+n$ 个顶点处被重复计数一次），得到生成树数目
$$
\tau(K_{m,n})=\frac{(m+n)\,n^{\,m-1}m^{\,n-1}}{m+n}=m^{\,n-1}n^{\,m-1}.
$$

**严格说明非零特征值的进入方式：** 矩阵树定理中的余子式 $\det L_{ii}$ 等于 $L$ 的伴随矩阵 $\operatorname{adj}(L)$ 的对角元。由于 $L\mathbf{1}=0$ 且 $L$ 对称，$\operatorname{adj}(L)=c\,J$（$J$ 为全 1 矩阵），其中 $c$ 为任意非零余子式的值。另一方面，对对称矩阵 $L$，有 $\operatorname{adj}(L)=\prod_{i=2}^{m+n}\lambda_i\cdot \frac{\mathbf{1}\mathbf{1}^{\mathsf T}}{m+n}$，从而 $c=\frac{1}{m+n}\prod_{i=2}^{m+n}\lambda_i$。这严格表明：拉普拉斯矩阵的全部非零特征值之积除以顶点数，恰等于任一余子式的值，亦即生成树总数。

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

**(1) 类方程论证 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$。**

$G$ 的类方程为
$$|G|=|Z(G)|+\sum_{i=1}^k [G:C_G(x_i)],$$
其中 $x_1,\dots,x_k$ 为各非中心共轭类的代表元。对任意 $x\notin Z(G)$，有 $C_G(x)\subsetneq G$，且 $Z(G)\subseteq C_G(x)$，故 $|C_G(x)|$ 为 $p^3$ 的真因子且至少为 $p$（因 $Z(G)$ 至少含单位元，而 $C_G(x)$ 至少包含 $\langle x\rangle$ 与 $Z(G)$）。于是 $[G:C_G(x_i)]\in\{p,p^2\}$，特别地 $p\mid [G:C_G(x_i)]$。

由类方程得 $p^3=|Z(G)|+\sum p\cdot(\text{整数})$，故 $p\mid |Z(G)|$。又 $|Z(G)|$ 整除 $|G|=p^3$，所以 $|Z(G)|\in\{p,p^2,p^3\}$，且 $|Z(G)|\ge p>1$，即 $Z(G)\neq 1$。

**(2) 若 $|Z(G)|\ge p^2$ 则 $G$ 为阿贝尔群。**

- 若 $|Z(G)|=p^3$，则 $Z(G)=G$，显然 $G$ 阿贝尔。
- 若 $|Z(G)|=p^2$，则 $|G/Z(G)|=p$，故 $G/Z(G)$ 为 $p$ 阶循环群。下面证明：**若 $G/Z(G)$ 循环，则 $G$ 阿贝尔**。设 $G/Z(G)=\langle gZ(G)\rangle$，则任意 $a,b\in G$ 可写成 $a=g^i z_1,\ b=g^j z_2$（$z_1,z_2\in Z(G)$）。于是
$$ab=g^i z_1 g^j z_2=g^{i+j}z_1z_2=g^j z_2 g^i z_1=ba,$$
因为 $z_1,z_2$ 与所有元素可交换。故 $G$ 阿贝尔。

因此 $|Z(G)|=p^2$ 不可能出现在非阿贝尔群中。

**(3) 非阿贝尔阶 $p^3$ 群的结构。**

若 $G$ 非阿贝尔，由 (1) 知 $|Z(G)|\in\{p,p^2,p^3\}$，由 (2) 排除 $p^2$ 与 $p^3$，故 $|Z(G)|=p$。此时 $|G/Z(G)|=p^2$。已知阶为 $p^2$ 的群必为阿贝尔，且只能是 $C_{p^2}$ 或 $C_p\times C_p$。若 $G/Z(G)\cong C_{p^2}$（循环），则由 (2) 的引理知 $G$ 阿贝尔，矛盾。故 $G/Z(G)\cong C_p\times C_p$。

综上，任意非阿贝尔阶 $p^3$ 群满足 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
