import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt

st.set_page_config(page_title="SAEPI JF - Inteligência Educacional", layout="wide", page_icon="🎓")

# --- BANCO DE DADOS PEDAGÓGICO (EXEMPLO 9º ANO) ---
# (Repita esta estrutura para os 66 itens conforme as listas enviadas)
GABARITO_OFICIAL = {
    'Q01': 'C', 'Q02': 'B', 'Q03': 'A', 'Q04': 'C', 'Q05': 'B', 
    'Q06': 'C', 'Q07': 'C', 'Q08': 'A', 'Q09': 'B', 'Q10': 'C',
    'Q11': 'C', 'Q12': 'C', 'Q13': 'D', 'Q14': 'C', 'Q15': 'B',
    'Q16': 'A', 'Q17': 'C', 'Q18': 'C', 'Q19': 'A', 'Q20': 'C',
    'Q21': 'B', 'Q22': 'B'
}

# --- FUNÇÕES DE ESTILO E PROFICIÊNCIA ---
def obter_nivel(score):
    if score < 125: return "Abaixo do Básico", "#FF4B4B" # Vermelho
    if score < 175: return "Básico", "#FACA2E" # Amarelo
    if score < 225: return "Proficiente", "#00CC96" # Verde
    return "Avançado", "#1F77B4" # Azul

# --- MOTOR TRI ---
def calcular_tri(respostas):
    acertos = sum(respostas)
    if acertos == 0: return 100.0
    # Simulação de escala SAEB (0-400)
    return (acertos / 22) * 300 + 100

# --- GERADOR DE PDF PROFISSIONAL ---
class PDF_SAEPI(FPDF):
    def header(self):
        self.set_fill_color(31, 119, 180)
        self.rect(0, 0, 210, 35, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 15, 'PREFEITURA DE JOSÉ DE FREITAS - SEMED', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Relatório de Proficiência e Diagnóstico Pedagógico', 0, 1, 'C')
        self.ln(15)

def baixar_pdf(pdf_buffer, nome_arquivo):
    b64 = base64.b64encode(pdf_buffer).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{nome_arquivo}" style="padding:12px; background-color:#1F77B4; color:white; border-radius:8px; text-decoration:none; font-weight:bold;">📥 BAIXAR RELATÓRIO PDF</a>'

# --- INTERFACE ---
st.title("📊 Portal de Inteligência Educacional - SAEPI JF")
st.markdown("---")

perfil = st.sidebar.radio("Selecione o Perfil:", ["Gestor Municipal", "Professor"])
serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

uploaded_file = st.file_uploader("Suba a planilha de resultados (Excel)", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    
    # Processamento de Dados
    for index, row in df.iterrows():
        resps_binarias = [1 if row[q] == GABARITO_OFICIAL[q] else 0 for q in cols_q]
        df.at[index, 'Proficiência'] = calcular_tri(resps_binarias)

    media_geral = df['Proficiência'].mean()
    nivel_txt, cor_nivel = obter_nivel(media_geral)

    # Dashboard Principal
    c1, c2 = st.columns([1, 3])
    with c1:
        st.metric("Média de Proficiência", f"{media_geral:.1f}")
        st.markdown(f"<h3 style='color:{cor_nivel};'>{nivel_txt}</h3>", unsafe_allow_html=True)

    with c2:
        st.subheader("Desempenho por Questão (Vertical)")
        # Calculando percentual de acerto por questão
        acertos_por_q = (df[cols_q] == pd.Series(GABARITO_OFICIAL)).mean() * 100
        
        fig, ax = plt.subplots(figsize=(10, 4))
        acertos_por_q.plot(kind='bar', color='#1F77B4', ax=ax, width=0.4)
        ax.set_ylim(0, 100)
        ax.set_ylabel("% de Acerto")
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("🔍 Análise de Alternativas e Distratores")
    
    # Tabela de Distratores
    col_dist = st.columns(3)
    for i, q in enumerate(cols_q[:6]): # Exemplo para as primeiras 6 questões
        with col_dist[i % 3]:
            st.write(f"**Questão {q}** (Gabarito: :green[{GABARITO_OFICIAL[q]}])")
            freq = df[q].value_counts(normalize=True).sort_index() * 100
            for alt in ['A', 'B', 'C', 'D']:
                p = freq.get(alt, 0)
                cor = "green" if alt == GABARITO_OFICIAL[q] else "grey"
                st.write(f"- {alt}: {p:.1f}%")
                st.progress(p/100)

    # --- GERAÇÃO DE PDF ---
    if st.button("Gerar Relatório Oficial"):
        pdf = PDF_SAEPI()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Diagnóstico: {serie} - José de Freitas", ln=True)
        pdf.set_text_color(31, 119, 180)
        pdf.cell(0, 10, f"Proficiência Média: {media_geral:.1f} ({nivel_txt})", ln=True)
        
        pdf.ln(10)
        pdf.set_text_color(0,0,0)
        pdf.cell(0, 10, "Análise de Itens Críticos:", ln=True)
        pdf.set_font("Arial", '', 10)
        
        for q in cols_q:
            p_acerto = (df[q] == GABARITO_OFICIAL[q]).mean() * 100
            if p_acerto < 50:
                pdf.cell(0, 8, f"Item {q}: Baixo desempenho ({p_acerto:.1f}%). Gabarito {GABARITO_OFICIAL[q]}.", ln=True)
        
        pdf_out = pdf.output(dest='S').encode('latin-1')
        st.markdown(baixar_pdf(pdf_out, f"Relatorio_SAEPI_{serie}.pdf"), unsafe_allow_html=True)

else:
    st.info("Aguardando upload da planilha Excel para gerar os gráficos e a proficiência...")
