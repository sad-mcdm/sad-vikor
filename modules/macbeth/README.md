# Método MACBETH (Measuring Attractiveness by a Categorical Based Evaluation Technique)

Este módulo implementa o método **MACBETH**, proposto por Carlos Bana e Costa e Jean-Claude Vansnick no início dos anos 1990. Trata-se de uma técnica de apoio à decisão multicritério baseada em julgamentos qualitativos (semânticos) sobre a diferença de atratividade entre opções.

---

## 1. Funcionamento Teórico

Ao contrário do AHP, que utiliza comparações de razão numérica direta (ex. "3 vezes mais importante"), o MACBETH exige apenas que o tomador de decisão expresse verbalmente a diferença de atratividade entre dois elementos de forma par a par, utilizando sete categorias semânticas ordinais:

- **Nula (Null)**: diferença $d = 0$
- **Muito Fraca (Very Weak)**: diferença $d = 1$
- **Fraca (Weak)**: diferença $d = 2$
- **Moderada (Moderate)**: diferença $d = 3$
- **Forte (Strong)**: diferença $d = 4$
- **Muito Forte (Very Strong)**: diferença $d = 5$
- **Extrema (Extreme)**: diferença $d = 6$

Esses julgamentos semânticos são convertidos em restrições matemáticas em um modelo de **Programação Linear (PL)** para gerar uma escala de intervalo cardinal.

---

## 2. Modelo de Programação Linear (PL)

Dada uma ordenação decrescente de elementos $e_1 > e_2 > \dots > e_n$, onde o decisor avalia a diferença de atratividade de $e_i$ sobre $e_j$ como sendo $M_{ij} \in \{0, 1, 2, 3, 4, 5, 6\}$, buscamos determinar valores de escala $s_i \in [0, 1]$ para cada elemento resolvendo o seguinte problema de otimização:

$$\text{Maximizar } \delta$$

sujeito a:
- $s_{\text{best}} = 1.0$ (âncora superior)
- $s_{\text{worst}} = 0.0$ (âncora inferior)
- $s_i - s_j \ge M_{ij} \cdot \delta \quad \forall i, j$ onde $e_i > e_j$ (ou seja, a distância cardinal respeita a categoria qualitativa)
- $s_i - s_j = 0 \quad \forall i, j$ onde $e_i$ e $e_j$ são avaliados como equivalentes.
- $s_i \ge 0 \quad \forall i$
- $\delta \ge 0.001$ (onde $\delta$ é o passo mínimo da escala cardinal)

O solucionador resolve este modelo utilizando programação linear (`scipy.optimize.linprog`). Se o sistema for consistente, os valores de escala $s_i$ são obtidos com sucesso. Caso o decisor cometa alguma inconsistência transitiva de julgamento, o sistema sinaliza um aviso e utiliza um modelo relaxado de ranks para fornecer uma solução aproximada estável.

---

## 3. Lógica de Avaliação

- **Inter-critério (Pesos)**: A matriz de comparações qualitativas par a par dos critérios é usada no modelo de PL. Os escores de escala cardinal resultantes $s_j$ são normalizados para que somem 1.0, gerando os pesos $w_j$.
- **Intra-critério (Funções de Valor)**: Para cada critério $c_j$, o sistema cria 5 níveis cardinais ordenados igualmente distribuídos no intervalo $[x_{j,\text{min}}, x_{j,\text{max}}]$. O decisor compara qualitativamente a atratividade desses níveis par a par. O modelo de PL resolve as utilidades desses níveis no intervalo $[0, 1]$ (onde a utilidade do pior nível é 0 e do melhor é 1). A utilidade final $v_j(a_i)$ de cada alternativa é calculada interpolando linearmente a consequência física $x_{ij}$ da alternativa entre os níveis de referência cardinalizados.

---

## Referências
- **Bana e Costa, C. A., & Vansnick, J. C. (1994).** *MACBETH — An interactive path towards the construction of cardinal value functions.* International Transactions in Operational Research, 1(4), 489-500.
