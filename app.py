import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. MOTORES DE CÁLCULO ---
def calcular_tri(respostas):
    num_q = len(respostas)
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

# --- 3. INTERFACE ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🏛️ Sistema de Inteligência - José de Freitas")
    u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "12345" and s == "000": # Ajuste conforme sua necessidade
            st.session_state['autenticado'] = True; st.rerun()
else:
    menu = st.sidebar.radio("Navegação", ["📝 Importar Planilha", "📊 Painel Analítico", "🏢 Relatórios", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()

    elif menu == "📝 Importar Planilha":
        st.header("📝 Upload da Planilha de Rede")
        arq = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type="xlsx")
        
        if arq:
            # Lemos a planilha bruta
            df_raw = pd.read_excel(arq, header=None)
            
            # 1. Captura Escola e Turma (posições baseadas no seu arquivo)
            try:
                escola = str(df_raw.iloc[4, 9]).strip() # Célula J5
                turma = str(df_raw.iloc[7, 10]).strip()  # Célula K8
                disciplina = str(df_raw.iloc[6, 30]).strip() # Célula AE7
            except:
                escola, turma, disciplina = "Escola", "A", "Geral"

            # 2. Localizar a linha do GABARITO (Procurando em qualquer coluna)
            # Na sua planilha, "GABARITO" está na Coluna A (índice 0)
            mascara = df_raw.apply(lambda row: row.astype(str).str.contains('GABARITO').any(), axis=1)
            idx_gabarito = df_raw[mascara].index
            
            if not idx_gabarito.empty:
                linha_gab = idx_gabarito[0]
                # O Gabarito oficial está na linha identificada, começando da coluna D (índice 3)
                # Saltando de 2 em 2 colunas (onde estão as letras)
                linha_dados_gab = df_raw.iloc[linha_gab].tolist()
                gabarito_oficial = [str(x).strip().upper() for x in linha_dados_gab[2:45] if str(x).strip() in ['A', 'B', 'C', 'D', 'E']]
                
                num_questoes = len(gabarito_oficial)
                
                # 3. Processar Alunos (começam logo abaixo do gabarito)
                lista_alunos = []
                for idx in range(linha_gab + 1, len(df_raw)):
                    row = df_raw.iloc[idx].tolist()
                    nome_aluno = str(row[1]).strip() # Nome está na Coluna B
                    
                    # Para se parar quando encontrar o "TOTAL DE ACERTOS"
                    if nome_aluno == "nan" or "TOTAL" in nome_aluno.upper() or "OBSERVAÇÕES" in nome_aluno.upper():
                        continue
                    
                    # Extrair respostas (também saltando colunas)
                    res_binaria = {}
                    respostas_aluno = [str(x).strip().upper() for x in row[2:45]]
                    # Filtramos apenas as letras nas colunas corretas
                    letras_aluno = []
                    for val in respostas_aluno:
                        if val in ['A', 'B', 'C', 'D', 'E', 'N/A']:
                            letras_aluno.append(val)
                    
                    for i in range(num_questoes):
                        gab = gabarito_oficial[i]
                        resp = letras_aluno[i] if i < len(letras_aluno) else ""
                        res_binaria[f"Q{i+1:02d}"] = 1 if resp == gab else 0
                    
                    prof = calcular_tri(res_binaria)
                    nivel, _ = obter_nivel_escala(prof, disciplina)
                    
                    lista_alunos.append({
                        "NOME": nome_aluno,
                        "PROF_TRI": prof,
                        "DESEMPENHO": nivel,
                        "ESCOLA": escola,
                        "TURMA": turma,
                        "DISCIPLINA": disciplina
                    })
                
                df_final = pd.DataFrame(lista_alunos)
                st.session_state['consolidado'] = df_final
                st.success(f"✅ Processado: {escola} | {disciplina} | {len(df_final)} alunos")
                st.dataframe(df_final[['NOME', 'PROF_TRI', 'DESEMPENHO']].head())
            else:
                st.error("Palavra 'GABARITO' não encontrada. Verifique se a planilha segue o modelo da rede.")

    elif menu == "📊 Painel Analítico":
        if 'consolidado' in st.session_state:
            df = st.session_state['consolidado']
            st.subheader(f"📊 Diagnóstico: {df['ESCOLA'].iloc[0]} - {df['DISCIPLINA'].iloc[0]}")
            st.dataframe(df[['NOME', 'PROF_TRI', 'DESEMPENHO']], use_container_width=True)
        else:
            st.warning("Importe os dados primeiro.")

    elif menu == "🏢 Relatórios":
        if 'consolidado' in st.session_state:
            df = st.session_state['consolidado']
            if st.button("📥 Gerar PDF"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, t(f"RELATÓRIO DE DESEMPENHO - {df['ESCOLA'].iloc[0]}"), ln=True, align='C')
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(100, 8, "NOME DO ALUNO", 1); pdf.cell(40, 8, "NOTA TRI", 1); pdf.cell(60, 8, "NÍVEL", 1)
                pdf.ln()
                pdf.set_font('Arial', '', 9)
                for _, r in df.iterrows():
                    pdf.cell(100, 7, t(r['NOME'][:45]), 1)
                    pdf.cell(40, 7, f"{r['PROF_TRI']:.1f}", 1)
                    pdf.cell(60, 7, t(r['DESEMPENHO']), 1)
                    pdf.ln()
                st.download_button("Baixar PDF", pdf.output(dest='S').encode('latin-1'), "Relatorio.pdf")
