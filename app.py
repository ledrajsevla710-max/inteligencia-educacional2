import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor Pedagógico - José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. MATRIZES DE DESCRITORES (SAEB/SAEPI) ---
MATRIZ_PORTUGUES = {
    "Q01": "D1 - Localizar informações explícitas.",
    "Q02": "D3 - Inferir sentido de palavra/expressão.",
    "Q03": "D4 - Inferir informação implícita.",
    "Q04": "D6 - Identificar o tema do texto.",
    "Q05": "D14 - Distinguir fato de opinião.",
    "Q06": "D12 - Identificar finalidade do texto.",
    "Q07": "D2 - Estabelecer relações entre partes.",
    "Q08": "D5 - Interpretar texto com auxílio de imagem.",
    "Q09": "D7 - Identificar a tese do texto.",
    "Q10": "D8 - Relação tese e argumentos.",
    "Q11": "D9 - Partes principais e secundárias.",
    "Q12": "D10 - Conflito gerador do enredo.",
    "Q13": "D11 - Relação causa e consequência.",
    "Q14": "D13 - Marcas linguísticas (locutor).",
    "Q15": "D15 - Relações lógico-discursivas.",
    "Q16": "D16 - Efeitos de ironia ou humor.",
    "Q17": "D17 - Efeito de sentido da pontuação.",
    "Q18": "D18 - Escolha de palavras/expressões.",
    "Q19": "D19 - Recursos gráficos (caixa alta, negrito).",
    "Q20": "D20 - Diferentes formas de tratar o tema.",
    "Q21": "D21 - Posições distintas entre textos.",
    "Q22": "D22 - Recursos ortográficos e estilísticos."
}

MATRIZ_MATEMATICA = {
    "Q01": "D1 - Identificar figuras bifidimensionais.",
    "Q02": "D2 - Planificação de sólidos geométricos.",
    "Q03": "D3 - Relações entre polígonos (lados/ângulos).",
    "Q04": "D4 - Identificar quadriláteros.",
    "Q05": "D5 - Reconhecer conservação de perímetro/área.",
    "Q06": "D6 - Localização/movimentação em mapas/malhas.",
    "Q07": "D12 - Resolver problemas com números naturais.",
    "Q08": "D13 - Calcular resultado de multiplicação/divisão.",
    "Q09": "D14 - Problemas com frações.",
    "Q10": "D16 - Números decimais na reta numérica.",
    "Q11": "D17 - Operações com números decimais.",
    "Q12": "D18 - Problemas com porcentagem (25%, 50%, 100%).",
    "Q13": "D19 - Resolver problemas com medidas de tempo.",
    "Q14": "D20 - Problemas com unidades de medida (m, kg, L).",
    "Q15": "D21 - Problemas com sistema monetário brasileiro.",
    "Q16": "D24 - Identificar representação algébrica.",
    "Q17": "D26 - Expressões numéricas com inteiros.",
    "Q18": "D28 - Resolver equações de 1º grau.",
    "Q19": "D32 - Problemas com teorema de Pitágoras.",
    "Q20": "D34 - Razões trigonométricas (sen, cos, tan).",
    "Q21": "D36 - Informações em tabelas.",
    "Q22": "D37 - Informações em gráficos de barras/setores."
}

# --- 3. LÓGICA DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None
if 'materia_selecionada' not in st.session_state: st.session_state['materia_selecionada'] = "Língua Portuguesa"

# --- 4. LOGIN ---
if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal Pedagógico</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if user == "12345" and senha == "000":
                st.session_state['autenticado'] = True
                st.rerun()
else:
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "📝 Enviar Avaliações", "📊 Painel de Resultados", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "🏠 Início":
        st.title(f"👋 Bem-vindo, Jardel Alves Vieira!")
        st.write(f"Você está visualizando dados de: **{st.session_state['materia_selecionada']}**")

    elif menu == "📝 Enviar Avaliações":
        st.header("📝 Nova Importação")
        if st.session_state['banco_dados'] is not None:
            if st.button("🗑️ LIMPAR DADOS"):
                st.session_state['banco_dados'] = None
                st.rerun()
        else:
            materia = st.selectbox("Selecione a Disciplina:", ["Língua Portuguesa", "Matemática"])
            st.session_state['materia_selecionada'] = materia
            arq = st.file_uploader("Arquivo Excel:", type="xlsx")
            if arq:
                st.session_state['banco_dados'] = pd.read_excel(arq).fillna("X")
                st.success(f"Avaliação de {materia} carregada!")

    elif menu == "📊 Painel de Resultados":
        if st.session_state['banco_dados'] is None:
            st.error("Envie os dados primeiro.")
        else:
            # DEFINE QUAL MATRIZ USAR
            matriz_ativa = MATRIZ_MATEMATICA if st.session_state['materia_selecionada'] == "Matemática" else MATRIZ_PORTUGUES
            
            df = st.session_state['banco_dados']
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B'] # Exemplo
            
            st.header(f"📊 Resultados: {st.session_state['materia_selecionada']}")
            
            # Tabela
            dados_tab = []
            for q in cols_q:
                perc = (len(df[df[q].astype(str).str.upper() == gab[int(q[1:])-1]]) / len(df)) * 100
                dados_tab.append({"Item": q, "Acerto (%)": f"{perc:.1f}%", "Habilidade": matriz_ativa.get(q)})
            
            st.table(pd.DataFrame(dados_tab))

            # Gráficos com a legenda correta
            grid = st.columns(4)
            for i, q in enumerate(cols_q):
                with grid[i % 4]:
                    with st.container(border=True):
                        st.caption(f"**{q}**: {matriz_ativa.get(q)[:35]}...")
                        # ... (lógica do gráfico igual à anterior)
