import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. MOTORES DE CÁLCULO (TRI & HABILIDADES 9º ANO) ---
def calcular_proficiencia_tri(respostas_binarias):
    """
    Calcula nota fictícia baseada nas habilidades de Matemática (EF09MA01, EF09MA03).
    1 = Acerto (C), 0 = Erro (E)
    """
    if not respostas_binarias: return 0
    acertos = sum(respostas_binarias.values())
    total = len(respostas_binarias)
    
    # Escala SAEB: 0 a 400
    percentual = acertos / total
    nota = (percentual * 300) + 100 + np.random.uniform(-10, 10)
    return round(nota, 1)

def identificar_nivel_saeb(nota):
    if nota < 225: return "Muito Crítico", "#D32F2F"
    if nota < 275: return "Crítico", "#F57C00"
    if nota < 325: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. CONTROLE DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'historico_geral' not in st.session_state:
    st.session_state['historico_geral'] = pd.DataFrame()

# --- 4. TELA DE LOGIN ---
if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Sistema SIMAR - Monitoramento</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1,1,1])
    with col_l2:
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("Acessar Painel", use_container_width=True):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("Acesso negado")
else:
    # --- MENU LATERAL ---
    st.sidebar.title("SISTEMA PEDAGÓGICO")
    menu = st.sidebar.radio("Navegação:", ["🏠 Página Inicial", "📝 Importar Planilha", "📊 Painel Analítico", "🚪 Sair"])

    # --- PÁGINA 1: INICIAL E TUTORIAL ---
    if menu == "🏠 Página Inicial":
        st.title("👋 Olá, Jardel Alves!")
        st.markdown("### Monitoramento Escola José Pacífico")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.info("""
            **📖 Tutorial:**
            1. Vá em 'Importar Planilha'.
            2. Suba o arquivo Excel da prova.
            3. O sistema identifica se é Matemática ou Português sozinho.
            4. O cálculo converte 'C' em 1 e erro em 0.
            """)
        with col_t2:
            st.success("""
            **🎯 Habilidades do 9º Ano:**
            - EF09MA01: Reta numérica e irracionais.
            - EF09MA03: Potências e Radicais.
            - EF09MA08: Grandezas proporcionais.
            """)

    # --- PÁGINA 2: IMPORTAÇÃO ---
    elif menu == "📝 Importar Planilha":
        st.header("📝 Importar Novos Dados")
        arq = st.file_uploader("Selecione o arquivo Excel", type="xlsx")
        
        if arq:
            try:
                df_raw = pd.read_excel(arq, header=None).fillna("")
                # Varre o topo para identificar a matéria
                cabecalho = " ".join(df_raw.iloc[:15].astype(str).values.flatten()).upper()
                
                disciplina = "MATEMÁTICA" if "MATEMÁTICA" in cabecalho else "LÍNGUA PORTUGUESA"
                turma = "A" if "TURMA A" in cabecalho or "TURMA: A" in cabecalho else "B"

                idx_gab = df_raw[df_raw[0].astype(str).str.upper().str.contains("GABARITO", na=False)].index
                
                if not idx_gab.empty:
                    linha_g = idx_gab[0]
                    gabarito = [str(x).strip().upper() for x in df_raw.iloc[linha_g, 2:45].tolist() if str(x).strip() != ""]
                    
                    num_q = len(gabarito)
                    novos_registros = []

                    for i in range(linha_g + 1, len(df_raw)):
                        row = df_raw.iloc[i].tolist()
                        nome_aluno = str(row[1]).strip().upper()
                        if nome_aluno in ["NAN", "", "TOTAL", "OBSERVAÇÕES"]: break
                        
                        # Lógica de acerto (1) e erro (0)
                        acertos_bin = {}
                        for j in range(num_q):
                            resp = str(row[2 + (j*2)]).strip().upper()
                            acertos_bin[f"Q{j+1}"] = 1 if resp == gabarito[j] else 0
                        
                        nota_tri = calcular_proficiencia_tri(acertos_bin)
                        nivel, cor = identificar_nivel_saeb(nota_tri)
                        
                        novos_registros.append({
                            "ALUNO": nome_aluno, "NOTA": nota_tri, "NÍVEL": nivel,
                            "DISCIPLINA": disciplina, "TURMA": turma
                        })

                    df_novo = pd.DataFrame(novos_registros)
                    st.session_state['historico_geral'] = pd.concat([st.session_state['historico_geral'], df_novo]).drop_duplicates(subset=['ALUNO', 'DISCIPLINA'])
                    st.success(f"✅ Sucesso: {disciplina} Turma {turma}!")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

    # --- PÁGINA 3: PAINEL ANALÍTICO (CORRIGIDO) ---
    elif menu == "📊 Painel Analítico":
        if not st.session_state['historico_geral'].empty:
            df_full = st.session_state['historico_geral']
            lista_disc = df_full['DISCIPLINA'].unique()
            escolha = st.sidebar.selectbox("Escolha a Matéria", lista_disc)
            
            df = df_full[df_full['DISCIPLINA'] == escolha]
            
            st.title(
