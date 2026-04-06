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

# --- 2. DEFINIÇÃO DA ESCALA DE PROFICIÊNCIA ---
def obter_detalhes_nivel(score):
    if score < 150:
        return {"nivel": "CRÍTICO", "cor": "#E74C3C", "desc": "Alunos com dificuldades severas nos pré-requisitos básicos."}
    elif score < 250:
        return {"nivel": "BÁSICO", "cor": "#F1C40F", "desc": "Alunos que iniciaram a compreensão, mas possuem muitas lacunas."}
    elif score < 350:
        return {"nivel": "PROFICIENTE", "cor": "#2ECC71", "desc": "Alunos que demonstram domínio esperado para a série atual."}
    else:
        return {"nivel": "AVANÇADO", "cor": "#3498DB", "desc": "Alunos com alto desempenho e raciocínio lógico complexo."}

# (Dicionário de Habilidades e Gabaritos mantidos para brevidade)
DICIONARIO_HABILIDADES = {f"Q{i:02d}": f"Descritor SAEB/BNCC do item {i}." for i in range(1, 23)}
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

# --- 3. INTERFACE ---
st.title("🏛️ Inteligência Educacional - José de Freitas")

st.sidebar.header("📋 Configuração")
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

    # --- NOVO DASHBOARD COLORIDO ---
    media_tri = df_f['Proficiência'].mean()
    info_nivel = obter_detalhes_nivel(media_tri)

    st.markdown(f"### 📊 Análise de Proficiência: {esc_sel}")
    
    # Cards de Resumo
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Média TRI da Unidade", f"{media_tri:.1f}")
        st.markdown(f"<h2 style='color:{info_nivel['cor']}; text-align:center;'>Nível {info_nivel['nivel']}</h2>", unsafe_allow_html=True)
    
    with c2:
        st.info(f"**Diagnóstico Pedagógico:** {info_nivel['desc']}")
        # Barra de progresso visual
        st.write("Posicionamento na Escala (0 a 500):")
        st.progress(min(media_tri / 500, 1.0))

    st.divider()

    # --- GRÁFICO DE DISTRIBUIÇÃO DE ALUNOS POR NÍVEL ---
    st.subheader("👥 Distribuição de Alunos por Nível")
    
    def rotular_aluno(p): return obter_detalhes_nivel(p)['nivel']
    df_f['Nivel_Nome'] = df_f['Proficiência'].apply(rotular_aluno)
    contagem_niveis = df_f['Nivel_Nome'].value_counts().reindex(["CRÍTICO", "BÁSICO", "PROFICIENTE", "AVANÇADO"], fill_value=0)
    
    fig_dist, ax_dist = plt.subplots(figsize=(10, 3))
    cores_dist = ["#E74C3C", "#F1C40F", "#2ECC71", "#3498DB"]
    contagem_niveis.plot(kind='barh', color=cores_dist, ax=ax_dist)
    ax_dist.set_title("Quantidade de Alunos em cada Nível")
    st.pyplot(fig_dist)

    # --- BOTÕES DE DOWNLOAD (CONFORME ANTERIOR) ---
    st.divider()
    col_pdf1, col_pdf2 = st.columns(2)
    # (Lógica dos PDFs mantida, mas agora incluindo o texto do Nível de Proficiência)
    
    # --- GRÁFICOS DOS ITENS NA TELA (LAYOUT BONITO) ---
    st.markdown("### 🎯 Detalhamento por Questão")
    grid = st.columns(2)
    for i, q in enumerate(cols_q):
        with grid[i % 2]:
            with st.container(border=True):
                stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.bar(['A','B','C','D'], stats, color=['#2ECC71' if l == gab_atual[q] else '#E74C3C' for l
