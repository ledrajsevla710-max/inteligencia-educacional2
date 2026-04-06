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

# --- 2. ESCALA DE PROFICIÊNCIA COLORIDA ---
def obter_detalhes_nivel(score):
    if score < 150:
        return {"nivel": "CRÍTICO", "cor": "#E74C3C", "desc": "Desempenho muito abaixo do esperado. Requer intervenção imediata."}
    elif score < 250:
        return {"nivel": "BÁSICO", "cor": "#F1C40F", "desc": "Desenvolveu habilidades parciais. Necessita de reforço em descritores base."}
    elif score < 350:
        return {"nivel": "PROFICIENTE", "cor": "#2ECC71", "desc": "Domina os conteúdos essenciais previstos para a série."}
    else:
        return {"nivel": "AVANÇADO", "cor": "#3498DB", "desc": "Excelente domínio e capacidade de resolução de problemas complexos."}

# --- 3. DICIONÁRIO DE HABILIDADES ---
DICIONARIO_HABILIDADES = {f"Q{i:02d}": f"Descritor SAEB/BNCC correspondente ao item {i}." for i in range(1, 23)}
DICIONARIO_HABILIDADES.update({
    "Q01": "D6 - Identificar ângulos como mudança de direção ou giros.",
    "Q02": "EF06MA27 - Classificar ângulos (agudo, reto, obtuso).",
    "Q21": "D21 - Converter números decimais em frações e vice-versa."
})

GABARITOS_MESTRE = {
    "2º Ano": ['A']*22, 
    "5º Ano": ['B']*22, 
    "9º Ano": ['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B']
}

# --- 4. CÁLCULO TRI ---
def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- 5. INTERFACE ---
st.title("🏛️ Inteligência Educacional - José de Freitas")

st.sidebar.header("📋 Painel de Controle")
disciplina_sel = st.sidebar.selectbox("Disciplina:", ["Matemática"])
serie_sel = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

uploaded_file = st.file_uploader(f"📂 Carregar Planilha ({serie_sel})", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gab_atual = {f'Q{i:02d}': GABARITOS_MESTRE[serie_sel][i-1] for i in range(1, 23)}

    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gab_atual[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    esc_sel = st.sidebar.selectbox("Escola:", ["Geral"] + sorted(list(df['Escola'].unique())))
    df_f = df if esc_sel == "Geral" else df[df['Escola'] == esc_sel]

    # --- DASHBOARD DE PROFICIÊNCIA ---
    media_tri = df_f['Proficiência'].mean()
    info = obter_detalhes_nivel(media_tri)

    st.subheader(f"📊 Resultado da Unidade: {esc_sel}")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Média TRI", f"{media_tri:.1f}")
        st.markdown(f"<h2 style='color:{info['cor']}; text-align:center;'>NÍVEL {info['nivel']}</h2>", unsafe_allow_html=True)
    with c2:
        st.info(f"**Diagnóstico:** {info['desc']}")
        st.progress(min(media_tri / 500, 1.0))

    st.divider()

    # --- BOTÕES DE PDF ---
    cp1, cp2 = st.columns(2)
    
    with cp1:
        if st.button("📄 PDF COM GRÁFICOS", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f'Relatório com Gráficos - {esc_sel}', ln=True, align='C')
            for q in cols_q:
                stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                fig, ax = plt.subplots(figsize=(4, 3))
                # CORREÇÃO DA LINHA DO ERRO:
                cores = ['#2ECC71' if l == gab_atual[q] else '#E74C3C' for l in ['A','B','C','D']]
                ax.bar(['A','B','C','D'], stats, color=cores)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    fig.savefig(tmp.name)
                    plt.close(fig)
                    if pdf.get_y() > 210: pdf.add_page()
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 10, f"Questão {q} - Acerto: {stats[gab_atual[q]]:.1f}%", ln=True)
                    pdf.image(tmp.name, x=10, w=80)
            pdf_b = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Baixar PDF com Gráficos", pdf_b, "relatorio_grafico.pdf")

    with cp2:
        if st.button("📄 PDF ANALÍTICO (SEM GRÁFICOS)", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f'Relatório Analítico - {esc_sel}', ln=True, align='C')
            pdf.ln(10)
            for q in cols_q:
                stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 8, f"Questão {q} | Gabarito: {gab_atual[q]} | Acerto: {stats[gab_atual[q]]:.1f}%", ln=True)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 6, f"Distratores: A:{stats['A']:.0f}% B:{stats['B']:.0f}% C:{stats['C']:.0f}% D:{stats['D']:.0f}%", ln=True)
                pdf.ln(4)
            pdf_b = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Baixar PDF sem Gráficos", pdf_b, "relatorio_analitico.pdf")

    # --- EXIBIÇÃO NA TELA ---
    st.markdown("### 🎯 Detalhamento dos Itens")
    grid = st.columns(2)
    for i, q in enumerate(cols_q):
        with grid[i % 2]:
            with st.container(border=True):
                stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                fig, ax = plt.subplots(figsize=(6, 4))
                # CORREÇÃO DA LINHA DO ERRO AQUI TAMBÉM:
                cores = ['#2ECC71' if l == gab_atual[q] else '#E74C3C' for l in ['A','B','C','D']]
                ax.bar(['A','B','C','D'], stats, color=cores, edgecolor='black')
                ax.set_title(f"Item {q} (Gabarito: {gab_atual[q]})", fontweight='bold')
                st.pyplot(fig)
                st.caption(f"**Habilidade:** {DICIONARIO_HABILIDADES[q]}")
