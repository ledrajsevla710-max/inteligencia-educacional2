import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io

st.set_page_color = "white"
st.set_page_config(page_title="SAEPI JF - Unificado", layout="wide", page_icon="📝")

# --- BANCOS DE DADOS DE GABARITOS (22 ITENS CADA) ---
GABARITOS = {
    "Matemática": {f'Q{i:02d}': g for i, g in enumerate(['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B'], 1)},
    "Língua Portuguesa": {f'Q{i:02d}': g for i, g in enumerate(['A','D','B','C','A','D','B','C','B','A','D','C','B','A','D','C','B','B','A','D','C','A'], 1)}
}

# --- FUNÇÕES DE APOIO ---
def obter_nivel(score):
    if score < 125: return "Abaixo do Básico", "#FF4B4B"
    if score < 175: return "Básico", "#FACA2E"
    if score < 225: return "Proficiente", "#00CC96"
    return "Avançado", "#1F77B4"

def calcular_proficiencia(respostas, disciplina):
    gabarito = GABARITOS[disciplina]
    acertos = sum(1 for q, resp in respostas.items() if str(resp).upper() == gabarito[q])
    return (acertos / 22) * 300 + 100

def gerar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    return output.getvalue()

# --- INTERFACE ---
st.title("🎓 Sistema Unificado de Avaliação - José de Freitas")
st.info("Painel de monitoramento integrado para Professores e Gestores.")

# Sidebar de Configuração
st.sidebar.header("Configurações do Simulado")
disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

# --- GERADOR DE PLANILHA FICTÍCIA ---
if st.sidebar.button("📂 Gerar Planilha de Teste (Exemplo)"):
    nomes = ["Ana Silva", "Bruno Costa", "Carla Souza", "Daniel Oliveira", "Eduarda Lima", "Fabio Santos"]
    data_fake = {
        "Nome": nomes,
        "Escola": ["Escola Municipal A"] * 6,
        "Turma": ["Única"] * 6
    }
    for i in range(1, 23):
        data_fake[f'Q{i:02d}'] = np.random.choice(['A', 'B', 'C', 'D'], 6)
    
    df_fake = pd.DataFrame(data_fake)
    excel_fake = gerar_excel(df_fake)
    st.sidebar.download_button("⬇️ Baixar Planilha Exemplo", excel_fake, "planilha_exemplo_SAEPI.xlsx")

# --- UPLOAD E PROCESSAMENTO ---
uploaded_file = st.file_uploader("Suba sua planilha oficial (Excel)", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito_atual = GABARITOS[disciplina]

    # Cálculo de Proficiência por Aluno
    for index, row in df.iterrows():
        resps = {q: row[q] for q in cols_q}
        df.at[index, 'Proficiência'] = calcular_proficiencia(resps, disciplina)

    media_geral = df['Proficiência'].mean()
    nivel_txt, cor_nivel = obter_nivel(media_geral)

    # --- DASHBOARD VISUAL ---
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric(f"Média {disciplina}", f"{media_geral:.1f}")
        st.markdown(f"<div style='padding:20px; border-radius:10px; background-color:{cor_nivel}; color:white; text-align:center;'><strong>NÍVEL: {nivel_txt.upper()}</strong></div>", unsafe_allow_html=True)
        
        st.write("### 📥 Exportar Resultados")
        # Botão Excel
        excel_data = gerar_excel(df)
        st.download_button("📊 Baixar em Excel", excel_data, f"Resultado_{disciplina}_{serie}.xlsx")
        
    with col2:
        st.subheader("Percentual de Acerto por Questão")
        acertos_serie = []
        for q in cols_q:
            pct = (df[q].str.upper() == gabarito_atual[q]).mean() * 100
            acertos_serie.append(pct)
        
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(cols_q, acertos_serie, color='#1F77B4', width=0.3) # Barras finas
        ax.set_ylim(0, 100)
        plt.xticks(rotation=45)
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("🎯 Análise Detalhada (Gabarito vs Marcadas)")
    
    # Grid de Questões
    col_q_grid = st.columns(4)
    for i, q in enumerate(cols_q):
        with col_q_grid[i % 4]:
            freq = df[q].str.upper().value_counts(normalize=True).sort_index() * 100
            st.write(f"**Questão {q}** (Gab: :green[{gabarito_atual[q]}])")
            for alt in ['A', 'B', 'C', 'D']:
                p = freq.get(alt, 0)
                label = f"{alt}: {p:.0f}%"
                if alt == gabarito_atual[q]:
                    st.success(label)
                else:
                    st.text(label)
            st.write("---")

else:
    st.warning("⚠️ Por favor, suba a planilha para visualizar os dados.")
