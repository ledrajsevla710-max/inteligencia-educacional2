import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inteligência Educacional PI", page_icon="🎓", layout="wide")

st.title("📊 Sistema de Proficiência SAEPI/SAEB")
st.markdown("---")

# Menu Lateral
st.sidebar.header("Painel de Controle")
opcao = st.sidebar.radio("Escolha a função:", ["Lançamento Individual", "Upload de Planilha (Lote)", "Relatórios"])

if opcao == "Lançamento Individual":
    st.subheader("📝 Cadastro de Desempenho por Aluno")
    
    col_inf1, col_inf2, col_inf3 = st.columns(3)
    with col_inf1:
        aluno = st.text_input("Nome Completo do Aluno")
    with col_inf2:
        serie = st.selectbox("Série", ["2º Ano", "5º Ano", "9º Ano"])
    with col_inf3:
        materia = "Matemática" # Fixo conforme seu foco

    st.write("---")
    st.write(f"**Marque os acertos do aluno nas 22 questões de {materia}:**")
    
    # Criar 22 checkboxes divididos em colunas para não ficar gigante
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    respostas = []
    
    for i in range(1, 23):
        if i <= 6: col = col_q1
        elif i <= 12: col = col_q2
        elif i <= 17: col = col_q3
        else: col = col_q4
        
        with col:
            check = st.checkbox(f"Questão {i:02d}", key=f"q{i}")
            respostas.append(1 if check else 0)

    if st.button("Gerar Diagnóstico"):
        # Lógica de pesos simulada (depois você ajusta por descritor)
        pesos = [1]*10 + [2]*7 + [3]*5 # 10 fáceis, 7 médias, 5 difíceis
        nota = (sum(r * p for r, p in zip(respostas, pesos)) / sum(pesos)) * 1000
        
        st.metric(label="Nota de Proficiência Estimada", value=f"{nota:.1f}")
        
        if nota < 250: st.error("Nível: **INSUFICIENTE**")
        elif nota < 325: st.warning("Nível: **BÁSICO**")
        elif nota < 400: st.success("Nível: **PROFICIENTE**")
        else: st.info("Nível: **AVANÇADO**")

elif opcao == "Upload de Planilha (Lote)":
    st.subheader("📂 Processamento em Massa (Excel)")
    st.write("Suba aqui a planilha preenchida pelos professores para calcular a proficiência de toda a turma de uma vez.")
    
    arquivo = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])
    
    if arquivo:
        df = pd.read_excel(arquivo)
        st.write("Visualização dos dados carregados:")
        st.dataframe(df.head())
        st.success("Dados prontos para processamento! (Lógica de cálculo vinculada aos seus descritores).")

else:
    st.subheader("📈 Relatórios de Gestão")
    st.info("Aqui serão gerados os gráficos por descritor (Ex: 40% da turma errou o Descritor D12).")
