import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64

st.set_page_config(page_title="Gestão Educacional TRI", layout="wide")

# --- MOTOR TRI (Mesma lógica anterior) ---
def calcular_score_tri(respostas, parametros):
    if not any(respostas): return 0.0
    theta = 0.0
    for _ in range(20):
        p_acerto = [1 / (1 + np.exp(-p['a'] * (theta - p['b']))) for p in parametros]
        erro = sum(respostas) - sum(p_acerto)
        theta += erro * 0.1
    return max(0, min(1000, (theta * 50) + 250))

# Configuração de Itens (Simulando Descritores SAEPI)
itens_config = []
for i in range(22):
    if i < 7: itens_config.append({'a': 1.2, 'b': -1.5, 'desc': f'D{i+1}'})
    elif i < 15: itens_config.append({'a': 1.5, 'b': 0.0, 'desc': f'D{i+1}'})
    else: itens_config.append({'a': 2.0, 'b': 1.8, 'desc': f'D{i+1}'})

# --- FUNÇÃO PARA GERAR PDF ---
def gerar_pdf(df_geral, media_mun, analise_habilidades):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Relatorio de Proficiencia Municipal - SAEPI", ln=True, align='C')
    
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Media Geral do Municipio: {media_mun:.1f} pontos", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Habilidades que precisam de intervencao:", ln=True)
    pdf.set_font("Arial", '', 11)
    for hab in analise_habilidades:
        pdf.multi_cell(0, 10, f"- {hab}")

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Resumo por Escola:", ln=True)
    pdf.set_font("Arial", '', 10)
    
    resumo = df_geral.groupby('Escola')['Proficiência_TRI'].mean().reset_index()
    for index, row in resumo.iterrows():
        pdf.cell(0, 10, f"{row['Escola']}: {row['Proficiência_TRI']:.1f}", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.title("📊 Painel de Monitoramento Municipal (TRI)")

arquivo = st.file_uploader("Suba a planilha (Escola, Turma, Nome, Q01-Q22)", type=["xlsx"])

if arquivo:
    df = pd.read_excel(arquivo)
    colunas_q = [f'Q{i:02d}' for i in range(1, 23)]
    
    if all(c in df.columns for c in colunas_q):
        df['Proficiência_TRI'] = df[colunas_q].apply(lambda x: calcular_score_tri(x.tolist(), itens_config), axis=1)
        
        media_municipio = df['Proficiência_TRI'].mean()
        
        # Métrica em destaque
        st.metric("Média Geral do Município", f"{media_municipio:.1f}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Proficiência por Escola")
            media_escola = df.groupby('Escola')['Proficiência_TRI'].mean().sort_values()
            st.bar_chart(media_escola)
            
        with col2:
            st.write("### Análise de Habilidades (Críticas)")
            # Calcula % de acerto por questão para identificar fraquezas
            percentual_acerto = df[colunas_q].mean() * 100
            questoes_criticas = percentual_acerto[percentual_acerto < 50].index.tolist()
            
            alertas = []
            for q in questoes_criticas:
                st.warning(f"Alerta: Baixo desempenho na {q}")
                alertas.append(f"A questao {q} teve menos de 50% de acertos. Revisar Descritor correspondente.")

        # Botão para PDF
        if st.button("Gerar Relatório em PDF"):
            pdf_bytes = gerar_pdf(df, media_municipio, alertas)
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_Municipal.pdf">Baixar PDF Agora</a>'
            st.markdown(href, unsafe_allow_html=True)
