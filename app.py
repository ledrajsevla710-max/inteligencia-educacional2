import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64

st.set_page_config(page_title="SAEPI - Inteligência Educacional", layout="wide", page_icon="🎓")

# --- MAPEAMENTO DE DESCRITORES (Ajuste conforme a matriz do Piauí) ---
MAPA_DESCRITORES = {f'Q{i:02d}': f'Descritor D{i}' for i in range(1, 23)}

# --- MOTOR TRI AVANÇADO (MODELO 2PL) ---
def calcular_score_tri(respostas, parametros):
    if not any(respostas): return 0.0
    theta = 0.0
    for _ in range(25):
        p_acerto = [1 / (1 + np.exp(-p['a'] * (theta - p['b']))) for p in parametros]
        erro = sum(respostas) - sum(p_acerto)
        theta += (erro * 0.1)
    return max(0, min(1000, (theta * 50) + 250))

# Parâmetros fixos para simulação (7 fáceis, 8 médias, 7 difíceis)
itens_config = []
for i in range(22):
    if i < 7: itens_config.append({'a': 1.2, 'b': -1.5})
    elif i < 15: itens_config.append({'a': 1.5, 'b': 0.0})
    else: itens_config.append({'a': 2.0, 'b': 1.8})

# --- FUNÇÃO GERADORA DE PDF ---
def gerar_pdf_detalhado(df_geral, media_mun, escola, serie, alertas_descritores):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATORIO DE DESEMPENHO - JOSE DE FREITAS", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, f"Serie: {serie} | Unidade: {escola}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f"Proficiencia Media: {media_mun:.1f}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "DIAGNOSTICO DE HABILIDADES CRITICAS", ln=True)
    pdf.set_font("Arial", '', 11)
    for alerta in alertas_descritores[:8]:
        pdf.multi_cell(0, 8, f"- {alerta}")
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.sidebar.title("Portal SAEPI-JF")
perfil = st.sidebar.selectbox("Perfil de Acesso", ["Professor", "Gestor"])
disciplina = st.sidebar.selectbox("Disciplina", ["Matematica", "Portugues"])
serie_ref = st.sidebar.selectbox("Ano/Serie", ["2 Ano", "5 Ano", "9 Ano"])

if perfil == "Professor":
    st.header(f"Lancamento: {disciplina} - {serie_ref}")
    t1, t2 = st.tabs(["Individual", "Planilha"])
    
    with t1:
        st.write("Marque os acertos:")
        cols = st.columns(4)
        resps = []
        for i in range(1, 23):
            with cols[(i-1)%4]:
                r = st.checkbox(f"Q{i:02d}", key=f"p_{i}")
                resps.append(1 if r else 0)
        if st.button("Calcular"):
            nota = calcular_score_tri(resps, itens_config)
            st.success(f"Nota TRI: {nota:.1f}")

    with t2:
        arq_p = st.file_uploader("Subir Excel da Turma", type="xlsx", key="up_p")
        if arq_p:
            dfp = pd.read_excel(arq_p)
            qs = [f'Q{i:02d}' for i in range(1, 23)]
            if all(c in dfp.columns for c in qs):
                # LINHA CORRIGIDA ABAIXO (Parênteses fechados)
                dfp['Proficiência_TRI'] = dfp[qs].apply(lambda x: calcular_score_tri(x.tolist(), itens_config), axis=1)
                st.
