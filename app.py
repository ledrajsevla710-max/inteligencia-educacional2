import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import os

# --- 1. CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="SAEPI JF - TRI System", layout="wide")

# Parâmetros TRI (Curva Logística 3PL simulada para 22 itens)
PARAMETROS_TRI = {
    f'Q{i:02d}': {'a': 1.5, 'b': np.linspace(-2, 2, 22)[i-1], 'c': 0.2} 
    for i in range(1, 23)
}

GABARITOS = {
    "Matemática": {f'Q{i:02d}': g for i, g in enumerate(['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B'], 1)},
    "Língua Portuguesa": {f'Q{i:02d}': g for i, g in enumerate(['A','D','B','C','A','D','B','C','B','A','D','C','B','A','D','C','B','B','A','D','C','A'], 1)}
}

# Sugestões de Melhoria por Disciplina (Aparecerão no PDF)
SUGESTOES = {
    "Matemática": "Reforçar o uso de materiais concretos (Ábaco/Material Dourado) para Sistema de Numeração e focar em resolução de problemas de campo multiplicativo.",
    "Língua Portuguesa": "Ampliar a leitura de gêneros diversos e trabalhar a localização de informações explícitas e inferência de sentido em textos curtos."
}

# --- 2. FUNÇÕES MATEMÁTICAS ---
def prob_acerto(theta, a, b, c):
    return c + (1 - c) / (1 + np.exp(-1.7 * a * (theta - b)))

def calcular_proficiencia_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.zeros_like(thetas)
    for i, theta in enumerate(thetas):
        prob_total = 1.0
        for q, acerto in respostas_binarias.items():
            p = prob_acerto(theta, PARAMETROS_TRI[q]['a'], PARAMETROS_TRI[q]['b'], PARAMETROS_TRI[q]['c'])
            prob_total *= p if acerto == 1 else (1 - p)
        verossimilhanca[i] = prob_total
    theta_final = thetas[np.argmax(verossimilhanca)]
    return (theta_final + 4) * 50

def obter_nivel(score):
    if score < 150: return "Abaixo do Básico", "#FF4B4B"
    if score < 200: return "Básico", "#FACA2E"
    if score < 250: return "Proficiente", "#00CC96"
    return "Avançado", "#1F77B4"

def gerar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- 3. INTERFACE ---
st.title("📊 SAEPI José de Freitas - Inteligência TRI")
st.markdown("---")

disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

if st.sidebar.button("📂 Gerar Planilha de Teste"):
    data = {"Nome": [f"Aluno {i}" for i in range(1, 11)], "Escola": ["Semed JF"]*10}
    for i in range(1, 23): data[f'Q{i:02d}'] = np.random.choice(['A','B','C','D'], 10)
    st.sidebar.download_button("⬇️ Baixar Modelo", gerar_excel(pd.DataFrame(data)), "modelo_saepi.xlsx")

uploaded_file = st.file_uploader("Suba o arquivo Excel dos alunos", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito_atual = GABARITOS[disciplina]

    for index, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito_atual[q] else 0 for q in cols_q}
        df.at[index, 'Proficiência'] = calcular_proficiencia_tri(binario)

    media_geral = df['Proficiência'].mean()
    nivel_txt, cor_nivel = obter_nivel(media_geral)

    # Gráfico Geral
    acertos_pct = [(df[q].str.upper() == gabarito_atual[q]).mean() * 100 for q in cols_q]
    fig_geral, ax_geral = plt.subplots(figsize=(10, 4))
    ax_geral.bar(cols_q, acertos_pct, color='#1F77B4', width=0.4)
    ax_geral.set_ylim(0, 100)
    ax_geral.set_title("Percentual de Acerto por Item")
    st.pyplot(fig_geral)

    # --- 4. BOTÃO DE PDF (CORREÇÃO DEFINITIVA) ---
    if st.button("📄 GERAR RELATÓRIO PEDAGÓGICO COMPLETO", use_container_width=True):
        # SALVANDO O GRÁFICO COMO ARQUIVO REAL PARA EVITAR O ERRO ATTRIBUTERROR
        temp_img = "grafico_temp.png"
        fig_geral.savefig(temp_img, format='png', bbox_inches='tight')

        pdf = FPDF()
        pdf.add_page()
        
        # Cabeçalho Blue
        pdf.set_fill_color(31, 119, 180); pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 20, 'SAEPI JF - RELATÓRIO PEDAGÓGICO TRI', 0, 1, 'C')
        pdf.set_font('Arial', '', 12); pdf.cell(0, 5, f'{disciplina} - {serie}', 0, 1, 'C')
        
        pdf.ln(20); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f"Proficiência Média: {media_geral:.1f} ({nivel_txt})", ln=True)
        
        # Inserindo imagem do arquivo salvo
        pdf.image(temp_img, x=10, y=pdf.get_y()+5, w=190)
        pdf.ln(85)
        
        # Sugestões de Melhoria
        pdf.set_fill_color(230, 240, 255); pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, " PLANO DE INTERVENÇÃO SUGERIDO", 0, 1, 'L', True)
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 8, SUGESTOES[disciplina])
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, " ITENS CRÍTICOS (ABAIXO DE 50%)", ln=True)
        pdf.set_font('Arial', '', 10)
        for q in cols_q:
            p = (df[q].str.upper() == gabarito_atual[q]).mean() * 100
            if p < 50: pdf.cell(0, 7, f"Item {q}: {p:.1f}% acertos. Reforçar Habilidade (Gab: {gabarito_atual[q]}).", ln=True)

        # Gerar Download
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_SAEPI_JF.pdf" style="display:block; text-align:center; padding:15px; background-color:#2e7bcf; color:white; border-radius:10px; text-decoration:none; font-weight:bold;">⬇️ BAIXAR RELATÓRIO AGORA</a>', unsafe_allow_html=True)
        
        # Limpar arquivo temporário
        if os.path.exists(temp_img):
            os.remove(temp_img)

    # --- 5. DIAGNÓSTICO DE DISTRATORES NA TELA ---
    st.markdown("---")
    grid = st.columns(3)
    for i, q in enumerate(cols_q):
        with grid[i % 3]:
            contagem = df[q].str.upper().value_counts(normalize=True).sort_index() * 100
            st.write(f"**Questão {q}** (Gabarito: {gabarito_atual[q]})")
            fig_q, ax_q = plt.subplots(figsize=(4, 5))
            cores = ['#00CC96' if alt == gabarito_atual[q] else '#FF4B4B' for alt in ['A', 'B', 'C', 'D']]
            ax_q.bar(['A', 'B', 'C', 'D'], [contagem.get(a, 0) for a in ['A', 'B', 'C', 'D']], color=cores, width=0.3)
            st.pyplot(fig_q)

else:
    st.info("Aguardando planilha...")
