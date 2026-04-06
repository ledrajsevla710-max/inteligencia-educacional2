import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor Pedagógico - José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. MATRIZES DE DESCRITORES (DINÂMICAS) ---
MATRIZ_LP = {
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

MATRIZ_MAT = {
    "Q01": "D1 - Identificar figuras bidimensionais.",
    "Q02": "D2 - Reconhecer propriedades de polígonos.",
    "Q03": "D3 - Identificar relações entre figuras espaciais.",
    "Q04": "D4 - Identificar polígonos regulares.",
    "Q05": "D5 - Reconhecer conservação de perímetro/área.",
    "Q06": "D6 - Reconhecer ângulos como mudança de direção.",
    "Q07": "D12 - Resolver problemas com medidas de grandeza.",
    "Q08": "D13 - Calcular área de figuras planas.",
    "Q09": "D14 - Resolver problema com noções de volume.",
    "Q10": "D16 - Identificar localização em mapas/malhas.",
    "Q11": "D17 - Identificar coordenadas no plano cartesiano.",
    "Q12": "D18 - Reconhecer expressão algébrica.",
    "Q13": "D19 - Resolver problema com inequações de 1º grau.",
    "Q14": "D20 - Analisar crescimento/decrescimento de função.",
    "Q15": "D21 - Resolver sistema de equações de 1º grau.",
    "Q16": "D22 - Identificar gráfico de funções de 1º grau.",
    "Q17": "D23 - Resolver problemas com porcentagem.",
    "Q18": "D24 - Resolver problemas com juros simples.",
    "Q19": "D25 - Resolver problemas com grandezas proporcionais.",
    "Q20": "D26 - Associar informações de tabelas/gráficos.",
    "Q21": "D27 - Calcular média aritmética de dados.",
    "Q22": "D28 - Resolver problema com probabilidade simples."
}

# --- 3. LÓGICA DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None
if 'materia_selecionada' not in st.session_state: st.session_state['materia_selecionada'] = "Língua Portuguesa"

# --- 4. LOGIN ---
if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal de Avaliação Municipal</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
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
            st.success(f"✅ Há uma planilha de {st.session_state['materia_selecionada']} pronta para análise.")
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
                st.session_state['materia_selecionada'] = mat
                st.success(f"Dados de {mat} carregados!")

    elif menu == "📊 Painel de Resultados":
        if st.session_state['banco_dados'] is None:
            st.error("Envie os dados primeiro.")
        else:
            df = st.session_state['banco_dados']
            # Define qual matriz usar baseado na seleção
            matriz_ativa = MATRIZ_MAT if st.session_state['materia_selecionada'] == "Matemática" else MATRIZ_LP
            
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']
            gab_dict = {f'Q{i:02d}': gab[i-1] for i in range(1, 23)}

            f_esc = st.sidebar.selectbox("Escola:", ["Visão Geral"] + list(df['Escola'].unique()))
            df_f = df if f_esc == "Visão Geral" else df[df['Escola'] == f_esc]

            st.header(f"📊 Análise ({st.session_state['materia_selecionada']}): {f_esc}")
            
            # Tabela
            dados_tab = []
            for q in cols_q:
                perc = (len(df_f[df_f[q].astype(str).str.upper() == gab_dict[q]]) / len(df_f)) * 100
                dados_tab.append({"Item": q, "Acerto (%)": f"{perc:.1f}%", "Habilidade": matriz_ativa.get(q)})
            st.table(pd.DataFrame(dados_tab))

            # Gráficos
            st.divider()
            grid = st.columns(4)
            for i, q in enumerate(cols_q):
                with grid[i % 4]:
                    with st.container(border=True):
                        st.caption(f"**{q}**: {matriz_ativa.get(q)[:35]}...")
                        freq = df_f[q].astype(str).str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                        fig, ax = plt.subplots(figsize=(4, 3))
                        ax.bar(['A','B','C','D'], freq, color=['#2ECC71' if l == gab_dict[q] else '#E74C3C' for l in ['A','B','C','D']])
                        st.pyplot(fig)

            # Botão PDF
            if st.button("📄 Gerar Relatório Oficial"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f'RELATÓRIO TÉCNICO ({st.session_state["materia_selecionada"]}) - {f_esc}', ln=True, align='C')
                
                fig_p, ax_p = plt.subplots(figsize=(12, 4))
                ax_p.bar([d['Item'] for d in dados_tab], [float(d['Acerto (%)'].replace('%','')) for d in dados_tab], color='#1E3A8A')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); pdf.image(tmp.name, x=10, y=30, w=275)
                
                pdf.set_y(130); pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, "HABILIDADES MAIS CRÍTICAS:", ln=True)
                piores = sorted(dados_tab, key=lambda x: float(x['Acerto (%)'].replace('%','')))[:3]
                for p in piores:
                    pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, f"{p['Item']} - {p['Habilidade']} ({p['Acerto (%)']})", ln=True)
                
                st.download_button("Baixar PDF", pdf.output(dest='S').encode('latin-1'), "Relatorio.pdf")
