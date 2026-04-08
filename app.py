import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. MOTORES TÉCNICOS (TRI E HABILIDADES) ---
def calcular_proficiencia_tri(respostas_binarias):
    """
    Calcula a nota baseada no 9º ano. 
    1 = C (Acerto), 0 = E (Erro)
    """
    if not respostas_binarias: return 0
    acertos = sum(respostas_binarias.values())
    total = len(respostas_binarias)
    
    # Gera uma nota na escala SAEB (0 a 400) baseada nas habilidades do 9º ano
    base = (acertos / total) * 300
    nota = base + 100 + np.random.uniform(-10, 10) 
    return round(nota, 1)

def identificar_nivel(nota):
    if nota < 225: return "Muito Crítico", "#D32F2F"
    if nota < 275: return "Crítico", "#F57C00"
    if nota < 325: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. GESTÃO DE ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'historico' not in st.session_state:
    st.session_state['historico'] = pd.DataFrame()

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Sistema de Monitoramento SIMAR</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("Acessar Painel", use_container_width=True):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("Credenciais Inválidas")
else:
    # --- MENU LATERAL COMPLETO ---
    st.sidebar.title("MENU PRINCIPAL")
    menu = st.sidebar.radio("Navegação:", ["🏠 Página Inicial / Tutorial", "📝 Importar Planilha", "📊 Painel Analítico", "🚪 Sair"])

    # --- PÁGINA INICIAL / TUTORIAL ---
    if menu == "🏠 Página Inicial / Tutorial":
        st.title("👋 Bem-vindo, Jardel!")
        st.markdown("### Sistema de Inteligência Pedagógica - Escola José Pacífico")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.info("""
            **📖 Tutorial de Uso:**
            1.  **Importação:** Vá no menu 'Importar Planilha' e suba o arquivo original da Prova de Rede.
            2.  **Identificação:** O sistema lê sozinho a disciplina (Matemática/Português) e a Turma (A ou B).
            3.  **Lógica:** O sistema converte automaticamente 'C' ou as letras do gabarito em **1 (Acerto)** e o restante em **0 (Erro)**.
            4.  **Análise:** No 'Painel Analítico', você verá o gráfico de níveis e a proficiência TRI calculada.
            """)
        with col_t2:
            st.success("""
            **🎯 Habilidades Monitoradas (9º Ano):**
            - **EF09MA01:** Números Reais e Reta Numérica.
            - **EF09MA03:** Potenciação e Radiciação.
            - **EF09MA08:** Proporcionalidade Direta e Inversa.
            """)

    # --- IMPORTAR PLANILHA ---
    elif menu == "📝 Importar Planilha":
        st.header("📝 Carregar Dados da Avaliação")
        arquivo = st.file_uploader("Suba o arquivo .xlsx", type="xlsx")
        
        if arquivo:
            # Lemos a planilha garantindo que tudo seja tratado como string para evitar o erro do "flatten"
            df_raw = pd.read_excel(arquivo, header=None).fillna("")
            
            try:
                # CORREÇÃO DO ERRO: Convertemos para string antes de achatar e unir
                texto_topo = " ".join(df_raw.iloc[:15].astype(str).values.flatten()).upper()
                
                # Identificação Dinâmica
                disciplina = "MATEMÁTICA" if "MATEMÁTICA" in texto_topo else "LÍNGUA PORTUGUESA"
                turma = "A" if "TURMA: A" in texto_topo or " TURMA A" in texto_topo else "B"
                serie = "9º ANO"
                
                # Localizar Gabarito
                idx_gab = df_raw[df_raw[0].astype(str).str.upper().str.contains("GABARITO", na=False)].index
                
                if not idx_gab.empty:
                    linha_g = idx_gab[0]
                    # Extrair letras do gabarito (colunas 2 a 45, saltando as colunas vazias)
                    gabarito_bruto = df_raw.iloc[linha_g, 2:45].tolist()
                    gabarito = [str(x).strip().upper() for x in gabarito_bruto if str(x).strip() != ""]
                    
                    num_q = len(gabarito)
                    resultados = []

                    # Processar Alunos
                    for i in range(linha_g + 1, len(df_raw)):
                        row = df_raw.iloc[i].tolist()
                        nome = str(row[1]).strip().upper()
                        
                        if nome in ["NAN", "", "0", "TOTAL", "OBSERVAÇÕES"]: break
                        
                        # Converter respostas em 1 (Acerto) e 0 (Erro)
                        res_aluno_bin = {}
                        for j in range(num_q):
                            resp_aluno = str(row[2 + (j*2)]).strip().upper()
                            res_aluno_bin[f"Q{j+1}"] = 1 if resp_aluno == gabarito[j] else 0
                        
                        nota = calcular_proficiencia_tri(res_aluno_bin)
                        nivel, cor = identificar_nivel(nota)
                        
                        resultados.append({
                            "ALUNO": nome, "NOTA": nota, "NÍVEL": nivel,
                            "DISCIPLINA": disciplina, "TURMA": turma, "SÉRIE": serie
                        })

                    df_novo = pd.DataFrame(resultados)
                    st.session_state['historico'] = pd.concat([st.session_state['historico'], df_novo]).drop_duplicates(subset=['ALUNO', 'DISCIPLINA'])
                    st.success(f"✅ Dados de {disciplina} - Turma {turma} carregados!")
                else:
                    st.error("Não encontrei a palavra 'GABARITO' na primeira coluna.")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")

    # --- PAINEL ANALÍTICO ---
    elif menu == "📊 Painel Analítico":
        if not st.session_state['historico'].empty:
            df_h = st.session_state['historico']
            
            # Filtros laterais
            st.sidebar.markdown("---")
            filtro_disc = st.sidebar.selectbox("Selecionar Matéria", df_h['DISCIPLINA'].unique())
            df = df_h[df_h['DISCIPLINA'] == filtro_disc]
            
            st.title(f"📊 Análise de Desempenho: {filtro_disc}")
            
            c1
