import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor Pedagógico - José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. MATRIZES DE DESCRITORES REAIS ---
MATRIZ_LP = {f"Q{i:02d}": f"Descritor de Língua Portuguesa {i}" for i in range(1, 23)} 
MATRIZ_MAT = {f"Q{i:02d}": f"Descritor de Matemática {i}" for i in range(1, 23)}

# --- 3. LÓGICA DE INTERVENÇÃO ---
def sugerir_intervencao(item, matriz):
    desc = matriz.get(item, "")
    if "D1" in desc or "D4" in desc: return "Oficinas de sublinhar palavras-chave."
    return "Reforço teórico e exercícios práticos em grupo."

# --- 4. MOTOR TRI ---
def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- 5. SESSÃO E LOGIN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal de Avaliação Municipal</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True; st.rerun()
else:
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "📝 Enviar Avaliações", "📊 Painel de Resultados", "🚪 Sair"])

    if menu == "🏠 Início":
        st.title(f"👋 Bem-vindo, Jardel Alves Vieira!")
        st.write("Sistema de Monitoramento de Proficiência TRI.")

    elif menu == "📝 Enviar Avaliações":
        st.header("📝 Nova Importação")
        if st.session_state['banco_dados'] is not None:
            if st.button("🗑️ LIMPAR DADOS", type="primary"): st.session_state['banco_dados'] = None; st.rerun()
        else:
            c1, c2 = st.columns(2)
            mat = c1.selectbox("Disciplina:", ["Língua Portuguesa", "Matemática"])
            arq = st.file_uploader("Arquivo Excel:", type="xlsx")
            if arq:
                df = pd.read_excel(arq).fillna("X")
                cols_q = [f'Q{i:02d}' for i in range(1, 23)]
                gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
                for idx, row in df.iterrows():
                    binario = {q: 1 if str(row[q]).upper() == gab[int(q[1:])-1] else 0 for q in cols_q}
                    df.at[idx, 'Proficiência_TRI'] = calcular_tri(binario)
                st.session_state['banco_dados'] = df
                st.session_state['mat_ativa'] = mat
                st.success("Dados processados!")

    elif menu == "📊 Painel de Resultados":
        if st.session_state['banco_dados'] is not None:
            df = st.session_state['banco_dados']
            matriz = MATRIZ_MAT if st.session_state.get('mat_ativa') == "Matemática" else MATRIZ_LP
            f_esc = st.sidebar.selectbox("Escola:", ["Visão Geral"] + list(df['Escola'].unique()))
            df_f = df if f_esc == "Visão Geral" else df[df['Escola'] == f_esc]

            st.header(f"📊 Análise: {f_esc}")
            
            # Cálculo de estatísticas para exibição e PDF
            stats = []
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            for i, q in enumerate([f'Q{i:02d}' for i in range(1, 23)]):
                perc = (len(df_f[df_f[q].astype(str).str.upper() == gab[i]]) / len(df_f)) * 100
                stats.append({"Item": q, "Acerto": perc, "Habilidade": matriz.get(q, "Habilidade não definida")})
            
            df_stats = pd.DataFrame(stats)

            # Botão PDF (CORREÇÃO CARACTERES E GRÁFICOS)
            if st.button("📄 Gerar Relatório Técnico"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                
                # Função interna para limpar texto para o PDF (Resolve o erro latin1)
                def clean_txt(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

                pdf.cell(0, 10, clean_txt(f'RELATÓRIO - {f_esc} ({st.session_state.get("mat_ativa", "Geral")})'), ln=True, align='C')
                
                # Gráfico Geral (Gerado na hora do clique)
                fig_pdf, ax_pdf = plt.subplots(figsize=(12, 4))
                ax_pdf.bar(df_stats['Item'], df_stats['Acerto'], color='#1E3A8A')
                ax_pdf.set_ylim(0, 100)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name)
                    pdf.image(tmp.name, x=10, y=35, w=275)
                plt.close(fig_pdf) # Limpa memória

                # Segunda Página: Destaques
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, clean_txt("🏆 PONTOS FORTES E ATENÇÃO"), ln=True)
                
                # Piores e Melhores
                df_ord = df_stats.sort_values(by="Acerto")
                for label, subset in zip(["PIORES", "MELHORES"], [df_ord.head(3), df_ord.tail(3)]):
                    pdf.set_font('Arial', 'B', 11); pdf.cell(0, 7, clean_txt(label), ln=True)
                    pdf.set_font('Arial', '', 9)
                    for _, r in subset.iterrows():
                        pdf.cell(0, 5, clean_txt(f"- {r['Item']}: {r['Habilidade']} ({r['Acerto']:.1f}%)"), ln=True)
                    pdf.ln(3)

                st.download_button("📥 Baixar PDF", pdf.output(dest='S'), "Relatorio.pdf")

            # Exibição na Tela
            st.subheader("Gráficos de Desempenho")
            grid = st.columns(4)
            for i, r in enumerate(stats):
                with grid[i % 4]:
                    with st.container(border=True):
                        st.write(f"**{r['Item']}**")
                        fig_ui, ax_ui = plt.subplots(figsize=(3,2))
                        ax_ui.bar(["Acerto", "Erro"], [r['Acerto'], 100-r['Acerto']], color=['green', 'red'])
                        ax_ui.set_ylim(0,100)
                        st.pyplot(fig_ui)
                        plt.close(fig_ui)
