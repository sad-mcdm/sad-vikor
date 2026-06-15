# Nexus VIKOR — Otimização de Compromisso Multicritério

Este repositório é o módulo independente do ecossistema **NEXUS MCDM**, configurado para operar exclusivamente com o método **VIKOR (ViseKriterijumska Optimizacija I Kompromisno Resenje)**.

---

## 🎨 Identidade Visual e Branding
- **Nome Oficial:** Nexus VIKOR
- **Cores Oficiais:** Esmeralda (`#059669`) e Bronze (`#B45309`)
- **Conceito Visual:** Curvas de utilidade social e arrependimento individual convergentes.
- **Copyright:** Direitos Reservados © 2026 NEXUS-MCDM.

---

## 🌟 Recursos e Matemática

- **Compromisso Social:** O VIKOR ranqueia as alternativas através da ponderação entre a utilidade de grupo ($S_i$, correspondente ao benefício médio) e o arrependimento individual ($R_i$, correspondente à pior desvantagem local):
  - `S_i = Sum_{j} (w_j * (f_j* - x_ij) / (f_j* - f_j-))`
  - `R_i = Max_{j} (w_j * (f_j* - x_ij) / (f_j* - f_j-))`
- **Pontuação de Compromisso (Q_i):**
  - `Q_i = v * (S_i - S*) / (S- - S*) + (1-v) * (R_i - R*) / (R- - R*)`
- **Condições de Estabilidade:** Validação de 'Vantagem Aceitável' e 'Estabilidade Aceitável' no relatório final em PDF.

---

## 🚀 Instalação e Execução
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
