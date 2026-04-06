import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Inteligência Educacional PI", page_icon="🎓", layout="wide")

# --- MOTOR TRI AVANÇADO (MODELO DE 2 PARÂMETROS) ---
def calcular_score_tri(respostas, parametros_itens):
    """
    Calcula a proficiência usando o Modelo Logístico de 2 Parâmetros.
    Considera Discriminação (a) e Dificuldade (b).
    """
    if not any(respostas): return 0.0
    
    # Habilidade inicial (Theta)
    theta = 0.0 
    passo = 0.1
    
    # Iterações para encontrar o Theta mais provável (Máxima Verossimilhança Simplificada)
    for _ in range(25):
        p_acerto = []
        for i, res in enumerate(respostas):
            a = parametros_itens[i]['a']
            b = parametros_itens[i]['b']
            # Fórmula da TRI
            p = 1 / (1 + np.exp(-a * (theta - b)))
            p_acerto.append(p)
        
        # Ajuste do erro: diferença entre acerto real e probabilidade esperada
        erro = sum(respostas) - sum(p_acerto)
        theta += erro * passo
        
    # Conversão para Escala SAEB/SAEPI (Média 250, DP 50)
    # Alinhando para que 22 acertos fiquem próximos de 400-450 no 5º ano
    nota_final = (theta * 50) + 250
    return max(0, min(1000, nota_final))

# --- CONFIGURAÇÃO DOS ITENS (22 questões) ---
# Aqui simulamos a 'calibragem' dos itens
itens_config = []
for i in range(22):
    if i < 7: itens_config.append({'a': 1.2, 'b': -1.5}) # Fáceis
    elif i < 15: itens_config.append({'a': 1.5, 'b': 0.0}) # Médias
    else: itens_config.append({'a': 2.0, 'b': 1.8}) # Difíceis (Alta discriminação)

# --- INTERFACE ---
st.title("📊 Inteligência Educacional - Motor TRI v2.0")
st.sidebar.header("Menu de Navegação")
disciplina = st.sidebar.selectbox("Disciplina", ["Matemática", "Português"])
serie = st.sidebar.selectbox("Série", ["2º Ano", "5º Ano", "9º Ano"])
menu = st.sidebar.radio("Ir para:", ["Lançamento Individual", "Processar Planilha Excel"])

if menu == "Lançamento Individual":
    st.subheader(f"Análise Individual: {disciplina}")
    nome = st.text_input("Nome do Aluno")
    
    st.write("Marque as questões que o aluno **ACERTOU**:")
    cols = st.columns(4)
    respostas = []
    for i in range(1, 23):
        with cols[(i-1)%4]:
            res = st.checkbox(f"Q{i:02d}", key=f"q_{i}")
            respostas.append(1 if res else 0)
            
    if st.button("Calcular Proficiência TRI"):
        nota = calcular_score_tri(respostas, itens_config)
        st.metric("Proficiência Calculada", f"{nota:.1f}")
        
        if nota < 200: st.error("Nível: Abaixo do Básico")
        elif nota < 325: st.warning("Nível: Básico")
        else: st.success("Nível: Proficiente/Avançado")

elif menu == "Processar Planilha Excel":
    st.subheader("📂 Upload de Dados da Turma")
    arquivo = st.file_uploader("Selecione o Excel (.xlsx)", type=["xlsx"])
    
    if arquivo:
        try:
            df = pd.read_excel(arquivo)
            colunas_q = [f'Q{i:02d}' for i in range(1, 23)]
            
            if all(c in df.columns for c in colunas_q):
                # O ERRO ESTAVA AQUI: Agora chamando o nome correto da função
                df['Proficiência_TRI'] = df[colunas_q].apply(lambda x: calcular_score_tri(x.tolist(), itens_config), axis=1)
                
                st.success("✅ Processamento TRI concluído!")
                st.dataframe(df[['Nome', 'Proficiência_TRI']])
                
                # Resumo da Turma
                media_turma = df['Proficiência_TRI'].mean()
                st.info(f"Média de Proficiência da Turma: {media_turma:.1f}")
            else:
                st.error("Planilha fora do padrão. Verifique se as colunas são de Q01 a Q22.")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")
