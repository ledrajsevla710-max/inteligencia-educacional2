import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SAEPI JF - TRI System", layout="wide")

# --- PARÂMETROS TRI REAIS (SIMULADOS PARA 22 ITENS) ---
# b = dificuldade, a = discriminação, c = chute
PARAMETROS_TRI = {
    f'Q{i:02d}': {'a': 1.5, 'b': np.linspace(-2, 2, 22)[i-1], 'c': 0.2} 
    for i in range(1, 23)
}

GABARITOS = {
    "Matemática": {f'Q{i:02d}': g for i, g in enumerate(['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B'], 1)},
    "Língua Portuguesa": {f'Q{i:02d}': g for i, g in enumerate(['A','D','B','C','A','D','B','C','B','A','D','C','B','A','D','C','B','B','A','D','C','A'], 1)}
}

# --- FUNÇÃO MATEMÁTICA DA CURVA TRI (LOGÍSTICA 3PL) ---
def prob_acerto(theta, a, b, c):
    """Fórmula da Curva Característica do Item: P(theta)"""
    return c + (1 - c) / (1 + np.exp(-1.7 * a * (theta - b)))

def calcular_proficiencia_tri(respostas_binarias):
    """Estima o Theta (Proficiência) por Máxima Verossimilhança Simples"""
    thetas = np.linspace(-4, 4, 100) # Escala padrão TRI
    verossimilhanca = np.zeros_like(thetas)
    
    for i, theta in enumerate(thetas):
        prob_total = 1.0
        for q, acerto in respostas_binarias.items():
            p = prob_acerto(theta, PARAMETROS_TRI[q]['a'], PARAMETROS_TRI[q]['b'], PARAMETROS_TRI[q]['c'])
            prob_total *= p if acerto == 1 else (1 - p)
        verossimilhanca[i] = prob_total
    
    theta_final = thetas[np.argmax(verossimilhanca)]
    # Converte escala -4 a 4 para escala SAEB 0 a 400
    return (theta_final + 4) * 50

def obter_nivel(score):
    if score < 150: return "Abaixo do Básico", "#FF4B4B"
    if score < 200: return "Básico", "#FACA2E"
    if score < 250: return "Proficiente", "#00CC96"
    return "Avançado", "#1F77B4"

# --- INTERFACE PRINCIPAL ---
st.title("📊 SAEPI José de Freitas - Inteligência TRI")
st.subheader("Avaliação Diagnóstica Integrada")

# Sidebar
st.sidebar.header("Menu de Controle")
disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

# Botão de Planilha Exemplo
if st.sidebar.button("📂 Gerar Planilha de Teste"):
    data = {"Nome": [f"Aluno {i}" for i in range(1, 11)], "Escola": ["Semed JF"]*10}
    for i in range(1, 23): data[f'Q{i:02d}'] = np.random.choice(['A','B','C','D'], 10)
    df_fake = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_fake.to_excel(writer, index=False)
    st.sidebar.download_button("⬇️ Baixar Exemplo", output.getvalue(), "modelo_saepi.xlsx")

uploaded_file = st.file_uploader("Suba o arquivo Excel dos alunos", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito = GABARITOS[disciplina]

    # Processamento TRI
    for index, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito[q] else 0 for q in cols_q}
        df.at[index, 'Proficiência'] = calcular_proficiencia_tri(binario)

    media_geral = df['Proficiência'].mean()
    nivel_txt, cor_nivel = obter_nivel(media_geral)

    # Gráficos
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Proficiência Média (Escala TRI)", f"{media_geral:.1f}")
        st.markdown(f"<h2 style='color:{cor_nivel};'>{nivel_txt}</h2>", unsafe_allow_html=True)
        
        # Exportar Excel Processado
        out_ex = io.BytesIO()
        with pd.ExcelWriter(out_ex, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📊 Baixar Excel com Notas TRI", out_ex.getvalue(), "resultados_tri.xlsx")

    with col2:
        acertos_serie = [(df[q].str.upper() == gabarito[q]).mean() * 100 for q in cols_q]
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(cols_q, acertos_serie, color='#1F77B4', width=0.3)
        ax.set_ylim(0, 100)
        ax.set_title("Percentual de Acerto por Item")
        st.pyplot(fig)

    # --- BOTÃO DE RELATÓRIO PDF COM GRÁFICO ---
    st.markdown("---")
    if st.button("📄 GERAR RELATÓRIO PEDAGÓGICO COMPLETO", use_container_width=True):
        # Salva gráfico para o PDF
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png', bbox_inches='tight')
        img_buf.seek(0)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(31, 119, 180); pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 20, 'SAEPI JF - RELATÓRIO TRI', 0, 1, 'C')
        pdf.set_font('Arial', '', 12); pdf.cell(0, 5, f'{disciplina} - {serie}', 0, 1, 'C')
        
        pdf.ln(20); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f"Proficiência Média: {media_geral:.1f} - {nivel_txt}", ln=True)
        
        pdf.image(img_buf, x=10, y=pdf.get_y()+5, w=190)
        pdf.ln(80)
        
        pdf.set_fill_color(240, 240, 240); pdf.cell(0, 10, " ANÁLISE DE DISTRATORES (ITENS CRÍTICOS)", 0, 1, 'L', True)
        pdf.set_font('Arial', '', 9)
        for q in cols_q:
            p = (df[q].str.upper() == gabarito[q]).mean() * 100
            if p < 50: pdf.cell(0, 7, f"Item {q}: {p:.1f}% acertos. Revisar habilidade do gabarito {gabarito[q]}.", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_TRI.pdf" style="display:block; text-align:center; padding:20px; background-color:#2e7bcf; color:white; border-radius:10px; text-decoration:none;">💾 CLIQUE AQUI PARA SALVAR O PDF</a>', unsafe_allow_html=True)

    # Detalhamento de Alternativas na tela
    st.markdown("### 🎯 Análise por Alternativa")
    cols = st.columns(4)
    for i, q in enumerate(cols_q):
        with cols[i%4]:
            st.write(f"**Questão {q}** (Gabarito: {gabarito[q]})")
            st.bar_chart(df[q].str.upper().value_counts())

else:
    st.info("Aguardando planilha...")
