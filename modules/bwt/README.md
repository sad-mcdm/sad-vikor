# Método BWT (Best Worst Tradeoff)

Este módulo implementa o método **BWT**, proposto por Liang, Brunelli e Rezaei em 2022. É um método de vanguarda que une a estruturação cognitiva do Best-Worst Method (BWM) com a fundamentação teórica rigorosa do procedimento Tradeoff da Teoria da Utilidade Multiatributo (MAVT).

---

## 1. Funcionamento Teórico

Ao contrário do BWM tradicional, que expressa a importância em termos de julgamentos de razão qualitativos subjetivos em uma escala ordinal direta (1-9), o BWT interpreta a relação entre pesos como **taxas de substituição** (tradeoffs cardinais reais) baseadas nos intervalos de variação dos critérios.

- O decisor escolhe o melhor critério ($c_B$) e o pior ($c_W$).
- O decisor insere taxas de substituição reais e positivas $t_{Bj}$ (Best vs Others) e $t_{jW}$ (Others vs Worst), representando as taxas reais de troca subjetiva de valor entre os critérios considerando suas amplitudes físicas.

---

## 2. Modelo de Programação Linear (PL)

Os pesos ótimos dos critérios ($w_1, \dots, w_n$) são encontrados resolvendo o problema minimax semelhante ao BWM, mas utilizando as taxas reais de tradeoff fornecidas:

$$\text{Minimizar } \xi$$

sujeito a:
- $|w_B - t_{Bj} \cdot w_j| \le \xi \quad \forall j$
- $|w_j - t_{jW} \cdot w_W| \le \xi \quad \forall j$
- $\sum_{j=1}^n w_j = 1$
- $w_j \ge 0 \quad \forall j$

O modelo é resolvido via programação linear (`scipy.optimize.linprog`).

---

## 3. Fase Intra-critério (Método da Bisseção)

Conforme as especificações, a elicitação intra-critério no BWT utiliza o **Método da Bisseção** (bisection method) para estimar a função de valor do decisor de forma interativa:

1. Para cada critério $c_j$, o tomador de decisão define o ponto de indiferença de valor médio $x_{0.5}$ no intervalo $[x_{j,\text{min}}, x_{j,\text{max}}]$, tal que a atratividade deste ponto seja exatamente metade da atratividade total do critério:
   $$v_j(x_{0.5}) = 0.5$$
2. O sistema constrói uma **função de valor linear por partes** (piecewise linear):
   - **Para Benefício**:
     - Se $x \le x_{0.5}$: $v_j(x) = 0.5 \times \frac{x - x_{j,\text{min}}}{x_{0.5} - x_{j,\text{min}}}$
     - Se $x > x_{0.5}$: $v_j(x) = 0.5 + 0.5 \times \frac{x - x_{0.5}}{x_{j,\text{max}} - x_{0.5}}$
   - **Para Custo**:
     - Se $x \le x_{0.5}$: $v_j(x) = 1.0 - 0.5 \times \frac{x - x_{j,\text{min}}}{x_{0.5} - x_{j,\text{min}}}$
     - Se $x > x_{0.5}$: $v_j(x) = 0.5 \times \frac{x_{j,\text{max}} - x}{x_{j,\text{max}} - x_{0.5}}$
3. A pontuação $v_j(a_i)$ de cada alternativa é obtida interpolando sua consequência física bruta $x_{ij}$ nesta função. Isso permite representar formas côncavas (aversão ao risco) ou convexas (propensão ao risco) de maneira simples e intuitiva.

---

## Referências
- **Liang, F., Brunelli, M., & Rezaei, J. (2022).** *Best-worst Tradeoff method.* Information Sciences, 610, 957-976.
