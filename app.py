import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import os

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestão Municipal TRI", layout="wide", page_icon="📈")

# --- 2. MATRIZ DE REFERÊNCIA (EXEMPLO 9º ANO) ---
MAPA_HABILIDADES = {
    "Matemática": {f"Q{i:02d}": f"Descritor D{i} - Habilidade Pedagógica SAEPI/SAEB" for i in range(1, 23)}
}
# Personalizando algumas para o 9º ano conforme solicitado anteriormente
MAPA_HABILIDADES["Matemática"].update({
    "Q01": "D6 - Reconhecer ângulos como mudança de direção ou giros.",
    "Q02": "EF06MA27 - Determinar medidas de ângulos (reto, agudo, obtuso).",
    "Q03": "EF06MA26 - Problemas com noção de ângulo.",
    "Q04": "D16 - Números inteiros na reta numérica.",
})

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
    colunas = ["Escola", "Turma", "Nome"] + [f"Q{i:02d}" for i in range(1, 23)]
    dados = [["Escola A", "9º Ano A", "Aluno 1"] + ["C"]*22, ["Escola B", "9º Ano B", "Aluno 2"] + ["A"]*22]
    df_m = pd.DataFrame(dados, columns=colunas)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_m.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. INTERFACE ---
st.title("📊 Painel de Inteligência Educacional - Monitoramento TRI")

st.sidebar.header("⚙️ Painel de Controle")
st.sidebar.download_button("📥 Baixar Planilha Modelo", gerar_modelo_excel(), "modelo_gestao.xlsx", use_container_width=True)

disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática"])
# CORRIGIDO: Agora aparecem todas as séries
serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

uploaded_file = st.file_uploader("📂 Faça o upload da planilha de resultados", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito = GABARITOS[disciplina]

    # Processamento TRI
    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    # --- 1. VISÃO GERAL DAS ESCOLAS ---
    st.subheader("🏫 Ranking Geral das Escolas")
    ranking = df.groupby('Escola')['Proficiência'].mean().sort_values(ascending=False).reset_index()
    
    col_rank1, col_rank2 = st.columns([2, 1])
    with col_rank1:
        fig_r, ax_r = plt.subplots(figsize=(10, 4))
        ax_r.barh(ranking['Escola'], ranking['Proficiência'], color='#1F77B4')
        ax_r.set_xlabel("Proficiência Média")
        st.pyplot(fig_r)
    with col_rank2:
        st.dataframe(ranking.style.format({"Proficiência": "{:.1f}"}), hide_index=True)

    st.divider()

    # --- 2. FILTROS POR TURMA ---
    st.subheader("🔍 Detalhamento por Unidade e Turma")
    c1, c2 = st.columns(2)
    esc_sel = c1.selectbox("Selecionar Escola:", ["Todas"] + sorted(list(df['Escola'].unique())))
    tur_sel = c2.selectbox("Selecionar Tur
