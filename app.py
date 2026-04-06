import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64

st.set_page_config(page_title="SAEPI - Inteligência Educacional", layout="wide", page_icon="🎓")

# --- MAPEAMENTO DE DESCRITORES (Exemplo para Matemática) ---
# Você pode ajustar esses nomes de acordo com a matriz do Piauí
MAPA_DESCRITORES = {
    f'Q{i:02d}': f'Descritor D{i+1}' for i in range(1, 23)
}

# --- MOTOR TRI AVANÇADO ---
def calcular_score_tri(respostas, parametros):
    if not any(respostas): return 0.0
    theta = 0.0
    for _ in range(25):
        p_acerto = [1 / (1 + np.exp(-p['a'] * (theta - p['b']))) for p in parametros]
        erro = sum(respostas) - sum(p_acerto)
        theta += erro * 0.1
    return max(0, min(1000, (theta * 50) + 250))

itens_config = []
for i in range(22):
    if i < 7: itens_config.append({'a': 1.2, 'b': -1.5})
    elif i < 15: itens_config.append({'a': 1.5, 'b': 0.0})
    else: itens_config.append({'a': 2.0, 'b': 1.8})

# --- FUNÇÃO GERADORA DE PDF DETALHADO ---
def gerar_pdf_detalhado(df_geral, media_mun, escola, serie, alertas_descritores):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATÓRIO DE DESEMPENHO - JOSÉ DE FREITAS", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, f"Série: {serie} | Unidade: {escola if escola != 'Todas' else 'Geral'}", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f"Proficiência Média: {media_mun:.1f}", ln=True)
    
    # Análise de Habilidades
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "DIAGNÓSTICO DE HABILIDADES CRÍTICAS", ln=True, fill=True)
    
    pdf.set_font("Arial", '', 11)
    pdf.ln(2)
    for alerta in alertas_descritores:
        pdf.multi_cell(0, 8, f"- {alerta}")

    # Tabela por Escola (se for visão Geral)
    if escola == "Todas":
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "DESEMPENHO POR ESCOLA", ln=True)
        resumo = df_geral.groupby('Escola')['Proficiência_TRI'].mean().reset_index()
        pdf.set_font("Arial", '', 10)
        for _, row in resumo.iterrows():
            pdf.cell(0, 8, f"{row['Escola']}: {row['Proficiência_TRI']:.1f} pts", ln=True)
            
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.sidebar.title("Portal SAEPI-JF")

# Filtros Globais na Sidebar
perfil = st.sidebar.selectbox("Perfil de Acesso", ["👨‍🏫 Professor", "📊 Gestor"])
disciplina = st.sidebar.selectbox("Disciplina", ["Matemática", "Português"])
serie_selecionada = st.sidebar.selectbox("Série/Ano", ["2º Ano", "5º Ano", "9º Ano"])

if perfil == "👨‍🏫 Professor":
    st.header(f"Lançamento: {disciplina} - {serie_selecionada}")
    tabs = st.tabs(["Individual", "Lote (Excel)"])
    
    with tabs[0]:
        nome = st.text_input("Nome do Estudante")
        c1, c2 = st.columns(2)
        esc_input = c1.text_input("Nome da Escola")
        turma_input = c2.text_input("Turma")
        
        st.write("Marque os acertos:")
        cols = st.columns(4)
        resps = []
        for i in range(1, 23):
            with cols[(i-1)%4]:
                r = st.checkbox(f"Q{i:02d}", key=f"check_{i}")
                resps.append(1 if r else 0)
        if st.button("Calcular Proficiência"):
            n = calcular_score_tri(resps, itens_config)
            st.metric("Resultado", f"{n:.1f}")

    with tabs[1]:
        arq = st.file_uploader("Subir Planilha da Turma", type="xlsx", key="upload_prof")
        if arq:
            dfp = pd.read_excel(arq)
            qs = [f'Q{i:02d}' for i in range(1, 23)]
            if all(c in dfp.columns for c in qs):
                dfp['Proficiência_TRI'] = dfp[qs].apply(lambda x: calcular_score_tri(x
