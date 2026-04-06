import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import os

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestão TRI - Protótipo", layout="wide", page_icon="📊")

# --- 2. MAPA DE HABILIDADES ---
MAPA_HABILIDADES = {
    "Matemática": {
        f"Q{i:02d}": "Habilidade técnica vinculada ao descritor de Matemática." for i in range(1, 23)
    }
}
# Atualizando com as suas habilidades específicas (Exemplos)
MAPA_HABILIDADES["Matemática"].update({
    "Q01": "D6 - Reconhecer ângulos como mudança de direção ou giros.",
    "Q02": "EF06MA27 - Determinar medidas de ângulos (reto, agudo, obtuso).",
    "Q03": "EF06MA26 - Resolver problemas envolvendo noção de ângulo.",
    "Q04": "D16 - Identificar a localização de números inteiros na reta numérica.",
    "Q05": "D20 - Resolver problema com números inteiros (adição/subtração).",
})

GABARITOS = {
    "Matemática": {f'Q{i:02d}': g for i, g in enumerate(['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B'], 1)}
}

# --- 3. FUNÇÕES TÉCNICAS ---
def calcular_tri(respostas_binarias):
    if not respostas_binarias: return 0
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        # Dificuldade progressiva simulada
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel(score):
    if score < 150: return "Abaixo do Básico", "#FF4B4B"
    if score < 200: return "Básico", "#FACA2E"
    if score < 250: return "Proficiente", "#00CC96"
    return "Avançado", "#1F77B4"

def gerar_modelo_excel():
    output = io.BytesIO()
    colunas = ["Escola", "Turma", "Nome"] + [f"Q{i:02d}" for i in range(1, 23)]
    # Criando 5 linhas de exemplo para o gráfico não vir zerado
    dados = []
    for i in range(1, 6):
        linha = ["Escola Municipal Teste", "9º Ano A", f"Aluno Exemplo {i}"] + list(np.random.choice(['A','B','C','D'], 22))
        dados.append(linha)
    
    df_m = pd.DataFrame(dados, columns=colunas)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_m.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. INTERFACE ---
st.title("📊 Monitoramento Pedagógico TRI")

st.sidebar.header("⚙️ Ferramentas")
st.sidebar.download_button(
    "📥 Baixar Planilha Modelo (Preencher)", 
    gerar_modelo_excel(), 
    "modelo_tri_preencher.xlsx", 
    use_container_width=True
)

disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática"])
serie = st.sidebar.selectbox("Série:", ["9º Ano"])

uploaded_file = st.file_uploader("📂 Suba sua planilha preenchida aqui", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X") # Evita erro com campos vazios
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito = GABARITOS[disciplina]

    # Processamento
    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    # Filtros
    st.divider()
    c_esc, c_tur = st.columns(2)
    escolas = ["Todas"] + sorted(list(df['Escola'].unique()))
    turmas = ["Todas"] + sorted(list(df['Turma'].unique()))
    
    esc_sel = c_esc.selectbox("Escola:", escolas)
    tur_sel = c_tur.selectbox("Turma:", turmas)

    df_f = df.copy()
    if esc_sel != "Todas": df_f = df_f[df_f['Escola'] == esc_sel]
    if tur_sel != "Todas": df_f = df_f[df_f['Turma'] == tur_sel]

    # Dashboard
    media_geral = df_f['Proficiência'].mean()
    nivel_t, cor_t = obter_nivel(media_geral)

    col_m1, col_m2 = st.columns([1, 3])
    with col_m1:
        st.metric("Proficiência Média", f"{media_geral:.1f}")
        st.markdown(f"<div style='background-color:{cor_t}; padding:15px; border-radius:10px; color:white; text-align:center; font-weight:bold;'>{nivel_t}</div>", unsafe_allow_html=True)
    
    with col_m2:
        # Gráfico de Acertos por Item
        acertos = [(df_f[q].str.upper() == gabarito[q]).mean() * 100 for q in cols_q]
        fig, ax = plt.subplots(figsize=(10, 3.5))
        ax.bar(cols_q, acertos, color='#1F77B4', alpha=0.8)
        ax.set_ylim(0, 100)
        ax.set_ylabel("% de Acerto")
        st.pyplot(fig)

    # Botão PDF
    if st.button("📄 Gerar Relatório PDF Detalhado", use_container_width=True):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'RELATÓRIO TRI - {esc_sel} / {tur_sel}', ln=True, align='C')
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 10, f'Média de Proficiência: {media_geral:.1f} - Nível: {nivel_t}', ln=True)
        pdf.ln(5)

        for q in cols_q:
            perc_q = (df_f[q].str.upper() == gabarito[q]).mean() * 100
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 7, f"Item {q} | Gab: {gabarito[q]} | Acerto: {perc_q:.1f}%", ln=True)
            pdf.set_font('Arial', 'I', 9)
            pdf.multi_cell(0, 5, f"Habilidade: {MAPA_HABILIDADES[disciplina].get(q, 'Não cadastrada')}")
            pdf.ln(2)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_TRI.pdf" style="display:block; text-align:center; padding:10px; background-color:#2e7bcf; color:white; border-radius:5px; text-decoration:none;">📥 BAIXAR PDF</a>', unsafe_allow_html=True)

else:
    st.warning("⚠️ Por favor, suba uma planilha com dados para visualizar os gráficos.")
