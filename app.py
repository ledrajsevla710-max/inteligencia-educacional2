import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="Sistema de Inteligência Educacional", layout="wide", page_icon="📊")

# --- 2. MATRIZES DE DESCRITORES ---
MATRIZES = {
    "Língua Portuguesa": {
        f"Q{i:02d}": f"Descritor de Língua Portuguesa {i} - Habilidade de Leitura" for i in range(1, 23)
    },
    "Matemática": {
        f"Q{i:02d}": f"Descritor de Matemática {i} - Habilidade Lógico-Matemática" for i in range(1, 23)
    }
}
# Nota: Você pode substituir os textos acima pelos descritores específicos da BNCC conforme desejar.

# --- 3. MOTOR DE CÁLCULO TRI (ESCALA DE PROFICIÊNCIA) ---
def estimar_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 80)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas_binarias.items()):
        b = np.linspace(-2.5, 2.5, 22)[i] 
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    theta_final = thetas[np.argmax(verossimilhanca)]
    return (theta_final + 4) * 50 

# --- 4. GESTÃO DE SESSÃO ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'dados' not in st.session_state: st.session_state.dados = None

# --- 5. INTERFACE DE LOGIN ---
if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Portal de Avaliação Educacional</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.container(border=True):
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.button("Acessar Sistema", use_container_width=True):
                if u == "12345" and s == "000":
                    st.session_state.logado = True
                    st.rerun()
                else: st.error("Credenciais inválidas.")
else:
    # --- 6. BARRA LATERAL ---
    st.sidebar.title(f"📊 Painel do Gestor")
    aba = st.sidebar.radio("Menu", ["Início", "Upload de Dados", "Painel Analítico", "Sair"])

    if aba == "Sair":
        st.session_state.logado = False
        st.rerun()

    elif aba == "Início":
        st.title("🎯 Monitoramento de Aprendizagem")
        st.info("Sistema universal para análise de proficiência baseada em Teoria de Resposta ao Item (TRI).")
        st.markdown("""
        **Funcionalidades Ativas:**
        * Cálculo automático de Proficiência (Escala 0-400).
        * Identificação de Habilidades Críticas.
        * Geração de Relatórios Técnicos em PDF (Formato Paisagem).
        """)

    elif aba == "Upload de Dados":
        st.header("📝 Importar Resultados")
        c1, c2 = st.columns(2)
        disc = c1.selectbox("Disciplina", ["Língua Portuguesa", "Matemática"])
        arq = st.file_uploader("Selecione a planilha (Excel)", type="xlsx")

        if arq:
            df = pd.read_excel(arq).fillna("X")
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            
            with st.spinner("Processando Matriz e TRI..."):
                for idx, row in df.iterrows():
                    resps = {q: 1 if str(row[q]).upper() == gab[i] else 0 for i, q in enumerate(cols_q)}
                    df.at[idx, 'Prof_TRI'] = estimar_tri(resps)
            
            st.session_state.dados = df
            st.session_state.materia = disc
            st.success(f"✅ Processamento concluído: {len(df)} alunos analisados.")

    elif aba == "Painel Analítico":
        if st.session_state.dados is None:
            st.warning("Por favor, realize o upload dos dados primeiro.")
        else:
            df = st.session_state.dados
            matriz = MATRIZES[st.session_state.materia]
            
            st.header(f"📊 Resultados Detalhados: {st.session_state.materia}")
            
            # Métricas Gerais
            m_tri = df['Prof_TRI'].mean()
            c1, c2 = st.columns(2)
            c1.metric("Média de Proficiência (TRI)", f"{m_tri:.1f}")
            c2.metric("Total de Participantes", len(df))

            st.divider()

            # Cálculo por Questão
            resumo = []
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            for i, q in enumerate([f'Q{i:02d}' for i in range(1, 23)]):
                perc = (len(df[df[q].astype(str).str.upper() == gab[i]]) / len(df)) * 100
                resumo.append({"Questão": q, "Acerto (%)": perc, "Habilidade": matriz.get(q, "N/A")})
            
            df_res = pd.DataFrame(resumo)

            # Gráficos com Habilidade Abaixo
            st.subheader("🎯 Desempenho por Item e Habilidade")
            grid = st.columns(4)
            for i, row in df_res.iterrows():
                with grid[i % 4]:
                    with st.container(border=True):
                        st.write(f"**{row['Questão']}**")
                        fig, ax = plt.subplots(figsize=(3,2))
                        ax.bar(["Acerto"], [row['Acerto (%)']], color='#28A745')
                        ax.set_ylim(0, 100)
