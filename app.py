import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io

# --- 1. CONFIGURAÇÕES E ESTÉTICA ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

def aplicar_design():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stMetric { background-color: #ffffff; border-left: 5px solid #1E3A8A; padding: 10px; border-radius: 5px; }
        h1, h2 { color: #1E3A8A; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. MOTORES TÉCNICOS (TRI) ---
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
    # O .upper() garante que a regra funcione mesmo se digitar 'matemática' ou 'MATEMÁTICA'
    corte = 200 if "PORTUGUESA" in disciplina.upper() else 225
    if valor < corte: return "Muito Crítico", "#D32F2F"
    if valor < corte + 50: return "Crítico", "#F57C00"
    if valor < corte + 100: return "Intermediário", "#FBC02D"
    return "Adequado", "#388E3C"

# --- 3. GESTÃO DE ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal de Inteligência Educacional</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("Acessar Painel", use_container_width=True):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True; st.rerun()
            else: st.error("Acesso Negado")
else:
    aplicar_design()
    menu = st.sidebar.radio("Navegação Principal", ["🏠 Início", "📝 Importar Planilha", "📊 Painel Analítico", "🏢 Relatórios PDF", "🚪 Sair"])

    if menu == "🏠 Início":
        st.title("👋 Bem-vindo ao Sistema, Jardel!")
        st.markdown("### Monitoramento Pedagógico - José de Freitas/PI")
        
        c1, c2 = st.columns(2)
        with c1:
            st.info("""
            **📋 Funcionalidades Ativas:**
            - **Filtro de Disciplina:** Agora você escolhe qual matéria quer ver.
            - **Padronização:** Todo o texto é convertido para **MAIÚSCULAS** (.upper).
            - **TRI Inteligente:** Nota calculada pela dificuldade das questões.
            """)
        with c2:
            st.success("""
            **🛠️ Tutorial Rápido:**
            1. Carregue o arquivo em **'Importar Planilha'**.
            2. O sistema reconhece Escola e Matéria automaticamente.
            3. No **Painel Analítico**, use o botão lateral para trocar entre Português e Matemática.
            """)

    elif menu == "📝 Importar Planilha":
        st.header("📝 Carregamento de Dados")
        arq = st.file_uploader("Suba a planilha original (.xlsx)", type="xlsx")
        
        if arq:
            df_raw = pd.read_excel(arq, header=None)
            
            try:
                # Extração com .upper() para segurança total
                escola = str(df_raw.iloc[4, 9]).strip().upper() 
                disc = str(df_raw.iloc[6, 30]).strip().upper()
                turma = str(df_raw.iloc[7, 10]).strip().upper()
            except:
                escola, disc, turma = "ESCOLA MUNICIPAL", "GERAL", "A"

            # Localiza Gabarito na Coluna A
            idx_gab = df_raw[df_raw[0].astype(str).str.upper().str.contains("GABARITO", na=False)].index
            
            if not idx_gab.empty:
                linha_g = idx_gab[0]
                gabarito = [str(x).strip().upper() for x in df_raw.iloc[linha_g, 2:45].tolist() if str(x).strip().upper() in ['A', 'B', 'C', 'D']]
                
                num_q = len(gabarito)
                lista_final = []

                # Processa Alunos
                for i in range(linha_g + 1, len(df_raw)):
                    row = df_raw.iloc[i].tolist()
                    nome = str(row[1]).strip().upper()
                    
                    if nome in ["NAN", "0", "1.0", ""] or "TOTAL" in nome or "OBSERV" in nome:
                        break
                    
                    res_aluno = [str(x).strip().upper() for x in row[2:45] if str(x).strip().upper() in ['A', 'B', 'C', 'D', 'N/A', '']]
                    
                    res_bin = {f"Q{j+1:02d}": (1 if (j < len(res_aluno) and res_aluno[j] == gabarito[j]) else 0) for j in range(num_q)}
                    
                    prof = calcular_tri(res_bin)
                    nivel, cor = obter_nivel(prof, disc)
                    
                    lista_final.append({
                        "ALUNO": nome, "NOTA": prof, "NÍVEL": nivel,
                        "ESCOLA": escola, "TURMA": turma, "DISCIPLINA": disc
                    })

                # Armazena no Histórico
                novo_df = pd.DataFrame(lista_final)
                if 'historico' not in st.session_state:
                    st.session_state['historico'] = novo_df
                else:
                    st.session_state['historico'] = pd.concat([st.session_state['historico'], novo_df]).drop_duplicates(subset=['ALUNO', 'DISCIPLINA'])
                
                st.success(f"✅ Dados de {disc} carregados com sucesso!")
            else:
                st.error("⚠️ Linha 'GABARITO' não encontrada.")

    elif menu == "📊 Painel Analítico":
        if 'historico' in st.session_state:
            df_hist = st.session_state['historico']
            
            # --- O BOTÃO DA DISCIPLINA (SELECTBOX) ---
            st.sidebar.markdown("---")
            disc_selecionada = st.sidebar.selectbox("🎯 Filtrar Disciplina", df_hist['DISCIPLINA'].unique())
            
            df = df_hist[df_hist['DISCIPLINA'] == disc_selecionada]
            
            st.title(f"📊 Análise: {disc_selecionada}")
            st.write(f"**Escola:** {df['ESCOLA'].iloc[0]} | **Turma:** {df['TURMA'].iloc[0]}")
            
            c1, c2 = st.columns(2)
            c1.metric("Média da Turma", f"{df['NOTA'].mean():.1f}")
            c2.metric("Qtd. Alunos", len(df))

            # Gráfico de Desempenho
            fig, ax = plt.subplots(figsize=(8, 4))
            contagem = df['NÍVEL'].value_counts().reindex(["Muito Crítico", "Crítico", "Intermediário", "Adequado"], fill_value=0)
            contagem.plot(kind='bar', color=["#D32F2F", "#F57C00", "#FBC02D", "#388E3C"], ax=ax)
            plt.xticks(rotation=0)
            st.pyplot(fig)
            
            st.table(df[['ALUNO', 'NOTA', 'NÍVEL']])
        else:
            st.warning("Importe os dados primeiro.")

    elif menu == "🏢 Relatórios PDF":
        if 'historico' in st.session_state:
            df_full = st.session_state['historico']
            disc_pdf = st.selectbox("Escolha a disciplina para o PDF:", df_full['DISCIPLINA'].unique())
            df = df_full[df_full['DISCIPLINA'] == disc_pdf]
            
            if st.button("Gerar Relatório"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, t(f"RELATÓRIO: {df['ESCOLA'].iloc[0]} - {disc_pdf}"), ln=True, align='C')
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(110, 8, "ALUNO", 1); pdf.cell(30, 8, "NOTA", 1); pdf.cell(60, 8, "NÍVEL", 1)
                pdf.ln()
                pdf.set_font('Arial', '', 9)
                for _, r in df.iterrows():
                    pdf.cell(110, 7, t(r['ALUNO']), 1); pdf.cell(30, 7, f"{r['NOTA']:.1f}", 1); pdf.cell(60, 7, t(r['NÍVEL']), 1)
                    pdf.ln()
                st.download_button("Baixar PDF", pdf.output(dest='S').encode('latin-1'), "Relatorio.pdf")

    elif menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()
