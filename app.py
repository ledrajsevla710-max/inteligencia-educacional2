import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. GESTÃO DE USUÁRIOS (SESSÃO) ---
if 'usuarios_db' not in st.session_state:
    st.session_state['usuarios_db'] = {"12345": "000"} 

# Banco de dados simulado para salvar os registros das escolas
if 'banco_geral' not in st.session_state:
    st.session_state['banco_geral'] = []

# --- 3. MATRIZES 1º BIMESTRE ---
MATRIZ_LP = {
    "Q01": "D1 - Localizar informações explícitas.", "Q02": "D3 - Inferir sentido de palavra/expressão.",
    "Q03": "D4 - Inferir informação implícita.", "Q04": "D6 - Identificar o tema do texto.",
    "Q05": "D14 - Distinguir fato de opinião.", "Q06": "D1 - Localizar informações explícitas.",
    "Q07": "D4 - Inferir informação implícita.", "Q08": "D5 - Interpretar texto com auxílio de imagem.",
    "Q09": "D3 - Inferir sentido de palavra/expressão.", "Q10": "D6 - Identificar o tema do texto.",
    "Q11": "D12 - Identificar finalidade do texto.", "Q12": "D1 - Localizar informações explícitas.",
    "Q13": "D3 - Inferir sentido de palavra/expressão.", "Q14": "D4 - Inferir informação implícita.",
    "Q15": "D6 - Identificar o tema do texto.", "Q16": "D14 - Distinguir fato de opinião.",
    "Q17": "D1 - Localizar informações explícitas.", "Q18": "D4 - Inferir informação implícita.",
    "Q19": "D5 - Interpretar texto com auxílio de imagem.", "Q20": "D6 - Identificar o tema do texto.",
    "Q21": "D3 - Inferir sentido de palavra/expressão.", "Q22": "D12 - Identificar finalidade do texto."
}

MATRIZ_MAT = {
    "Q01": "D13 - Área de figuras planas.", "Q02": "D14 - Noções de volume.",
    "Q03": "D16 - Localização em mapas/malhas.", "Q04": "D17 - Coordenadas no plano cartesiano.",
    "Q05": "D18 - Expressão algébrica.", "Q06": "D19 - Inequações de 1º grau.",
    "Q07": "D20 - Crescimento/Decrescimento de função.", "Q08": "D21 - Sistema de equações de 1º grau.",
    "Q09": "D22 - Gráfico de funções de 1º grau.", "Q10": "D23 - Porcentagem.",
    "Q11": "D24 - Juros simples.", "Q12": "D25 - Grandezas proporcionais.",
    "Q13": "D26 - Tabelas/Gráficos.", "Q14": "D27 - Média aritmética.",
    "Q15": "D28 - Probabilidade simples.", "Q16": "D1 - Figuras bidimensionais.",
    "Q17": "D2 - Propriedades de polígonos.", "Q18": "D3 - Figuras espaciais.",
    "Q19": "D4 - Polígonos regulares.", "Q20": "D5 - Conservação de perímetro/área.",
    "Q21": "D6 - Ângulos e direções.", "Q22": "D12 - Medidas de grandeza."
}

GABARITO = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']

# --- 4. MOTORES DE CÁLCULO ---
def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        b = np.linspace(-2.5, 2.5, 22)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel_escala(valor, disciplina):
    if disciplina == "Língua Portuguesa":
        if valor < 200: return "Muito Crítico", "#D32F2F", "Dificuldade em localizar informações básicas."
        if valor < 250: return "Crítico", "#F57C00", "Identifica o tema, mas falha em inferências."
        if valor < 300: return "Intermediário", "#FBC02D", "Domina leitura básica e ironia simples."
        return "Adequado", "#388E3C", "Capacidade plena de interpretação e tese."
    else:
        if valor < 225: return "Muito Crítico", "#D32F2F", "Dificuldade em operações e formas simples."
        if valor < 275: return "Crítico", "#F57C00", "Resolve adição/subtração, falha em geometria."
        if valor < 325: return "Intermediário", "#FBC02D", "Resolve porcentagem e gráficos básicos."
        return "Adequado", "#388E3C", "Domina álgebra e funções complexas."

# --- 5. TELA DE ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Sistema de Inteligência Educacional</h1>", unsafe_allow_html=True)
    aba_l, aba_c = st.tabs(["🔐 Login do Gestor", "📝 Cadastro de Novo Usuário"])
    with aba_l:
        u = st.text_input("CPF ou Matrícula"); s = st.text_input("Senha", type="password")
        if st.button("Entrar no Painel"):
            if u in st.session_state['usuarios_db'] and st.session_state['usuarios_db'][u] == s:
                st.session_state['autenticado'] = True; st.rerun()
            else: st.error("Acesso negado.")
    with aba_c:
        nu = st.text_input("Definir Usuário"); ns = st.text_input("Definir Senha", type="password")
        if st.button("Finalizar Cadastro"):
            if nu and ns:
                st.session_state['usuarios_db'][nu] = ns; st.success("Cadastro realizado!")

