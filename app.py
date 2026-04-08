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

# --- 3. MATRIZES 1º BIMESTRE (DESCRIÇÕES) ---
MATRIZ_LP = {f"Q{i:02d}": f"Descritor D{i} - Língua Portuguesa" for i in range(1, 23)}
MATRIZ_MAT = {f"Q{i:02d}": f"Descritor D{i} - Matemática" for i in range(1, 23)}

GABARITO = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']

# --- 4. MOTORES DE CÁLCULO ---
def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
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

# --- 5. LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Inteligência Educacional</h1>", unsafe_allow_html=True)
    u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
    if st.button("Aceder"):
        if u in st.session_state['usuarios_db'] and st.session_state['usuarios_db'][u] == s:
            st.session_state['autenticado'] = True; st.rerun()
else:
    menu = st.sidebar.radio("Navegação", ["📝 Importar Planilha", "📊 Painel Analítico", "🏢 Relatório Escola/Município", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()

    elif menu == "📝 Importar Planilha":
        st.header("📝 Carregar Planilha da Rede")
        disc = st.selectbox("Disciplina", ["Língua Portuguesa", "Matemática"])
        arq = st.file_uploader("Selecione o arquivo Excel", type="xlsx")
        
        if arq:
            # Lemos o arquivo bruto para extrair metadados das células do topo
            df_raw = pd.read_excel(arq, header=None)
            
            # Tentar localizar Escola e Turma em células específicas (baseado no seu modelo)
            nome_escola = str(df_raw.iloc[4, 9]).strip() if len(df_raw) > 4 else "Não Identificada"
            nome_turma = str(df_raw.iloc[7, 10]).strip() if len(df_raw) > 7 else "A"
            
            # Lemos novamente focando na tabela de alunos (geralmente começa após a linha 12)
            df = pd.read_excel(arq, skiprows=12)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Renomear coluna de nomes se necessário (procurando por "NOME" ou "ALUNO")
            col_nome = [c for c in df.columns if "NOME" in c or "DÉBORHA" in str(df[c].iloc[0]).upper()]
            if col_nome: df.rename(columns={col_nome[0]: "NOME_ALUNO"}, inplace=True)

            if "NOME_ALUNO" in df.columns:
                # Limpeza: remove linhas de "TOTAL" ou vazias
                df = df[df['NOME_ALUNO'].notna() & (df['NOME_ALUNO'] != "0")]
                
                for idx, row in df.iterrows():
                    # Mapeia as questões Q01, Q02...
                    res_bin = {}
                    for i in range(1, 23):
                        col_q = f"Q{i:02d}"
                        # Se a coluna não existir exatamente, tentamos achar por aproximação
                        val_res = str(row.get(col_q, row.iloc[i*2] if i*2 < len(row) else '')).upper()
                        res_bin[col_q] = 1 if val_res == GABARITO[i-1] else 0
                    
                    prof = calcular_tri(res_bin)
                    df.at[idx, 'PROF_TRI'] = prof
                    nivel, _ = obter_nivel_escala(prof, disc)
                    df.at[idx, 'DESEMPENHO'] = nivel

                df['ESCOLA'] = nome_escola
                df['TURMA'] = nome_turma
                df['DISCIPLINA'] = disc
                
                st.session_state['consolidado'] = df
                st.success(f"✅ Planilha da Escola {nome_escola} processada!")
                st.dataframe(df[['NOME_ALUNO', 'PROF_TRI', 'DESEMPENHO']].head())
            else:
                st.error("Não foi possível localizar a coluna de nomes dos alunos.")

    elif menu == "📊 Painel Analítico":
        if 'consolidado' in st.session_state:
            df = st.session_state['consolidado']
            st.subheader(f"Análise: {df['ESCOLA'].iloc[0]} - Turma {df['TURMA'].iloc[0]}")
            st.write("### Lista de Proficiência Individual")
            st.dataframe(df[['NOME_ALUNO', 'PROF_TRI', 'DESEMPENHO']], use_container_width=True)
        else:
            st.warning("Importe a planilha primeiro.")

    elif menu == "🏢 Relatório Escola/Município":
        if 'consolidado' in st.session_state:
            df_final = st.session_state['consolidado']
            matriz = MATRIZ_MAT if df_final['DISCIPLINA'].iloc[0] == "Matemática" else MATRIZ_LP
            
            if st.button("📥 Gerar PDF Completo"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, t(f"DIAGNÓSTICO: {df_final['ESCOLA'].iloc[0]}"), ln=True, align='C')
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, t(f"Turma: {df_final['TURMA'].iloc[0]} | Disciplina: {df_final['DISCIPLINA'].iloc[0]}"), ln=True, align='C')
                
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(90, 8, "ALUNO", 1); pdf.cell(40, 8, "NOTA TRI", 1); pdf.cell(60, 8, "NÍVEL", 1)
                pdf.ln()
                
                pdf.set_font('Arial', '', 9)
                for _, r in df_final.iterrows():
                    pdf.cell(90, 7, t(r['NOME_ALUNO'][:40]), 1)
                    pdf.cell(40, 7, f"{r['PROF_TRI']:.1f}", 1)
                    pdf.cell(60, 7, t(r['DESEMPENHO']), 1)
                    pdf.ln()
                
                st.download_button("Baixar PDF", pdf.output(dest='S').encode('latin-1'), "Relatorio_Rede.pdf")
