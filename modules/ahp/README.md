# Método AHP (Analytic Hierarchy Process)

Este módulo implementa o método **AHP**, proposto por Thomas Saaty na década de 1970. É uma ferramenta amplamente consolidada para tomada de decisão multicritério baseada em avaliações par a par.

---

## 1. Funcionamento Teórico

O AHP decompõe o problema de decisão em uma hierarquia (Meta → Critérios → Alternativas) e utiliza a comparação par a par (pairwise comparison) para expressar a importância relativa dos elementos em cada nível da estrutura:

1. **Inter-critério**: Comparação da importância relativa dos critérios para atingir o objetivo meta.
2. **Intra-critério**: Comparação da preferência relativa das alternativas em relação a cada critério isoladamente.

O modelo é aditivo e gera a pontuação global $V(a_i)$ de cada alternativa como:

$$V(a_i) = \sum_{j=1}^n w_j \cdot v_j(a_i)$$

Onde:
- $w_j$ é o peso prioridade do critério $c_j$.
- $v_j(a_i)$ é a prioridade local da alternativa $a_i$ em relação ao critério $c_j$.

---

## 2. Escala Fundamental de Saaty

Para realizar as comparações par a par, utiliza-se a escala numérica de 1 a 9:

| Intensidade | Definição |
| :---: | :--- |
| **1** | Importância igual |
| **3** | Importância moderada de um sobre o outro |
| **5** | Importância forte de um sobre o outro |
| **7** | Importância muito forte demonstrada |
| **9** | Importância extrema |
| **2, 4, 6, 8** | Valores intermediários entre julgamentos adjacentes |

Se o elemento $A$ tem importância $x$ sobre o elemento $B$, então o elemento $B$ tem importância recíproca $1/x$ sobre o elemento $A$.

---

## 3. Lógica de Cálculo dos Pesos e Prioridades

Dada uma matriz de comparação par a par $A_{n \times n}$ recíproca ($A_{ji} = 1/A_{ij}$ e $A_{ii} = 1$):

1. **Cálculo das Prioridades (Método da Média Geométrica Normalizada)**:
   Calcula-se a média geométrica dos elementos de cada linha e depois normaliza-se:
   $$w_i = \frac{(\prod_{j=1}^n A_{ij})^{1/n}}{\sum_{k=1}^n (\prod_{j=1}^n A_{kj})^{1/n}}$$

2. **Cálculo da Consistência**:
   - Obtém-se o autovalor máximo aproximado:
     $$\lambda_{\text{max}} = \frac{1}{n} \sum_{i=1}^n \frac{(A \cdot w)_i}{w_i}$$
   - Calcula-se o Índice de Consistência (CI):
     $$\text{CI} = \frac{\lambda_{\text{max}} - n}{n - 1}$$
   - Calcula-se a Razão de Consistência (CR):
     $$\text{CR} = \frac{\text{CI}}{\text{RI}_n}$$
     Onde $\text{RI}_n$ é o Índice Aleatório de Saaty para uma matriz de tamanho $n$. Julgamentos com $\text{CR} < 0.10$ são considerados satisfatoriamente consistentes.

---

## 4. Elicitação Intra-critério (Alternativas)

Neste sistema, como a matriz de consequências é fornecida numericamente:
- O sistema **pré-preenche** as matrizes de comparação das alternativas $A^{(j)}$ para cada critério aplicando uma função matemática na razão das consequências ($x_{ij} / x_{kj}$), convertendo a proporção real em valores equivalentes na escala Saaty de 1 a 9.
- O usuário tem a flexibilidade de revisar, ajustar e salvar preferências qualitativas adicionais sobre esse pré-preenchimento, e o sistema recalcula as prioridades locais $v_j(a_i)$ aplicando o mesmo método de média geométrica.

---

## Referências
- **Saaty, T. L. (1980).** *The Analytic Hierarchy Process.* McGraw-Hill, New York.
