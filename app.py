import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Inteligência Educacional", layout="wide")

# --- 2. MOTOR DE CÁLCULO (TRI) ---
def calcular_tri(respostas_binarias):
    if not respostas_binarias: return 0
    num_q = len(respostas_binarias)
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas_binarias.items()):
        # Se for 1 (Acerto), usa probabilidade de acerto. Se for 0 (Erro), o inverso.
        b = np.linspace(-2, 2, num_q)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel(valor, disciplina):
    corte = 200 if "PORTUGUESA" in disciplina.upper() else 225
    if valor < corte: return "Muito Crítico", "#D32F2F"
    if valor < corte + 50: return "Crítico", "#F57C00"
    if valor < corte + 100: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'historico' not in st.session_state:
    st.session_state['historico'] = pd.DataFrame()

if not st.session_state['autenticado']:
    st.title("🏛️ Portal de Inteligência Educacional")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "12345" and s == "000":
            st.session_state['autenticado'] = True
            st.rerun()
else:
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📝 Importar", "📊 Painel", "🏢 Relatórios", "🚪 Sair"])

    if menu == "🏠 Início":
        st.title(f"👋 Olá, Jardel!")
        st.write("Sistema pronto para processar as planilhas da Escola José Pacífico.")

    elif menu == "📝 Importar":
        st.header("📝 Carregar Planilha")
        arq = st.file_uploader("Selecione o arquivo Excel", type="xlsx")
        
        if arq:
            df_raw = pd.read_excel(arq, header=None).astype(str)
            
            # Tenta capturar disciplina e turma buscando no texto
            conteudo_total = " ".join(df_raw.iloc[:10].values.flatten()).upper()
            
            disc = "MATEMÁTICA" if "MATEMÁTICA" in conteudo_total else "LÍNGUA PORTUGUESA"
            turma = "A" if "TURMA: A" in conteudo_total else "B"
            escola = "JOSÉ PACÍFICO"

            # Localiza o Gabarito
            idx_gab = df_raw[df_raw[0].str.upper().str.contains("GABARITO", na=False)].index
            
            if not idx_gab.empty:
                linha_g = idx_gab[0]
                # Pega as letras do gabarito (Colunas C em diante)
                gabarito = [x.strip().upper() for x in df_raw.iloc[linha_g, 2:45].tolist() if x.strip().upper() in ['A','B','C','D']]
                num_q = len(gabarito)
                
                processados = []
                # Percorre alunos abaixo do gabarito
                for i in range(linha_g + 1, len(df_raw)):
                    row = df_raw.iloc[i].tolist()
                    nome = row[1].strip().upper()
                    if nome in ["NAN", "", "TOTAL", "OBSERVAÇÕES"]: break
                    
                    # Lógica de correção: 1 se bater com gabarito, 0 se não.
                    res_binaria = {}
                    for j in range(num_q):
                        resp_aluno = row[2 + (j*2)].strip().upper() if (2 + (j*2)) < len(row) else ""
                        res_binaria[f"Q{j+1}"] = 1 if resp_aluno == gabarito[j] else 0
                    
                    prof = calcular_tri(res_binaria)
                    nivel, cor = obter_nivel(prof, disc)
                    
                    processados.append({
                        "ALUNO": nome, "NOTA": round(prof, 1), 
                        "NÍVEL": nivel, "COR": cor, "DISCIPLINA": disc, "TURMA": turma
                    })

                df_novo = pd.DataFrame(processados)
                st.session_state['historico'] = pd.concat([st.session_state['historico'], df_novo]).drop_duplicates(subset=['ALUNO', 'DISCIPLINA'])
                st.success(f"✅ {disc} - Turma {turma} importada!")

    elif menu == "📊 Painel":
        if not st.session_state['historico'].empty:
            df_h = st.session_state['historico']
            escolha = st.sidebar.selectbox("Filtrar Matéria", df_h['DISCIPLINA'].unique())
            df = df_h[df_h['DISCIPLINA'] == escolha]
            
            st.title(f"📊 Desempenho: {escolha}")
            col1, col2 = st.columns(2)
            col1.metric("Média da Turma", round(df['NOTA'].mean(), 1))
            col2.metric("Total Alunos", len(df))

            # --- GRÁFICO DE BARRAS ---
            st.subheader("Distribuição por Níveis")
            fig, ax = plt.subplots(figsize=(10, 4))
            ordem = ["Muito Crítico", "Crítico", "Intermediário", "Adequado"]
            cores = ["#D32F2F", "#F57C00", "#FBC02D", "#388E3C"]
            contagem = df['NÍVEL'].value_counts().reindex(ordem, fill_value=0)
            contagem.plot(kind='bar', color=cores, ax=ax)
            plt.xticks(rotation=0)
            st.pyplot(fig)

            st.table(df[['ALUNO', 'NOTA', 'NÍVEL']])
        else:
            st.warning("Importe dados primeiro.")

    elif menu == "🏢 Relatórios":
        if not st.session_state['historico'].empty:
            # Botão de download simples do que está na tela
            csv = st.session_state['historico'].to_csv(index=False).encode('utf-8')
            st.download_button("Baixar Planilha Consolidada (CSV)", csv, "resultado.csv")
            
    elif menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()
