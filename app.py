import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Sistema de Monitoramento Pedagógico", layout="wide", page_icon="🏛️")

# --- 2. MATRIZ DE HABILIDADES (Exemplos de Língua Portuguesa) ---
MATRIZ_OFICIAL = {f"Q{i:02d}": f"Descritor de Habilidade {i} - Matriz de Referência" for i in range(1, 23)}

# --- 3. LÓGICA DE ACESSO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

# --- 4. TELA DE ENTRADA (LOGIN) ---
if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Portal de Avaliação Municipal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Acesse o sistema para gerenciar os índices de proficiência.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            user = st.text_input("Usuário / INEP")
            senha = st.text_input("Senha de Acesso", type="password")
            if st.button("Entrar no Sistema", use_container_width=True):
                if user == "12345" and senha == "000":
                    st.session_state['autenticado'] = True
                    st.rerun()
                else: st.error("Acesso negado. Verifique suas credenciais.")

# --- 5. INTERFACE PRINCIPAL ---
else:
    # Menu com nomes amigáveis (sem termos técnicos)
    st.sidebar.title("💎 Menu Principal")
    menu = st.sidebar.radio("Escolha uma opção:", 
                           ["🏠 Página Inicial", 
                            "📝 Enviar Avaliações", 
                            "📊 Painel de Resultados", 
                            "🚪 Sair do Sistema"])

    if menu == "🚪 Sair do Sistema":
        st.session_state['autenticado'] = False
        st.rerun()

    # --- PÁGINA INICIAL ---
    elif menu == "🏠 Página Inicial":
        st.title("👋 Bem-vindo ao Gestor Pedagógico")
        st.markdown(f"### Olá, Jardel!")
        st.write("Este ambiente foi desenvolvido para facilitar a análise dos dados do SAEB e SAEPI no município.")
        
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.subheader("📍 Resumo Atual")
                if st.session_state['banco_dados'] is not None:
                    st.success("✅ Existe uma avaliação carregada e pronta para análise.")
                else:
                    st.info("ℹ️ Nenhuma avaliação enviada hoje. Vá em 'Enviar Avaliações'.")
        
        with c2:
            with st.container(border=True):
                st.subheader("📅 Calendário")
                st.write(f"Hoje é dia: **{datetime.date.today().strftime('%d/%m/%Y')}**")

    # --- ENVIAR AVALIAÇÕES (ANTIGO IMPORTAR) ---
    elif menu == "📝 Enviar Avaliações":
        st.header("📝 Cadastro de Nova Avaliação")
        
        if st.session_state['banco_dados'] is not None:
            st.warning("⚠️ Uma avaliação já está em processamento.")
            if st.button("🗑️ LIMPAR ARQUIVO E ENVIAR NOVO", type="primary"):
                st.session_state['banco_dados'] = None
                st.rerun()
        else:
            col_a, col_b = st.columns(2)
            materia = col_a.selectbox("Escolha a Disciplina:", ["Língua Portuguesa", "Matemática"])
            ano_escolar = col_b.selectbox("Escolha o Ano Escolar:", ["2º Ano", "5º Ano", "9º Ano"])
            
            arquivo = st.file_uploader("Selecione o arquivo da turma (Excel):", type="xlsx")
            if arquivo:
                df_temp = pd.read_excel(arquivo).fillna("X")
                st.session_state['banco_dados'] = df_temp
                st.success(f"✅ Avaliação de {materia} ({ano_escolar}) recebida com sucesso!")
                st.balloons()

    # --- PAINEL DE RESULTADOS (ANTIGO DASHBOARD) ---
    elif menu == "📊 Painel de Resultados":
        if st.session_state['banco_dados'] is None:
            st.error("⚠️ Nenhuma avaliação encontrada. Por favor, envie os dados na opção 'Enviar Avaliações' primeiro.")
        else:
            df = st.session_state['banco_dados']
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            gab_dict = {f'Q{i:02d}': gab[i-1] for i in range(1, 23)}

            st.sidebar.divider()
            f_esc = st.sidebar.selectbox("Selecionar Unidade Escolar:", ["Visão Geral Município"] + list(df['Escola'].unique()))
            df_f = df if f_esc == "Visão Geral Município" else df[df['Escola'] == f_esc]

            st.title(f"📊 Resultados: {f_esc}")
            
            # --- TABELA DE PERCENTUAIS ---
            st.subheader("📌 Percentual de Acertos por Questão")
            dados_tabela = []
            for q in cols_q:
                total = len(df_f)
                certos = len(df_f[df_f[q].astype(str).str.upper() == gab_dict[q]])
                perc = (certos / total) * 100
                dados_tabela.append({
                    "Questão": q,
                    "Acerto (%)": f"{perc:.1f}%",
                    "Habilidade": MATRIZ_OFICIAL.get(q)
                })
            st.table(pd.DataFrame(dados_tabela))

            # --- ANÁLISE POR ITEM (GRÁFICOS PEQUENOS) ---
            st.divider()
            st.subheader("🎯 Gráficos por Questão")
            col_graficos = st.columns(4)
            for i, q in enumerate(cols_q):
                with col_graficos[i % 4]:
                    with st.container(border=True):
                        st.write(f"**Item {q}**")
                        freq = df_f[q].astype(str).str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                        fig, ax = plt.subplots(figsize=(4, 3))
                        cores = ['#2ECC71' if letra == gab_dict[q] else '#E74C3C' for letra in ['A','B','C','D']]
                        ax.bar(['A','B','C','D'], freq, color=cores)
                        ax.set_ylim(0, 100)
                        st.pyplot(fig)

            # --- RELATÓRIO PDF ---
            st.divider()
            if st.button("📄 Gerar Relatório Oficial (Formato Paisagem)"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 15, f'RELATÓRIO DE MONITORAMENTO - {f_esc}', ln=True, align='C')
                
                # Gráfico Geral
                fig_pdf, ax_pdf = plt.subplots(figsize=(12, 5))
                questoes = [d['Questão'] for d in dados_tabela]
                valores = [float(d['Acerto (%)'].replace('%','')) for d in dados_tabela]
                ax_pdf.bar(questoes, valores, color='#1E3A8A')
                ax_pdf.set_ylim(0, 100)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name, bbox_inches='tight')
                    pdf.image(tmp.name, x=10, y=40, w=275)
                
                st.download_button("📥 Baixar Relatório para Impressão", pdf.output(dest='S').encode('latin-1'), f"Relatorio_{f_esc}.pdf")
