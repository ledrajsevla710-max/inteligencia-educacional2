import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestão TRI José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. MATRIZ DE REFERÊNCIA (1 A 22) ---
MAPA_HABILIDADES = {
    "Matemática": {
        f"Q{i:02d}": {"desc": f"Habilidade da Questão {i}", "sugestao": "Reforçar base teórica."} for i in range(1, 23)
    }
}
# Adicionando as descrições específicas que tínhamos
MAPA_HABILIDADES["Matemática"]["Q01"] = {"desc": "D6 - Ângulos e Giros", "sugestao": "Praticar com transferidor."}
MAPA_HABILIDADES["Matemática"]["Q02"] = {"desc": "EF06MA27 - Classificação de Ângulos", "sugestao": "Identificar ângulos no cotidiano."}

GABARITOS = {
    "Matemática": {f'Q{i:02d}': g for i, g in enumerate(['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B'], 1)}
}

# --- 3. FUNÇÕES TÉCNICAS ---
def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def gerar_modelo_excel():
    output = io.BytesIO()
    colunas = ["Escola", "Turma", "Nome"] + [f"Q{i:02d}" for i in range(1, 23)]
    df_m = pd.DataFrame([["Escola A", "9º A", "Aluno Teste"] + ["C"]*22], columns=colunas)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_m.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. INTERFACE ---
st.title("🏛️ Sistema de Monitoramento TRI - José de Freitas")

st.sidebar.header("Painel de Controle")
st.sidebar.download_button("📥 Baixar Planilha Modelo", gerar_modelo_excel(), "modelo_gestao.xlsx", use_container_width=True)

disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática"])
serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

uploaded_file = st.file_uploader("📂 Carregar Planilha Preenchida", type="xlsx")

if uploaded_file:
    # Garante a leitura e preenche vazios com 'X'
    df = pd.read_excel(uploaded_file).fillna("X")
    
    # FORÇAR ORDEM DAS QUESTÕES DE 01 A 22
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito = GABARITOS[disciplina]

    # Processamento TRI Individual
    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    # --- FILTROS DE VISUALIZAÇÃO ---
    st.sidebar.divider()
    st.sidebar.subheader("Filtros de Análise")
    esc_sel = st.sidebar.selectbox("Escola:", ["Geral"] + sorted(list(df['Escola'].unique())))
    
    df_esc = df if esc_sel == "Geral" else df[df['Escola'] == esc_sel]
    tur_sel = st.sidebar.selectbox("Turma:", ["Geral"] + sorted(list(df_esc['Turma'].unique())))
    
    df_f = df_esc if tur_sel == "Geral" else df_esc[df_esc['Turma'] == tur_sel]

    # --- RESULTADOS MÉDIOS ---
    media_f = df_f['Proficiência'].mean()
    st.subheader(f"📊 Resultados: {esc_sel} - {tur_sel}")
    st.metric("Proficiência Média (TRI)", f"{media_f:.1f}")

    # --- GRÁFICOS DE DISTRATORES (QUESTÃO 1 A 22) ---
    st.markdown("### 🎯 Análise de Respostas por Item (A, B, C, D)")
    st.info("O gráfico abaixo mostra a porcentagem de alunos que escolheram cada letra. A barra verde indica o gabarito.")

    # Criar 3 colunas para os gráficos ficarem organizados
    grid = st.columns(3)
    
    for i, q in enumerate(cols_q): # Segue a ordem exata da lista cols_q (Q01 a Q22)
        with grid[i % 3]:
            # Conta as marcações e converte para porcentagem
            analise = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
            
            fig, ax = plt.subplots(figsize=(4, 5))
            cores = ['#2ECC71' if letra == gabarito[q] else '#E74C3C' for letra in ['A','B','C','D']]
            
            bars = ax.bar(['A','B','C','D'], analise, color=cores, edgecolor='black', alpha=0.8)
            ax.set_title(f"Questão {q}", fontsize=12, fontweight='bold')
            ax.set_ylabel("% de Alunos")
            ax.set_ylim(0, 105)
            
            # Adiciona o rótulo de % no topo de cada barra
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:.0f}%', ha='center', va='bottom', fontsize=9)
            
            st.pyplot(fig)
            st.caption(f"**Gabarito: {gabarito[q]}** | {MAPA_HABILIDADES[disciplina][q]['desc']}")
            st.divider()

    # --- BOTÃO DE PDF ---
    if st.button("📄 GERAR RELATÓRIO PDF DA SELEÇÃO", use_container_width=True):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'Relatório Pedagógico - {esc_sel}', ln=True, align='C')
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Turma: {tur_sel} | Média TRI: {media_f:.1f}', ln=True, align='C')
        pdf.ln(10)

        for q in cols_q:
            perc_acerto = (df_f[q].str.upper() == gabarito[q]).mean() * 100
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, f"Questão {q} - Acerto: {perc_acerto:.1f}%", ln=True)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, f"Habilidade: {MAPA_HABILIDADES[disciplina][q]['desc']}")
            pdf.ln(3)
            if pdf.get_y() > 250: pdf.add_page()
            
        pdf_out = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_out).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_{esc_sel}.pdf" style="display:block; text-align:center; padding:12px; background-color:#2e7bcf; color:white; border-radius:8px; text-decoration:none; font-weight:bold;">📥 BAIXAR RELATÓRIO PDF</a>', unsafe_allow_html=True)
