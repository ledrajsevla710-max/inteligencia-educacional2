import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io

# --- 1. CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. MOTORES TÉCNICOS ---
def calcular_tri(respostas_binarias):
    if not respostas_binarias: return 0
    num_q = len(respostas_binarias)
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas_binarias.items()):
        b = np.linspace(-2.5, 2.5, num_q)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel(valor, disciplina):
    corte = 200 if "PORTUGUESA" in disciplina.upper() else 225
    if valor < corte: return "Muito Crítico", "#D32F2F"
    if valor < corte + 50: return "Crítico", "#F57C00"
    if valor < corte + 100: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. INTERFACE DE ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Portal de Inteligência Educacional</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        u = st.text_input("Usuário (CPF/Matrícula)")
        s = st.text_input("Senha", type="password")
        if st.button("Acessar Sistema", use_container_width=True):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True; st.rerun()
            else: st.error("Acesso negado.")
else:
    menu = st.sidebar.radio("Navegação", ["🏠 Home", "📝 Importar Planilha", "📊 Painel Analítico", "🏢 Relatórios PDF", "🚪 Sair"])

    if menu == "🏠 Home":
        st.title("👋 Bem-vindo ao Sistema de Diagnóstico")
        st.markdown("### Gestão Pedagógica Baseada em Dados")
        
        c1, c2 = st.columns(2)
        with c1:
            st.info("""
            **💡 Como o App Funciona?**
            1. **Padronização:** O sistema converte automaticamente todas as respostas para **MAIÚSCULAS**, evitando erros de digitação.
            2. **Leitura de Gabarito:** Ele localiza a linha 'GABARITO' na sua planilha e usa esses dados para corrigir a prova.
            3. **Filtro Inteligente:** Identifica onde terminam os alunos e ignora as 'Observações' e 'Totais' do final do arquivo.
            """)
        with c2:
            st.success("""
            **🚀 Tutorial Rápido:**
            - Vá em **Importar Planilha** e envie o arquivo .xlsx.
            - O sistema fará o cálculo da nota **TRI** (Metodologia SAEB).
            - No **Painel Analítico**, visualize o gráfico de desempenho da sua turma.
            """)
        st.divider()
        st.markdown("#### Status do Sistema: 🟢 Operacional")

    elif menu == "📝 Importar Planilha":
        st.header("📝 Upload de Dados da Rede")
        arq = st.file_uploader("Selecione a planilha Excel", type="xlsx")
        
        if arq:
            df_raw = pd.read_excel(arq, header=None)
            
            # Identificação de Metadados (Escola, Disciplina, Turma)
            try:
                escola = str(df_raw.iloc[4, 9]).strip().upper() 
                disc = str(df_raw.iloc[6, 30]).strip().upper()
                turma = str(df_raw.iloc[7, 10]).strip().upper()
            except:
                escola, disc, turma = "ESCOLA MUNICIPAL", "GERAL", "A"

            # Localiza a linha do GABARITO (Scan na coluna A)
            idx_gab = df_raw[df_raw[0].astype(str).str.contains("GABARITO", na=False, case=False)].index
            
            if not idx_gab.empty:
                linha_g = idx_gab[0]
                # Captura gabarito em linha (D, F, H...) e garante MAIÚSCULAS
                gabarito_oficial = [str(x).strip().upper() for x in df_raw.iloc[linha_g, 2:45].tolist() if str(x).strip().upper() in ['A', 'B', 'C', 'D']]
                
                num_q = len(gabarito_oficial)
                processados = []

                # Processa Alunos
                for i in range(linha_g + 1, len(df_raw)):
                    row = df_raw.iloc[i].tolist()
                    nome = str(row[1]).strip().upper()
                    
                    # Filtro para parar nas Observações ou Totais
                    if nome in ["NAN", "0", "1.0", ""] or "TOTAL" in nome or "OBSERV" in nome:
                        break
                    
                    # Respostas do aluno (Normalizadas para Maiúsculas)
                    res_aluno_bruto = [str(x).strip().upper() for x in row[2:45] if str(x).strip().upper() in ['A', 'B', 'C', 'D', 'N/A', '']]
                    
                    res_bin = {}
                    for q_idx in range(num_q):
                        gab = gabarito_oficial[q_idx]
                        resp = res_aluno_bruto[q_idx] if q_idx < len(res_aluno_bruto) else ""
                        res_bin[f"Q{q_idx+1:02d}"] = 1 if resp == gab else 0
                    
                    prof = calcular_tri(res_bin)
                    nivel, cor = obter_nivel(prof, disc)
                    
                    processados.append({
                        "ALUNO": nome, "PROF_TRI": prof, "NÍVEL": nivel, "COR": cor,
                        "ESCOLA": escola, "TURMA": turma, "DISCIPLINA": disc
                    })

                st.session_state['consolidado'] = pd.DataFrame(processados)
                st.success(f"✅ Sucesso! {len(processados)} alunos processados de {escola}.")
                st.dataframe(st.session_state['consolidado'][['ALUNO', 'PROF_TRI', 'NÍVEL']])
            else:
                st.error("Erro: A palavra 'GABARITO' não foi encontrada na planilha.")

    elif menu == "📊 Painel Analítico":
        if 'consolidado' in st.session_state:
            df = st.session_state['consolidado']
            st.title(f"📊 Painel de Desempenho - {df['ESCOLA'].iloc[0]}")
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Média da Turma", f"{df['PROF_TRI'].mean():.1f}")
            col_m2.metric("Total de Alunos", len(df))
            col_m3.metric("Disciplina", df['DISCIPLINA'].iloc[0])

            # --- GRÁFICO ---
            st.subheader("Distribuição por Níveis de Aprendizagem")
            fig, ax = plt.subplots(figsize=(10, 5))
            cores_map = {"Muito Crítico": "#D32F2F", "Crítico": "#F57C00", "Intermediário": "#FBC02D", "Adequado": "#388E3C"}
            
            contagem = df['NÍVEL'].value_counts().reindex(["Muito Crítico", "Crítico", "Intermediário", "Adequado"], fill_value=0)
            contagem.plot(kind='bar', color=[cores_map[n] for n in contagem.index], ax=ax)
            plt.ylabel("Quantidade de Alunos")
            plt.xticks(rotation=0)
            st.pyplot(fig)
            
            st.table(df[['ALUNO', 'PROF_TRI', 'NÍVEL']])
        else:
            st.warning("Importe dados primeiro.")

    elif menu == "🏢 Relatórios PDF":
        if 'consolidado' in st.session_state:
            df = st.session_state['consolidado']
            if st.button("Gerar PDF para Impressão"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, t(f"DIAGNÓSTICO EDUCACIONAL - {df['ESCOLA'].iloc[0]}"), ln=True, align='C')
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(100, 8, "NOME DO ALUNO", 1); pdf.cell(40, 8, "NOTA TRI", 1); pdf.cell(60, 8, "NÍVEL", 1)
                pdf.ln()
                pdf.set_font('Arial', '', 9)
                for _, r in df.iterrows():
                    pdf.cell(100, 7, t(r['ALUNO']), 1); pdf.cell(40, 7, f"{r['PROF_TRI']:.1f}", 1); pdf.cell(60, 7, t(r['NÍVEL']), 1)
                    pdf.ln()
                st.download_button("Baixar Relatório", pdf.output(dest='S').encode('latin-1'), "Relatorio_Final.pdf")

    elif menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()
