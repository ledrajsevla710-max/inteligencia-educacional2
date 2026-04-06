import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inteligência Educacional PI", page_icon="🎓", layout="wide")

# --- FUNÇÃO DE CÁLCULO (TRI SIMULADA) ---
def calcular_tri_simulada(respostas, pesos):
    if not respostas: return 0
    pontos_obtidos = sum(r * p for r, p in zip(respostas, pesos))
    total_possivel = sum(pesos)
    nota_bruta = (pontos_obtidos / total_possivel) * 1000
    
    # Lógica de Coerência (TRI)
    # Se acertar mais de 70% das difíceis e menos de 40% das fáceis = Provável Chute
    faceis = respostas[:7]
    dificeis = respostas[15:]
    if sum(dificeis) > sum(faceis) and sum(faceis) < 3:
        nota_bruta *= 0.85 # Penalidade por incoerência
        
    return min(nota_bruta, 1000)

# --- INTERFACE ---
st.title("📊 Painel de Monitoramento de Proficiência")

# Sidebar
st.sidebar.header("Configurações")
disciplina = st.sidebar.selectbox("Disciplina", ["Matemática", "Língua Portuguesa"])
serie = st.sidebar.selectbox("Série", ["2º Ano", "5º Ano", "9º Ano"])
menu = st.sidebar.radio("Navegação", ["Calculadora Individual", "Upload de Planilha (Lote)"])

pesos_padrao = [1]*7 + [2]*8 + [3]*7 # 22 questões

if menu == "Calculadora Individual":
    st.subheader(f"Lançamento: {disciplina} - {serie}")
    aluno = st.text_input("Nome do Aluno")
    
    st.write("Marque apenas as questões que o aluno **ACERTOU**:")
    cols = st.columns(4)
    respostas = []
    for i in range(1, 23):
        with cols[(i-1)%4]:
            res = st.checkbox(f"Q{i:02d}")
            respostas.append(1 if res else 0)
    
    if st.button("Calcular Nota"):
        nota = calcular_tri_simulada(respostas, pesos_padrao)
        st.metric("Proficiência", f"{nota:.1f}")
        if nota < 250: st.error("Nível: Insuficiente")
        elif nota < 350: st.warning("Nível: Básico")
        else: st.success("Nível: Proficiente/Avançado")

elif menu == "Upload de Planilha (Lote)":
    st.subheader("📂 Processamento por Planilha")
    st.info("Sua planilha deve ter as colunas: 'Nome' e de 'Q01' até 'Q22'.")
    
    arquivo = st.file_uploader("Suba o arquivo Excel (.xlsx)", type=["xlsx"])
    
    if arquivo:
        try:
            df = pd.read_excel(arquivo)
            # Padroniza nomes de colunas para evitar erros
            colunas_q = [f'Q{i:02d}' for i in range(1, 23)]
            
            # Verifica se as colunas existem
            if all(c in df.columns for c in colunas_q):
                df['Proficiência'] = df[colunas_q].apply(lambda x: calcular_tri_simulada(x.tolist(), pesos_padrao), axis=1)
                st.success("✅ Processado com sucesso!")
                st.dataframe(df[['Nome', 'Proficiência']].style.background_gradient(cmap='RdYlGn'))
            else:
                st.error("❌ Erro: As colunas de Q01 a Q22 não foram encontradas na sua planilha.")
                st.write("Colunas encontradas no seu arquivo:", list(df.columns))
        except Exception as e:
            st.error(f"Erro na leitura: {e}")
