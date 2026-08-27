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

结论：The number of spanning trees of the complete bipartite graph $K_{m,n}$ is $m^{n-1}n^{m-1}$.

证明过程：
**结论**：完全二分图 $K_{m,n}$ 的生成树总数为 $m^{n-1}n^{m-1}$。

**证明（基于矩阵树定理与拉普拉斯谱分析）**：

记 $K_{m,n}$ 的顶点集划分为 $U=\{u_1,\dots,u_m\}$ 与 $V=\{v_1,\dots,v_n\}$。其拉普拉斯矩阵 $L$ 为 $(m+n)\times(m+n)$ 分块矩阵：
$$
L=\begin{pmatrix}
n I_m & -J_{m\times n}\\
-J_{n\times m} & m I_n
\end{pmatrix},
$$
其中 $I_k$ 为 $k$ 阶单位阵，$J$ 为全 1 矩阵（适当维数）。

**步骤 1：验证矩阵树定理条件。**
$K_{m,n}$ 是连通图（因 $m,n\ge 2$），故其拉普拉斯矩阵 $L$ 的秩为 $m+n-1$，零特征值的重数为 1。矩阵树定理（Matrix-Tree Theorem）指出：连通图 $G$ 的生成树数 $\tau(G)$ 等于 $L$ 的任意一个余子式（cofactor）的行列式，也等于 $L$ 的所有非零特征值的乘积除以顶点数 $N=m+n$：
$$
\tau(K_{m,n}) = \frac{1}{m+n}\prod_{i=1}^{m+n-1}\lambda_i,
$$
其中 $\lambda_1,\dots,\lambda_{m+n-1}$ 为 $L$ 的非零特征值。

**步骤 2：计算 $L$ 的特征值。**
利用分块矩阵结构求谱。设特征向量为 $(x,y)^T$，其中 $x\in\mathbb{R}^m, y\in\mathbb{R}^n$，特征方程 $L(x,y)^T=\lambda(x,y)^T$ 给出：
$$
n x - (\mathbf{1}_n^T y)\mathbf{1}_m = \lambda x,\quad m y - (\mathbf{1}_m^T x)\mathbf{1}_n = \lambda y.
$$
记 $a=\mathbf{1}_m^T x$，$b=\mathbf{1}_n^T y$。

- **情形 A**：$a=b=0$。则方程化为 $n x=\lambda x$ 与 $m y=\lambda y$。在 $x\perp\mathbf{1}_m$ 子空间（维数 $m-1$）中，$\lambda=n$；在 $y\perp\mathbf{1}_n$ 子空间（维数 $n-1$）中，$\lambda=m$。故 $n$ 的重数为 $m-1$，$m$ 的重数为 $n-1$。

- **情形 B**：$(a,b)\neq(0,0)$。此时 $x$ 与 $y$ 必为全 1 向量的倍数，代入得 $2\times 2$ 系统：
$$
\begin{pmatrix} n-\lambda & -n \\ -m & m-\lambda \end{pmatrix}\begin{pmatrix} a \\ b \end{pmatrix}=0.
$$
行列式为 $(n-\lambda)(m-\lambda)-mn=\lambda^2-(m+n)\lambda=0$，解得 $\lambda=0$ 或 $\lambda=m+n$。$\lambda=0$ 对应全 1 向量（零特征值），$\lambda=m+n$ 为单重非零特征值。

综上，$L$ 的非零特征值为：
- $m+n$（重数 1），
- $n$（重数 $m-1$），
- $m$（重数 $n-1$）。

**步骤 3：代入矩阵树定理公式。**
$$
\tau(K_{m,n}) = \frac{1}{m+n}\cdot (m+n)^1 \cdot n^{m-1} \cdot m^{n-1} = m^{n-1}n^{m-1}.
$$

