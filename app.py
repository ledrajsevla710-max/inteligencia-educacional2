import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import os

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestão Educacional - TRI", layout="wide", page_icon="🏫")

# --- 2. MAPA DE HABILIDADES (9º ANO MATEMÁTICA) ---
MAPA_HABILIDADES = {
    "Matemática": {
        "Q01": "D6 - Reconhecer ângulos como mudança de direção ou giros de segmentos de reta.",
        "Q02": "EF06MA27 - Determinar medidas de ângulos (reto, agudo, obtuso) e utilizar transferidor.",
        "Q03": "EF06MA26 - Resolver problemas que envolvam a noção de ângulo em diferentes contextos.",
        "Q04": "D16 - Identificar a localização de números inteiros na reta numérica.",
        "Q05": "D20 - Resolver problemas com números inteiros envolvendo as operações fundamentais.",
        "Q06": "EF07MA04 - Resolver e elaborar problemas que envolvam operações com números inteiros.",
        "Q07": "D21 - Reconhecer as diferentes representações de um número racional (fração, decimal, %).",
        "Q08": "D23 - Identificar frações equivalentes a partir de representações gráficas ou numéricas.",
        "Q09": "D26 - Resolver problemas com números racionais envolvendo as operações fundamentais.",
        "Q10": "EF07MA10 - Comparar e ordenar números racionais em diferentes contextos e na reta.",
        "Q11": "EF07MA01.1PI - Calcular raiz quadrada exata de números naturais.",
        "Q12": "D19 - Resolver problemas com potenciação de números naturais (expoente inteiro).",
        "Q13": "D6/EF06MA25 - Reconhecer giros de uma volta completa (360°) em medidores e ponteiros.",
        "Q14": "D16/EF07MA03 - Comparar e ordenar números inteiros em situações de pontuação/saldo.",
        "Q15": "D21/EF06MA08 - Converter frações usuais (1/2, 1/4, 1/5) para sua representação decimal.",
        "Q16": "D23/EF06MA07 - Reconhecer frações equivalentes por simplificação ou amplificação.",
        "Q17": "D26/EF07MA12 - Operações combinadas entre frações e decimais no cotidiano.",
        "Q18": "D19/EF07MA01 - Resolver problemas envolvendo o Mínimo Múltiplo Comum (MMC).",
        "Q19": "D20/EF07MA04 - Aplicar regra de sinais na divisão de números inteiros.",
        "Q20": "EF06MA27 - Classificar ângulos obtusos (entre 90° e 180°) em figuras ou giros.",
        "Q21": "D21/EF07MA10 - Transformar números decimais finitos em frações decimais.",
        "Q22": "D26/EF06MA03 - Multiplicação de números decimais e posicionamento da vírgula."
    }
}

GABARITOS = {
    "Matemática": {f'Q{i:02d}': g for i, g in enumerate(['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B'], 1)}
}

# --- 3. FUNÇÕES TÉCNICAS ---
def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel(score):
    if score < 150: return "Abaixo do Básico", "#FF4B4B"
    if score < 200: return "Básico", "#FACA2E"
    if score < 250: return "Proficiente", "#00CC96"
    return "Avançado", "#1F77B4"

def gerar_modelo_excel():
    output = io.BytesIO()
    # Criando uma planilha com colunas Escola, Turma, Aluno e Q01-Q22
    colunas = ["Escola", "Turma", "Nome"] + [f"Q{i:02d}" for i in range(1, 23)]
    df_modelo = pd.DataFrame(columns=colunas)
    # Exemplo de preenchimento
    df_modelo.loc[0] = ["Escola Municipal A", "9º Ano A", "Exemplo Aluno"] + ["A"]*22
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_modelo.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. INTERFACE ---
st.title("🏫 Sistema de Monitoramento Pedagógico (TRI)")

# Barra Lateral com Botão de Download do Modelo
st.sidebar.header("⚙️ Configurações")
st.sidebar.download_button(
    label="📂 Baixar Planilha Modelo",
    data=gerar_modelo_excel(),
    file_name="modelo_respostas_tri.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática"])
serie = st.sidebar.selectbox("S
