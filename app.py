import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. GESTÃO DE USUÁRIOS ---
if 'usuarios_db' not in st.session_state:
    st.session_state['usuarios_db'] = {"12345": "000"} 

# --- 3. MATRIZES 1º BIMESTRE ---
MATRIZ_LP = {f"Q{i:02d}": f"Habilidade {i} - Língua Portuguesa" for i in range(1, 23)}
MATRIZ_MAT = {f"Q{i:02d}": f"Habilidade {i} - Matemática" for i in range(1, 23)}

# --- 4. MOTORES DE CÁLCULO ---
def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        # Dificuldade estimada (b) baseada na posição da questão
        b = np.linspace(-2.5, 2.5, 22)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel_escala(valor, disciplina):
    ponto = 200 if disciplina == "Língua Portuguesa" else 225
    if valor < ponto: return "Muito Crítico", "#D32F2F"
    if valor < ponto + 50: return "Crítico", "#F57C00"
    if valor < ponto + 100: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 5. TELA DE ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Sistema de Inteligência Educacional</h1>", unsafe_allow_html=True)
    u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in st.session_state['usuarios_db'] and st.session_state['usuarios_db'][u] == s:
            st.session_state['autenticado'] = True; st.rerun()
        else: st.error("Acesso negado.")

# --- 6. AMBIENTE LOGADO ---
else:
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📝 Importar Dados", "📊 Painel Analítico", "🏢 Relatório Escola", "🏙️ Relatório Municipal", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()

    elif menu == "📝 Importar Dados":
        st.header("📝 Importar Planilha de Rede")
        ano_letivo = st.selectbox("Ano Escolar", ["2º Ano", "5º Ano", "9º Ano"])
        disc = st.selectbox("Disciplina", ["Língua Portuguesa", "Matemática"])
        
        arq = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type="xlsx")
        
        if arq:
            # Lemos a planilha bruta sem cabeçalho para localizar a estrutura
            df_raw = pd.read_excel(arq, header=None)
            
            # 1. Extrair Escola e Turma de células fixas (J5 e K8 aprox.)
            try:
                escola_nome = str(df_raw.iloc[4, 9]).strip() # Coluna J, Linha 5
                turma_nome = str(df_raw.iloc[7, 10]).strip() # Coluna K, Linha 8
            except:
                escola_nome = "ESCOLA NÃO IDENTIFICADA"
                turma_nome = "A"

            # 2. Localizar a linha onde está o "GABARITO" para começar a ler os alunos
            # Procuramos na coluna B (índice 1) onde costumam estar os nomes
            idx_gabarito = df_raw[df_raw[1].astype(str).str.contains("GABARITO", na=False)].index
            
            if not idx_gabarito.empty:
                linha_inicio = idx_gabarito[0]
                # O gabarito oficial está nesta linha
                gabarito_oficial = df_raw.iloc[linha_inicio, 3:45:2].tolist() # Pega as letras nas colunas cinzas
                
                # Os alunos começam logo abaixo do Gabarito
                df_alunos = df_raw.iloc[linha_inicio + 1:].copy()
                
                lista_processada = []
                
                for idx, row in df_alunos.iterrows():
                    nome_aluno = str(row[1]).strip()
                    # Ignora linhas de Total ou Observações
                    if nome_aluno == "nan" or "TOTAL" in nome_aluno.upper() or "OBSERVAÇÕES" in nome_aluno.upper():
                        continue
                    
                    # Extrair respostas (colunas D, F, H... intercaladas)
                    respostas_aluno = row[3:45:2].tolist()
                    res_binaria = {}
                    
                    for i in range(len(gabarito_oficial)):
                        q_key = f"Q{i+1:02d}"
                        gab = str(gabarito_oficial[i]).strip().upper()
                        resp = str(respostas_aluno[i]).strip().upper()
                        res_binaria[q_key] = 1 if resp == gab and resp != "NAN" else 0
                    
                    # Cálculo da Proficiência
                    prof = calcular_tri(res_binaria)
                    nivel, cor = obter_nivel_escala(prof, disc)
                    
                    lista_processada.append({
                        "NOME": nome_aluno,
                        "ESCOLA": escola_nome,
                        "TURMA": turma_nome,
                        "PROF_TRI": prof,
                        "DESEMPENHO": nivel,
                        "COR": cor,
                        **res_binaria
                    })
                
                df_final = pd.DataFrame(lista_processada)
                df_final['DISCIPLINA'] = disc
                
                st.session_state['consolidado'] = df_final
                st.success(f"✅ Sucesso! Escola: {escola_nome} | Alunos: {len(df_final)}")
                st.dataframe(df_final[['NOME', 'PROF_TRI', 'DESEMPENHO']].head())
            else:
                st.error("Não encontramos a palavra 'GABARITO' na coluna dos nomes. Verifique o formato da planilha.")

    elif menu == "📊 Painel Analítico":
        if 'consolidado' in st.session_state:
            df = st.session_state['consolidado']
            st.subheader(f"📊 Análise: {df['ESCOLA'].iloc[0]} - Turma {df['TURMA'].iloc[0]}")
            
            media_turma = df['PROF_TRI'].mean()
            nivel_t, cor_t = obter_nivel_escala(media_turma, df['DISCIPLINA'].iloc[0])
            
            st.metric("Média de Proficiência da Turma", f"{media_turma:.1f}", nivel_t)
            
            st.write("### 👥 Desempenho Individual")
            st.dataframe(df[['NOME', 'PROF_TRI', 'DESEMPENHO']], use_container_width=True)
        else:
            st.warning("Importe dados primeiro.")

    elif menu in ["🏢 Relatório Escola", "🏙️ Relatório Municipal"]:
        if 'consolidado' in st.session_state:
            df_geral = st.session_state['consolidado']
            if st.button("📥 Gerar Relatório em PDF"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, t(f"DIAGNÓSTICO EDUCACIONAL - {df_geral['ESCOLA'].iloc[0]}"), ln=True, align='C')
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 8, t(f"Disciplina: {df_geral['DISCIPLINA'].iloc[0]} | Turma: {df_geral['TURMA'].iloc[0]}"), ln=True, align='C')
                
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(100, 8, "NOME DO ALUNO", 1); pdf.cell(40, 8, "PROFICIÊNCIA", 1); pdf.cell(60, 8, "NÍVEL", 1)
                pdf.ln()
                
                pdf.set_font('Arial', '', 9)
                for _, r in df_geral.iterrows():
                    pdf.cell(100, 7, t(r['NOME'][:45]), 1)
                    pdf.cell(40, 7, f"{r['PROF_TRI']:.1f}", 1)
                    pdf.cell(60, 7, t(r['DESEMPENHO']), 1)
                    pdf.ln()
                
                st.download_button("Clique para baixar", pdf.output(dest='S').encode('latin-1'), "Relatorio_Final.pdf")
        else:
            st.warning("Sem dados consolidados.")
