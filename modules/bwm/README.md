# Método BWM (Best Worst Method)

Este módulo implementa o método **BWM**, desenvolvido por Jafar Rezaei em 2015. É uma técnica estruturada de tomada de decisão baseada em duas referências principais: o Melhor (Best) e o Pior (Worst) critério.

---

## 1. Funcionamento Teórico

Diferente do AHP clássico, que realiza todas as comparações par a par possíveis entre os critérios (exigindo $n(n-1)/2$ comparações), o BWM foca apenas nas comparações a partir do melhor critério e em direção ao pior critério. Isso reduz o esforço do tomador de decisão para $2n-3$ comparações, aumentando a consistência dos julgamentos.

1. **Seleção de Referências**: O decisor escolhe, entre o conjunto de critérios, o melhor critério ($c_B$, mais importante) e o pior critério ($c_W$, menos importante).
2. **Vetor Best-to-Others (BO)**: O decisor compara a preferência de $c_B$ sobre cada outro critério $c_j$ na escala de 1 a 9, gerando $A_B = (a_{B1}, a_{B2}, \dots, a_{Bn})$.
3. **Vetor Others-to-Worst (OW)**: O decisor compara a preferência de cada critério $c_j$ sobre $c_W$ na escala de 1 a 9, gerando $A_W = (a_{1W}, a_{2W}, \dots, a_{nW})$.

---

## 2. Modelo de Programação Linear (PL)

Para determinar os pesos ótimos dos critérios ($w_1, \dots, w_n$), formulamos um problema minimax que minimiza a discrepância absoluta máxima entre os pesos calculados e os julgamentos fornecidos ($\xi$):

$$\text{Minimizar } \xi$$

sujeito a:
- $|w_B - a_{Bj} \cdot w_j| \le \xi \quad \forall j$ (relação com o melhor)
- $|w_j - a_{jW} \cdot w_W| \le \xi \quad \forall j$ (relação com o pior)
- $\sum_{j=1}^n w_j = 1$
- $w_j \ge 0 \quad \forall j$

O sistema resolve este modelo de PL usando programação linear de forma eficiente. O valor ótimo resultante $\xi^*$ serve como um indicador do nível de inconsistência dos julgamentos (quanto menor o $\xi^*$, mais consistente a decisão).

---

## 3. Fase Intra-critério (Igual ao AHP)

De acordo com as especificações do sistema:
- O BWM compartilha a **mesma lógica intra-critério do AHP**.
- Para cada critério $c_j$, realiza-se a comparação par a par de todas as alternativas na escala Saaty (1-9), pré-preenchida dinamicamente com base nas razões de suas consequências brutas.
- O solucionador calcula os escores locais das alternativas $v_j(a_i)$ como o autovetor principal normalizado (média geométrica das linhas da matriz de comparação de alternativas).

---

## Referências
- **Rezaei, J. (2015).** *Best-worst multi-criteria decision-making method.* Omega, 53, 49-57.
- **Rezaei, J. (2016).** *Best-worst multi-criteria decision-making method: Some properties and a linear model.* Omega, 64, 126-130.
