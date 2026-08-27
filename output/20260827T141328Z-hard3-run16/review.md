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

结论：The number of spanning trees of the complete bipartite graph $K_{m,n}$ is $m^{n-1} n^{m-1}$.

证明过程：
**Claim.** For integers $m,n\ge 2$, the complete bipartite graph $K_{m,n}$ has exactly $m^{n-1}n^{m-1}$ spanning trees.

**Proof via the Matrix-Tree Theorem.**

1. **Laplacian of $K_{m,n}$.**  
   Label the $m$ vertices of the first part as $A=\{a_1,\dots,a_m\}$ and the $n$ vertices of the second part as $B=\{b_1,\dots,b_n\}$.  
   Every $a_i$ has degree $n$, and every $b_j$ has degree $m$. The Laplacian matrix $L$ (ordered as $A$ then $B$) is the block matrix
   $$
   L=\begin{pmatrix}
   n I_m & -J_{m\times n}\\[2pt]
   -J_{n\times m} & m I_n
   \end{pmatrix},
   $$
   where $I_k$ is the $k\times k$ identity and $J$ denotes an all-ones matrix of the indicated size.

2. **Statement of the Matrix-Tree Theorem.**  
   For any connected graph $G$ on $N$ vertices, let $L$ be its Laplacian. Then every cofactor of $L$ (i.e., the determinant of $L$ with one row and the corresponding column deleted) equals the number $\tau(G)$ of spanning trees of $G$. Equivalently, if $0=\lambda_1<\lambda_2\le\cdots\le\lambda_N$ are the eigenvalues of $L$, then
   $$
   \tau(G)=\frac{1}{N}\prod_{i=2}^N \lambda_i.
   $$
   The graph $K_{m,n}$ is connected for $m,n\ge 1$, so the theorem applies.

3. **Eigenvalues of $L$.**  
   Because $L\mathbf{1}=0$, one eigenvalue is $0$ with eigenvector $\mathbf{1}$.  
   To find the remaining eigenvalues, consider vectors of the form $(x\mathbf{1}_m,\;y\mathbf{1}_n)^T$. The action of $L$ on this subspace is represented by
   $$
   \begin{pmatrix} n & -n\\ -m & m \end{pmatrix},
   $$
   whose eigenvalues are $0$ and $m+n$. The eigenvalue $m+n$ corresponds to the eigenvector $(n\mathbf{1}_m,\;-m\mathbf{1}_n)^T$.

   Now consider vectors orthogonal to the all-ones vector on each part.  
   - If $u\in\mathbb{R}^m$ satisfies $\sum u_i=0$ and we extend it by zeros on $B$, then $L(u,0)^T = n(u,0)^T$. There are $m-1$ linearly independent such vectors, giving eigenvalue $n$ with multiplicity $m-1$.  
   - Similarly, if $v\in\mathbb{R}^n$ satisfies $\sum v_j=0$ and we extend by zeros on $A$, then $L(0,v)^T = m(0,v)^T$. This yields eigenvalue $m$ with multiplicity $n-1$.

   Thus the spectrum of $L$ is
   $$
   \underbrace{0}_{1},\quad \underbrace{m+n}_{1},\quad \underbrace{n,\dots,n}_{m-1},\quad \underbrace{m,\dots,m}_{n-1}.
   $$

4. **Cofactor via eigenvalues.**  
   Since $K_{m,n}$ has $N=m+n$ vertices, the Matrix-Tree Theorem gives
   $$
   \tau(K_{m,n})=\frac{1}{m+n}\cdot (m+n)\cdot n^{\,m-1}\cdot m^{\,n-1}=m^{\,n-1}n^{\,m-1}.
   $$
   Here the factor $m+n$ (the non-zero eigenvalue coming from the cross-part coupling) cancels exactly with the $1/(m+n)$ prefactor, leaving the product of the remaining non-zero eigenvalues $n^{m-1}m^{n-1}$.

5. **Why the non-zero eigenvalues enter the cofactor.**  
   The Laplacian $L$ is real symmetric positive semidefinite with rank $N-1$ for a connected graph. Hence $L$ has exactly one zero eigenvalue. The adjugate matrix $\operatorname{adj}(L)$ equals the product of all non-zero eigenvalues times the projection onto the orthogonal complement of $\mathbf{1}$, and every diagonal cofactor equals $\frac{1}{N}\prod_{i=2}^N\lambda_i$. This is precisely the step where the non-zero eigenvalues are inserted into the determinant-of-minor calculation: deleting any row and column removes the zero eigenvalue from the product, and the normalization $1/N$ accounts for the fact that all $N$ principal cofactors are equal.

Therefore, the number of spanning trees of $K_{m,n}$ is $m^{n-1}n^{m-1}$.

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

结论：对任意 $|G|=p^3$（$p$ 为素数），有 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$；若 $|Z(G)|\ge p^2$ 则 $G$ 必为阿贝尔群；因此若 $G$ 非阿贝尔，则必有 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

证明过程：
设 $|G|=p^3$，$p$ 为素数。

**Step 1（类方程得 $Z(G)\neq1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$）。**  
类方程为
\[
|G|=|Z(G)|+\sum_{i}[G:C_G(x_i)],
\]
其中 $x_i$ 取遍各非中心共轭类的代表元。每个非中心共轭类大小 $[G:C_G(x_i)]>1$ 且必为 $|G|$ 的真因子，故只能是 $p$ 或 $p^2$。于是
\[
p^3=|Z(G)|+(\text{若干 }p\text{ 或 }p^2\text{ 之和}),
\]
从而 $p\mid |Z(G)|$。又 $Z(G)\le G$，故 $|Z(G)|=1,p,p^2$ 或 $p^3$。结合 $p\mid |Z(G)|$ 得 $|Z(G)|\neq1$，即 $|Z(G)|\in\{p,p^2,p^3\}$。

**Step 2（若 $|Z(G)|\ge p^2$ 则 $G$ 阿贝尔）。**  
- 若 $|Z(G)|=p^3$，则 $Z(G)=G$，显然 $G$ 阿贝尔。  
- 若 $|Z(G)|=p^2$，则商群 $G/Z(G)$ 的阶为 $p$，必为循环群 $C_p$。

**Step 3（$G/Z(G)$ 循环 $\Rightarrow G$ 阿贝尔）。**  
设 $G/Z(G)=\langle gZ(G)\rangle$。任取 $a,b\in G$，可写成
\[
a=g^m z_1,\qquad b=g^n z_2,\qquad z_1,z_2\in Z(G).
\]
由于中心元与一切元素相乘可交换，且 $g^m$ 与 $g^n$ 显然可交换，有
\[
ab=g^m z_1 g^n z_2=g^{m+n}z_1z_2=g^n z_2 g^m z_1=ba.
\]
故 $G$ 阿贝尔。

**Step 4（非阿贝尔情形的结论）。**  
综上，若 $G$ 非阿贝尔，则 $|Z(G)|$ 不能为 $p^2$ 或 $p^3$，只能为 $p$。此时 $G/Z(G)$ 的阶为 $p^2$。阶为 $p^2$ 的群必阿贝尔；又由 Step 3 知 $G/Z(G)$ 不能是循环群（否则 $G$ 阿贝尔），故只能是
\[
G/Z(G)\cong C_p\times C_p.
\]

因此，任意非阿贝尔的 $p^3$ 阶群满足 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。证毕。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
