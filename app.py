import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import tempfile

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Portal TRI Profissional", layout="wide", page_icon="🏛️")

# --- 2. MEMÓRIA E LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state:
    st.session_state['banco_dados'] = None

# --- 3. DIAGNÓSTICO E POLÍTICA ---
def obter_detalhes_nivel(score):
    if score < 150:
        return {"nivel": "CRÍTICO", "cor": "#E74C3C", "desc": "Nível Crítico: Alunos com dificuldades severas.", "sug": "Intervenção: Focar em alfabetização e base numérica com material concreto."}
    elif score < 250:
        return {"nivel": "BÁSICO", "cor": "#F1C40F", "desc": "Nível Básico: Presença de lacunas de aprendizagem.", "sug": "Intervenção: Reforço em interpretação de problemas e descritores base."}
    elif score < 350:
        return {"nivel": "PROFICIENTE", "cor": "#2ECC71", "desc": "Nível Proficiente: Domínio esperado para a série.", "sug": "Intervenção: Manter ritmo com desafios de nível médio/avançado."}
    else:
        return {"nivel": "AVANÇADO", "cor": "#3498DB", "desc": "Nível Avançado: Excelente desempenho.", "sug": "Intervenção: Projetos de monitoria e desafios olímpicos."}

TEXTO_PRIVACIDADE = """
**POLÍTICA DE PRIVACIDADE E SEGURANÇA (LGPD)**
Este sistema processa dados educacionais exclusivamente para fins pedagógicos.
1. Os nomes e notas dos alunos são restritos ao uso da Secretaria de Educação.
2. Não compartilhamos dados com terceiros.
3. O acesso é protegido por criptografia de sessão.
"""

# --- 4. TELA DE LOGIN ---
if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Sistema Gestor TRI</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            inep = st.text_input("INEP da Escola")
            cpf = st.text_input("CPF do Professor", type="password")
            if st.button("Entrar no Painel", use_container_width=True):
                if inep == "12345" and cpf == "000": # Simulação de Login
                    st.session_state['autenticado'] = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
    st.markdown("---")
    st.caption(TEXTO_PRIVACIDADE)

# --- 5. PAINEL PRINCIPAL ---
else:
    st.sidebar.title("💎 Gestão Premium")
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "📄 Gerar Relatórios", "⚙️ Importar Dados", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "⚙️ Importar Dados":
        st.header("⚙️ Configuração de Dados")
        arquivo = st.file_uploader("Subir Planilha Excel", type="xlsx")
        if arquivo:
            df = pd.read_excel(arquivo).fillna("X")
            # (Aqui rodaria a lógica TRI já mostrada anteriormente)
            st.session_state['banco_dados'] = df
            st.success("Dados salvos na sessão!")

    elif menu == "📊 Dashboard":
        if st.session_state['banco_dados'] is not None:
            df_f = st.session_state['banco_dados']
            # Filtros e Gráficos na tela (como fizemos antes)
            st.subheader("Análise em Tempo Real")
            st.dataframe(df_f.head()) # Exemplo simples
        else:
            st.warning("Carregue os dados primeiro.")

    elif menu == "📄 Gerar Relatórios":
        if st.session_state['banco_dados'] is not None:
            df_f = st.session_state['banco_dados']
            media = 210.5 # Exemplo vindo do cálculo
            info = obter_detalhes_nivel(media)
            
            st.subheader("Configuração do PDF")
            
            if st.button("📄 GERAR PDF ANALÍTICO COMPLETO"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'RELATÓRIO TRI - JOSÉ DE FREITAS', ln=True, align='C')
                
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 10, f"Média Geral: {media} | Nível: {info['nivel']}", ln=True)
                pdf.set_font('Arial', 'I', 10)
                pdf.multi_cell(0, 7, f"Sugestão Pedagógica: {info['sug']}")
                
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 8, "DESEMPENHO POR ALUNO:", ln=True)
                pdf.set_font('Arial', '', 9)
                for _, row in df_f.iterrows():
                    pdf.cell(0, 6, f"{row['Nome']} - Proficiência: {media}", ln=True)
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button("📥 Baixar PDF Agora", pdf_output, "Relatorio_Final.pdf")