**步骤 4：严格说明非零特征值如何进入余子式行列式计算。**
由矩阵树定理，$\tau(G)=\det(L_{ii})$，其中 $L_{ii}$ 为删去第 $i$ 行第 $i$ 列后的余子式。对任意连通图，$L$ 的特征多项式为 $p(\lambda)=\det(\lambda I-L)=\lambda\prod_{i=1}^{N-1}(\lambda-\lambda_i)$。对 $p(\lambda)$ 求导并在 $\lambda=0$ 处取值，得 $p'(0)=(-1)^{N-1}\prod_{i=1}^{N-1}\lambda_i$。另一方面，由行列式展开的伴随矩阵性质，$p'(0)=(-1)^{N-1}\sum_i \det(L_{ii})$。因图连通，所有余子式相等且非零，故 $\det(L_{ii})=\frac{1}{N}\prod_{i=1}^{N-1}\lambda_i$。这正是上述公式中"除以 $m+n$"的来源：非零特征值乘积被顶点数归一化后等于余子式行列式。

因此，$K_{m,n}$ 的生成树总数确为 $m^{n-1}n^{m-1}$。证毕。

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
- Model calls: `4`
- Repair count: `0`
- Local reference relation: `unknown`

### Problem

设$G$为阶$p^3$的有限群，$p$为素数。证明$Z(G)\neq1$且$|Z(G)|\in\{p,p^2,p^3\}$；进一步证明若$|Z(G)|\ge p^2$则$G$必为阿贝尔群；因此任意非阿贝尔阶$p^3$群都有$|Z(G)|=p$且$G/Z(G)\cong C_p\times C_p$。要求给出类方程论证，并说明为什么$G/Z(G)$循环会迫使$G$阿贝尔。

### Agent final response

结论：对任意阶为 $p^3$（$p$ 为素数）的有限群 $G$，有 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$。若 $|Z(G)|\ge p^2$，则 $G$ 为阿贝尔群。因而若 $G$ 非阿贝尔，则必有 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

证明过程：
设 $|G|=p^3$，$p$ 为素数。

**1. 类方程与 $Z(G)\neq 1$**  
类方程为  
$$|G|=|Z(G)|+\sum_{i}[G:C_G(x_i)],$$  
其中 $x_i$ 取遍非中心共轭类的代表元。每个 $[G:C_G(x_i)]$ 是 $|G|=p^3$ 的真因子且大于 $1$，故必为 $p$ 或 $p^2$，从而 $p\mid [G:C_G(x_i)]$。于是  
$$p^3-|Z(G)|=\sum_i [G:C_G(x_i)]\equiv 0\pmod p,$$  
得 $p\mid |Z(G)|$。因此 $|Z(G)|\in\{p,p^2,p^3\}$，特别地 $Z(G)\neq 1$。

**2. 若 $|Z(G)|\ge p^2$ 则 $G$ 阿贝尔**  
- 若 $|Z(G)|=p^3$，则 $Z(G)=G$，显然阿贝尔。  
- 若 $|Z(G)|=p^2$，则 $|G/Z(G)|=p$，故 $G/Z(G)$ 为循环群。引理：若 $G/Z(G)$ 循环，则 $G$ 阿贝尔。证明如下：设 $G/Z(G)=\langle gZ(G)\rangle$，则任意 $a,b\in G$ 可写成 $a=g^m z_1,\; b=g^n z_2$（$z_1,z_2\in Z(G)$）。于是  
  $$ab=g^m z_1 g^n z_2=g^{m+n}z_1z_2=g^n g^m z_2 z_1=g^n z_2 g^m z_1=ba,$$  
  因为 $z_1,z_2$ 与所有元素可交换且 $g$ 的幂次彼此可交换。故 $G$ 阿贝尔。

由以上两点，若 $G$ 非阿贝尔，则 $|Z(G)|$ 既不能为 $p^3$ 也不能为 $p^2$，只能为 $p$。

**3. 非阿贝尔情形下 $G/Z(G)$ 的结构**  
当 $|Z(G)|=p$ 时，$|G/Z(G)|=p^2$。已知阶为 $p^2$ 的群必阿贝尔，且只能是循环群 $C_{p^2}$ 或初等阿贝尔群 $C_p\times C_p$。但上一步已证 $G/Z(G)$ 不能是循环群（否则 $G$ 阿贝尔），故只能有  
$$G/Z(G)\cong C_p\times C_p.$$

综上，任意非阿贝尔阶 $p^3$ 群满足 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
