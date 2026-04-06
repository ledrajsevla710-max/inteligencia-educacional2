import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io

# --- 1. CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="SAEPI JF - Sistema TRI", layout="wide")

# Parâmetros TRI (Curva Logística 3PL simulada para 22 itens)
PARAMETROS_TRI = {
    f'Q{i:02d}': {'a': 1.5, 'b': np.linspace(-2, 2, 22)[i-1], 'c': 0.2} 
    for i in range(1, 23)
}

GABARITOS = {
    "Matemática": {f'Q{i:02d}': g for i, g in enumerate(['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B'], 1)},
    "Língua Portuguesa": {f'Q{i:02d}': g for i, g in enumerate(['A','D','B','C','A','D','B','C','B','A','D','C','B','A','D','C','B','B','A','D','C','A'], 1)}
}

# --- 2. FUNÇÕES MATEMÁTICAS (TRI E UTILITÁRIOS) ---
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
    return (theta_final + 4) * 50  # Escala 0-400

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

# --- 3. INTERFACE STREAMLIT ---
st.title("📊 SAEPI José de Freitas - Inteligência TRI")
st.markdown("---")

# Menu Lateral
disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

if st.sidebar.button("📂 Gerar Planilha de Teste"):
    data = {"Nome": [f"Aluno {i}" for i in range(1, 11)], "Escola": ["Semed JF"]*10}
    for i in range(1, 23): data[f'Q{i:02d}'] = np.random.choice(['A','B','C','D'], 10)
    df_fake = pd.DataFrame(data)
    st.sidebar.download_button("⬇️ Baixar Modelo", gerar_excel(df_fake), "modelo_saepi.xlsx")

uploaded_file = st.file_uploader("Suba o arquivo Excel dos alunos", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito_atual = GABARITOS[disciplina]

    # Processamento dos dados
    for index, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito_atual[q] else 0 for q in cols_q}
        df.at[index, 'Proficiência'] = calcular_proficiencia_tri(binario)

    media_geral = df['Proficiência'].mean()
    nivel_txt, cor_nivel = obter_nivel(media_geral)

    # Dashboard de Resumo
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Proficiência Média TRI", f"{media_geral:.1f}")
        st.markdown(f"<div style='background-color:{cor_nivel}; padding:20px; border-radius:10px; color:white; text-align:center;'><h3>{nivel_txt}</h3></div>", unsafe_allow_html=True)
        st.download_button("📊 Baixar Resultados (Excel)", gerar_excel(df), "resultados_saepi.xlsx")

    with c2:
        # Gráfico Geral de Acertos
        acertos_pct = [(df[q].str.upper() == gabarito_atual[q]).mean() * 100 for q in cols_q]
        fig_geral, ax_geral = plt.subplots(figsize=(10, 4))
        ax_geral.bar(cols_q, acertos_pct, color='#1F77B4', width=0.4)
        ax_geral.set_ylim(0, 100)
        ax_geral.set_title("Percentual de Acerto por Item")
        st.pyplot(fig_geral)

    # --- 4. DIAGNÓSTICO DE DISTRATORES (BARRAS FINAS E CORES) ---
    st.markdown("---")
    st.subheader("🎯 Diagnóstico de Distratores (Alternativas)")
    
    grid = st.columns(3)
    for i, q in enumerate(cols_q):
        with grid[i % 3]:
            # Estatísticas da questão
            contagem = df[q].str.upper().value_counts(normalize=True).sort_index() * 100
            acerto_q = contagem.get(gabarito_atual[q], 0)
            erro_q = 100 - acerto_q
            
            st.write(f"**Questão {q}** (Gab: :green[{gabarito_atual[q]}])")
            st.write(f"✅ {acerto_q:.1f}% | ❌ Erro: {erro_q:.1f}%")
            
            # Gráfico de barras finas coloridas
            fig_q, ax_q = plt.subplots(figsize=(4, 5))
            cores = ['#00CC96' if alt == gabarito_atual[q] else '#FF4B4B' for alt in ['A', 'B', 'C', 'D']]
            valores = [contagem.get(alt, 0) for alt in ['A', 'B', 'C', 'D']]
            
            bars = ax_q.bar(['A', 'B', 'C', 'D'], valores, color=cores, width=0.3)
            ax_q.set_ylim(0, 110)
            
            for bar in bars:
                h = bar.get_height()
                ax_q.text(bar.get_x() + bar.get_width()/2, h + 2, f'{h:.0f}%', ha='center', fontsize=9)
            
            st.pyplot(fig_q)
            st.write("---")

    # --- 5. BOTÃO DE RELATÓRIO PDF ---
    if st.button("📄 GERAR RELATÓRIO PEDAGÓGICO COMPLETO", use_container_width=True):
        img_buf = io.BytesIO()
        fig_geral.savefig(img_buf, format='png', bbox_inches='tight')
        img_buf.seek(0)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(31, 119, 180); pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 20, 'SAEPI JF - RELATÓRIO PEDAGÓGICO', 0, 1, 'C')
        pdf.set_font('Arial', '', 12); pdf.cell(0, 5, f'{disciplina} - {serie}', 0, 1, 'C')
        
        pdf.ln(20); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f"Proficiência Média: {media_geral:.1f} ({nivel_txt})", ln=True)
        
        # Gráfico no PDF corrigido
        pdf.image(img_buf, x=10, y=pdf.get_y()+5, w=190, type='PNG')
        pdf.ln(85)
        
        pdf.set_fill_color(240, 240, 240); pdf.cell(0, 10, " ITENS CRÍTICOS (ABAIXO DE 50% DE ACERTO)", 0, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
        for q in cols_q:
            p = (df[q].str.upper() == gabarito_atual[q]).mean() * 100
            if p < 50: pdf.cell(0, 8, f"Item {q}: {p:.1f}% de acertos. Habilidade crítica (Gabarito {gabarito_atual[q]}).", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_SAEPI.pdf" style="display:block; text-align:center; padding:15px; background-color:#2e7bcf; color:white; border-radius:8px; text-decoration:none;">💾 BAIXAR RELATÓRIO EM PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

else:
    st.info("Aguardando upload da planilha Excel...")
