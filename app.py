import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64

st.set_page_config(page_title="SAEPI - Inteligência Educacional", layout="wide", page_icon="🎓")

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

# --- FUNÇÃO GERADORA DE PDF ---
def gerar_pdf(df_geral, media_mun, alertas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Relatorio de Gestao - Jose de Freitas", ln=True, align='C')
    
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Media de Proficiencia Municipal: {media_mun:.1f}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Alertas de Habilidades:", ln=True)
    pdf.set_font("Arial", '', 11)
    for alerta in alertas[:10]: # Limita a 10 alertas no PDF
        pdf.multi_cell(0, 8, f"- {alerta}")

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Resumo por Escola:", ln=True)
    resumo = df_geral.groupby('Escola')['Proficiência_TRI'].mean().reset_index()
    pdf.set_font("Arial", '', 10)
    for _, row in resumo.iterrows():
        pdf.cell(0, 8, f"{row['Escola']}: {row['Proficiência_TRI']:.1f}", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.sidebar.title("Portal SAEPI-JF")
perfil = st.sidebar.selectbox("Perfil", ["Professor", "Gestor"])

if perfil == "Professor":
    st.header("Lançamento de Resultados")
    tabs = st.tabs(["Individual", "Planilha"])
    
    with tabs[0]:
        nome = st.text_input("Nome do Aluno")
        cols = st.columns(4)
        resps = []
        for i in range(1, 23):
            with cols[(i-1)%4]:
                r = st.checkbox(f"Q{i:02d}")
                resps.append(1 if r else 0)
        if st.button("Calcular"):
            n = calcular_score_tri(resps, itens_config)
            st.success(f"Nota: {n:.1f}")

    with tabs[1]:
        arq = st.file_uploader("Upload Excel", type="xlsx", key="p1")
        if arq:
            dfp = pd.read_excel(arq)
            qs = [f'Q{i:02d}' for i in range(1, 23)]
            dfp['Proficiência_TRI'] = dfp[qs].apply(lambda x: calcular_score_tri(x.tolist(), itens_config), axis=1)
            st.dataframe(dfp[['Nome', 'Proficiência_TRI']])

else:
    st.header("Painel do Gestor")
    arq_g = st.file_uploader("Upload Planilha Municipal", type="xlsx", key="g1")
    if arq_g:
        dfg = pd.read_excel(arq_g)
        qs = [f'Q{i:02d}' for i in range(1, 23)]
        dfg['Proficiência_TRI'] = dfg[qs].apply(lambda x: calcular_score_tri(x.tolist(), itens_config), axis=1)
        
        m_mun = dfg['Proficiência_TRI'].mean()
        st.metric("Média Municipal", f"{m_mun:.1f}")
        
        st.bar_chart(dfg.groupby('Escola')['Proficiência_TRI'].mean())
        
        percentuais = dfg[qs].mean() * 100
        criticas = percentuais[percentuais < 50].index.tolist()
        alertas = [f"Questao {q}: Baixo acerto" for q in criticas]
        
        # O ERRO ESTAVA AQUI: As aspas agora estão fechadas corretamente
        if st.button("📄 Gerar PDF"):
            pdf_bytes = gerar_pdf(dfg, m_mun, alertas)
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_JF.pdf">Clique aqui para baixar o PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
