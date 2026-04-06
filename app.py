import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor TRI Municipal", layout="wide", page_icon="🏛️")

# --- 2. MATRIZ DE HABILIDADES ---
MATRIZ_OFICIAL = {f"Q{i:02d}": f"Descritor de Habilidade do item {i}" for i in range(1, 23)}

# --- 3. LÓGICA DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

# --- 4. TELA DE LOGIN ---
if not st.session_state['autenticado']:
    st.title("🏛️ Portal TRI Municipal")
    with st.container(border=True):
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if user == "12345" and senha == "000":
                st.session_state['autenticado'] = True
                st.rerun()
            else: st.error("Credenciais inválidas.")

# --- 5. PAINEL DO GESTOR ---
else:
    st.sidebar.title("💎 Menu de Gestão")
    menu = st.sidebar.radio("Navegação", ["⚙️ Importar Dados", "📊 Dashboard Analítico", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    # --- ABA: IMPORTAR DADOS ---
    elif menu == "⚙️ Importar Dados":
        st.header("⚙️ Central de Importação")
        
        if st.session_state['banco_dados'] is not None:
            st.warning("⚠️ Já existe uma planilha carregada no sistema.")
            if st.button("🗑️ EXCLUIR DADOS ATUAIS E RECOMEÇAR", type="primary"):
                st.session_state['banco_dados'] = None
                st.rerun()
        else:
            materia = st.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
            arquivo = st.file_uploader("Selecione a Planilha Excel (.xlsx)", type="xlsx")
            if arquivo:
                df_temp = pd.read_excel(arquivo).fillna("X")
                st.success("✅ Planilha carregada com sucesso!")
                st.session_state['banco_dados'] = df_temp
                st.info("Vá para a aba 'Dashboard Analítico' para ver os resultados.")

    # --- ABA: DASHBOARD ---
    elif menu == "📊 Dashboard Analítico":
        if st.session_state['banco_dados'] is None:
            st.error("🚫 ACESSO BLOQUEADO: Você precisa carregar uma planilha na aba 'Importar Dados' primeiro.")
            st.image("https://cdn-icons-png.flaticon.com/512/3064/3064155.png", width=100)
        else:
            df = st.session_state['banco_dados']
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            gab_dict = {f'Q{i:02d}': gab[i-1] for i in range(1, 23)}

            f_esc = st.sidebar.selectbox("Escola:", ["Geral Município"] + list(df['Escola'].unique()))
            df_f = df if f_esc == "Geral Município" else df[df['Escola'] == f_esc]

            st.title(f"📊 Dashboard: {f_esc}")
            
            # --- SEÇÃO 1: RESUMO EM TABELA ---
            st.subheader("📋 Percentual de Acertos e Habilidades")
            dados_dashboard = []
            for q in cols_q:
                total = len(df_f)
                acertos = len(df_f[df_f[q].astype(str).str.upper() == gab_dict[q]])
                perc = (acertos / total) * 100
                dados_dashboard.append({
                    "Item": q,
                    "Acerto (%)": f"{perc:.1f}%",
                    "Habilidade": MATRIZ_OFICIAL.get(q, "Não mapeada")
                })
            st.table(pd.DataFrame(dados_dashboard))

            # --- SEÇÃO 2: MINI-GRÁFICOS POR QUESTÃO ---
            st.divider()
            st.subheader("🎯 Análise Individual por Item")
            
            # Criando colunas para os gráficos pequenos (4 por linha)
            col_charts = st.columns(4)
            for i, q in enumerate(cols_q):
                with col_charts[i % 4]:
                    with st.container(border=True):
                        st.write(f"**Item {q}**")
                        # Cálculo de frequência de respostas (A, B, C, D)
                        freq = df_f[q].astype(str).str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                        
                        fig, ax = plt.subplots(figsize=(4, 3))
                        cores = ['#2ECC71' if letra == gab_dict[q] else '#E74C3C' for letra in ['A','B','C','D']]
                        ax.bar(['A','B','C','D'], freq, color=cores)
                        ax.set_ylim(0, 100)
                        st.pyplot(fig)
                        st.caption(f"{MATRIZ_OFICIAL[q][:30]}...") # Mostra início da habilidade

            # --- SEÇÃO 3: DOWNLOAD RELATÓRIO PAISAGEM ---
            st.divider()
            if st.button("📄 Gerar Relatório PDF Profissional (Paisagem)"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f'RELATÓRIO DE DESEMPENHO - {f_esc}', ln=True, align='C')
                
                # Gráfico Geral para o PDF
                fig_pdf, ax_pdf = plt.subplots(figsize=(12, 5))
                questoes = [d['Item'] for d in dados_dashboard]
                valores = [float(d['Acerto (%)'].replace('%','')) for d in dados_dashboard]
                ax_pdf.bar(questoes, valores, color='#3498DB')
                ax_pdf.set_ylim(0, 100)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name, bbox_inches='tight')
                    pdf.image(tmp.name, x=10, y=40, w=270)
                
                st.download_button("📥 Baixar Relatório", pdf.output(dest='S').encode('latin-1'), f"Relatorio_{f_esc}.pdf")
