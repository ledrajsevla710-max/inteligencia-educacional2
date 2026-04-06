import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Protótipo SAEPI - TRI", layout="wide", page_icon="📊")

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
    },
    "Língua Portuguesa": {
        "Q01": "D1 - Localizar informações explícitas em textos.",
        "Q02": "D3 - Inferir o sentido de palavra ou expressão.",
        "Q03": "D4 - Inferir uma informação implícita em um texto.",
        "Q04": "D6 - Identificar o tema de um texto."
    }
}

GABARITOS = {
    "Matemática": {f'Q{i:02d}': g for i, g in enumerate(['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B'], 1)},
    "Língua Portuguesa": {f'Q{i:02d}': g for i, g in enumerate(['A','D','B','C','A','D','B','C','B','A','D','C','B','A','D','C','B','B','A','D','C','A'], 1)}
}

# --- 3. FUNÇÕES TÉCNICAS (TRI E ARQUIVOS) ---
def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    theta_f = thetas[np.argmax(verossimilhanca)]
    return (theta_f + 4) * 50

def obter_nivel(score):
    if score < 150: return "Abaixo do Básico", "#FF4B4B"
    if score < 200: return "Básico", "#FACA2E"
    if score < 250: return "Proficiente", "#00CC96"
    return "Avançado", "#1F77B4"

def gerar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. INTERFACE DO USUÁRIO ---
st.title("📊 Protótipo de Inteligência Educacional - Matriz TRI")
st.markdown("---")

disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

if st.sidebar.button("📂 Gerar Planilha de Teste"):
    data = {"Nome": [f"Aluno {i}" for i in range(1, 11)], "Escola": ["Escola Modelo"]*10}
    for i in range(1, 23): data[f'Q{i:02d}'] = np.random.choice(['A','B','C','D'], 10)
    st.sidebar.download_button("⬇️ Baixar Modelo", gerar_excel(pd.DataFrame(data)), "modelo_saepi.xlsx")

uploaded_file = st.file_uploader("Suba a planilha Excel para processamento", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito_atual = GABARITOS[disciplina]
    mapa_atual = MAPA_HABILIDADES.get(disciplina, {})

    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito_atual[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    media_geral = df['Proficiência'].mean()
    nivel_txt, cor_nivel = obter_nivel(media_geral)

    # Dashboard Principal
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Média de Proficiência", f"{media_geral:.1f}")
        st.markdown(f"<div style='background-color:{cor_nivel}; padding:20px; border-radius:10px; color:white; text-align:center;'><h3>{nivel_txt}</h3></div>", unsafe_allow_html=True)
        st.download_button("📊 Baixar Resultados (Excel)", gerar_excel(df), "resultados_tri.xlsx")

    with c2:
