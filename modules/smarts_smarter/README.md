# Métodos SMARTS e SMARTER

Este módulo implementa os métodos de apoio à decisão multicritério **SMARTS** (Simple Multi-Attribute Rating Technique using Swings) e **SMARTER** (SMART Exploiting Ranks), conforme propostos por Edwards e Barron (1994).

---

## 1. Funcionamento Teórico

Ambos os métodos são baseados na **Teoria da Utilidade Multiatributo (MAVT)** sob uma racionalidade compensatória aditiva. O valor global $V(a_i)$ de cada alternativa é calculado como a média ponderada de suas utilidades parciais nos critérios:

$$V(a_i) = \sum_{j=1}^n w_j \cdot v_j(a_i)$$

Onde:
- $w_j$ é o peso (constante de escala) do critério $c_j$, de tal forma que $\sum_{j=1}^n w_j = 1$.
- $v_j(a_i)$ é o valor intra-critério (utilidade) da alternativa $a_i$ no critério $c_j$, normalizado no intervalo $[0, 1]$.

---

## 2. Fase Intra-critério (Normalização)

Para converter as consequências físicas brutas $x_{ij}$ da matriz de decisão em utilidades $v_j(a_i) \in [0, 1]$, os métodos utilizam **funções de valor lineares**:

- **Critérios de Benefício** (quanto maior o valor bruto, melhor):
  $$v_j(a_i) = \frac{x_{ij} - x_{j,\text{min}}}{x_{j,\text{max}} - x_{j,\text{min}}}$$

- **Critérios de Custo** (quanto menor o valor bruto, melhor):
  $$v_j(a_i) = \frac{x_{j,\text{max}} - x_{ij}}{x_{j,\text{max}} - x_{j,\text{min}}}$$

*(Caso $x_{j,\text{max}} = x_{j,\text{min}}$, a atratividade é definida como $v_j(a_i) = 1.0$).*

---

## 3. Fase Inter-critério (Determinação de Pesos)

A diferença fundamental entre os dois métodos está no processo de obtenção dos pesos dos critérios ($w_j$):

### SMARTS
No SMARTS, os pesos são definidos de forma direta baseados na avaliação subjetiva do tomador de decisão (método Swing Weighting):
1. O tomador atribui pontuações diretas $s_j \in [0, 100]$ refletindo a importância relativa de alterar cada critério do seu pior nível para o seu melhor nível.
2. Os pesos finais são calculados normalizando as pontuações para que a soma seja unitária:
   $$w_j = \frac{s_j}{\sum_{k=1}^n s_k}$$

### SMARTER
O SMARTER simplifica o esforço cognitivo do tomador de decisão exigindo apenas uma **ordenação ordinal** dos critérios por relevância:
1. O tomador ordena os critérios do mais importante ao menos importante:
   $$c_{(1)} > c_{(2)} > \dots > c_{(n)}$$
2. O sistema calcula automaticamente os pesos utilizando a fórmula do **ROC (Rank-Order Centroid)**, que extrai o centroide do espaço de pesos que satisfaz a ordenação ordenada:
   $$w_j = \frac{1}{n} \sum_{k=\pi(j)}^n \frac{1}{k}$$
   Onde $\pi(j)$ representa o rank (posição na ordenação) do critério $c_j$ (ex. o primeiro critério tem rank 1, o segundo tem rank 2, etc.).

---

## Referências
- **Edwards, W., & Barron, F. H. (1994).** *SMARTS and SMARTER: Improved Simple Methods for Multiattribute Utility Measurement.* Organizational Behavior and Human Decision Processes, 60(3), 306-325.
