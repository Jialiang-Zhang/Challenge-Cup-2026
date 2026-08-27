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
**Theorem (Matrix-Tree Theorem).** For a connected graph $G$ with Laplacian matrix $L$, the number of spanning trees $\tau(G)$ equals any cofactor of $L$, i.e., $\tau(G)=(-1)^{i+j}\det L(i|j)$, where $L(i|j)$ is the submatrix obtained by deleting row $i$ and column $j$. Equivalently, if $0=\lambda_1<\lambda_2\le\cdots\le\lambda_N$ are the eigenvalues of $L$ ($N=|V(G)|$), then
$$\tau(G)=\frac{1}{N}\prod_{k=2}^N \lambda_k.$$

**Step 1: Laplacian of $K_{m,n}$.**  
Let the bipartition be $A=\{a_1,\dots,a_m\}$ and $B=\{b_1,\dots,b_n\}$. Every vertex in $A$ has degree $n$, and every vertex in $B$ has degree $m$. Ordering vertices as $A$ then $B$, the Laplacian is the $(m+n)\times(m+n)$ block matrix
$$L=\begin{pmatrix} n I_m & -J_{m\times n} \\ -J_{n\times m} & m I_n \end{pmatrix},$$
where $J$ denotes the all-ones matrix and $I$ the identity.

**Step 2: Eigenvalues of $L$.**  
Because $L\mathbf{1}=0$, $0$ is an eigenvalue with eigenvector $\mathbf{1}$. For vectors of the form $(x,0,\dots,0,-y,0,\dots,0)^T$ with $x$ on one $A$-vertex and $-y$ on one $B$-vertex, direct computation shows:
- There are $m-1$ independent eigenvectors supported on $A$ with eigenvalue $n$ (take differences of $A$-vertices).
- There are $n-1$ independent eigenvectors supported on $B$ with eigenvalue $m$ (take differences of $B$-vertices).
- The remaining two eigenvectors lie in the span of $(\mathbf{1}_A,0)$ and $(0,\mathbf{1}_B)$. Restricting $L$ to this 2D subspace gives the matrix $\begin{pmatrix} n & -n \\ -m & m \end{pmatrix}$, whose non-zero eigenvalue is $m+n$.

Thus the spectrum of $L$ is:
$$\underbrace{0}_{1\text{ time}},\quad \underbrace{n}_{m-1\text{ times}},\quad \underbrace{m}_{n-1\text{ times}},\quad \underbrace{m+n}_{1\text{ time}}.$$

**Step 3: Apply Matrix-Tree Theorem via eigenvalues.**  
Since $K_{m,n}$ is connected, the theorem gives
$$\tau(K_{m,n})=\frac{1}{m+n}\prod_{k=2}^{m+n}\lambda_k=\frac{1}{m+n}\cdot n^{m-1}\cdot m^{n-1}\cdot(m+n)=n^{m-1}m^{n-1}.$$

**Step 4: How non-zero eigenvalues enter the cofactor.**  
The adjugate matrix satisfies $\operatorname{adj}(L)=\prod_{k=2}^{m+n}\lambda_k\cdot \frac{\mathbf{1}\mathbf{1}^T}{m+n}$ because $L$ has rank $m+n-1$ and its nullspace is spanned by $\mathbf{1}$. Hence every diagonal cofactor (delete row $i$ and column $i$) equals $\frac{1}{m+n}\prod_{k=2}^{m+n}\lambda_k$, exactly the product of all non-zero eigenvalues divided by the number of vertices. This rigorously shows that the non-zero eigenvalues enter the cofactor determinant as their product scaled by $1/(m+n)$.

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

结论：对任意有限$p$-群$G$（$|G|=p^3$），有$Z(G)\neq 1$且$|Z(G)|\in\{p,p^2,p^3\}$；若$|Z(G)|\ge p^2$则$G$必为阿贝尔群；因此非阿贝尔阶$p^3$群必有$|Z(G)|=p$且$G/Z(G)\cong C_p\times C_p$。

证明过程：
**结论**：设$G$为阶$p^3$的有限群（$p$为素数），则$Z(G)\neq 1$且$|Z(G)|\in\{p,p^2,p^3\}$。若$|Z(G)|\ge p^2$，则$G$为阿贝尔群。因此，任意非阿贝尔阶$p^3$群满足$|Z(G)|=p$且$G/Z(G)\cong C_p\times C_p$。

---

### **证明**

#### **1. 类方程论证$Z(G)\neq 1$且$|Z(G)|\in\{p,p^2,p^3\}$**

有限$p$-群$G$的**类方程**为
$$
|G| = |Z(G)| + \sum_{i} [G:C_G(x_i)],
$$
其中$x_i$取遍各非中心共轭类的代表元，且$[G:C_G(x_i)]>1$为$|G|=p^3$的真因子，故每个$[G:C_G(x_i)]$均被$p$整除。

由$p\mid |G|=p^3$及$p\mid \sum [G:C_G(x_i)]$，立得$p\mid |Z(G)|$。又$Z(G)\le G$，故$|Z(G)|$为$p$的幂且至少为$p$，即
$$
|Z(G)|\in\{p,p^2,p^3\},
$$
特别地$Z(G)\neq 1$。

#### **2. 若$|Z(G)|\ge p^2$则$G$为阿贝尔群**

- **情形$|Z(G)|=p^3$**：显然$G=Z(G)$，故$G$阿贝尔。
- **情形$|Z(G)|=p^2$**：此时商群$|G/Z(G)|=p$，故$G/Z(G)\cong C_p$为循环群。

**关键引理**：若$G/Z(G)$循环，则$G$为阿贝尔群。

*引理的证明*：设$G/Z(G)=\langle gZ(G)\rangle$。任取$x,y\in G$，可写
$$
x=g^a z_1,\quad y=g^b z_2,\qquad z_1,z_2\in Z(G).
$$
由于$z_1,z_2$与任意元素可交换，且$g^a$与$g^b$可交换，有
$$
xy = g^a z_1 g^b z_2 = g^{a+b}z_1z_2 = g^b z_2 g^a z_1 = yx.
$$
故$G$为阿贝尔群。

因此，当$|Z(G)|=p^2$时$G$也阿贝尔。综上，$|Z(G)|\ge p^2$蕴含$G$阿贝尔。

#### **3. 非阿贝尔阶$p^3$群的结构**

若$G$非阿贝尔，则$|Z(G)|\neq p^3$且$|Z(G)|\neq p^2$（否则由上一步知$G$阿贝尔），故必有
$$
|Z(G)|=p.
$$
此时$|G/Z(G)|=p^2$。阶为$p^2$的群必为阿贝尔群，且只能是$C_{p^2}$或$C_p\times C_p$。但$G/Z(G)$**不可能是循环群**（否则由引理$G$将阿贝尔，矛盾），故
$$
G/Z(G)\cong C_p\times C_p.
$$

---

**总结**：类方程给出$p\mid |Z(G)|$从而$|Z(G)|\in\{p,p^2,p^3\}$；$G/Z(G)$循环$\Rightarrow G$阿贝尔的引理排除了非阿贝尔情形下$|Z(G)|\ge p^2$的可能，迫使非阿贝尔阶$p^3$群的中心阶恰为$p$，且商群同构于$C_p\times C_p$。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
