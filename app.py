import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor Pedagógico - Análise de Distratores", layout="wide", page_icon="📊")

# --- 2. MATRIZES DE DESCRITORES ---
MATRIZ_LP = {
    f"Q{i:02d}": desc for i, desc in enumerate([
        "D1 - Localizar informações explícitas.", "D3 - Inferir o sentido de palavra/expressão.",
        "D4 - Inferir informação implícita.", "D6 - Identificar o tema do texto.",
        "D14 - Distinguir fato de opinião.", "D12 - Identificar finalidade do texto.",
        "D2 - Relações entre partes do texto.", "D5 - Interpretar com auxílio de imagem.",
        "D7 - Identificar a tese do texto.", "D8 - Relação tese/argumentos.",
        "D9 - Partes principais/secundárias.", "D10 - Conflito do enredo.",
        "D11 - Causa/consequência.", "D13 - Marcas linguísticas.",
        "D15 - Relações lógico-discursivas.", "D16 - Ironia/humor.",
        "D17 - Efeito de pontuação.", "D18 - Escolha de palavras.",
        "D19 - Recursos gráficos.", "D20 - Diferentes formas de tratar o tema.",
        "D21 - Posições distintas.", "D22 - Recursos ortográficos."
    ], 1)
}

MATRIZ_MAT = {
    f"Q{i:02d}": desc for i, desc in enumerate([
        "D1 - Figuras bidimensionais.", "D2 - Propriedades de polígonos.",
        "D3 - Figuras espaciais.", "D4 - Polígonos regulares.",
        "D5 - Perímetro/área.", "D6 - Ângulos.",
        "D12 - Medidas de grandeza.", "D13 - Área de figuras planas.",
        "D14 - Noções de volume.", "D16 - Localização em mapas.",
        "D17 - Plano cartesiano.", "D18 - Expressão algébrica.",
        "D19 - Inequações.", "D20 - Funções.",
        "D21 - Sistemas de equações.", "D22 - Gráfico de funções.",
        "D23 - Porcentagem.", "D24 - Juros simples.",
        "D25 - Grandezas proporcionais.", "D26 - Tabelas/gráficos.",
        "D27 - Média aritmética.", "D28 - Probabilidade."
    ], 1)
}

GABARITO = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']

# --- 3. MOTOR TRI ---
def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        b = np.linspace(-2.5, 2.5, 22)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- 4. LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'db' not in st.session_state: st.session_state.db = None

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center;'>🏛️ Sistema de Monitoramento</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if u == "12345" and s == "000": st.session_state.auth = True; st.rerun()
else:
    menu = st.sidebar.radio("Navegação:", ["Início", "Upload", "Análise Detalhada", "Sair"])

    if menu == "Sair": st.session_state.auth = False; st.rerun()

    elif menu == "Upload":
        st.header("📝 Importação")
        c1, c2 = st.columns(2)
        disc = c1.selectbox("Disciplina", ["Língua Portuguesa", "Matemática"])
        ano = c2.selectbox("Ano", ["2º Ano", "5º Ano", "9º Ano"])
        arq = st.file_uploader("Arquivo Excel", type="xlsx")
        
        if arq:
            df = pd.read_excel(arq).fillna("X")
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            for idx, row in df.iterrows():
                resps = {q: 1 if str(row[q]).upper() == GABARITO[i] else 0 for i, q in enumerate(cols_q)}
                df.at[idx, 'Prof_TRI'] = calcular_tri(resps)
            st.session_state.db = df
            st.session_state.info = {"mat": disc, "ano": ano}
            st.success("Dados Processados!")

    elif menu == "Análise Detalhada":
        if st.session_state.db is not None:
            df = st.session_state.db
            matriz = MATRIZ_MAT if st.session_state.info['mat'] == "Matemática" else MATRIZ_LP
            
            st.title(f"📊 {st.session_state.info['mat']} - {st.session_state.info['ano']}")
            st.metric("Proficiência Média (TRI)", f"{df['Prof_TRI'].mean():.1f}")

            # --- GRÁFICOS DE DISTRATORES ---
            st.subheader("🔍 Distribuição de Respostas por Item (A, B, C, D)")
            grid = st.columns(3)
            
            for i, q in enumerate([f'Q{i:02d}' for i in range(1, 23)]):
                with grid[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"**Item {q}**")
                        st.caption(f"_{matriz[q]}_")
                        
                        # Cálculo das frequências
                        counts = df[q].astype(str).str.upper().value_counts(normalize=True) * 100
                        options = ['A', 'B', 'C', 'D']
                        values = [counts.get(opt, 0) for opt in options]
                        
                        # Cores: Verde para a correta, cinza para os distratores
                        colors = ['#2ECC71' if opt == GABARITO[i] else '#BDC3C7' for opt in options]
                        
                        fig, ax = plt.subplots(figsize=(4, 3))
                        bars = ax.bar(options, values, color=colors)
                        ax.set_ylim(0, 100)
                        ax.set_ylabel("% de escolha")
                        
                        # Adiciona rótulos de porcentagem nas barras
                        for bar in bars:
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:.0f}%', ha='center', fontsize=8)
                        
                        st.pyplot(fig)
                        plt.close(fig)

            # --- PDF ---
            if st.button("📄 Gerar Relatório de Distratores"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                def clean(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.cell(0, 10, clean(f"RELATÓRIO TÉCNICO - {st.session_state.info['mat']}"), ln=True, align='C')
                
                # Resumo das habilidades
                pdf.add_page()
                pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, clean("MAPEAMENTO DE HABILIDADES E DESEMPENHO"), ln=True)
                pdf.set_font('Arial', '', 10)
                for i, q in enumerate([f'Q{i:02d}' for i in range(1, 23)]):
                    acerto = (len(df[df[q].astype(str).str.upper() == GABARITO[i]]) / len(df)) * 100
                    txt = f"{q} (Gabarito {GABARITO[i]}): {matriz[q]} | Acerto: {acerto:.1f}%"
                    pdf.cell(0, 6, clean(txt), ln=True)
                
                st.download_button("📥 Baixar PDF", pdf.output(dest='S'), "Relatorio_Pedagogico.pdf")
        else:
            st.warning("Carregue os dados primeiro!")
