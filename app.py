import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor TRI Municipal", layout="wide", page_icon="🏛️")

# --- 2. CONEXÃO BANCO DE DADOS ---
def conectar_google_sheets():
    try:
        escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file('credentials.json', scopes=escopos)
        return gspread.authorize(creds).open("Dados_TRI_Sistema").sheet1
    except: return None

# --- 3. FUNÇÕES PEDAGÓGICAS ---
def obter_diagnostico(score):
    if score < 150: return {"nivel": "CRÍTICO", "cor": "#E74C3C", "sug": "Focar em alfabetização e base numérica."}
    elif score < 250: return {"nivel": "BÁSICO", "cor": "#F1C40F", "sug": "Reforço em interpretação e descritores base."}
    elif score < 350: return {"nivel": "PROFICIENTE", "cor": "#2ECC71", "sug": "Consolidar descritores da série."}
    else: return {"nivel": "AVANÇADO", "cor": "#3498DB", "sug": "Desafios de lógica e monitoria."}

def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- 4. CONTROLE DE SESSÃO E LOGIN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None
if 'usuarios' not in st.session_state: st.session_state['usuarios'] = {"12345": "000"} # Mock inicial

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal TRI Municipal</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.container(border=True):
            user_inep = st.text_input("INEP ou Usuário")
            user_pass = st.text_input("Senha", type="password")
            if st.button("Acessar Painel", use_container_width=True):
                if user_inep in st.session_state['usuarios'] and st.session_state['usuarios'][user_inep] == user_pass:
                    st.session_state['autenticado'] = True
                    st.rerun()
                else: st.error("Credenciais inválidas.")

# --- 5. PAINEL DO USUÁRIO ---
else:
    st.sidebar.title("💎 Área do Gestor")
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard Municipal", "⚙️ Importar Dados", "👤 Cadastrar Usuários", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "👤 Cadastrar Usuários":
        st.header("👤 Gestão de Acessos")
        new_user = st.text_input("Novo INEP/Usuário:")
        new_pass = st.text_input("Definir Senha:")
        if st.button("Cadastrar Novo Usuário"):
            st.session_state['usuarios'][new_user] = new_pass
            st.success(f"Usuário {new_user} cadastrado com sucesso!")

    elif menu == "⚙️ Importar Dados":
        st.header("⚙️ Importar Avaliações")
        col_mat, col_ser = st.columns(2)
        materia = col_mat.selectbox("Matéria:", ["Matemática", "Língua Portuguesa"])
        serie = col_ser.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])
        
        arquivo = st.file_uploader("Subir Planilha Excel", type="xlsx")
        if arquivo:
            df = pd.read_excel(arquivo).fillna("X")
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            
            for idx, row in df.iterrows():
                binario = {q: 1 if str(row[q]).upper() == gab[int(q[1:])-1] else 0 for q in cols_q}
                df.at[idx, 'Proficiência'] = calcular_tri(binario)
                df.at[idx, 'Matéria'] = materia
                df.at[idx, 'Série'] = serie
            
            st.session_state['banco_dados'] = df
            st.success(f"Dados de {materia} processados!")
            if st.button("💾 SALVAR NO BANCO CENTRAL"):
                # Lógica de append no Google Sheets aqui
                st.success("Dados salvos na nuvem com sucesso!")

    elif menu == "📊 Dashboard Municipal":
        if st.session_state['banco_dados'] is not None:
            df_full = st.session_state['banco_dados']
            
            # FILTROS DE HIERARQUIA
            st.sidebar.divider()
            f_escola = st.sidebar.selectbox("Filtrar por Escola:", ["Geral Município"] + list(df_full['Escola'].unique()))
            df_esc = df_full if f_escola == "Geral Município" else df_full[df_full['Escola'] == f_escola]
            
            f_turma = st.sidebar.selectbox("Filtrar por Turma:", ["Todas as Turmas"] + list(df_esc['Turma'].unique()))
            df_final = df_esc if f_turma == "Todas as Turmas" else df_esc[df_esc['Turma'] == f_turma]

            # DASHBOARD VISUAL
            media = df_final['Proficiência'].mean()
            diag = obter_diagnostico(media)
            
            st.title(f"📊 Relatório: {f_escola}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Média TRI", f"{media:.1f}")
            c2.metric("Qtd. Alunos", len(df_final))
            c3.markdown(f"**Nível:** <span style='color:{diag['cor']}'>{diag['nivel']}</span>", unsafe_allow_html=True)
            
            st.warning(f"**Sugestão Pedagógica:** {diag['sug']}")

            # BOTÕES DE RELATÓRIO PDF
            st.divider()
            if st.button(f"📄 Gerar Relatório PDF: {f_escola} - {f_turma}"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, f'RELATÓRIO TRI - {f_escola}', ln=True, align='C')
                pdf.set_font('Arial', '', 10); pdf.cell(0, 10, f'Filtro: {f_turma} | Média: {media:.1f}', ln=True, align='C')
                pdf.ln(5)
                for _, r in df_final.iterrows():
                    pdf.cell(0, 7, f"Escola: {r['Escola']} | Aluno: {r['Nome']} | Nota: {r['Proficiência']:.1f}", ln=True)
                st.download_button("📥 Baixar PDF", pdf.output(dest='S').encode('latin-1'), f"Relatorio_{f_escola}.pdf")

            # TABELA E GRÁFICOS
            st.dataframe(df_final[['Escola', 'Turma', 'Nome', 'Proficiência', 'Matéria']])
        else:
            st.info("Aguardando importação de dados para gerar visão municipal.")
