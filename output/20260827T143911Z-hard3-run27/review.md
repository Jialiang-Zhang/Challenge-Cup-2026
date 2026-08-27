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
**结论**：完全二分图 $K_{m,n}$（$m,n\ge 2$）的生成树总数为 $m^{n-1}n^{m-1}$。

**证明**（基于矩阵树定理与拉普拉斯谱分解）：

1. **拉普拉斯矩阵的构造**  
   将 $K_{m,n}$ 的顶点分为两部分 $U=\{u_1,\dots,u_m\}$ 与 $V=\{v_1,\dots,v_n\}$。其度矩阵 $D$ 为对角阵，前 $m$ 个对角元为 $n$，后 $n$ 个对角元为 $m$。邻接矩阵为  
   $$
   A=\begin{pmatrix}0_{m\times m}&J_{m\times n}\\ J_{n\times m}&0_{n\times n}\end{pmatrix},
   $$  
   其中 $J$ 为全 1 矩阵。于是拉普拉斯矩阵 $L=D-A$ 为  
   $$
   L=\begin{pmatrix}nI_m&-J_{m\times n}\\ -J_{n\times m}&mI_n\end{pmatrix}.
   $$

2. **矩阵树定理**  
   矩阵树定理指出：图的生成树数 $\tau(G)$ 等于 $L$ 的任意一个余子式（即删去第 $i$ 行第 $i$ 列后的行列式）。等价地，若 $L$ 的非零特征值为 $\lambda_1,\dots,\lambda_{N-1}$（$N=m+n$ 为顶点数），则  
   $$
   \tau(G)=\frac{1}{N}\prod_{i=1}^{N-1}\lambda_i.
   $$  
   该公式成立的前提是 $L$ 为对称半正定矩阵且恰有一个零特征值（对应连通图的常数特征向量），$K_{m,n}$ 显然满足。

3. **求 $L$ 的非零特征值**  
   考虑特征向量 $(x,y)^T$，其中 $x\in\mathbb{R}^m,y\in\mathbb{R}^n$，满足  
   $$
   \begin{cases}
   nx-Jy=\lambda x,\\
   -J^Tx+my=\lambda y.
   \end{cases}
   $$  
   - **情形 A**：若 $x\perp\mathbf{1}_m$ 且 $y=\mathbf{0}$，则 $Jy=0$，方程化为 $nx=\lambda x$，得特征值 $\lambda=n$，重数为 $m-1$（因为 $x$ 在 $m-1$ 维正交补中）。  
   - **情形 B**：若 $y\perp\mathbf{1}_n$ 且 $x=\mathbf{0}$，同理得特征值 $\lambda=m$，重数为 $n-1$。  
   - **情形 C**：若 $x=a\mathbf{1}_m,\;y=b\mathbf{1}_n$，则 $Jy=nb\mathbf{1}_m,\;J^Tx=ma\mathbf{1}_n$，方程组化为  
     $$
     \begin{pmatrix}n&-n\\ -m&m\end{pmatrix}\begin{pmatrix}a\\ b\end{pmatrix}=\lambda\begin{pmatrix}a\\ b\end{pmatrix}.
     $$  
     该 $2\times2$ 矩阵的特征值为 $0$ 与 $m+n$。零特征值对应全 1 向量（连通图的平凡特征值），非零特征值为 $\lambda=m+n$，重数为 $1$。

   综上，$L$ 的全部特征值为：  
   $$
   0,\quad n\ (\text{重数 }m-1),\quad m\ (\text{重数 }n-1),\quad m+n\ (\text{重数 }1).
   $$

4. **代入乘积公式**  
   由矩阵树定理的谱形式：  
   $$
   \tau(K_{m,n})=\frac{1}{m+n}\cdot n^{m-1}\cdot m^{n-1}\cdot(m+n)=m^{n-1}n^{m-1}.
   $$  
   这里 $m+n$ 与分母恰好约去，得到闭式。

5. **关于非零特征值进入余子式的严格说明**  
   设 $L=Q\operatorname{diag}(0,\lambda_1,\dots,\lambda_{N-1})Q^T$ 为正交对角化。记 $e_i$ 为第 $i$ 个标准基向量，则删去第 $i$ 行第 $i$ 列的余子式等于 $e_i^T\operatorname{adj}(L)e_i$。由于 $L$ 的零特征值对应特征向量 $\frac{1}{\sqrt{N}}\mathbf{1}$，利用矩阵恒等式 $\operatorname{adj}(L)=\prod_{j=1}^{N-1}\lambda_j\cdot\frac{1}{N}\mathbf{1}\mathbf{1}^T$（可由谱分解直接验证：$L$ 的伴随矩阵在零特征值方向上的投影系数恰为其余特征值之积除以 $N$），得到  
   $$
   e_i^T\operatorname{adj}(L)e_i=\frac{1}{N}\prod_{j=1}^{N-1}\lambda_j.
   $$  
   因此余子式行列式完全由非零特征值的乘积决定，且与删去的行列指标无关（图的顶点可交换对称性亦保证此点）。

