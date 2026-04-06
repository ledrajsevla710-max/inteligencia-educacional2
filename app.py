import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Sistema de Inteligência Educacional", layout="wide", page_icon="📊")

# --- 2. MATRIZES E GABARITO (CONSOLIDADO) ---
MATRIZ_LP = {f"Q{i:02d}": f"Descritor LP {i}" for i in range(1, 23)} # Simplificado para o exemplo, mantenha as suas descrições longas aqui
MATRIZ_MAT = {f"Q{i:02d}": f"Descritor MAT {i}" for i in range(1, 23)}
GABARITO = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']

def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        b = np.linspace(-2.5, 2.5, 22)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- 3. SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal de Inteligência</h1>", unsafe_allow_html=True)
    u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "12345" and s == "000":
            st.session_state['autenticado'] = True; st.rerun()
else:
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "📝 Importar Dados", "📊 Painel Analítico", "🚪 Sair"])

    if menu == "🏠 Início":
        st.title("👋 Bem-vindo, Jardel!")
        st.info("Sistema configurado para Escala SAEB (0-400) com análise de distratores.")
        st.latex(r"P_i(\theta) = c_i + \frac{1 - c_i}{1 + e^{-1.7a_i(\theta - b_i)}}")

    elif menu == "📝 Importar Dados":
        c1, c2 = st.columns(2)
        disc = c1.selectbox("Disciplina:", ["Língua Portuguesa", "Matemática"])
        ano = c2.selectbox("Ano:", ["2º Ano", "5º Ano", "9º Ano"])
        arq = st.file_uploader("Upload Excel", type="xlsx")
        if arq:
            df = pd.read_excel(arq).fillna("N/A")
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            for idx, row in df.iterrows():
                resps_bin = {q: 1 if str(row[q]).upper() == GABARITO[i] else 0 for i, q in enumerate(cols_q)}
                df.at[idx, 'Prof_TRI'] = calcular_tri(resps_bin)
            st.session_state['banco_dados'] = df
            st.session_state['mat_ativa'] = disc
            st.session_state['ano_ativo'] = ano
            st.success("✅ Dados carregados!")

    elif menu == "📊 Painel Analítico":
        if st.session_state['banco_dados'] is not None:
            df = st.session_state['banco_dados']
            matriz = MATRIZ_MAT if st.session_state['mat_ativa'] == "Matemática" else MATRIZ_LP
            st.header(f"Análise: {st.session_state['mat_ativa']}")
            
            stats_list = []
            grid = st.columns(3)
            for i, q in enumerate([f'Q{i:02d}' for i in range(1, 23)]):
                dist = df[q].astype(str).str.upper().value_counts(normalize=True) * 100
                alt = ['A', 'B', 'C', 'D']
                val = [dist.get(a, 0) for a in alt]
                stats_list.append({"Item": q, "Acerto": dist.get(GABARITO[i], 0), "Hab": matriz.get(q), "Gab": GABARITO[i]})
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.write(f"Questão {q}")
                        fig, ax = plt.subplots(figsize=(4, 2))
                        ax.bar(alt, val, color=['#2ECC71' if x == GABARITO[i] else '#E74C3C' for x in alt])
                        st.pyplot(fig); plt.close(fig)
                        st.caption(f"Habilidade: {matriz.get(q)}")

            # --- CORREÇÃO DO PDF ---
            if st.button("📄 Gerar Relatório PDF"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, t(f"RELATÓRIO: {st.session_state['mat_ativa']} ({st.session_state['ano_ativo']})"), ln=True, align='C')
                
                # Gráfico Geral
                df_res = pd.DataFrame(stats_list)
                fig_g, ax_g = plt.subplots
