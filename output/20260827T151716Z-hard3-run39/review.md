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
n I_m & -J_{m\times n}\\
-J_{n\times m} & m I_n
\end{pmatrix},
$$
其中 $J$ 为全 1 矩阵。矩阵树定理指出生成树数 $\tau(K_{m,n})$ 等于 $L$ 的任意一个代数余子式（即删去任意一行一列后的行列式）。

**特征值分析。** 直接验证 $L$ 的作用：
- 对任意满足 $\sum x_i=0$ 的 $\mathbf x\in\mathbb R^m$，有 $L(\mathbf x,\mathbf 0)=(n\mathbf x,\mathbf 0)$，故 $n$ 是特征值，重数 $m-1$。
- 对任意满足 $\sum y_j=0$ 的 $\mathbf y\in\mathbb R^n$，有 $L(\mathbf 0,\mathbf y)=(\mathbf 0,m\mathbf y)$，故 $m$ 是特征值，重数 $n-1$。
- 在子空间 $\mathrm{span}\{(\mathbf 1_m,\mathbf 0),(\mathbf 0,\mathbf 1_n)\}$ 上，$L$ 的矩阵表示为 $\begin{pmatrix}n&-m\\-n&m\end{pmatrix}$，其特征值为 $0$ 与 $m+n$。

因此 $L$ 的 $N$ 个特征值为
$$0,\quad m+n,\quad n^{(m-1)},\quad m^{(n-1)}.$$
非零特征值之积为 $(m+n)\,n^{m-1}\,m^{n-1}$。

**从特征值到余子式。** 对任意连通图，拉普拉斯矩阵 $L$ 满足 $L\mathbf 1=0$ 且 $\mathrm{rank}(L)=N-1$。由矩阵理论（或 Jacobi 公式对 $L+\varepsilon J$ 取极限），$L$ 的任意代数余子式等于 $\frac1N\prod_{i=2}^N\lambda_i$，其中 $\lambda_2,\dots,\lambda_N$ 为 $L$ 的非零特征值。这里 $N=m+n$，故
$$\tau(K_{m,n})=\frac1{m+n}\cdot(m+n)\,n^{m-1}\,m^{n-1}=m^{n-1}n^{m-1}.$$

**严格说明非零特征值如何进入余子式计算：** 因为 $L$ 的零特征值恰为单重，对应特征向量 $\mathbf 1$，而余子式等价于在正交补空间 $\mathbf 1^\perp$ 上限制 $L$ 后取行列式；该限制的特征值正是 $L$ 的全部非零特征值，故余子式行列式等于这些特征值之积除以 $N$（归一化正交基的体积因子）。代入即得所求。

### Public reference answer

设$K_{m,n}$的拉普拉斯矩阵为$L$。其谱为$0$（重数1）、$m$（重数$n-1$）、$n$（重数$m-1$）、$m+n$（重数1）。对任意$n+m$阶图拉普拉斯矩阵，矩阵树定理与非零谱给出$\tau(G)=\frac{1}{m+n}\prod_{\lambda_i\ne0}\lambda_i$。因此$\tau(K_{m,n})=\frac{1}{m+n}m^{n-1}n^{m-1}(m+n)=m^{n-1}n^{m-1}$。谱的求法可由分别考察两侧顶点和为零的子空间以及两侧常数向量张成的二维子空间得到。

## idx 40 — 测度积分

- Status: `success`
- Route: `R2`
- Model calls: `4`
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

结论：设$G$为阶$p^3$的有限群，$p$为素数。则$Z(G)\neq1$且$|Z(G)|\in\{p,p^2,p^3\}$；若$|Z(G)|\ge p^2$则$G$必为阿贝尔群；因此任意非阿贝尔阶$p^3$群都有$|Z(G)|=p$且$G/Z(G)\cong C_p\times C_p$。

证明过程：
**Step 1: 类方程论证 $Z(G)\neq 1$。**  
$G$ 的类方程为  
$$|G|=|Z(G)|+\sum_{i}[G:C_G(x_i)],$$  
其中 $x_i$ 取遍各非中心共轭类的代表元。每个 $[G:C_G(x_i)]>1$ 且整除 $|G|=p^3$，故必为 $p$ 的倍数（$p$ 或 $p^2$）。于是  
$$p^3\equiv |Z(G)|\pmod p,$$  
得 $p\mid |Z(G)|$。因 $Z(G)$ 至少含单位元，$|Z(G)|\ge p>1$，故 $Z(G)\neq1$。

**Step 2: $|Z(G)|\in\{p,p^2,p^3\}$。**  
由 Lagrange 定理，$|Z(G)|$ 整除 $p^3$，可能值为 $1,p,p^2,p^3$。Step 1 已排除 $1$，故 $|Z(G)|\in\{p,p^2,p^3\}$。

**Step 3: 若 $|Z(G)|\ge p^2$ 则 $G$ 阿贝尔。**  
- 若 $|Z(G)|=p^3$，则 $Z(G)=G$，显然 $G$ 阿贝尔。  
- 若 $|Z(G)|=p^2$，则 $|G/Z(G)|=p$。阶为素数的群必循环，故 $G/Z(G)$ 循环。  

**Step 4: $G/Z(G)$ 循环 $\Rightarrow$ $G$ 阿贝尔（关键引理）。**  
设 $G/Z(G)=\langle gZ(G)\rangle$。任取 $a,b\in G$，可写成  
$$a=g^i z_1,\quad b=g^j z_2,\qquad z_1,z_2\in Z(G).$$  
则  
$$ab=g^i z_1 g^j z_2=g^{i+j}z_1z_2=g^j z_2 g^i z_1=ba,$$$  
因为 $z_1,z_2$ 与所有元素可交换且 $g^i$ 与 $g^j$ 可交换。故 $G$ 阿贝尔。

**Step 5: 非阿贝尔阶 $p^3$ 群的结论。**  
若 $G$ 非阿贝尔，则 $|Z(G)|\neq p^3$（否则 $G$ 阿贝尔），且由 Step 3 知 $|Z(G)|\neq p^2$（否则 $G/Z(G)$ 循环迫使 $G$ 阿贝尔）。故必有 $|Z(G)|=p$。此时  
$$|G/Z(G)|=\frac{p^3}{p}=p^2.$$  
阶为 $p^2$ 的群只有两种：循环群 $C_{p^2}$ 或初等阿贝尔群 $C_p\times C_p$。若 $G/Z(G)\cong C_{p^2}$，则由 Step 4 知 $G$ 阿贝尔，矛盾。因此 $G/Z(G)\cong C_p\times C_p$。

综上，所有要求得证。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