**结论**：$K_{m,n}$ 的生成树总数为 $m^{n-1}n^{m-1}$，且拉普拉斯矩阵的非零特征值通过上述谱乘积公式精确进入余子式行列式的计算。

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

结论：对任意阶为 $p^3$ 的有限群 $G$（$p$ 为素数），有 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$；若 $|Z(G)|\ge p^2$ 则 $G$ 必为阿贝尔群；因此若 $G$ 非阿贝尔，则 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

证明过程：
**证明：**

**1. 类方程论证 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$。**

$G$ 的类方程为
$$|G|=|Z(G)|+\sum_{i=1}^k[G:C_G(x_i)],$$
其中 $x_1,\dots,x_k$ 为各非平凡共轭类的代表元，$C_G(x_i)$ 为 $x_i$ 的中心化子。由于 $G$ 是 $p$-群（$|G|=p^3$），Lagrange 定理给出 $|C_G(x_i)|$ 为 $p$ 的幂；又因 $x_i\notin Z(G)$，有 $C_G(x_i)\subsetneq G$，故 $[G:C_G(x_i)]\in\{p,p^2\}$，特别地每个指数都被 $p$ 整除。于是
$$p^3=|Z(G)|+\sum_{i=1}^k[G:C_G(x_i)]\equiv|Z(G)|\pmod p.$$
左端为 $0\pmod p$，故 $|Z(G)|\equiv0\pmod p$，即 $p\mid|Z(G)|$。由 Lagrange 定理 $|Z(G)|\mid p^3$，所以
$$|Z(G)|\in\{p,p^2,p^3\},$$
且 $|Z(G)|\ge p$，即 $Z(G)\neq 1$。

**2. 若 $|Z(G)|\ge p^2$ 则 $G$ 必为阿贝尔。**

由上一步，$|Z(G)|$ 只能为 $p^2$ 或 $p^3$。

- 若 $|Z(G)|=p^3$，则 $Z(G)=G$，显然 $G$ 阿贝尔。
- 若 $|Z(G)|=p^2$，则 $|G/Z(G)|=p$。阶为素数的群必循环，故 $G/Z(G)$ 循环。设 $G/Z(G)=\langle gZ(G)\rangle$。对任意 $x,y\in G$，它们在商群中的像可写成 $xZ(G)=g^iZ(G)$，$yZ(G)=g^jZ(G)$，于是存在 $z_1,z_2\in Z(G)$ 使 $x=g^iz_1$，$y=g^jz_2$。由于 $z_1,z_2$ 与所有元素可交换，且 $g^i$ 与 $g^j$ 可交换，得
$$xy=g^iz_1g^jz_2=g^{i+j}z_1z_2=g^jz_2g^iz_1=yx.$$
故 $G$ 阿贝尔。（一般结论：若 $G/Z(G)$ 循环，则 $G$ 阿贝尔。）

**3. 非阿贝尔情形。**

若 $G$ 非阿贝尔，则 $|Z(G)|$ 不能为 $p^2$ 或 $p^3$，结合第一步只能有 $|Z(G)|=p$。此时
$$|G/Z(G)|=\frac{p^3}{p}=p^2.$$
阶为 $p^2$ 的阿贝尔群只有两种：$C_{p^2}$（循环）与 $C_p\times C_p$。若 $G/Z(G)\cong C_{p^2}$，则由第 2 步的论证知 $G$ 阿贝尔，矛盾。因此 $G/Z(G)\cong C_p\times C_p$。

**结论：** 任意阶 $p^3$ 群满足 $Z(G)\neq 1$ 且 $|Z(G)|\in\{p,p^2,p^3\}$；若 $|Z(G)|\ge p^2$ 则 $G$ 阿贝尔；故非阿贝尔阶 $p^3$ 群必有 $|Z(G)|=p$ 且 $G/Z(G)\cong C_p\times C_p$。

### Public reference answer

由类方程$|G|=|Z(G)|+\sum [G:C_G(x_i)]$，非中心共轭类大小均为$p$的正幂，故模$p$有$|Z(G)|\equiv|G|\equiv0\pmod p$，所以$Z(G)\ne1$且其阶只能为$p,p^2,p^3$。若$|Z(G)|=p^3$显然阿贝尔；若$|Z(G)|=p^2$，则$|G/Z(G)|=p$为循环群。一般若$G/Z(G)=\langle gZ(G)\rangle$，任意$a,b\in G$可写$a=g^mz_1,b=g^nz_2$，其中$z_1,z_2\in Z(G)$，于是$ab=ba$，故$G$阿贝尔。因此非阿贝尔情形只能有$|Z(G)|=p$。此时$G/Z(G)$阶为$p^2$且不循环，否则仍推出$G$阿贝尔；阶$p^2$群均阿贝尔，故只能同构于$C_p\times C_p$。
