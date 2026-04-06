import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import tempfile
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Portal TRI Profissional", layout="wide", page_icon="🏛️")

# --- 2. LIGAÇÃO AO BANCO DE DADOS (GOOGLE SHEETS) ---
def conectar_google_sheets():
    try:
        escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Usa o ficheiro credentials.json que guardaste na mesma pasta
        creds = Credentials.from_service_account_file('credentials.json', scopes=escopos)
        client = gspread.authorize(creds)
        # Tenta abrir a planilha pelo nome exato
        return client.open("Dados_TRI_Sistema").sheet1
    except Exception as e:
        st.error(f"Erro de conexão: Certifique-se de que a planilha 'Dados_TRI_Sistema' existe e foi partilhada com o e-mail do JSON. Erro: {e}")
        return None

def salvar_no_banco(df_final):
    folha = conectar_google_sheets()
    if folha:
        try:
            df_final['Data_Registro'] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            dados = df_final.astype(str).values.tolist()
            folha.append_rows(dados)
            return True
        except: return False
    return False

# --- 3. LÓGICA PEDAGÓGICA ---
def obter_detalhes_nivel(score):
    if score < 150: return {"nivel": "CRÍTICO", "cor": "#E74C3C", "sug": "Focar em alfabetização e base numérica."}
    elif score < 250: return {"nivel": "BÁSICO", "cor": "#F1C40F", "sug": "Reforço em interpretação e descritores base."}
    elif score < 350: return {"nivel": "PROFICIENTE", "cor": "#2ECC71", "sug": "Manter ritmo e consolidar descritores da série."}
    else: return {"nivel": "AVANÇADO", "cor": "#3498DB", "sug": "Desafios de lógica e monitoria."}

def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- 4. CONTROLO DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

# --- 5. TELA DE LOGIN ---
if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Sistema Gestor TRI</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            inep = st.text_input("INEP da Escola")
            cpf = st.text_input("CPF do Professor", type="password")
            if st.button("Entrar no Painel", use_container_width=True):
                if inep == "12345" and cpf == "000": 
                    st.session_state['autenticado'] = True
                    st.rerun()
                else: st.error("Credenciais inválidas.")
    st.caption("Política de Privacidade: Dados processados conforme a LGPD para fins pedagógicos.")

# --- 6. PAINEL PRINCIPAL ---
else:
    st.sidebar.title("💎 Gestão Premium")
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "⚙️ Importar Dados", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "⚙️ Importar Dados":
        st.header("⚙️ Importar Planilha de Alunos")
        materia = st.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
        arquivo = st.file_uploader("Subir Excel (.xlsx)", type="xlsx")
        
        if arquivo:
            df = pd.read_excel(arquivo).fillna("X")
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            # Gabarito Adaptado à sua planilha (9º ano)
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            
            for idx, row in df.iterrows():
                binario = {q: 1 if str(row[q]).upper() == gab[int(q[1:])-1] else 0 for q in cols_q}
                df.at[idx, 'Proficiência'] = calcular_tri(binario)
            
            st.session_state['banco_dados'] = df
            st.success("Dados processados com sucesso!")
            
            if st.button("💾 SALVAR PERMANENTEMENTE NO BANCO DE DADOS"):
                if salvar_no_banco(df):
                    st.success("✅ Enviado para a Nuvem com sucesso!")
                else:
                    st.error("Erro ao salvar. Verifique se partilhou a planilha com o e-mail do JSON.")

    elif menu == "📊 Dashboard":
        if st.session_state['banco_dados'] is None:
            st.warning("Por favor, importe os dados primeiro na aba 'Importar Dados'.")
        else:
            df_f = st.session_state['banco_dados']
            media = df_f['Proficiência'].mean()
            info = obter_detalhes_nivel(media)
            
            st.metric("Média Geral TRI", f"{media:.1f}")
            st.markdown(f"### Nível: <span style='color:{info['cor']}'>{info['nivel']}</span>", unsafe_allow_html=True)
            st.info(f"**Sugestão:** {info['sug']}")
            
            st.subheader("Notas Individuais")
            st.dataframe(df_f[['Nome', 'Turma', 'Proficiência']])
            
            # (Aqui podes adicionar os gráficos por questão que já tínhamos)