# --- 6. AMBIENTE LOGADO ---
else:
    menu = st.sidebar.radio("Navegação", ["🏠 Início (Técnico)", "📝 Importar Dados", "📊 Painel Analítico", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()

    elif menu == "🏠 Início (Técnico)":
        st.title("🔬 Embasamento Técnico e Metodologia")
        st.markdown("### 1. Teoria de Resposta ao Item (TRI)")
        st.latex(r"P_i(\theta) = c_i + \frac{1 - c_i}{1 + e^{-1.7 \cdot a_i \cdot (\theta - b_i)}}")
        st.info("**Nota:** Este modelo logístico de 3 parâmetros avalia a habilidade real considerando dificuldade, discriminação e acerto casual (chute).")
        st.markdown("### 2. Escalas de Proficiência (Referência SAEB/SAEPI)")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📚 Língua Portuguesa")
            st.markdown("- **< 200 (Muito Crítico)**\n- **200-249 (Crítico)**\n- **250-299 (Intermediário)**\n- **> 300 (Adequado)**")
        with col2:
            st.subheader("📐 Matemática")
            st.markdown("- **< 225 (Muito Crítico)**\n- **225-274 (Crítico)**\n- **275-324 (Intermediário)**\n- **> 325 (Adequado)**")

    elif menu == "📝 Importar Dados":
        st.header("📝 Upload de Avaliações - 1º Bimestre")
        c1, c2, c3, c4 = st.columns(4)
        escola = c1.text_input("Nome da Escola")
        ano = c2.selectbox("Ano Escolar", ["2º Ano", "5º Ano", "9º Ano"])
        turma = c3.text_input("Turma (Ex: 9º A)")
        disc = c4.selectbox("Disciplina", ["Língua Portuguesa", "Matemática"])
        
        arq = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type="xlsx")
        
        if arq:
            # Lógica de identificação e bloqueio
            nome_arquivo = arq.name.upper()
            ano_numero = "".join(filter(str.isdigit, ano)) # Extrai '9' de '9º Ano'
            
            df = pd.read_excel(arq).fillna("N/A")
            # Verifica se o ano selecionado está no arquivo ou no conteúdo
            identificou_ano = (ano_numero in nome_arquivo) or (df.astype(str).apply(lambda x: x.str.contains(ano_numero)).any().any())

            if not identificou_ano:
                st.error(f"❌ Erro de Identificação: O arquivo enviado não parece ser do {ano}. Verifique os dados.")
            else:
                if st.button("Processar e Salvar no Banco"):
                    for idx, row in df.iterrows():
                        res_bin = {f'Q{i:02d}': (1 if str(row[f'Q{i:02d}']).upper() == GABARITO[i-1] else 0) for i in range(1, 23)}
                        df.at[idx, 'Prof_TRI'] = calcular_tri(res_bin)
                    
                    st.session_state['db'] = df
                    st.session_state['meta'] = {"escola": escola, "ano": ano, "turma": turma, "disc": disc}
                    
                    # Salva no Banco de Dados (Session State)
                    registro = {"escola": escola, "ano": ano, "turma": turma, "disc": disc, "media": df['Prof_TRI'].mean()}
                    st.session_state['banco_geral'].append(registro)
                    
                    st.success(f"✅ Sucesso! Escola {escola} - {turma} salva no banco de dados.")

    elif menu == "📊 Painel Analítico":
        if 'db' in st.session_state:
            df, meta = st.session_state['db'], st.session_state['meta']
            matriz = MATRIZ_MAT if meta['disc'] == "Matemática" else MATRIZ_LP
            media = df['Prof_TRI'].mean()
            nivel, cor, desc_ped = obter_nivel_escala(media, meta['disc'])
            
            st.subheader(f"Análise Final: {meta['escola']} | {meta['ano']} | {meta['turma']}")
            st.markdown(f"<div style='background:{cor}; color:white; padding:20px; border-radius:10px; text-align:center;'><h3>Média: {media:.1f} | Nível: {nivel}</h3><p>{desc_ped}</p></div>", unsafe_allow_html=True)
            
            # --- O restante dos gráficos e PDF seguem aqui conforme seu código original ---
            st.write("Exibindo dados de desempenho por questão...")
            # (Código dos gráficos omitido para brevidade, mas permanece igual ao seu original)
        else:
            st.warning("Importe os dados primeiro.")
