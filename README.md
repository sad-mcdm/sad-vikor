# SAD VIKOR — Otimização de Compromisso Multicritério

Este repositório é o módulo independente do ecossistema **SAD MCDM**, configurado para operar exclusivamente com o método **VIKOR**.

---

## 🎨 Identidade Visual e Branding
- **Nome Oficial:** SAD VIKOR
- **Cores Oficiais:** Esmeralda (`#059669`) e Bronze (`#B45309`)
- **Conceito Visual:** Curvas de utilidade social e arrependimento individual convergentes.
- **Copyright:** Direitos Reservados © 2026 SAD-MCDM. Todos os direitos reservados.

---

## 🧠 Formulação Matemática e Funcionamento

O método **VIKOR** ranqueia e determina uma solução de compromisso de múltiplos critérios sob desvios e interesses conflitantes. Ele baseia-se em uma métrica de distância agregada que pondera a utilidade média do grupo (maioria) e o arrependimento do pior critério (indivíduo).

### Passos Matemáticos do Processo:

#### 1. Determinação de Melhor ($f_j^*$) e Pior ($f_j^-$) valor físico
* Para Critérios de Benefício: $f_j^* = \max_i x_{ij}$ e $f_j^- = \min_i x_{ij}$
* Para Critérios de Custo: $f_j^* = \min_i x_{ij}$ e $f_j^- = \max_i x_{ij}$

#### 2. Cálculo dos Índices de Utilidade ($S_i$) e Arrependimento ($R_i$)
* **Índice de Utilidade ($S_i$):** Representa o benefício total médio ou utilidade social de grupo:
  $$S_i = \sum_{j=1}^n w_j \cdot \frac{f_j^* - x_{ij}}{f_j^* - f_j^-}$$
* **Índice de Arrependimento ($R_i$):** Representa a pior desvantagem local (arrependimento individual):
  $$R_i = \max_j \left[ w_j \cdot \frac{f_j^* - x_{ij}}{f_j^* - f_j^-} \right]$$

#### 3. Cálculo do Índice VIKOR Multicritério ($Q_i$)
Calcula-se o índice de compromisso ponderado $Q_i \in [0, 1]$:
$$Q_i = v \cdot \frac{S_i - S^*}{S^- - S^*} + (1-v) \cdot \frac{R_i - R^*}{R^- - R^*}$$
Onde:
* $S^* = \min_i S_i$ e $S^- = \max_i S_i$
* $R^* = \min_i R_i$ e $R^- = \max_i R_i$
* $v$ é o peso da estratégia do voto da maioria ("utilidade de grupo"). Tipicamente adota-se $v = 0.5$ para balancear.

#### 4. Condições de Decisão e Estabilidade
O VIKOR propõe como solução a alternativa que obtém o menor valor de $Q_i$ (primeiro do ranking), desde que atenda a duas condições estritas:
* **Condição 1: Vantagem Aceitável ($C1$):**
  $$Q(A^{(2)}) - Q(A^{(1)}) \ge DQ$$
  Onde $A^{(2)}$ é o segundo melhor ranqueado, $A^{(1)}$ é o melhor e $DQ = \frac{1}{m - 1}$ ($m$ sendo a quantidade de alternativas).
* **Condição 2: Estabilidade Aceitável ($C2$):**
  A alternativa $A^{(1)}$ deve também ser a melhor ranqueada em termos de $S_i$ ou $R_i$.

Caso uma das condições não seja cumprida, o algoritmo propõe um conjunto de compromisso de alternativas que empatam.

---

## 🚀 Instalação e Execução
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Acesse: `http://127.0.0.1:5000`
