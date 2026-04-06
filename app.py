import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestão TRI José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. BANCO DE DADOS DE HABILIDADES DETALHADAS (MATEMÁTICA) ---
# Aqui estão os descritores reais para o 9º ano (SAEB/BNCC) como base
DICIONARIO_HABILIDADES = {
    "Q01": "D6 - Identificar ângulos como mudança de direção ou giros, reconhecendo ângulos retos e não retos.",
    "Q02": "EF06MA27 - Determinar medidas de ângulos de polígonos convexos e classificar ângulos (agudo, reto, obtuso).",
    "Q03": "EF06MA26 - Resolver problemas que envolvam a noção de ângulo em diferentes contextos.",
    "Q04": "D16 - Identificar a localização de números inteiros na reta numérica.",
    "Q05": "D20 - Resolver problemas com números inteiros envolvendo as operações (adição, subtração).",
    "Q06": "EF07MA04 - Resolver e elaborar problemas que envolvam operações com números inteiros (multiplicação e divisão).",
    "Q07": "D21 - Reconhecer as diferentes representações de um número racional (fração e decimal).",
    "Q08": "D23 - Identificar frações equivalentes.",
    "Q09": "D26 - Resolver problemas com números racionais envolvendo as quatro operações fundamentais.",
    "Q10": "EF07MA10 - Comparar e ordenar números racionais em diferentes contextos.",
    "Q11": "EF07MA01 - Calcular a raiz quadrada exata de um número racional.",
    "Q12": "D19 - Resolver problemas com números naturais, envolvendo potenciação.",
    "Q13": "D6 - Reconhecer ângulos em situações do cotidiano (ponteiros de relógio, esquinas).",
    "Q14": "D16 - Relacionar números inteiros a situações de saldo bancário ou temperatura.",
    "Q15": "D21 - Identificar a escrita decimal de frações com denominadores 10, 100 ou 1000.",
    "Q16": "D23 - Simplificar frações para encontrar a forma irredutível.",
    "Q17": "D26 - Resolver problemas envolvendo valores monetários (números decimais).",
    "Q18": "EF07MA01 - Resolver situações-problema que envolvam o cálculo de MMC e MDC.",
    "Q19": "D20 - Aplicar regras de sinais em expressões numéricas com números inteiros.",
    "Q20": "EF06MA27 - Analisar a abertura de ângulos em figuras geométricas.",
    "Q21": "D21 - Converter números decimais finitos em frações e vice-versa.",
    "Q22": "D26 - Calcular porcentagens simples a partir de números racionais."
}

GABARITOS_MESTRE = {
    "2º Ano": ['A','B','C','A','D','B','C','A','B','C','A','B','C','D','A','B','C','A','D','B','C','A'],
    "5º Ano": ['B','C','A','D','B','C','A','B','C','D','A','B','C','A','D','B','C','A','B','C','D','A'],
    "9º Ano": ['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B']
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

# --- 4. INTERFACE ---
st.title("🏛️ Sistema de Gestão Pedagógica TRI - José de Freitas")

st.sidebar.header("Configuração da Avaliação")
serie_sel = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])
uploaded_file = st.file_uploader(f"📂 Envie a Planilha do {serie_sel}", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    lista_gab = GABARITOS_MESTRE[serie_sel]
    gabarito_dict = {f'Q{i:02d}': lista_gab[i-1] for i in range(1, 23)}

    # Processamento TRI
    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito_dict[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    # Filtros
    st.sidebar.subheader("Filtros de Visão")
    esc_sel = st.sidebar.selectbox("Escola:", ["Geral"] + sorted(list(df['Escola'].unique())))
    df_esc = df if esc_sel == "Geral" else df[df['Escola'] == esc_sel]
    tur_sel = st.sidebar.selectbox("Turma:", ["Todas"] + sorted(list(df_esc['Turma'].unique())))
    df_f = df_esc if tur_sel == "Todas" else df_esc[df_esc['Turma'] == tur_sel]

    st.subheader(f"📊 Dashboard: {serie_sel} | {esc_sel} | {tur_sel}")
    st.metric("Média de Proficiência", f"{df_f['Proficiência'].mean():.1f}")

    # --- GRÁFICOS COM HABILIDADES DETALHADAS ---
    st.markdown("### 🎯 Análise por Item")
    grid = st.columns(2) # Duas colunas para dar mais espaço ao texto da habilidade
    
    for i, q in enumerate(cols_q):
        with grid[i % 2]:
            stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
            fig, ax = plt.subplots(figsize=(6, 4))
            gab_atual = gabarito_dict[q]
            cores = ['#2ECC71' if l == gab_atual else '#E74C3C' for l in ['A','B','C','D']]
            
            bars = ax.bar(['A','B','C','D'], stats, color=cores, edgecolor='black')
            ax.set_ylim(0, 110)
            ax.set_title(f"Questão {q} (Gabarito: {gab_atual})", fontweight='bold', fontsize=14)
            
            for bar in bars:
                h = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., h + 1, f'{h:.0f}%', ha='center', va='bottom', fontweight='bold')
            
            st.pyplot(fig)
            # EXIBIÇÃO DA HABILIDADE DETALHADA NA TELA
            st.warning(f"**Habilidade:** {DICIONARIO_HABILIDADES[q]}")
            st.divider()

    # --- RELATÓRIO PDF PROFISSIONAL ---
    if st.button("📄 GERAR RELATÓRIO PEDAGÓGICO COMPLETO", use_container_width=True):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'RELATÓRIO TÉCNICO PEDAGÓGICO - TRI', ln=True, align='C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 7, f'Série: {serie_sel} | Escola: {esc_sel} | Turma: {tur_sel}', ln=True, align='C')
        pdf.ln(10)

        for q in cols_q:
            stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
            gab = gabarito_dict[q]
            acerto = stats[gab]
            
            pdf.set_font('Arial', 'B', 11)
            cor_alerta = "CRÍTICO" if acerto < 40 else "ATENÇÃO" if acerto < 70 else "CONSOLIDADO"
            pdf.cell(0, 8, f"Questão {q} | Gabarito: {gab} | Acerto: {acerto:.1f}% ({cor_alerta})", ln=True)
            
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 6, f"Respostas: A: {stats['A']:.0f}% | B: {stats['B']:.0f}% | C: {stats['C']:.0f}% | D: {stats['D']:.0f}%", ln=True)
            
            # TEXTO DA HABILIDADE NO PDF
            pdf.set_font('Arial', 'I', 9)
            pdf.multi_cell(0, 5, f"Habilidade Detalhada: {DICIONARIO_HABILIDADES[q]}")
            pdf.ln(5)
            
            if pdf.get_y() > 250: pdf.add_page()

        pdf_out = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_out).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_Final.pdf" style="display:block; text-align:center; padding:15px; background-color:#2ecc71; color:white; border-radius:10px; text-decoration:none; font-weight:bold;">📥 BAIXAR RELATÓRIO PEDAGÓGICO</a>', unsafe_allow_html=True)
