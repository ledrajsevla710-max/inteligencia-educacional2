import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64

st.set_page_config(page_title="SAEPI - Inteligência Educacional", layout="wide", page_icon="🎓")

# --- MOTOR TRI AVANÇADO (MODELO 2PL) ---
def calcular_score_tri(respostas, parametros):
    if not any(respostas): return 0.0
    theta = 0.0
    for _ in range(25):
        p_acerto = [1 / (1 + np.exp(-p['a'] * (theta - p['b']))) for p in parametros]
        erro = sum(respostas) - sum(p_acerto)
        theta += erro * 0.1
    return max(0, min(1000, (theta * 50) + 250))

# Configuração Padrão de Itens (22 Questões - Dificuldade Crescente)
itens_config = []
for i in range(22):
    if i < 7: itens_config.append({'a': 1.2, 'b': -1.5, 'desc': f'Habilidade Básica {i+1}'})
    elif i < 15: itens_config.append({'a': 1.5, 'b': 0.0, 'desc': f'Habilidade Intermediária {i+1}'})
    else: itens_config.append({'a': 2.0, 'b': 1.8, 'desc': f'Habilidade Avançada {i+1}'})

# --- FUNÇÃO GERADORA DE PDF ---
def gerar_pdf(df_geral, media_mun, alertas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Relatorio de Gestao Educacional - Jose de Freitas", ln=True, align='C')
    
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Media de Proficiencia Municipal: {media_mun:.1f}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Habilidades Criticas (Necessitam de Intervencao):", ln=True)
    pdf.set_font("Arial", '', 11)
    for alerta in alertas:
        pdf.multi_cell(0, 8, f"- {alerta}")

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Desempenho por Unidade Escolar:", ln=True)
    resumo = df_geral.groupby('Escola')['Proficiência_TRI'].mean().reset_index()
    pdf.set_font("Arial", '', 10)
    for _, row in resumo.iterrows():
        pdf.cell(0, 8, f"{row['Escola']}: {row['Proficiência_TRI']:.1f} pontos", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ÚNICA ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3976/3976625.png", width=100)
st.sidebar.title("Portal SAEPI-JF")

# Escolha do Perfil
perfil = st.sidebar.selectbox("Selecione o Perfil", ["👨‍🏫 Professor / Lançamento", "📊 Gestor / Secretaria"])

if perfil == "👨‍🏫 Professor / Lançamento":
    st.header("Lançamento de Resultados")
    sub_menu = st.tabs(["Individual", "Planilha de Turma"])
    
    with sub_menu[0]:
        nome_aluno = st.text_input("Nome do Estudante")
        c1, c2 = st.columns(2)
        esc = c1.text_input("Escola")
        tur = c2.text_input("Turma")
        
        st.write("Marque os acertos (Q01 a Q22):")
        cols = st.columns(4)
        resps = []
        for i in range(1, 23):
            with cols[(i-1)%4]:
                r = st.checkbox(f"Q{i:02d}")
                resps.append(1 if r else 0)
        
        if st.button("Calcular Agora"):
            nota = calcular_score_tri(resps, itens_config)
            st.success(f"Proficiência Estimada: {nota:.1f}")

    with sub_menu[1]:
        st.info("Suba sua planilha com: Escola, Turma, Nome, Q01...Q22")
        arq = st.file_uploader("Upload Excel", type="xlsx", key="prof")
        if arq:
            df_prof = pd.read_excel(arq)
            qs = [f'Q{i:02d}' for i in range(1, 23)]
            df_prof['Proficiência_TRI'] = df_prof[qs].apply(lambda x: calcular_score_tri(x.tolist(), itens_config), axis=1)
            st.dataframe(df_prof[['Nome', 'Proficiência_TRI']])

else: # VISÃO GESTOR
    st.header("Painel de Controle Municipal")
    arq_gestor = st.file_uploader("Upload da Planilha Consolidada", type="xlsx", key="gest")
    
    if arq_gestor:
        df_g = pd.read_excel(arq_gestor)
        qs = [f'Q{i:02d}' for i in range(1, 23)]
        
        if all(c in df_g.columns for c in qs):
            df_g['Proficiência_TRI'] = df_g[qs].apply(lambda x: calcular_score_tri(x.tolist(), itens_config), axis=1)
            
            # Médias
            med_mun = df_g['Proficiência_TRI'].mean()
            st.metric("Média Geral de José de Freitas", f"{med_mun:.1f}")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("### Ranking por Escola")
                st.bar_chart(df_g.groupby('Escola')['Proficiência_TRI'].mean())
            
            with col_b:
                st.write("### Habilidades em Alerta")
                percentuais = df_g[qs].mean() * 100
                criticas = percentuais[percentuais < 50].index.tolist()
                lista_alertas = [f"Habilidade {q}: Alunos apresentam dificuldade (Abaixo de 50% acerto)" for q in criticas]
                for a in lista_alertas[:5]: st.warning(a)

            # PDF
            if st.button("📄 Gerar Relatório PDF
            pdf_bytes = gerar_pdf(df, media_municipio, alertas)
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="Relatorio_Municipal.pdf">Baixar PDF Agora</a>'
            st.markdown(href, unsafe_allow_html=True)
