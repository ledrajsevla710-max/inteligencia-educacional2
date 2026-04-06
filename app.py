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
    
    arquivo = st.file_uploader("Suba a planilha preenchida", type=["xlsx"])
    
    if arquivo:
        # Lendo a planilha
        df = pd.read_excel(arquivo)
        
        # Definindo os pesos das 22 questões (Exemplo: as últimas 5 são difíceis)
        pesos = [1]*10 + [2]*7 + [3]*5 
        soma_pesos = sum(pesos)
        
        # Criando a coluna de questões para o cálculo (Q01 até Q22)
        colunas_questoes = [f'Q{i:02d}' for i in range(1, 23)]
        
        # Função para calcular a nota de cada linha (aluno)
        def calcular_nota(linha):
            pontos = sum(linha[colunas_questoes] * pesos)
            return (pontos / soma_pesos) * 1000

        # Aplicando o cálculo em toda a planilha
        df['Proficiência'] = df.apply(calcular_nota, axis=1)
        
        # Classificando os níveis
        def classificar(nota):
            if nota < 250: return "Insuficiente"
            elif nota < 325: return "Básico"
            elif nota < 400: return "Proficiente"
            else: return "Avançado"
            
        df['Nível'] = df['Proficiência'].apply(classificar)
        
        # Exibindo o resultado final
        st.write("### Resultado Processado")
        st.dataframe(df[['Nome do Aluno', 'Série', 'Proficiência', 'Nível']])
        
        # Botão para baixar a planilha pronta
        st.download_button(
            label="Baixar Resultados em Excel",
            data=arquivo, # Aqui você pode converter o DF de volta para excel se desejar
            file_name="resultados_saepi.xlsx"
        )

else:
    st.subheader("📈 Relatórios de Gestão")
    st.info("Aqui serão gerados os gráficos por descritor (Ex: 40% da turma errou o Descritor D12).")
