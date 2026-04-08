import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

def aplicar_design():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stMetric { background-color: #ffffff; border-left: 5px solid #1E3A8A; padding: 15px; border-radius: 10px; }
        h1, h2, h3 { color: #1E3A8A; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. MOTORES TÉCNICOS ---
def calcular_tri(respostas_binarias):
    if not respostas_binarias: return 0
    num_q = len(respostas_binarias)
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas_binarias.items()):
        b = np.linspace(-2.5, 2.5, num_q)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel(valor, disciplina):
    d_upper = disciplina.upper()
    corte = 200 if "PORTUGUESA" in d_upper or "LÍNGUA" in d_upper else 225
    if valor < corte: return "Muito Crítico", "#D32F2F"
    if valor < corte + 50: return "Crítico", "#F57C00"
    if valor < corte + 100: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. ACESSO E MEMÓRIA ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'historico_geral' not in st.session_state:
    st.session_state['historico_geral'] = pd.DataFrame()

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal de Inteligência Educacional</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("Acessar Painel", use_container_width=True):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("Acesso Negado")
else:
    aplicar_design()
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📝 Importar Planilha", "📊 Painel Analítico", "🏢 Relatórios PDF", "🚪 Sair"])

    if menu == "🏠 Início":
        st.title("👋 Olá, Jardel!")
        st.markdown("### Gestão de Dados - Escola José Pacífico de Sousa")
        st.info("Importe as planilhas de Matemática e Português separadamente para ver o filtro no gráfico.")

    elif menu == "📝 Importar Planilha":
        st.header("📝 Carregar Planilha (.xlsx)")
        arq = st.file_uploader("Selecione o arquivo", type="xlsx")
        
        if arq:
            df_raw = pd.read_excel(arq, header=None)
            try:
                escola = str(df_raw.iloc[4, 9]).strip().upper() 
                disc = str(df_raw.iloc[6, 30]).strip().upper()
                turma = str(df_raw.iloc[7, 10]).strip().upper()
            except:
                escola, disc, turma = "ESCOLA MUNICIPAL", "GERAL", "A"

            idx_gab = df_raw[df_raw[0].astype(str).str.upper().str.contains("GABARITO", na=False)].index
            
            if not idx_gab.empty:
                linha_g = idx_gab[0]
                # Linha corrigida para não quebrar:
                letras_validas = ['A', 'B', 'C', 'D']
                gabarito = [str(x).strip().upper() for x in df_raw.iloc[linha_g, 2:45].tolist() 
                            if str(x).strip().upper() in letras_validas]
                
                num_q = len(gabarito)
                processados = []

                for i in range(linha_g + 1, len(df_raw)):
                    row = df_raw.iloc[i].tolist()
                    nome = str(row[1]).strip().upper()
                    if nome in ["NAN", "0", "1.0", ""] or "TOTAL" in nome or "OBSERV" in nome:
                        break
                    
                    res_aluno = [str(x).strip().upper() for x in row[2:45] 
                                 if str(x).strip().upper() in letras_validas or str(x).strip() == ""]
                    
                    res_bin = {f"Q{j+1:02d}": (1 if (j < len(res_aluno) and res_aluno[j] == gabarito[j]) else 0) 
                               for j in range(num_q)}
                    
                    prof = calcular_tri(res_bin)
                    nivel, cor = obter_nivel(prof, disc)
                    processados.append({"ALUNO": nome, "NOTA": prof, "NÍVEL": nivel, "DISCIPLINA": disc, "ESCOLA": escola, "TUR
                
