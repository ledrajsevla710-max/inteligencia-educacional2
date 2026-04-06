import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor Pedagógico - José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. MATRIZ DE DESCRITORES REAIS (LP/9º ANO - EXEMPLO) ---
MATRIZ_REAL = {
    "Q01": "D1 - Localizar informações explícitas.",
    "Q02": "D3 - Inferir o sentido de palavra/expressão.",
    "Q03": "D4 - Inferir informação implícita.",
    "Q04": "D6 - Identificar o tema do texto.",
    "Q05": "D14 - Distinguir fato de opinião.",
    "Q06": "D12 - Identificar finalidade do texto.",
    "Q07": "D2 - Estabelecer relações entre partes do texto.",
    "Q08": "D5 - Interpretar texto com auxílio de imagem.",
    "Q09": "D7 - Identificar a tese do texto.",
    "Q10": "D8 - Estabelecer relação tese/argumentos.",
    "Q11": "D9 - Diferenciar partes principais/secundárias.",
    "Q12": "D10 - Identificar o conflito do enredo.",
    "Q13": "D11 - Estabelecer relação causa/consequência.",
    "Q14": "D13 - Identificar marcas linguísticas (locutor).",
    "Q15": "D15 - Estabelecer relações lógico-discursivas.",
    "Q16": "D16 - Identificar efeitos de ironia/humor.",
    "Q17": "D17 - Identificar efeito de pontuação.",
    "Q18": "D18 - Efeito de sentido (escolha de palavras).",
    "Q19": "D19 - Efeito de sentido (recursos gráficos).",
    "Q20": "D20 - Diferentes formas de tratar o tema.",
    "Q21": "D21 - Reconhecer posições distintas entre textos.",
    "Q22": "D22 - Identificar recursos ortográficos/estilísticos."
}

# --- 3. LÓGICA DE INTERVENÇÃO ---
def sugerir_intervencao(item):
    descritor = MATRIZ_REAL.get(item, "")
    if "D1" in descritor or "D4" in descritor:
        return "Trabalhar oficinas de leitura com foco em busca de pistas no texto e sublinhar informações-chave."
    elif "D3" in descritor or "D14" in descritor:
        return "Utilizar textos jornalísticos para separar o que é dado concreto (fato) do que é julgamento (opinião)."
    elif "D6" in descritor or "D12" in descritor:
        return "Explorar gêneros diversos (convites, receitas, notícias) para identificar para que serve cada texto."
    else:
        return "Reforçar a análise coletiva de itens similares em sala de aula, discutindo os distratores com os alunos."

# --- 4. ACESSO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Portal de Avaliação Municipal</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            user = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.button("Acessar Painel", use_container_width=True):
                if user == "12345" and senha == "000":
                    st.session_state['autenticado'] = True
                    st.rerun()

else:
    st.sidebar.title("💎 Menu")
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "📝 Enviar Avaliações", "📊 Painel de Resultados", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "🏠 Início":
        st.title(f"👋 Bem-vindo, Jardel Alves Vieira!")
        st.write("Sistema de Monitoramento de Proficiência - José de Freitas.")
        if st.session_state['banco_dados'] is not None:
            st.success("✅ Há uma planilha pronta para análise no painel.")
        else:
            st.info("💡 Comece enviando uma planilha na aba 'Enviar Avaliações'.")

    elif menu == "📝 Enviar Avaliações":
        st.header("📝 Nova Importação")
        if st.session_state['banco_dados'] is not None:
            if st.button("🗑️ EXCLUIR DADOS ATUAIS", type="primary"):
                st.session_state['banco_dados'] = None
                st.rerun()
        else:
            c1, c2 = st.columns(2)
            mat = c1.selectbox("Disciplina:", ["Língua Portuguesa", "Matemática"])
            ano = c2.selectbox("Ano Escolar:", ["9º Ano", "5º Ano", "2º Ano"])
            arq = st.file_uploader("Arquivo Excel:", type="xlsx")
            if arq:
                st.session_state['banco_dados'] = pd.read_excel(arq).fillna("X")
                st.success("Dados carregados!")

    elif menu == "📊 Painel de Resultados":
        if st.session_state['banco_dados'] is None:
            st.error("Envie os dados primeiro.")
        else:
            df = st.session_state['banco_dados']
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            gab_dict = {f'Q{i:02d}': gab[i-1] for i in range(1, 23)}

            f_esc = st.sidebar.selectbox("Escola:", ["Visão Geral"] + list(df['Escola'].unique()))
            df_f = df if f_esc == "Visão Geral" else df[df['Escola'] == f_esc]

            st.header(f"📊 Análise: {f_esc}")
            
            # Tabela Percentual
            dados_tab = []
            for q in cols_q:
                perc = (len(df_f[df_f[q].astype(str).str.upper() == gab_dict[q]]) / len(df_f)) * 100
                dados_tab.append({"Item": q, "Acerto (%)": f"{perc:.1f}%", "Habilidade": MATRIZ_REAL.get(q)})
            st.table(pd.DataFrame(dados_tab))

            # Gráficos com Legenda de Habilidade
            st.divider()
            st.subheader("🎯 Desempenho por Item")
            grid = st.columns(4)
            for i, q in enumerate(cols_q):
                with grid[i % 4]:
                    with st.container(border=True):
                        st.caption(f"**{q}**: {MATRIZ_REAL[q][:35]}...")
                        freq = df_f[q].astype(str).str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                        fig, ax = plt.subplots(figsize=(4, 3))
                        ax.bar(['A','B','C','D'], freq, color=['#2ECC71' if l == gab_dict[q] else '#E74C3C' for l in ['A','B','C','D']])
                        st.pyplot(fig)

            # Botão PDF com Diagnóstico
            st.divider()
            if st.button("📄 Gerar Relatório com Intervenção Pedagógica"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f'RELATÓRIO TÉCNICO - {f_esc}', ln=True, align='C')
                
                # Gráfico
                fig_p, ax_p = plt.subplots(figsize=(12, 4))
                ax_p.bar([d['Item'] for d in dados_tab], [float(d['Acerto (%)'].replace('%','')) for d in dados_tab], color='#1E3A8A')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); pdf.image(tmp.name, x=10, y=30, w=275)
                
                # Diagnóstico e Intervenção
                pdf.set_y(130)
                pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, "HABILIDADES CRÍTICAS E INTERVENÇÃO SUGERIDA:", ln=True)
                pdf.set_font('Arial', '', 10)
                
                # Pega as 3 piores
                piores = sorted(dados_tab, key=lambda x: float(x['Acerto (%)'].replace('%','')))[:3]
                for p in piores:
                    pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, f"Item {p['Item']} - {p['Habilidade']} (Acerto: {p['Acerto (%)']})", ln=True)
                    pdf.set_font('Arial', 'I', 10); pdf.multi_cell(0, 5, f"Sugestão: {sugerir_intervencao(p['Item'])}")
                    pdf.ln(2)

                st.download_button("Baixar PDF Oficial", pdf.output(dest='S').encode('latin-1'), "Relatorio_Intervencao.pdf")
