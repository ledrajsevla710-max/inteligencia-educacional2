import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. MOTORES DE CÁLCULO (TRI) ---
def calcular_tri(respostas):
    num_q = len(respostas)
    if num_q == 0: return 0
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        # b = dificuldade da questão distribuída na escala
        b = np.linspace(-2.5, 2.5, num_q)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel_escala(valor, disciplina):
    ponto = 200 if "PORTUGUESA" in disciplina.upper() else 225
    if valor < ponto: return "Muito Crítico", "#D32F2F"
    if valor < ponto + 50: return "Crítico", "#F57C00"
    if valor < ponto + 100: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. AMBIENTE LOGADO E NAVEGAÇÃO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Sistema de Inteligência Educacional</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Acesse com suas credenciais de servidor municipal.</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        u = st.text_input("Usuário (CPF/Matrícula)")
        s = st.text_input("Senha", type="password")
        if st.button("Entrar no Sistema", use_container_width=True):
            if u == "12345" and s == "000": # Ajuste conforme sua segurança
                st.session_state['autenticado'] = True; st.rerun()
            else: st.error("Credenciais inválidas.")

else:
    menu = st.sidebar.radio("Menu Principal", ["🏠 Início & Tutorial", "📝 Importar Planilha", "📊 Painel Analítico", "🏢 Gerar Relatórios", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()

    elif menu == "🏠 Início & Tutorial":
        st.title("👋 Bem-vindo ao Inteligência Educacional")
        st.markdown(f"### Olá, servidor! Este portal foi desenvolvido para transformar os dados das Provas de Rede de José de Freitas em estratégias pedagógicas.")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.info("""
            **📌 Como funciona o App?**
            O sistema utiliza a **Teoria de Resposta ao Item (TRI)**, a mesma metodologia do SAEB. 
            Ele não apenas conta acertos, mas analisa a consistência pedagógica do aluno, identificando quem realmente domina a habilidade e quem acertou por acaso.
            """)
        with col_t2:
            st.success("""
            **📖 Tutorial de Uso:**
            1. Vá em **'Importar Planilha'** no menu lateral.
            2. Carregue o arquivo original da Prova de Rede (.xlsx).
            3. O sistema lerá o **Gabarito** e a **Escola** automaticamente da planilha.
            4. Veja os resultados no **'Painel Analítico'** e baixe os PDFs em **'Relatórios'**.
            """)
        
        st.warning("⚠️ **Dica Importante:** Certifique-se de que a palavra 'GABARITO' esteja presente na planilha para que o sistema saiba quais são as respostas corretas!")

    elif menu == "📝 Importar Planilha":
        st.header("📝 Carregar Nova Avaliação")
        arq = st.file_uploader("Selecione o arquivo Excel da Prova de Rede", type="xlsx")
        
        if arq:
            df_raw = pd.read_excel(arq, header=None)
            
            # 1. Identificação Automática de Escola e Disciplina
            try:
                escola = str(df_raw.iloc[4, 9]).strip() # J5
                disciplina = str(df_raw.iloc[6, 30]).strip() # AE7
                turma = str(df_raw.iloc[7, 10]).strip() # K8
            except:
                escola, disciplina, turma = "Escola Municipal", "Geral", "A"

            # 2. Localização Dinâmica do Gabarito e Habilidades
            idx_gab = df_raw[df_raw.apply(lambda r: r.astype(str).str.contains('GABARITO').any(), axis=1)].index
            idx_hab = df_raw[df_raw.apply(lambda r: r.astype(str).str.contains('HABILIDADE').any(), axis=1)].index
            
            if not idx_gab.empty:
                linha_g = idx_gab[0]
                #
