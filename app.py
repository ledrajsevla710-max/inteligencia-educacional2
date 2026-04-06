import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import os

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Protótipo SAEPI - TRI", layout="wide")

# --- 2. MAPA DE HABILIDADES ---
MAPA_HABILIDADES = {
    "Matemática": {
        "Q01": "D6 - Reconhecer ângulos como mudança de direção ou giros de segmentos de reta.",
        "Q02": "EF06MA27 - Determinar medidas de ângulos (reto, agudo, obtuso) e utilizar transferidor.",
        "Q03": "EF06MA26 - Resolver problemas que envolvam a noção de ângulo em diferentes contextos.",
        "Q04": "D16 - Identificar a localização de números inteiros na reta numérica.",
        "Q05": "D20 - Resolver problemas com números inteiros envolvendo as operações fundamentais.",
        "Q06": "EF07MA04 - Resolver e elaborar problemas que envolvam operações com números inteiros.",
        "Q07": "D21 - Reconhecer as differentes representações de um número racional (fração, decimal, %).",
        "Q08": "D23 - Identificar frações equivalentes a partir de representações gráficas ou numéricas.",
        "Q09": "D26 - Resolver problemas com números racionais envolvendo as operações fundamentais.",
        "Q10": "EF07MA10 - Comparar e ordenar números racionais em diferentes contextos e na reta.",
        "Q11": "EF07MA01.1PI - Calcular raiz quadrada exata de números naturais.",
        "Q12": "D19 - Resolver problemas com potenciação de números naturais (expoente inteiro).",
        "Q13": "D6/EF06MA25 - Reconhecer giros de uma volta completa (360°) em medidores e ponteiros.",
        "Q14": "D16/EF07MA03 - Comparar e ordenar números inteiros em situações de pontuação/saldo.",
        "Q15": "D21/EF06MA08 - Converter frações usuais (1/2, 1/4, 1/5) para sua representação decimal.",
        "Q16": "D23/EF06MA07 - Reconhecer frações equivalentes por simplificação ou amplificação.",
        "Q17": "D26/EF07MA12 - Operações combinadas entre frações e decimais no cotidiano.",
        "Q18": "D19/EF07MA01 - Resolver problemas envolvendo o Mínimo Múltiplo Comum (MMC).",
        "Q19": "D20/EF07MA04 - Aplicar regra de sinais na divisão de números inteiros.",
        "Q20": "EF06MA27 - Classificar ângulos obtusos (entre 90° e 180°) em figuras ou giros.",
        "Q21": "D21/EF07MA10 - Transformar números decimais finitos em frações decimais.",
        "Q22": "D26/EF06MA03 - Multiplicação de números decimais e posicionamento da vírgula."
    },
    "Língua Portuguesa": {
        "Q01": "D1 - Localizar informações explícitas em textos.",
        "Q02": "D3 - Inferir o sentido de palavra ou expressão."
    }
}

GABARITOS = {
    "Matemática": {f'Q{i:02d}': g for i, g in enumerate(['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B'], 1)},
    "Língua Portuguesa": {f'Q{i:02d}': g for i, g in enumerate(['A','D','B','C','A','D','B','C','B','A','D','C','B','A','D','C','B','B','A','D','C','A'], 1)}
}

# --- 3. FUNÇÕES ---
def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

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

# --- 4. APP ---
st.title("📊 Protótipo de Inteligência Educacional - Matriz TRI")

disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

uploaded_file = st.file_uploader("Suba a planilha Excel", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito_atual = GABARITOS[disciplina]
    mapa_atual = MAPA_HABILIDADES.get(disciplina, {})

    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito_atual[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    media_geral = df['Proficiência'].mean()
    nivel_txt, cor_nivel = obter_nivel(media_geral)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Proficiência Média", f"{media_geral:.1f}")
        st.markdown(f"<div style='background-color:{cor_nivel}; padding:15px; border-radius:10px; color:white; text-align:center;'>{nivel_txt}</div>", unsafe_allow_html=True)
        st.download_button("📊 Baixar Excel", gerar_excel(df), "resultados.xlsx")

    with c2:
        acertos = [(df[q].str.upper() == gabarito_atual[q]).mean() * 100 for q in cols_q]
        fig_g, ax_g = plt.subplots(figsize=(10, 4))
        ax_g.bar(cols_q, acertos, color='#1F77B4', width=0.4)
        ax_g.set_ylim(0, 100)
        st.pyplot(fig_g)

    if st.button("📄 GERAR RELATÓRIO PDF", use_container_width=True):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'RELATÓRIO TÉCNICO DE HABILIDADES - PROTÓTIPO', ln=True, align='C')
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 10, f'Disciplina: {disciplina} | Média: {media_geral:.1f}', ln=True)
        pdf.ln(5)

        for q in cols_q:
            cont = df[q].str.upper().value_counts(normalize=True) * 100
            acerto_q = cont.get(gabarito_atual[q], 0)
            hab = mapa_atual.get(q, "N/A")
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 7, f"Questão {q} (Gab: {gabarito_atual[q]}) - Acerto: {acerto_q:.1f}%", ln=True)
            pdf.set_font('Arial', 'I', 9)
            pdf.multi_cell(0, 5, f"Descritor: {hab}")
            
            # Gráfico lateral no PDF
            fig_p, ax_p = plt.subplots(figsize=(2.5, 1.2))
            cores = ['#00CC96' if a == gabarito_atual[q] else '#FF4B4B' for a in ['A','B','C','D']]
            ax_p.bar(['A','B','C','D'], [cont.get(a, 0) for a in ['A','B','C','D']], color=cores, width=0.3)
            ax_p.set_ylim(0, 100)
            
            p_img = f"t_{q}.png"
            fig_p.savefig(p_img, bbox_inches='tight')
            plt.close(fig_p)
            pdf.image(p_img, x=150, y=pdf.get_y()-12, w=40)
            pdf.ln(10)
            if os.path.exists(p_img): os.remove(p_img)
            if pdf.get_y() > 250: pdf.add_page()

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio.pdf" style="display:block; text-align:center; padding:10px; background-color:#2e7bcf; color:white; border-radius:5px; text-decoration:none;">💾 BAIXAR PDF</a>', unsafe_allow_html=True)

    st.markdown("---")
    grid = st.columns(3)
    for i, q in enumerate(cols_q):
        with grid[i % 3]:
            cont_t = df[q].str.upper().value_counts(normalize=True).sort_index() * 100
            st.write(f"**Item {q}**")
            fig_t, ax_t = plt.subplots(figsize=(4, 5))
            c_t = ['#00CC96' if a == gabarito_atual[q] else '#FF4B4B' for a in ['A','B','C','D']]
            ax_t.bar(['A','B','C','D'], [cont_t.get(a, 0) for a in ['A','B','C','D']], color=c_t, width=0.3)
            st.pyplot(fig_t)
