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

# --- 2. ESCALA DE PROFICIÊNCIA COLORIDA ---
def obter_detalhes_nivel(score):
    if score < 150:
        return {"nivel": "CRÍTICO", "cor": "#E74C3C", "desc": "Desempenho muito baixo. Requer intervenção imediata."}
    elif score < 250:
        return {"nivel": "BÁSICO", "cor": "#F1C40F", "desc": "Desenvolveu habilidades parciais. Necessita de reforço em descritores base."}
    elif score < 350:
        return {"nivel": "PROFICIENTE", "cor": "#2ECC71", "desc": "Domina os conteúdos essenciais previstos para a série."}
    else:
        return {"nivel": "AVANÇADO", "cor": "#3498DB", "desc": "Excelente domínio e capacidade de resolução de problemas complexos."}

# --- 3. DICIONÁRIO DE HABILIDADES (EXEMPLO PARA AS DUAS MATÉRIAS) ---
HABILIDADES_MATEMATICA = {
    "Q01": "D6 - Identificar ângulos como mudança de direção ou giros.",
    "Q02": "EF06MA27 - Classificar ângulos (agudo, reto, obtuso).",
    "Q21": "D21 - Converter números decimais em frações e vice-versa."
}

HABILIDADES_PORTUGUESA = {
    "Q01": "D1 - Localizar informações explícitas em um texto.",
    "Q02": "D3 - Inferir o sentido de uma palavra ou expressão.",
    "Q21": "D4 - Inferir uma informação implícita em um texto."
}

# Preenchimento padrão para itens não listados
for i in range(1, 23):
    key = f"Q{i:02d}"
    if key not in HABILIDADES_MATEMATICA: HABILIDADES_MATEMATICA[key] = f"Descritor de Matemática item {i}"
    if key not in HABILIDADES_PORTUGUESA: HABILIDADES_PORTUGUESA[key] = f"Descritor de Língua Portuguesa item {i}"

# --- 4. GABARITOS ---
GABARITOS_MESTRE = {
    "9º Ano": ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
}

# --- 5. FUNÇÕES TÉCNICAS ---
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

st.sidebar.header("📋 Painel de Controle")
# Adicionada a opção de Língua Portuguesa
disciplina_sel = st.sidebar.selectbox("Selecione a Disciplina:", ["Matemática", "Língua Portuguesa"])
serie_sel = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])

# Seleciona o dicionário de habilidades correto
mapa_habilidades = HABILIDADES_PORTUGUESA if disciplina_sel == "Língua Portuguesa" else HABILIDADES_MATEMATICA

uploaded_file = st.file_uploader(f"📂 Carregar Planilha ({serie_sel})", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    
    # Gabarito (usando o do 9º ano como base adaptada)
    gab_list = GABARITOS_MESTRE.get(serie_sel, ['A']*22)
    gab_atual = {f'Q{i:02d}': gab_list[i-1] for i in range(1, 23)}

    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gab_atual[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    esc_sel = st.sidebar.selectbox("Escola:", ["Geral"] + sorted(list(df['Escola'].unique())))
    df_f = df if esc_sel == "Geral" else df[df['Escola'] == esc_sel]

    # Dashboard de Proficiência
    media_tri = df_f['Proficiência'].mean()
    info = obter_detalhes_nivel(media_tri)

    st.subheader(f"📊 {disciplina_sel} - {esc_sel}")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Média TRI", f"{media_tri:.1f}")
        st.markdown(f"<h2 style='color:{info['cor']};'>NÍVEL {info['nivel']}</h2>", unsafe_allow_html=True)
    with c2:
        st.info(f"**Diagnóstico:** {info['desc']}")
        st.progress(min(media_tri / 500, 1.0))

    st.divider()

    # --- BOTÕES DE PDF ---
    cp1, cp2 = st.columns(2)
    
    with cp1:
        if st.button("📄 PDF COM GRÁFICOS E HABILIDADES", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f'Relatório: {disciplina_sel} - {esc_sel}', ln=True, align='C')
            
            for q in cols_q:
                stats = df_f[q].str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                fig, ax = plt.subplots(figsize=(4, 3))
                cores = ['#2ECC71' if l == gab_atual[q] else '#E74C3C' for l in ['A','B','C','D']]
                ax.bar(['A','B','C','D'], stats, color=cores)
                ax.set_title(f"Questão {q}")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    fig.savefig(tmp.name, bbox_inches='tight')
                    plt.close(fig)
                    
                    if pdf.get_y() > 190: pdf.add_page()
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 10, f"Questão {q} | Acerto: {stats[gab_atual[q]]:.1f}%", ln=True)
                    pdf.image(tmp.name, x=10, w=85)
                    pdf.ln(2)
                    # INCLUSÃO DO NOME DA HABILIDADE ABAIXO DO GRÁFICO NO PDF
                    pdf.set_font('Arial', 'I', 9)
                    pdf.multi_cell(0, 5, f"Habilidade: {mapa_habilidades[q]}")
                    pdf.ln(5)

            pdf_b = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Baixar PDF Completo", pdf_b, f"Relatorio_{disciplina_sel}.pdf")

    # (Exibição dos itens na tela mantida conforme layout anterior)
