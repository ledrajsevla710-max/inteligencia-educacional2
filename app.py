import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. MOTORES DE CÁLCULO (TRI) ---
def calcular_tri(respostas):
    num_q = len(respostas)
    if num_q == 0: return 0
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        b = np.linspace(-2.5, 2.5, num_q)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel_escala(valor, disciplina):
    ponto = 200 if "PORTUGUESA" in disciplina.upper() else 225
    if valor < ponto: return "Muito Crítico", "#D32F2F"
    if valor < ponto + 50: return "Crítico", "#F57C00"
    if valor < ponto + 100: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. INTERFACE E NAVEGAÇÃO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🏛️ Sistema de Inteligência - José de Freitas")
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True; st.rerun()
else:
    menu = st.sidebar.radio("Menu", ["🏠 Início", "📝 Importar Planilha", "📊 Painel Analítico", "🏢 Relatórios", "🚪 Sair"])

    if menu == "🏠 Início":
        st.title("👋 Bem-vindo ao Portal Educacional")
        st.markdown("""
        ### Como utilizar:
        1. Carregue a planilha oficial da Prova de Rede.
        2. O sistema identifica o **Gabarito na horizontal** e os **Alunos na vertical**.
        3. A nota é gerada via **TRI** (Metodologia SAEB).
        """)

    elif menu == "📝 Importar Planilha":
        st.header("📝 Upload de Arquivo")
        arq = st.file_uploader("Selecione a planilha (.xlsx)", type="xlsx")
        
        if arq:
            # Lemos a planilha bruta sem processar nada primeiro
            df_raw = pd.read_excel(arq, header=None)
            
            # 1. Identificar Escola e Disciplina (Células fixas do modelo)
            escola = str(df_raw.iloc[4, 9]).strip() 
            disciplina = str(df_raw.iloc[6, 30]).strip()
            turma = str(df_raw.iloc[7, 10]).strip()

            # 2. Localizar a linha do GABARITO (Normalmente linha 13 no seu arquivo)
            # Procuramos em todas as linhas pela palavra "GABARITO"
            idx_gab = df_raw[df_raw[0].astype(str).str.contains("GABARITO", na=False)].index
            
            if not idx_gab.empty:
                linha_do_gabarito = idx_gab[0]
                # Extraímos as letras do gabarito (Colunas D, F, H... saltando as vazias)
                linha_vals = df_raw.iloc[linha_do_gabarito].tolist()
                gabarito_oficial = [str(x).strip().upper() for x in linha_vals[2:] if str(x).strip() in ['A', 'B', 'C', 'D']]
                
                # 3. Processar Alunos (começam na linha logo abaixo)
                dados_alunos = []
                for i in range(linha_do_gabarito + 1, len(df_raw)):
                    row = df_raw.iloc[i].tolist()
                    nome = str(row[1]).strip() # Coluna B
                    
                    # Critério para parar: se o nome for vazio ou for o "TOTAL"
                    if nome == "nan" or "TOTAL" in nome.upper() or nome == "0":
                        continue
                    
                    # Pegar respostas do aluno (intercaladas)
                    respostas_brutas = [str(x).strip().upper() for x in row[2:] if str(x).strip() in ['A', 'B', 'C', 'D', 'N/A', '']]
                    
                    res_bin = {}
                    for idx_q in range(len(gabarito_oficial)):
                        gab = gabarito_oficial[idx_q]
                        # Tenta pegar a resposta na mesma posição do gabarito
                        resp = respostas_brutas[idx_q] if idx_q < len(respostas_brutas) else ""
                        res_bin[f"Q{idx_q+1:02d}"] = 1 if resp == gab else 0
                    
                    prof = calcular_tri(res_bin)
                    nivel, _ = obter_nivel_escala(prof, disciplina)
                    
                    dados_alunos.append({
                        "NOME": nome, "PROF_TRI": prof, "DESEMPENHO": nivel,
                        "ESCOLA": escola, "TURMA": turma, "DISCIPLINA": disciplina
                    })

                df_final = pd.DataFrame(dados_alunos)
                st.session_state['consolidado'] = df_final
                st.success(f"✅ Planilha lida! Gabarito de {len(gabarito_oficial)} questões identificado.")
                st.dataframe(df_final[['NOME', 'PROF_TRI', 'DESEMPENHO']])
            else:
                st.error("Não localizei a linha escrita 'GABARITO' na primeira coluna.")

    elif menu == "📊 Painel Analítico":
        if 'consolidado' in st.session_state:
            df = st.session_state['consolidado']
            st.subheader(f"Resultados: {df['ESCOLA'].iloc[0]}")
            st.dataframe(df[['NOME', 'PROF_TRI', 'DESEMPENHO']], use_container_width=True)
        else:
            st.warning("Importe os dados primeiro.")

    elif menu == "🏢 Relatórios":
        if 'consolidado' in st.session_state:
            df = st.session_state['consolidado']
            if st.button("Gerar PDF"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, t(f"DIAGNÓSTICO: {df['ESCOLA'].iloc[0]}"), ln=True, align='C')
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(100, 8, "ALUNO", 1); pdf.cell(40, 8, "NOTA", 1); pdf.cell(60, 8, "NÍVEL", 1)
                pdf.ln()
                pdf.set_font('Arial', '', 9)
                for _, r in df.iterrows():
                    pdf.cell(100, 7, t(r['NOME']), 1); pdf.cell(40, 7, f"{r['PROF_TRI']:.1f}", 1); pdf.cell(60, 7, t(r['DESEMPENHO']), 1)
                    pdf.ln()
                st.download_button("Baixar", pdf.output(dest='S').encode('latin-1'), "Relatorio.pdf")

    elif menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()
