import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io

# --- 1. CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

def aplicar_estilo():
    st.markdown("""
        <style>
        .main { background-color: #f5f7f9; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #666; padding: 10px; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. MOTORES TÉCNICOS ---
def calcular_tri(respostas_binarias):
    if not respostas_binarias: return 0
    num_q = len(respostas_binarias)
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas_binarias.items()):
        b = np.linspace(-2.5, 2.5, num_q)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel(valor, disciplina):
    corte = 200 if "PORTUGUESA" in disciplina.upper() else 225
    if valor < corte: return "Muito Crítico", "#D32F2F"
    if valor < corte + 50: return "Crítico", "#F57C00"
    if valor < corte + 100: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. INTERFACE DE ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Portal de Inteligência Educacional</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Gestão de Dados e Proficiência TRI - José de Freitas/PI</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        u = st.text_input("CPF ou Matrícula")
        s = st.text_input("Senha", type="password")
        if st.button("Acessar Painel", use_container_width=True):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True; st.rerun()
            else: st.error("Acesso negado.")

else:
    aplicar_estilo()
    menu = st.sidebar.radio("Navegação", ["🏠 Home & Tutorial", "📝 Importar Planilha", "📊 Painel Analítico", "🏢 Relatórios PDF", "🚪 Sair"])

    if menu == "🏠 Home & Tutorial":
        st.title("👋 Olá! Bem-vindo ao Sistema de Análise")
        st.markdown("### O que este sistema faz?")
        col_a, col_b = st.columns(2)
        with col_a:
            st.info("""
            **✅ Correção Automática:**
            Lê o gabarito direto da sua planilha de rede e corrige todos os alunos instantaneamente.
            
            **📈 Cálculo TRI:**
            Diferente da nota comum, aqui calculamos a proficiência real (estilo SAEB/ENEM).
            """)
        with col_b:
            st.success("""
            **📖 Tutorial Rápido:**
            1. No menu **Importar**, suba o arquivo .xlsx original.
            2. O sistema ignora as notas manuais e calcula tudo do zero.
            3. No **Painel**, você verá os gráficos de desempenho da turma.
            """)
        st.image("https://img.freepik.com/vetores-gratis/analise-de-dados-em-uma-ilustracao-de-dispositivos-digitais_53876-64010.jpg", width=400)

    elif menu == "📝 Importar Planilha":
        st.header("📝 Carregar Avaliação de Rede")
        arq = st.file_uploader("Arraste o arquivo Excel aqui", type="xlsx")
        
        if arq:
            df_raw = pd.read_excel(arq, header=None)
            
            # Identificação de Metadados
            try:
                escola = str(df_raw.iloc[4, 9]).strip() 
                disc = str(df_raw.iloc[6, 30]).strip()
                turma = str(df_raw.iloc[7, 10]).strip()
            except:
                escola, disc, turma = "Escola Municipal", "Geral", "A"

            # Busca o Gabarito (Linha que contém a palavra GABARITO na
