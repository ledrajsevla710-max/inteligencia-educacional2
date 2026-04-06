import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import os

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestão Educacional TRI", layout="wide", page_icon="📈")

# --- 2. MATRIZ DE REFERÊNCIA ---
MAPA_HABILIDADES = {
    "Matemática": {f"Q{i:02d}": f"Habilidade Pedagógica D{i} - Matriz SAEPI/SAEB" for i in range(1, 23)}
}

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
    dados = [
        ["Escola Municipal A", "9º Ano A", "Aluno Exemplo 1"] + ["C"]*22,
        ["Escola Municipal B", "9º Ano B", "Aluno Exemplo 2"] + ["A"]*22
    ]
    df_m = pd.DataFrame(dados, columns=colunas)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_m.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. INTERFACE ---
st.title("📊 Painel de Monitoramento TRI - Gestão Municipal")

st.sidebar.header("⚙️ Configurações")
st.sidebar.download_button("📥 Baixar Planilha Modelo", gerar_modelo_excel(), "modelo_gestao_tri.xlsx", use_container_width=True)

# SELETOR DE SÉRIES CORRIGIDO
disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática"])
serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

uploaded_file = st.file_uploader("📂 Carregar planilha de resultados", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito = GABARITOS[disciplina]

    # Processamento TRI
    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    # --- VISÃO GERAL (RANKING) ---
    st.subheader("🏫 Desempenho por Escola")
    ranking = df.groupby('Escola')['Proficiência'].mean().sort_values(ascending=False).reset_index()
    c_rank1, c_rank2 = st.columns([2, 1])
    with c_rank1:
        fig_r, ax_r = plt.subplots(figsize=(10, 4))
        ax_r.barh(ranking['Escola'], ranking['Proficiência'], color='#1F77B4')
        ax_r.set_xlabel("Proficiência Média")
        st.pyplot(fig_r)
    with c_rank2:
        st.write("Ranking de Médias:")
        st.table(ranking)

    st.divider()

    # --- FILTROS ---
    st.subheader("🔍 Filtros de Turma")
    f1, f2 = st.columns(2)
    esc_sel = f1.selectbox("Escola:", ["Todas"] + sorted(list(df['Escola'].unique())))
    tur_sel = f2.selectbox("Turma:", ["Todas"] + sorted(list(df['Turma'].unique())))

    df_f = df.copy()
    if esc_sel != "Todas": df_f = df_f[df_f['Escola'] == esc_sel]
    if tur_sel != "Todas": df_f = df_f[df_f['Turma'] == tur_sel]

    m_f = df_f['Proficiência'].mean()
    n_f, c_f = obter_nivel(m_f)

    st.metric(f"Média da Seleção: {esc_sel} | {tur_sel}", f"{m_f:.1f}", n_f)

    # --- GRÁFICOS DE ALTERNATIVAS (DISTRATORES) ---
    st.markdown("### 🎯 Análise de Itens e Distratores")
    grid = st.columns(3)
    for i, q in enumerate(cols_q):
        with grid[i % 3]:
            # Contagem de respostas
            contagem = df_f[q].str.upper().value_counts(normalize=True).sort_index() * 100
            st.write(f"**Questão {q}** (Gab: {gabarito[q]})")
            
            fig_q, ax_q = plt.subplots(figsize=(4, 5))
            cores = ['#00CC96' if alt == gabarito[q] else '#FF4B4B' for alt in ['A','B','C','D']]
            ax_q.bar(['A','B','C','D'], [contagem.get(alt, 0) for alt in ['A','B','C','D']], color=cores)
            ax_q.set_ylim(0, 100)
            ax_q.set_ylabel("% Escolha")
            st.pyplot(fig_q)
            st.caption(f"Habilidade: {MAPA_HABILIDADES[disciplina].get(q)}")
            st.divider()

    # --- BOTÃO PDF ---
    if st.button("📄 Baixar Relatório PDF Completo", use_container_width=True):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'Relatório TRI - {esc_sel} | {tur_sel}', ln=True, align='C')
        pdf.ln(10)
        for q in cols_q:
            p_acerto = (df_f[q].str.upper() == gabarito[q]).mean() * 100
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 7, f"Item {q} | Acerto: {p_acerto:.1f}% | Gabarito: {gabarito[q]}", ln=True)
            pdf.set_font('Arial', 'I', 9)
            pdf.multi_cell(0, 5, f"Habilidade: {MAPA_HABILIDADES[disciplina].get(q)}")
            pdf.ln(3)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_TRI.pdf" style="display:block; text-align:center; padding:10px; background-color:#2e7bcf; color:white; border-radius:5px; text-decoration:none;">💾 SALVAR PDF</a>', unsafe_allow_html=True)

else:
    st.info("💡 Carregue a planilha para visualizar os dados de desempenho.")
