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

# --- 1. CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Portal TRI Profissional", layout="wide", page_icon="🏛️")

# --- 2. BANCO DE DADOS (GOOGLE SHEETS) ---
def conectar_google_sheets():
    try:
        escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file('credentials.json', scopes=escopos)
        client = gspread.authorize(creds)
        return client.open("Dados_TRI_Sistema").sheet1
    except: return None

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

# --- 6. PAINEL PRINCIPAL ---
else:
    st.sidebar.title("💎 Gestão Premium")
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "⚙️ Importar Dados", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "⚙️ Importar Dados":
        st.header("⚙️ Importar Planilha")
        arquivo = st.file_uploader("Subir Excel (.xlsx)", type="xlsx")
        if arquivo:
            df = pd.read_excel(arquivo).fillna("X")
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            for idx, row in df.iterrows():
                binario = {q: 1 if str(row[q]).upper() == gab[int(q[1:])-1] else 0 for q in cols_q}
                df.at[idx, 'Proficiência'] = calcular_tri(binario)
            st.session_state['banco_dados'] = df
            st.success("Dados processados!")
            if st.button("💾 SALVAR NA NUVEM"):
                if salvar_no_banco(df): st.success("✅ Salvo no Google Sheets!")

    elif menu == "📊 Dashboard":
        if st.session_state['banco_dados'] is not None:
            df_f = st.session_state['banco_dados']
            media = df_f['Proficiência'].mean()
            info = obter_detalhes_nivel(media)
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            gab_dict = {f'Q{i:02d}': gab[i-1] for i in range(1, 23)}

            # Cabeçalho
            st.title("📊 Análise de Desempenho")
            c1, c2 = st.columns(2)
            c1.metric("Média Geral TRI", f"{media:.1f}")
            c2.markdown(f"### Nível: <span style='color:{info['cor']}'>{info['nivel']}</span>", unsafe_allow_html=True)
            st.info(f"**Sugestão:** {info['sug']}")

            # --- SEÇÃO DE DOWNLOADS ---
            st.divider()
            st.subheader("📄 Exportar Relatórios")
            cd1, cd2 = st.columns(2)
            
            with cd1:
                if st.button("📑 Gerar PDF Analítico (Lista de Alunos)"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, 'RELATÓRIO ANALÍTICO', ln=True, align='C')
                    pdf.set_font('Arial', '', 10)
                    for _, r in df_f.iterrows():
                        pdf.cell(0, 7, f"Aluno: {r['Nome']} - Nota: {r['Proficiência']:.1f}", ln=True)
                    st.download_button("📥 Baixar PDF Analítico", pdf.output(dest='S').encode('latin-1'), "Analitico.pdf")

            with cd2:
                if st.button("📈 Gerar PDF com Gráficos e Habilidades"):
                    pdf = FPDF()
                    pdf.add_page()
                    for q in cols_q:
                        stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                        fig, ax = plt.subplots(figsize=(4, 2))
                        ax.bar(['A','B','C','D'], stats, color=['#2ECC71' if l == gab_dict[q] else '#E74C3C' for l in ['A','B','C','D']])
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                            fig.savefig(tmp.name, bbox_inches='tight'); plt.close(fig)
                            if pdf.get_y() > 230: pdf.add_page()
                            pdf.set_font('Arial', 'B', 11); pdf.cell(0, 10, f"Questão {q}", ln=True)
                            pdf.image(tmp.name, x=10, w=70)
                            pdf.set_font('Arial', 'I', 8); pdf.multi_cell(0, 5, f"Habilidade: Descritor mapeado para o item {q}.")
                    st.download_button("📥 Baixar PDF Gráfico", pdf.output(dest='S').encode('latin-1'), "Graficos.pdf")

            # --- GRÁFICOS NA TELA ---
            st.divider()
            st.subheader("🎯 Visualização por Item")
            grid = st.columns(2)
            for i, q in enumerate(cols_q):
                with grid[i % 2]:
                    with st.container(border=True):
                        stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                        fig, ax = plt.subplots(figsize=(6, 3))
                        ax.bar(['A','B','C','D'], stats, color=['#2ECC71' if l == gab_dict[q] else '#E74C3C' for l in ['A','B','C','D']])
                        ax.set_title(f"Item {q}")
                        st.pyplot(fig)
        else:
            st.warning("⚠️ Sem dados. Vá em 'Importar Dados' primeiro.")
