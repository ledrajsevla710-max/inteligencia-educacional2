import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inteligência Educacional PI", page_icon="🎓", layout="wide")

# --- CONFIGURAÇÃO DE PESOS (A "ALMA" DA TRI SIMULADA) ---
# Aqui você define quais questões são fáceis, médias ou difíceis
def calcular_tri_simulada(respostas, pesos):
    pontos_obtidos = sum(r * p for r, p in zip(respostas, pesos))
    total_possivel = sum(pesos)
    
    # Cálculo base (0 a 1000)
    nota_bruta = (pontos_obtidos / total_possivel) * 1000
    
    # Penalidade por Incoerência (Simulação TRI)
    # Se o aluno acertar as difíceis (peso 3) mas errar as fáceis (peso 1)
    acertos_faceis = sum(respostas[:7]) # Supondo as 7 primeiras fáceis
    acertos_dificeis = sum(respostas[15:]) # Supondo as 7 últimas difíceis
    
    if acertos_dificeis > acertos_faceis:
        nota_bruta *= 0.9 # Penalidade de 10% por provável "chute"
        
    return min(nota_bruta, 1000)

# --- INTERFACE ---
st.title("📊 Painel de Monitoramento de Proficiência")

# Sidebar com Seleção de Disciplina e Série
st.sidebar.header("Configurações do Simulado")
disciplina = st.sidebar.selectbox("Selecione a Disciplina", ["Matemática", "Língua Portuguesa"])
serie = st.sidebar.selectbox("Selecione a Série", ["2º Ano", "5º Ano", "9º Ano"])

menu = st.sidebar.radio("Navegação", ["Calculadora Individual", "Upload de Planilha"])

if menu == "Calculadora Individual":
    st.subheader(f"Lançamento Individual: {disciplina} - {serie}")
    aluno = st.text_input("Nome do Aluno")
    
    st.write("Marque as questões que o aluno **ACERTOU**:")
    cols = st.columns(4)
    respostas = []
    for i in range(1, 23):
        with cols[(i-1)%4]:
            res = st.checkbox(f"Q{i:02d}", key=f"ind_{i}")
            respostas.append(1 if res else 0)
    
    if st.button("Calcular Proficiência"):
        # Definindo pesos (7 fáceis, 8 médias, 7 difíceis)
        pesos = [1]*7 + [2]*8 + [3]*7
        nota = calcular_tri_simulada(respostas, pesos)
        
        st.metric("Proficiência Estimada", f"{nota:.1f}")
        if nota < 250: st.error("Nível: Insuficiente")
        elif nota < 350: st.warning("Nível: Básico")
        else: st.success("Nível: Proficiente/Avançado")

elif menu == "Upload de Planilha":
    st.subheader(f"Processamento de Turma: {disciplina}")
    arquivo = st.file_uploader("Suba o arquivo Excel", type=["xlsx"])
    
    if arquivo:
        df = pd.read_excel(arquivo)
        pesos = [1]*7 + [2]*8 + [3]*7
        
        # Processando cada linha da planilha
        colunas_q = [f'Q{i:02d}' for i in range(1, 23)]
        df['Proficiência'] = df[colunas_q].apply(lambda x: calcular_tri_simulada(x.tolist(), pesos), axis=1)
        
        st.write("### Resultado da Turma")
        st.dataframe(df[['Nome do Aluno', 'Proficiência']].style.background_gradient(cmap='RdYlGn'))
