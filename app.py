import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor TRI Municipal", layout="wide", page_icon="🏛️")

# --- 2. MATRIZ DE HABILIDADES (EXEMPLO) ---
MATRIZ = {f"Q{i:02d}": f"Habilidade/Descritor do item {i}" for i in range(1, 23)}

# --- 3. LÓGICA DE LOGIN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

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

else:
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "⚙️ Importar Dados", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    # --- ABA: IMPORTAR DADOS ---
    elif menu == "⚙️ Importar Dados":
        st.header("⚙️ Importar Avaliações")
        materia = st.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
        serie_sistema = st.selectbox("Série no Sistema:", ["2º Ano", "5º Ano", "9º Ano"])
        
        arquivo = st.file_uploader("Subir Excel", type="xlsx")
        if arquivo:
            df_temp = pd.read_excel(arquivo).fillna("X")
            
            # Ajuste na leitura da série (Pega apenas o número para evitar erro de texto)
            serie_planilha = str(df_temp['Série'].iloc[0]) if 'Série' in df_temp.columns else ""
            num_sistema = "".join(filter(str.isdigit, serie_sistema))
            num_planilha = "".join(filter(str.isdigit, serie_planilha))
            
            if num_sistema != num_planilha:
                st.error(f"❌ CONFLITO: Você selecionou {serie_sistema}, mas a planilha é do {serie_planilha}. Ajuste a seleção.")
            else:
                st.success(f"✅ Dados do {serie_sistema} validados!")
                st.session_state['banco_dados'] = df_temp

    # --- ABA: DASHBOARD ---
    elif menu == "📊 Dashboard":
        if st.session_state['banco_dados'] is not None:
            df = st.session_state['banco_dados']
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            gab_dict = {f'Q{i:02d}': gab[i-1] for i in range(1, 23)}

            # Filtros
            st.sidebar.subheader("Filtros de Visão")
            f_esc = st.sidebar.selectbox("Escola:", ["Geral Município"] + list(df['Escola'].unique()))
            df_f = df if f_esc == "Geral Município" else df[df['Escola'] == f_esc]

            st.header(f"📊 Desempenho: {f_esc}")

            # 1. TABELA DE ACERTOS (Substitui os gráficos amontoados)
            st.subheader("📋 Resumo por Item (Percentual)")
            analise_dados = []
            for q in cols_q:
                total = len(df_f)
                acertos = len(df_f[df_f[q].str.upper() == gab_dict[q]])
                perc_acerto = (acertos / total) * 100
                analise_dados.append({
                    "Questão": q,
                    "Acerto (%)": f"{perc_acerto:.1f}%",
                    "Erro (%)": f"{100 - perc_acerto:.1f}%",
                    "Habilidade": MATRIZ.get(q)
                })
            
            st.table(pd.DataFrame(analise_dados))

            # --- 2. RELATÓRIO PDF EM PAISAGEM ---
            st.divider()
            if st.button("📄 Gerar Relatório Profissional (Modo Paisagem)"):
                # 'L' para Landscape (Paisagem)
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f'RELATÓRIO DE DESEMPENHO TRI - {f_esc}', ln=True, align='C')
                
                # Gráfico Grande para o PDF
                fig, ax = plt.subplots(figsize=(12, 5))
                questoes = [d['Questão'] for d in analise_dados]
                valores = [float(d['Acerto (%)'].replace('%','')) for d in analise_dados]
                
                ax.bar(questoes, valores, color='#2ECC71', edgecolor='black')
                ax.set_ylabel('% de Acerto')
                ax.set_ylim(0, 100)
                ax.set_title("Visão Geral de Acertos por Item")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name, bbox_inches='tight')
                    pdf.image(tmp.name, x=10, y=40, w=270) # Largura quase total da folha A4 paisagem
                
                # Tabela de Habilidades Críticas abaixo do gráfico no PDF
                pdf.set_y(150)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "Habilidades Críticas Identificadas:", ln=True)
                pdf.set_font('Arial', '', 10)
                
                # Pega as 3 piores
                piores = sorted(analise_dados, key=lambda x: float(x['Acerto (%)'].replace('%','')))[:3]
                for p in piores:
                    pdf.cell(0, 7, f"- {p['Questão']}: {p['Habilidade']} (Apenas {p['Acerto (%)']} de acerto)", ln=True)

                st.download_button("📥 Baixar Relatório Paisagem", pdf.output(dest='S').encode('latin-1'), f"Relatorio_{f_esc}.pdf")

        else:
            st.info("⚠️ Aguardando importação de dados.")
