import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. MOTORES DE CÁLCULO (TRI & NOTAS FICTÍCIAS) ---
def calcular_proficiencia_tri(respostas_binarias):
    """
    Calcula a nota baseada nas habilidades de Matemática do 9º ano.
    1 = Acerto (C), 0 = Erro (E)
    """
    if not respostas_binarias: return 0
    acertos = sum(respostas_binarias.values())
    total = len(respostas_binarias)
    
    # Simula a escala SAEB (0 a 400) com base no percentual de acerto
    percentual = acertos / total
    nota = (percentual * 300) + 100 + np.random.uniform(-12, 12)
    return round(nota, 1)

def identificar_nivel_saeb(nota):
    if nota < 225: return "Muito Crítico", "#D32F2F"
    if nota < 275: return "Crítico", "#F57C00"
    if nota < 325: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. CONTROLE DE SESSÃO E ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'historico_geral' not in st.session_state:
    st.session_state['historico_geral'] = pd.DataFrame()

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Sistema SIMAR - Monitoramento</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("Acessar Painel", use_container_width=True):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("Usuário ou Senha incorretos")
else:
    # --- MENU LATERAL ---
    st.sidebar.title("SISTEMA PEDAGÓGICO")
    menu = st.sidebar.radio("Navegação:", ["🏠 Página Inicial", "📝 Importar Planilha", "📊 Painel Analítico", "🚪 Sair"])

    # --- PÁGINA 1: INICIAL E TUTORIAL ---
    if menu == "🏠 Página Inicial":
        st.title("👋 Bem-vindo, Jardel Alves!")
        st.markdown("### Monitoramento de Aprendizagem - Escola José Pacífico")
        
        c1, c2 = st.columns(2)
        with c1:
            st.info("""
            **📖 Tutorial de Operação:**
            1. **Menu Importar:** Utilize para subir o arquivo Excel da Prova de Rede.
            2. **Automação:** O código varre as primeiras 15 linhas para achar 'Matemática' ou 'Português'.
            3. **Correção:** Ele compara a resposta do aluno com a linha do Gabarito.
            4. **Conversão:** Transforma automaticamente o resultado em 1 (Acerto) ou 0 (Erro).
            """)
        with c2:
            st.success("""
            **🎯 Habilidades do 9º Ano Aplicadas:**
            - **EF09MA01/02:** Números Reais e Irracionais.
            - **EF09MA03:** Cálculos com Potências e Radicais.
            - **EF09MA08:** Proporcionalidade.
            """)

    # --- PÁGINA 2: IMPORTAÇÃO (ONDE O ERRO FOI CORRIGIDO) ---
    elif menu == "📝 Importar Planilha":
        st.header("📝 Carregar Nova Planilha de Avaliação")
        arq = st.file_uploader("Selecione o arquivo (.xlsx)", type="xlsx")
        
        if arq:
            try:
                # Lendo a planilha e garantindo que tudo seja texto
                df_raw = pd.read_excel(arq, header=None).fillna("")
                
                # BUSCA DINÂMICA DE CABEÇALHO
                texto_cabecalho = " ".join(df_raw.iloc[:15].astype(str).values.flatten()).upper()
                
                if "MATEMÁTICA" in texto_cabecalho:
                    disciplina_detectada = "MATEMÁTICA"
                elif "PORTUGUESA" in texto_cabecalho:
                    disciplina_detectada = "LÍNGUA PORTUGUESA"
                else:
                    disciplina_detectada = "DISCIPLINA NÃO IDENTIF."

                turma_detectada = "A" if "TURMA: A" in texto_cabecalho or "TURMA A" in texto_cabecalho else "B"

                # LOCALIZAR LINHA DO GABARITO
                idx_gab = df_raw[df_raw[0].astype(str).str.upper().str.contains("GABARITO", na=False)].index
                
                if not idx_gab.empty:
                    linha_g = idx_gab[0]
                    # Extrair o gabarito oficial (letras nas colunas pares a partir da C)
                    gabarito = [str(x).strip().upper() for x in df_raw.iloc[linha_g, 2:45].tolist() if str(x).strip() != ""]
                    
                    qtd_questoes = len(gabarito)
                    novos_dados = []

                    # PROCESSAR CADA ALUNO
                    for i in range(linha_g + 1, len(df_raw)):
                        row = df_raw.iloc[i].tolist()
                        nome = str(row[1]).strip().upper()
                        
                        # Para a leitura se chegar ao fim dos alunos
                        if nome in ["NAN", "", "0", "TOTAL", "OBSERVAÇÕES"]: break
                        
                        # Lógica 1 (Acerto) e 0 (Erro)
                        res_binarias = {}
                        for q in range(qtd_questoes):
                            resp_aluno = str(row[2 + (q*2)]).strip().upper()
                            res_binarias[f"Q{q+1}"] = 1 if resp_aluno == gabarito[q] else 0
                        
                        nota_tri = calcular_proficiencia_tri(res_binarias)
                        nivel, cor = identificar_nivel_saeb(nota_tri)
                        
                        novos_dados.append({
                            "ALUNO": nome, 
                            "NOTA": nota_tri, 
                            "NÍVEL": nivel,
                            "DISCIPLINA": disciplina_detectada,
                            "TURMA": turma_detectada
                        })

                    df_importado = pd.DataFrame(novos_dados)
                    st.session_state['historico_geral'] = pd.concat([st.session_state['historico_geral'], df_importado]).drop_duplicates(subset=['ALUNO', 'DISCIPLINA'])
                    st.success(f"✅ Sucesso! {disciplina_detectada} - Turma {turma_detectada} carregada.")
                else:
                    st.error("Erro crítico: A palavra 'GABARITO' não foi encontrada na primeira coluna.")
            except Exception as e:
                st.error(f"Ocorreu um erro no processamento: {e}")

    # --- PÁGINA 3: PAINEL ANALÍTICO E GRÁFICOS ---
    elif menu == "📊 Painel Analítico":
        if not st.session_state['historico_geral'].empty:
