import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import tempfile # Para gerenciar as imagens dos gráficos

# --- CONFIGURAÇÕES E DADOS (Mantidos conforme anterior) ---
st.set_page_config(page_title="Gestão TRI José de Freitas", layout="wide", page_icon="🏛️")

DICIONARIO_HABILIDADES = {f"Q{i:02d}": f"Habilidade detalhada do item {i} conforme matriz SAEB/BNCC." for i in range(1, 23)}
GABARITOS_MESTRE = {
    "2º Ano": ['A']*22, "5º Ano": ['B']*22, 
    "9º Ano": ['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B']
}

def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- INTERFACE ---
st.title("🏛️ Sistema de Gestão TRI - José de Freitas")

serie_sel = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])
uploaded_file = st.file_uploader("📂 Envie a Planilha", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito_dict = {f'Q{i:02d}': GABARITOS_MESTRE[serie_sel][i-1] for i in range(1, 23)}

    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito_dict[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    esc_sel = st.sidebar.selectbox("Escola:", ["Geral"] + sorted(list(df['Escola'].unique())))
    df_f = df if esc_sel == "Geral" else df[df['Escola'] == esc_sel]

    st.subheader(f"📊 Dashboard: {serie_sel} | {esc_sel}")
    
    # --- GERADOR DE RELATÓRIO PDF COM IMAGENS ---
    if st.button("📄 GERAR RELATÓRIO COM GRÁFICOS (PDF)", use_container_width=True):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'RELATÓRIO PEDAGÓGICO COM ANÁLISE DE ITENS', ln=True, align='C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 7, f'Série: {serie_sel} | Escola: {esc_sel}', ln=True, align='C')
        pdf.ln(5)

        for q in cols_q:
            # 1. Gerar o gráfico em memória
            stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
            fig, ax = plt.subplots(figsize=(4, 3))
            gab = gabarito_dict[q]
            cores = ['#2ECC71' if l == gab else '#E74C3C' for l in ['A','B','C','D']]
            ax.bar(['A','B','C','D'], stats, color=cores)
            ax.set_title(f"Questão {q} (Gab: {gab})")
            ax.set_ylim(0, 110)
            
            # 2. Salvar o gráfico como imagem temporária
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                fig.savefig(tmpfile.name, format="png", bbox_inches='tight')
                plt.close(fig)
                
                # 3. Inserir no PDF
                if pdf.get_y() > 200: pdf.add_page() # Nova página se não couber
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 8, f"Questão {q} - Acerto: {stats[gab]:.1f}%", ln=True)
                pdf.image(tmpfile.name, x=10, w=80) # Adiciona a imagem do gráfico
                pdf.set_y(pdf.get_y() + 5)
                pdf.set_font('Arial', 'I', 9)
                pdf.multi_cell(0, 5, f"Habilidade: {DICIONARIO_HABILIDADES[q]}")
                pdf.ln(10)

        pdf_out = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_out).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_Grafico.pdf" style="display:block; text-align:center; padding:15px; background-color:#2ecc71; color:white; border-radius:10px; text-decoration:none; font-weight:bold;">📥 BAIXAR RELATÓRIO COM GRÁFICOS</a>', unsafe_allow_html=True)

    # --- EXIBIÇÃO NA TELA ---
    grid = st.columns(2)
    for i, q in enumerate(cols_q):
        with grid[i % 2]:
            stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
            fig, ax = plt.subplots()
            ax.bar(['A','B','C','D'], stats, color=['#2ECC71' if l == gabarito_dict[q] else '#E74C3C' for l in ['A','B','C','D']])
            st.pyplot(fig)
            st.info(f"**Item {q}:** {DICIONARIO_HABILIDADES[q]}")
