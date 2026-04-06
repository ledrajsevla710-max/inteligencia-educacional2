import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import tempfile

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestão TRI José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. ESCALA E SUGESTÕES PEDAGÓGICAS ---
def obter_diagnostico(score):
    if score < 150:
        return {
            "nivel": "CRÍTICO", "cor": "#E74C3C", 
            "sugestao": "Focar em alfabetização matemática/letramento básico. Realizar oficinas de reforço com materiais concretos e jogos para retomar descritores de anos anteriores."
        }
    elif score < 250:
        return {
            "nivel": "BÁSICO", "cor": "#F1C40F", 
            "sugestao": "Trabalhar resolução de problemas contextualizados. Identificar os distratores mais marcados para corrigir vícios de raciocínio e interpretação de texto/enunciado."
        }
    elif score < 350:
        return {
            "nivel": "PROFICIENTE", "cor": "#2ECC71", 
            "sugestao": "Manter o ritmo com desafios de nível médio e avançado. Introduzir simulados de tempo para melhorar a gestão da prova e consolidar os descritores da série."
        }
    else:
        return {
            "nivel": "AVANÇADO", "cor": "#3498DB", 
            "sugestao": "Propor atividades de monitoria entre pares (alunos avançados ajudando os demais) e desafios de nível olímpico (OBMEP/Canguru)."
        }

# --- 3. DICIONÁRIOS DE HABILIDADES ---
HABILIDADES_MAT = {f"Q{i:02d}": f"Descritor de Matemática item {i}" for i in range(1, 23)}
HABILIDADES_POR = {f"Q{i:02d}": f"Descritor de Língua Portuguesa item {i}" for i in range(1, 23)}

# --- 4. GABARITOS ADAPTADOS ---
GABARITOS = {
    "9º Ano": ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
}

# --- 5. FUNÇÃO TRI ---
def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- 6. INTERFACE ---
st.title("🏛️ Inteligência Educacional - José de Freitas")

st.sidebar.header("📋 Configurações")
disc_sel = st.sidebar.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
serie_sel = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])
uploaded_file = st.file_uploader("📂 Carregar Planilha Excel", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gab_list = GABARITOS.get(serie_sel, ['A']*22)
    gab_dict = {f'Q{i:02d}': gab_list[i-1] for i in range(1, 23)}
    mapa_habil = HABILIDADES_POR if disc_sel == "Língua Portuguesa" else HABILIDADES_MAT

    # Processamento
    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gab_dict[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    # Filtros
    esc_sel = st.sidebar.selectbox("Escola:", ["Geral"] + sorted(list(df['Escola'].unique())))
    df_esc = df if esc_sel == "Geral" else df[df['Escola'] == esc_sel]
    
    tur_sel = st.sidebar.selectbox("Turma:", ["Todas"] + sorted(list(df_esc['Turma'].unique())))
    df_f = df_esc if tur_sel == "Todas" else df_esc[df_esc['Turma'] == tur_sel]

    # Dashboard de Cabeçalho
    media_unidade = df_f['Proficiência'].mean()
    diag = obter_diagnostico(media_unidade)
    
    st.markdown(f"### 📊 Resultado: {esc_sel} | {tur_sel}")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Média TRI", f"{media_unidade:.1f}")
        st.markdown(f"<h3 style='color:{diag['cor']}'>Nível {diag['nivel']}</h3>", unsafe_allow_html=True)
    with c2:
        st.warning(f"**Sugestão de Intervenção:** {diag['sugestao']}")

    st.divider()

    # --- BOTÕES DE DOWNLOAD ---
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        if st.button("📄 RELATÓRIO COMPLETO (COM GRÁFICOS)", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f'RELATÓRIO PEDAGÓGICO - {disc_sel}', ln=True, align='C')
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 7, f'Escola: {esc_sel} | Turma: {tur_sel} | Média: {media_unidade:.1f}', ln=True, align='C')
            
            # Tabela de Alunos no PDF
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, 'NOTAS POR ALUNO:', ln=True)
            pdf.set_font('Arial', '', 9)
            for _, r in df_f.iterrows():
                pdf.cell(0, 6, f"- {r['Nome']}: {r['Proficiência']:.1f}", ln=True)
            
            pdf.ln(10)
            for q in cols_q:
                stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                fig, ax = plt.subplots(figsize=(4, 2.5))
                ax.bar(['A','B','C','D'], stats, color=['#2ECC71' if l == gab_dict[q] else '#E74C3C' for l in ['A','B','C','D']])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    fig.savefig(tmp.name, bbox_inches='tight')
                    plt.close(fig)
                    if pdf.get_y() > 220: pdf.add_page()
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 8, f"Questão {q} | Acerto: {stats[gab_dict[q]]:.1f}%", ln=True)
                    pdf.image(tmp.name, x=10, w=70)
                    pdf.set_font('Arial', 'I', 8)
                    pdf.multi_cell(0, 4, f"Habilidade: {mapa_habil[q]}")
                    pdf.ln(4)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Baixar PDF com Gráficos", pdf_bytes, "Relatorio_Grafico.pdf", use_container_width=True)

    with col_d2:
        if st.button("📄 RELATÓRIO ANALÍTICO (SEM GRÁFICOS)", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'RELATÓRIO ANALÍTICO DE PROFICIÊNCIA', ln=True, align='C')
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, 'DESEMPENHO DOS ALUNOS:', ln=True)
            pdf.set_font('Arial', '', 10)
            for _, r in df_f.iterrows():
                pdf.cell(0, 6, f"{r['Nome']} (Turma: {r['Turma']}) -> Nota TRI: {r['Proficiência']:.1f}", ln=True)
            
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, 'INTERVENÇÃO SUGERIDA PARA A UNIDADE:', ln=True)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 6, diag['sugestao'])
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Baixar PDF Analítico", pdf_bytes, "Relatorio_Analitico.pdf", use_container_width=True)

    # --- GRÁFICOS NA TELA (RESTAURADOS) ---
    st.markdown("---")
    st.subheader("🎯 Análise por Item (Visualização em Tela)")
    grid = st.columns(2)
    for i, q in enumerate(cols_q):
        with grid[i % 2]:
            with st.container(border=True):
                stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                fig, ax = plt.subplots(figsize=(6, 3.5))
                ax.bar(['A','B','C','D'], stats, color=['#2ECC71' if l == gab_dict[q] else '#E74C3C' for l in ['A','B','C','D']], edgecolor='black')
                ax.set_title(f"Item {q} - Gabarito: {gab_dict[q]}")
                st.pyplot(fig)
                st.caption(f"**Habilidade:** {mapa_habil[q]}")
