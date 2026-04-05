# inteligencia-educacional2
"Sistema de Inteligência Educacional e Análise de Proficiência (Escala SAEPI/SAEB). Desenvolvido para processamento de dados pedagógicos, projeto de TRI simulado e monitoramento de descritores BNCC para a rede municipal."
# 🎓 Inteligência Educacional PI
> **Sistema de Monitoramento e Análise de Proficiência Pedagógica**

Este repositório centraliza as ferramentas de avaliação para o **2º, 5º e 9º anos**, focadas no alinhamento com os descritores do **SAEPI/SAEB**.

---

## 🚀 Funcionalidades
- [x] **Elaboração de Itens:** Questões inéditas por descritor (BNCC).
- [x] **Cálculo de Proficiência:** Algoritmo de pesos (Simulação TRI).
- [x] **Dashboards:** Visualização de desempenho por turma e habilidade.

## 📊 Metodologia de Cálculo
Diferente da contagem simples de acertos, este sistema utiliza **Média Ponderada por Dificuldade**:
- **Nível 1 (Fácil):** Peso 1.0
- **Nível 2 (Médio):** Peso 2.0
- **Nível 3 (Difícil):** Peso 3.0

### 📋 Escala de Proficiência (Exemplo 9º Ano)
| Nota | Nível | Descrição |
| :--- | :--- | :--- |
| < 250 | **Insuficiente** | Necessita intervenção imediata nos descritores base. |
| 250 - 300 | **Básico** | Domínio parcial das competências da série. |
| 300 - 350 | **Proficiente** | Domínio esperado para o período letivo. |
| > 350 | **Avançado** | Supera as expectativas de aprendizagem. |

---

## 🛠️ Como usar os arquivos
1. Acesse a pasta `/planilhas` para baixar o modelo de lançamento.
2. Os cadernos de prova estão em `/provas/pdf`.
3. Para rodar o analisador em Python, execute: `python analisador_saepi.py`.

---
**Desenvolvido por Jardel Alves Vieira** *Especialista em Educação Física e Gestão Pedagógica*
