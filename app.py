import streamlit as st

# Configuração da página
st.set_page_config(page_title="Inteligência Educacional PI", page_icon="🎓")

st.title("📊 Simulador de Proficiência SAEPI")
st.markdown("---")

# Barra lateral para informações
st.sidebar.header("Configurações da Avaliação")
serie = st.sidebar.selectbox("Selecione a Série", [2, 5, 9])
disciplina = st.sidebar.selectbox("Disciplina", ["Matemática", "Português"])

# Área de entrada de dados
st.subheader(f"Lançamento de Notas - {serie}º Ano ({disciplina})")
aluno = st.text_input("Nome do Aluno")

# Simulação de 10 questões para o exemplo (você pode aumentar para 22)
col1, col2 = st.columns(2)
respostas = []

with col1:
    for i in range(1, 6):
        res = st.radio(f"Questão {i}", ["Acerto", "Erro"], horizontal=True)
        respostas.append(1 if res == "Acerto" else 0)

with col2:
    for i in range(6, 11):
        res = st.radio(f"Questão {i}", ["Acerto", "Erro"], horizontal=True)
        respostas.append(1 if res == "Acerto" else 0)

# Botão de Calcular
if st.button("Gerar Diagnóstico de Proficiência"):
    # Lógica simples de peso (Fáceis 1-5, Difíceis 6-10)
    pesos = [1, 1, 1, 1, 1, 3, 3, 3, 3, 3]
    nota = (sum(r * p for r, p in zip(respostas, pesos)) / sum(pesos)) * 1000
    
    # Exibição do Resultado
    st.metric(label="Nota Estimada SAEPI", value=f"{nota:.1f}")
    
    if nota < 250:
        st.error(f"Nível: **INSUFICIENTE** (Aluno: {aluno})")
    elif nota < 325:
        st.warning(f"Nível: **BÁSICO** (Aluno: {aluno})")
    else:
        st.success(f"Nível: **PROFICIENTE/AVANÇADO** (Aluno: {aluno})")
