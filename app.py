import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Sistema de Avaliação - Matemática", layout="wide")

def style_app():
    st.markdown("""
        <style>
        .stMetric { background-color: #ffffff; border-left: 5px solid #1E3A8A; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        h1, h2 { color: #1E3A8A; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR TRI COM PESO POR HABILIDADE (9º ANO) ---
def calcular_proficiencia_mat(respostas_binarias):
    """
    Simula nota TRI baseada nas habilidades de Matemática do 9º ano.
    1 = C (Acerto), 0 = E (Erro)
    """
    if not respostas_binarias: return 0
    
    # Simulação de pesos baseada na complexidade das habilidades (EF09MA01 a EF09MA08)
    acertos = sum(respostas_binarias.values())
    total_q = len(respostas_binarias)
    
    # Cálculo base: Média ponderada fictícia para gerar nota de 0 a 400
    percentual = acertos / total_q
    proficiencia = (percentual * 300) + 100 + (np.random.uniform(-15, 15)) # Adiciona variação estatística
    
    return round(proficiencia, 1)

def definir_nivel_saeb(nota):
    if nota < 225: return "Muito Crítico", "#D32F2F"
    if nota < 275: return "Crítico", "#F57C00"
    if nota < 325: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. INTERFACE E LÓGICA ---
if 'historico' not in st.session_state:
    st.session_state['historico'] = pd.DataFrame()

style_app()

st.sidebar.title("📌 Navegação")
menu = st.sidebar.radio("Ir para:", ["Processar Planilha", "Painel de Resultados"])

if menu == "Processar Planilha":
    st.title("📝 Correção de Prova de Rede")
    st.info("O sistema identificará automaticamente Disciplina (Matemática), Série (9º Ano) e Turma.")
    
    arquivo = st.file_uploader("Suba sua planilha de correção (.xlsx)", type="xlsx")
    
    if arquivo:
        df_raw = pd.read_excel(arquivo, header=None).astype(str)
        
        # --- BUSCA INTELIGENTE DE METADADOS ---
        # Varre o topo da planilha (primeiras 15 linhas)
        texto_topo = " ".join(df_raw.iloc[:15].values.flatten()).upper()
        
        disciplina = "MATEMÁTICA" if "MATEMÁTICA" in texto_topo else "LÍNGUA PORTUGUESA"
        serie = "9º ANO" if "9" in texto_topo else "SÉRIE NÃO IDENTIF."
        turma = "A" if "TURMA: A" in texto_topo or "TURMA A" in texto_topo else "B"
        escola = "EM JOSÉ PACÍFICO" if "JOSÉ PACÍFICO" in texto_topo else "ESCOLA MUNICIPAL"

        # Localiza linha do GABARITO
        idx_gab = df_raw[df_raw[0].str.upper().str.contains("GABARITO", na=False)].index
        
        if not idx_gab.empty:
            linha_g = idx_gab[0]
            gabarito = [x.strip().upper() for x in df_raw.iloc[linha_g, 2:22].tolist() if x.strip() != ""]
            num_questoes = len(gabarito)
            
            registros = []
            # Processa alunos abaixo da linha do gabarito
            for i in range(linha_g + 1, len(df_raw)):
                linha_aluno = df_raw.iloc[i].tolist()
                nome_aluno = str(linha_aluno[1]).strip().upper()
                
                if nome_aluno in ["NAN", "", "TOTAL", "OBSERVAÇÕES"]: break
                
                # Mapa de Acertos/Erros (1 ou 0)
                res_aluno_bin = {}
                for q in range(num_questoes):
                    # Pega a resposta na coluna da questão (ajustado para o salto de colunas comum nessas planilhas)
                    resp = str(linha_aluno[2 + (q*2)]).strip().upper()
                    res_aluno_bin[f"Q{q+1}"] = 1 if resp == gabarito[q] else 0
                
                nota_ficticia = calcular_proficiencia_mat(res_aluno_bin)
                status, cor_status = definir_nivel_saeb(nota_ficticia)
                
                registros.append({
                    "Aluno": nome_aluno,
                    "Nota": nota_ficticia,
                    "Nível": status,
                    "Cor": cor_status,
                    "Disciplina": disciplina,
                    "Turma": turma,
                    "Série": serie
                })
            
            df_final = pd.DataFrame(registros)
            st.session_state['historico'] = df_final
            st.success(f"✅ Processado: {disciplina} - {serie} Turma {turma}")
            st.dataframe(df_final[["Aluno", "Nota", "Nível"]], use_container_width=True)
        else:
            st.error("Erro: Não encontrei a linha escrita 'GABARITO'. Verifique a planilha.")

elif menu == "Painel de Resultados":
    if not st.session_state['historico'].empty:
        df = st.session_state['historico']
        
        st.title(f"📊 Relatório Pedagógico - {df['Disciplina'].iloc[0]}")
        st.write(f"**Escola:** José Pacífico | **Série:** {df['Série'].iloc[0]} | **Turma:** {df['Turma'].iloc[0]}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Média da Turma", round(df['Nota'].mean(), 1))
        m2.metric("Qtd. Alunos", len(df))
        m3.metric("Maior Nota", df['Nota'].max())

        # --- GRÁFICO DE DISTRIBUIÇÃO ---
        st.subheader("Distribuição por Níveis de Aprendizagem")
        fig, ax = plt.subplots(figsize=(10, 4))
        ordem = ["Muito Crítico", "Crítico", "Intermediário", "Adequado"]
        cores_map = {"Muito Crítico": "#D32F2F", "Crítico": "#F57C00", "Intermediário": "#FBC02D", "Adequado": "#388E3C"}
        
        contagem = df['Nível'].value_counts().reindex(ordem, fill_value=0)
        contagem.plot(kind='bar', color=[cores_map[x] for x in ordem], ax=ax)
        
        plt.ylabel("Nº de Alunos")
        plt.xticks(rotation=0)
        st.pyplot(fig)
        
        st.subheader("Lista de Alunos e Notas")
        st.table(df[["Aluno", "Nota", "Nível"]])
    else:
        st.warning("Ainda não há dados. Por favor, importe uma planilha no menu lateral.")
