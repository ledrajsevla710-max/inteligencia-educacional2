import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Inteligência Educacional PI", page_icon="🎓", layout="wide")

# --- MOTOR TRI AVANÇADO ---
def calcular_score_tri(respostas, parametros_itens):
    """
    Simulação do Modelo de 2 Parâmetros (2PL)
    parametros_itens: lista de dicionários [{'a': discr, 'b': dific}]
    """
    if not any(respostas): return 0.0
    
    # Habilidade inicial estimada (Theta)
    theta = 0.0 
    passo = 0.1
    
    # Ajuste de Theta por Verossimilhança simplificada
    for _ in range(20): # Iterações para encontrar a nota ideal
        probabilidades = []
        for i, res in enumerate(respostas):
            a = parametros_itens[i]['a']
            b = parametros_itens[i]['b']
            # Função Logística da TRI: P(theta) = 1 / (1 + e^[-a(theta - b)])
            p = 1 / (1 + np.exp(-a * (theta - b)))
            probabilidades.append(p)
        
        # Ajusta theta com base nos acertos reais vs esperados
        erro = sum(respostas) - sum(probabilidades)
        theta += erro * passo
        
    # Converte Theta (escala -3 a 3) para Escala SAEB (0 a 1000)
    # Média 250, Desvio Padrão 50 (ajustável para sua rede)
    nota_saepi = (theta * 50) + 250
    
    # Trava os limites
    return max(0, min(1000, nota_saepi))

# --- CONFIGURAÇÃO DOS ITENS (22 questões) ---
# 'a' = Discriminação (1.0 a 2.0) | 'b' = Dificuldade (-2.0 fácil a 2.0 difícil)
itens_mat = []
for i in range(22):
    if i < 7: itens_mat.append({'a': 1.2, 'b': -1.5}) # Fáceis
    elif i < 15: itens_mat.append({'a': 1.5, 'b': 0.0}) # Médias
    else: itens_mat.append({'a': 1.8, 'b': 1.8}) # Difíceis

# --- INTERFACE STREAMLIT ---
st.title("📊 Sistema Avançado de Inteligência Educacional (Modelo TRI-2PL)")
st.sidebar.header("Parâmetros do Sistema")
disciplina = st.sidebar.selectbox("Disciplina", ["Matemática", "Português"])
menu = st.sidebar.radio("Navegação", ["Lançamento Individual", "Upload de Planilha"])

if menu == "Lançamento Individual":
    aluno = st.text_input("Nome do Aluno")
    cols = st.columns(4)
    respostas = []
    for i in range(1, 23):
        with cols[(i-1)%4]:
            res = st.checkbox(f"Q{i:02d}")
            respostas.append(1 if res else 0)
            
    if st.button("Calcular Proficiência Real"):
        nota = calcular_score_tri(respostas, itens_mat)
        st.metric("Nota TRI Final", f"{nota:.1f}")
        
        # Feedback Pedagógico
        if nota < 200: st.error("Nível: Abaixo do Básico")
        elif nota < 300: st.warning("Nível: Básico")
        else: st.success("Nível: Proficiente/Avançado")

elif menu == "Upload de Planilha":
    arquivo = st.file_uploader("Suba o Excel", type=["xlsx"])
    if arquivo:
        df = pd.read_excel(arquivo)
        colunas_q = [f'Q{i:02d}' for i in range(1, 23)]
        
        if all(c in df.columns for c in colunas_q):
            df['Proficiência_TRI'] = df[colunas_q].apply(lambda x: calcular_tri_simulada(x.tolist(), itens_mat), axis=1)
            st.dataframe(df[['Nome', 'Proficiência_TRI']])
