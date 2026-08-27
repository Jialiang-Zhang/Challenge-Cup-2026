# HORA-Math hard3 review

> The reference answers are public benchmark data and were never passed to the agent.
> Automated relation checks are heuristic; inspect proof logic manually.

## idx 0 — 离散数学

- Status: `success`
- Route: `R2`
- Model calls: `4`
- Repair count: `0`
- Local reference relation: `unknown`

### Problem

设$m,n\ge 2$。利用矩阵树定理而不是递推或直接枚举，求完全二分图$K_{m,n}$的生成树总数，并严格说明拉普拉斯矩阵的非零特征值如何进入余子式行列式的计算。

### Agent final response

结论：完全二分图 $K_{m,n}$ 的生成树总数为 $m^{\,n-1}\,n^{\,m-1}$。

证明过程：
设 $K_{m,n}$ 的顶点划分为 $U=\{u_1,\dots,u_m\}$ 与 $V=\{v_1,\dots,v_n\}$，总顶点数 $N=m+n$。其拉普拉斯矩阵 $L$ 按分块写为
$$
L=\begin{pmatrix}
n I_m & -J_{m\times n}\\[2pt]
-J_{n\times m} & m I_n
\end{pmatrix},
$$
其中 $J$ 为全 1 矩阵。由矩阵树定理，生成树数 $\tau(K_{m,n})$ 等于 $L$ 的任意一个余子式的值，也等于 $\frac1N\prod_{i=1}^{N-1}\lambda_i$，其中 $\lambda_1,\dots,\lambda_{N-1}$ 是 $L$ 的非零特征值（$L$ 恒有单零特征值对应全 1 向量）。

**特征值计算。** 对形如 $\begin{pmatrix}A&B\\C&D\end{pmatrix}$ 的分块矩阵，若 $D$ 可逆，则
$$
\det\begin{pmatrix}A&B\\C&D\end{pmatrix}=\det(D)\det(A-BD^{-1}C).
$$
对特征多项式 $\det(L-\lambda I)$ 取 $A=(n-\lambda)I_m$, $D=(m-\lambda)I_n$, $B=C^\top=-J$，当 $\lambda\neq m$ 时得到
$$
\det(L-\lambda I)=(m-\lambda)^n\det\!\Bigl((n-\lambda)I_m-\frac{1}{m-\lambda}J_m\Bigr).
$$
利用 $J_m$ 的特征值为 $m$（重数 1）和 $0$（重数 $m-1$），上式化为
$$
\det(L-\lambda I)=(m-\lambda)^{n-1}(n-\lambda)^{m-1}\bigl((n-\lambda)(m-\lambda)-mn\bigr).
$$
而 $(n-\lambda)(m-\lambda)-mn=\lambda^2-(m+n)\lambda=\lambda(\lambda-(m+n))$。故
$$
\det(L-\lambda I)=\lambda\,(m-\lambda)^{n-1}(n-\lambda)^{m-1}(\lambda-(m+n)).
$$
于是 $L$ 的特征值为：$0$（单重），$m$（重数 $n-1$），$n$（重数 $m-1$），以及 $m+n$（单重）。非零特征值恰为 $m$（$n-1$ 次）、$n$（$m-1$ 次）、$m+n$（1 次）。

**进入余子式的说明。** 矩阵树定理的谱形式给出
$$
\tau(G)=\frac1N\lambda_1\lambda_2\cdots\lambda_{N-1}.
$$
该式源于：若 $L$ 的特征值为 $0,\lambda_1,\dots,\lambda_{N-1}$，则伴随矩阵 $\operatorname{adj}(L)=\prod_{i=1}^{N-1}\lambda_i\cdot\frac1N J$（因为 $L$ 对称且零空间由 $\mathbf 1$ 张成），而每个对角余子式 $\det L(i,i)$ 恰为 $\operatorname{adj}(L)_{ii}$，故等于 $\frac1N\prod_{i=1}^{N-1}\lambda_i$。因此非零特征值以乘积形式除以 $N$ 后直接进入余子式行列式的计算。

代入 $K_{m,n}$ 的非零特征值得
$$
\tau(K_{m,n})=\frac1{m+n}\cdot m^{\,n-1}\cdot n^{\,m-1}\cdot(m+n)=m^{\,n-1}n^{\,m-1}.
$$
验证：当 $m=n=2$ 时得 $2^{1}2^{1}=4$，与 $K_4$ 去掉同部边后的 4 棵生成树一致；当 $m=2,n=3$ 时得 $2^{2}3^{1}=12$，亦符合已知结果。证毕。

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

结论：设 $G$ 为阶 $p^3$ 的有限群（$p$ 为素数）。则 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$；若 $|Z(G)|\ge p^2$ 则 $G$ 必为阿贝尔群；因此任意非阿贝尔阶 $p^3$ 群满足 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

证明过程：
**证明：**

**(1) $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$（类方程论证）**

$G$ 的类方程为
$$|G|=|Z(G)|+\sum_{i=1}^k [G:C_G(x_i)],$$
其中 $x_1,\dots,x_k$ 为各非中心共轭类的代表元。对任意 $x\notin Z(G)$，有 $C_G(x)\subsetneq G$，故 $[G:C_G(x)]$ 为 $|G|=p^3$ 的真因子且大于 $1$，必被 $p$ 整除。于是类方程模 $p$ 给出
$$p^3\equiv |Z(G)|\pmod p,$$
从而 $p\mid |Z(G)|$。因 $Z(G)\le G$，由 Lagrange 定理 $|Z(G)|$ 为 $p^3$ 的因子，故 $|Z(G)|\in\{p,p^2,p^3\}$，特别地 $Z(G)\neq 1$。

**(2) 若 $|Z(G)|\ge p^2$ 则 $G$ 为阿贝尔群**

- 若 $|Z(G)|=p^3$，则 $Z(G)=G$，显然 $G$ 阿贝尔。
- 若 $|Z(G)|=p^2$，则 $|G/Z(G)|=p$。任何素数阶群必循环，故 $G/Z(G)$ 循环。

**引理：** 若 $G/Z(G)$ 循环，则 $G$ 阿贝尔。
*证明：* 设 $G/Z(G)=\langle gZ(G)\rangle$。任取 $x,y\in G$，可写 $x=g^a z_1,\ y=g^b z_2$，其中 $z_1,z_2\in Z(G)$。则
$$xy=g^a z_1 g^b z_2=g^{a+b}z_1z_2=g^b g^a z_2 z_1=g^b z_2 g^a z_1=yx,$$
故 $G$ 阿贝尔。

由引理，$|Z(G)|=p^2$ 时 $G$ 亦阿贝尔。综上，$|Z(G)|\ge p^2$ 蕴含 $G$ 阿贝尔。

**(3) 非阿贝尔阶 $p^3$ 群的结论**

若 $G$ 非阿贝尔，则 $|Z(G)|$ 不能为 $p^2$ 或 $p^3$，故必为 $p$。此时 $|G/Z(G)|=p^2$。$p^2$ 阶群只有两种：循环群 $C_{p^2}$ 或初等阿贝尔群 $C_p\times C_p$。若 $G/Z(G)\cong C_{p^2}$，则由上述引理 $G$ 阿贝尔，矛盾。因此 $G/Z(G)\cong C_p\times C_p$。

证毕。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
