import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Gestão TRI José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. BANCO DE GABARITOS POR SÉRIE ---
# Aqui você pode ajustar as letras conforme o gabarito oficial de cada ano
GABARITOS_MESTRE = {
    "2º Ano": ['A','B','C','A','D','B','C','A','B','C','A','B','C','D','A','B','C','A','D','B','C','A'],
    "5º Ano": ['B','C','A','D','B','C','A','B','C','D','A','B','C','A','D','B','C','A','B','C','D','A'],
    "9º Ano": ['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B']
}

MAPA_HABILIDADES = {
    f"Q{i:02d}": {"desc": f"Habilidade avaliada no item {i}", "sugestao": "Trabalhar descritores críticos."} for i in range(1, 23)
}

# --- 3. FUNÇÕES TÉCNICAS ---
def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        # Curva de resposta ao item simplificada para o monitoramento
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def gerar_modelo_excel():
    output = io.BytesIO()
    colunas = ["Escola", "Turma", "Nome"] + [f"Q{i:02d}" for i in range(1, 23)]
    df_m = pd.DataFrame([["Escola Exemplo", "Turma A", "Nome do Aluno"] + ["A"]*22], columns=colunas)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_m.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. INTERFACE ---
st.title("🏛️ Monitoramento Educacional TRI - José de Freitas")

st.sidebar.header("⚙️ Configurações da Avaliação")
serie_sel = st.sidebar.selectbox("Selecione a Série:", ["2º Ano", "5º Ano", "9º Ano"])
disciplina = st.sidebar.selectbox("Disciplina:", ["Matemática"])

st.sidebar.divider()
st.sidebar.download_button("📥 Baixar Planilha Modelo", gerar_modelo_excel(), f"modelo_{serie_sel}.xlsx", use_container_width=True)

uploaded_file = st.file_uploader(f"📂 Envie a Planilha do {serie_sel}", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    
    # Busca o gabarito dinâmico conforme a série escolhida
    lista_gabarito = GABARITOS_MESTRE[serie_sel]
    gabarito_dict = {f'Q{i:02d}': lista_gabarito[i-1] for i in range(1, 23)}

    # Cálculo TRI
    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito_dict[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    # Filtros Dinâmicos
    st.sidebar.subheader("🔍 Filtros de Relatório")
    esc_sel = st.sidebar.selectbox("Escola:", ["Rede Municipal (Geral)"] + sorted(list(df['Escola'].unique())))
    df_esc = df if esc_sel == "Rede Municipal (Geral)" else df[df['Escola'] == esc_sel]
    
    tur_sel = st.sidebar.selectbox("Turma:", ["Todas as Turmas"] + sorted(list(df_esc['Turma'].unique())))
    df_f = df_esc if tur_sel == "Todas as Turmas" else df_esc[df_esc['Turma'] == tur_sel]

    # Dashboard
    m_tri = df_f['Proficiência'].mean()
    st.subheader(f"📊 Análise: {serie_sel} | {esc_sel}")
    st.metric("Proficiência Média TRI", f"{m_tri:.1f}")

    # --- GRÁFICOS DE DISTRATORES ---
    st.markdown("### 🎯 Desempenho por Item (1 a 22)")
    grid = st.columns(3)
    
    for i, q in enumerate(cols_q):
        with grid[i % 3]:
            # Cálculo de % para o gráfico
            stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
            
            fig, ax = plt.subplots(figsize=(4, 5))
            gab_atual = gabarito_dict[q]
            cores = ['#2ECC71' if letra == gab_atual else '#E74C3C' for letra in ['A','B','C','D']]
            
            bars = ax.bar(['A','B','C','D'], stats, color=cores, edgecolor='black')
            ax.set_ylim(0, 110)
            ax.set_title(f"Questão {q} (Gab: {gab_atual})", fontweight='bold')
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:.0f}%', ha='center', va='bottom')
            
            st.pyplot(fig)
            st.divider()

    # --- RELATÓRIO PDF COM DISTRATORES ---
    if st.button("📄 GERAR RELATÓRIO PEDAGÓGICO COMPLETO", use_container_width=True):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'RELATÓRIO TÉCNICO PEDAGÓGICO - TRI', ln=True, align='C')
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Município de José de Freitas - {serie_sel}', ln=True, align='C')
        pdf.cell(0, 10, f'Escola: {esc_sel} | Turma: {tur_sel}', ln=True, align='C')
        pdf.ln(10)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ANÁLISE DETALHADA POR ITEM:', ln=True)
        pdf.ln(2)

        for q in cols_q:
            stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
            gab = gabarito_dict[q]
            acerto = stats[gab]
            
            pdf.set_font('Arial', 'B', 11)
            status = "CONSOLIDADO" if acerto > 70 else "EM DESENVOLVIMENTO" if acerto > 40 else "ALERTA CRÍTICO"
            pdf.cell(0, 8, f"Questão {q} | Gabarito: {gab} | Acerto: {acerto:.1f}% ({status})", ln=True)
            
            pdf.set_font('Arial', '', 10)
            # Incluindo a porcentagem de cada distrator no PDF
            pdf.cell(0, 6, f"Distratores: A: {stats['A']:.0f}% | B: {stats['B']:.0f}% | C: {stats['C']:.0f}% | D: {stats['D']:.0f}%", ln=True)
            pdf.multi_cell(0, 5, f"Habilidade: {MAPA_HABILIDADES[q]['desc']}")
            pdf.ln(4)
            
            if pdf.get_y() > 250: pdf.add_page()

        pdf_output = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_output).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_{serie_sel}_{esc_sel}.pdf" style="display:block; text-align:center; padding:15px; background-color:#2ecc71; color:white; border-radius:10px; text-decoration:none; font-weight:bold;">📥 BAIXAR RELATÓRIO PEDAGÓGICO</a>', unsafe_allow_html=True)
