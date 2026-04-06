import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import tempfile

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestão TRI José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. BANCO DE DADOS (HABILIDADES E GABARITOS) ---
DICIONARIO_HABILIDADES = {
    f"Q{i:02d}": f"Descritor SAEB/BNCC correspondente ao item {i} da matriz de referência." for i in range(1, 23)
}
# Atualizando as que já temos detalhadas
DICIONARIO_HABILIDADES.update({
    "Q01": "D6 - Identificar ângulos como mudança de direção ou giros.",
    "Q02": "EF06MA27 - Classificar ângulos (agudo, reto, obtuso).",
    "Q21": "D21 - Converter números decimais em frações e vice-versa."
})

GABARITOS_MESTRE = {
    "2º Ano": ['A']*22, "5º Ano": ['B']*22, 
    "9º Ano": ['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B']
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

# --- 4. INTERFACE ---
st.title("🏛️ Inteligência Educacional - José de Freitas")

st.sidebar.header("📋 Configuração")
disciplina_sel = st.sidebar.selectbox("Disciplina:", ["Matemática"])
serie_sel = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

uploaded_file = st.file_uploader(f"📂 Envie a Planilha ({serie_sel})", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gab_atual = {f'Q{i:02d}': GABARITOS_MESTRE[serie_sel][i-1] for i in range(1, 23)}

    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gab_atual[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    esc_sel = st.sidebar.selectbox("Escola:", ["Geral"] + sorted(list(df['Escola'].unique())))
    df_f = df if esc_sel == "Geral" else df[df['Escola'] == esc_sel]

    st.subheader(f"📊 Dashboard: {serie_sel} - {esc_sel}")
    st.metric("Média TRI", f"{df_f['Proficiência'].mean():.1f}")

    # --- SEÇÃO DE DOWNLOADS ---
    col_pdf1, col_pdf2 = st.columns(2)

    with col_pdf1:
        if st.button("📄 PDF COMPLETO (COM GRÁFICOS)", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'RELATÓRIO PEDAGÓGICO COMPLETO - COM GRÁFICOS', ln=True, align='C')
            for q in cols_q:
                stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                fig, ax = plt.subplots(figsize=(4, 3))
                ax.bar(['A','B','C','D'], stats, color=['#2ECC71' if l == gab_atual[q] else '#E74C3C' for l in ['A','B','C','D']])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    fig.savefig(tmp.name, format="png")
                    plt.close(fig)
                    if pdf.get_y() > 210: pdf.add_page()
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 10, f"Item {q} - Acerto: {stats[gab_atual[q]]:.1f}%", ln=True)
                    pdf.image(tmp.name, x=10, w=80)
                    pdf.ln(5)
            
            pdf_b = pdf.output(dest='S').encode('latin-1')
            st.markdown(f'<a href="data:application/octet-stream;base64,{base64.b64encode(pdf_b).decode()}" download="Relatorio_Com_Graficos.pdf" style="text-decoration:none;"><button style="width:100%; padding:10px; background:#2e7bcf; color:white; border:none; border-radius:5px; cursor:pointer;">📥 Baixar com Gráficos</button></a>', unsafe_allow_html=True)

    with col_pdf2:
        if st.button("📄 PDF ANALÍTICO (SEM GRÁFICOS)", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'RELATÓRIO ANALÍTICO - APENAS DADOS', ln=True, align='C')
            pdf.ln(10)
            for q in cols_q:
                stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                acerto = stats[gab_atual[q]]
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 8, f"Questão {q} | Gabarito: {gab_atual[q]} | Acerto: {acerto:.1f}%", ln=True)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 6, f"A: {stats['A']:.0f}% | B: {stats['B']:.0f}% | C: {stats['C']:.0f}% | D: {stats['D']:.0f}%", ln=True)
                pdf.multi_cell(0, 5, f"Habilidade: {DICIONARIO_HABILIDADES[q]}")
                pdf.ln(4)
                if pdf.get_y() > 260: pdf.add_page()
            
            pdf_b = pdf.output(dest='S').encode('latin-1')
            st.markdown(f'<a href="data:application/octet-stream;base64,{base64.b64encode(pdf_b).decode()}" download="Relatorio_Sem_Graficos.pdf" style="text-decoration:none;"><button style="width:100%; padding:10px; background:#2ecc71; color:white; border:none; border-radius:5px; cursor:pointer;">📥 Baixar sem Gráficos</button></a>', unsafe_allow_html=True)

    # --- DASHBOARD VISUAL NA TELA ---
    st.markdown("---")
    grid = st.columns(2)
    for i, q in enumerate(cols_q):
        with grid[i % 2]:
            st.container(border=True)
            stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(['A','B','C','D'], stats, color=['#2ECC71' if l == gab_atual[q] else '#E74C3C' for l in ['A','B','C','D']], edgecolor='black')
            ax.set_title(f"Questão {q} (Gab: {gab_atual[q]})", fontweight='bold')
            st.pyplot(fig)
            st.info(f"**Habilidade:** {DICIONARIO_HABILIDADES[q]}")
