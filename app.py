import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Sistema de Inteligência Educacional", layout="wide", page_icon="📊")

# --- 2. BANCO DE USUÁRIOS (SESSÃO) ---
# Simulando um banco de dados simples que persiste enquanto o app está aberto
if 'usuarios_db' not in st.session_state:
    st.session_state['usuarios_db'] = {"12345": "000"} # Usuário padrão

# --- 3. MATRIZES E DEFINIÇÕES PEDAGÓGICAS ---
MATRIZ_LP = {
    "Q01": "D1 - Localizar informações explícitas.", "Q02": "D3 - Inferir o sentido de palavra/expression.",
    "Q03": "D4 - Inferir informação implícita.", "Q04": "D6 - Identificar o tema do texto.",
    "Q05": "D14 - Distinguir fato de opinião.", "Q06": "D12 - Identificar finalidade do texto.",
    "Q07": "D2 - Estabelecer relações entre partes do texto.", "Q08": "D5 - Interpretar texto com auxílio de imagem.",
    "Q09": "D7 - Identificar a tese do texto.", "Q10": "D8 - Estabelecer relação tese/argumentos.",
    "Q11": "D9 - Diferenciar partes principais/secundárias.", "Q12": "D10 - Identificar o conflito do enredo.",
    "Q13": "D11 - Estabelecer relação causa/consequência.", "Q14": "D13 - Identificar marcas linguísticas (locutor).",
    "Q15": "D15 - Estabelecer relações lógico-discursivas.", "Q16": "D16 - Identificar efeitos de ironia/humor.",
    "Q17": "D17 - Identificar efeito de pontuação.", "Q18": "D18 - Efeito de sentido (escolha de palavras).",
    "Q19": "D19 - Efeito de sentido (recursos gráficos).", "Q20": "D20 - Diferentes formas de tratar o tema.",
    "Q21": "D21 - Reconhecer posições distintas entre textos.", "Q22": "D22 - Identificar recursos ortográficos/estilísticos."
}

MATRIZ_MAT = {
    "Q01": "D1 - Identificar figuras bidimensionais.", "Q02": "D2 - Reconhecer propriedades de polígonos.",
    "Q03": "D3 - Identificar relações entre figuras espaciais.", "Q04": "D4 - Identificar polígonos regulares.",
    "Q05": "D5 - Reconhecer conservação de perímetro/área.", "Q06": "D6 - Reconhecer ângulos como mudança de direção.",
    "Q07": "D12 - Resolver problemas com medidas de grandeza.", "Q08": "D13 - Calcular área de figuras planas.",
    "Q09": "D14 - Resolver problema com noções de volume.", "Q10": "D16 - Identificar localização em mapas/malhas.",
    "Q11": "D17 - Identificar coordenadas no plano cartesiano.", "Q12": "D18 - Reconecedor expressão algébrica.",
    "Q13": "D19 - Resolver problema com inequações de 1º grau.", "Q14": "D20 - Analisar crescimento/decrescimento de função.",
    "Q15": "D21 - Resolver sistema de equações de 1º grau.", "Q16": "D22 - Identificar gráfico de funções de 1º grau.",
    "Q17": "D23 - Resolver problemas com porcentagem.", "Q18": "D24 - Resolver problemas com juros simples.",
    "Q19": "D25 - Resolver problemas com grandezas proporcionais.", "Q20": "D26 - Associar informações de tabelas/gráficos.",
    "Q21": "D27 - Calcular média aritmética de dados.", "Q22": "D28 - Resolver problema com probabilidade simples."
}

GABARITO = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']

def obter_nivel_escala(valor, disciplina):
    if disciplina == "Língua Portuguesa":
        if valor < 200: return "Muito Crítico", "#D32F2F"
        if valor < 250: return "Crítico", "#F57C00"
        if valor < 300: return "Intermediário", "#FBC02D"
        return "Adequado", "#388E3C"
    else:
        if valor < 225: return "Muito Crítico", "#D32F2F"
        if valor < 275: return "Crítico", "#F57C00"
        if valor < 325: return "Intermediário", "#FBC02D"
        return "Adequado", "#388E3C"

def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        b = np.linspace(-2.5, 2.5, 22)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    theta_final = thetas[np.argmax(verossimilhanca)]
    return (theta_final + 4) * 50

# --- 4. TELA DE ACESSO (LOGIN, CADASTRO E PRIVACIDADE) ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Inteligência Educacional</h1>", unsafe_allow_html=True)
    
    aba_login, aba_cadastro = st.tabs(["🔐 Acessar Sistema", "📝 Criar Nova Conta"])
    
    with aba_login:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.container(border=True):
                u = st.text_input("Usuário (CPF ou E-mail)")
                s = st.text_input("Senha de Acesso", type="password")
                
                st.markdown("---")
                st.caption("🛡️ **Política de Privacidade:** Ao entrar, você concorda que o processamento dos dados educacionais inseridos é de responsabilidade do operador e destina-se exclusivamente a fins pedagógicos, em conformidade com a LGPD.")
                
                if st.button("Entrar no Painel", use_container_width=True):
                    if u in st.session_state['usuarios_db'] and st.session_state['usuarios_db'][u] == s:
                        st.session_state['autenticado'] = True
                        st.session_state['usuario_nome'] = u
                        st.rerun()
                    else: st.error("Usuário ou senha incorretos.")

    with aba_cadastro:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.container(border=True):
                st.subheader("Cadastro de Gestor")
                novo_u = st.text_input("Defina seu Usuário")
                nova_s = st.text_input("Defina sua Senha", type="password")
                conf_s = st.text_input("Confirme a Senha", type="password")
                
                concorda = st.checkbox("Li e aceito os termos de privacidade e uso de dados.")
                
                if st.button("Finalizar Cadastro", use_container_width=True):
                    if novo_u == "" or nova_s == "":
                        st.warning("Preencha todos os campos.")
                    elif nova_s != conf_s:
                        st.error("As senhas não coincidem.")
                    elif not concorda:
                        st.error("Você precisa aceitar os termos de privacidade.")
                    else:
                        st.session_state['usuarios_db'][novo_u] = nova_s
                        st.success("✅ Conta criada! Volte na aba 'Acessar Sistema' para entrar.")

# --- 5. SISTEMA PÓS-LOGIN ---
else:
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "📝 Importar Dados", "📊 Painel Analítico", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "🏠 Início":
        st.title(f"👋 Bem-vindo ao Sistema!")
        
        st.markdown("### 📊 Escalas de Proficiência (Referência SAEB)")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**Língua Portuguesa**")
            st.write("🔴 < 200: Muito Crítico | 🟠 < 250: Crítico | 🟡 < 300: Intermediário | 🟢 > 300: Adequado", unsafe_allow_html=True)
        with c2:
            st.success("**Matemática**")
            st.write("🔴 < 225
