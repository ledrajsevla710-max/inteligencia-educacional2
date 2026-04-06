import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Sistema de Inteligência Educacional", layout="wide", page_icon="📊")

# --- 2. MATRIZES E DEFINIÇÕES PEDAGÓGICAS ---
MATRIZ_LP = {
    "Q01": "D1 - Localizar informações explícitas.", "Q02": "D3 - Inferir o sentido de palavra/expressão.",
    "Q03": "D4 - Inferir informação implícita.", "Q04": "D6 - Identificar o tema do texto.",
    "Q05": "D14 - Distinguir fato de opinião.", "Q06": "D12 - Identificar finalidade do texto.",
    "Q07": "D2 - Estabelecer relações entre partes do texto.", "Q08": "D5 - Interpretar texto com auxílio de imagem.",
    "Q09": "D7 - Identificar a tese do texto.", "Q10": "D8 - Estabelecer relação tese/argumentos.",
    "Q11": "D9 - Diferenciar partes principais/secundárias.", "Q12": "D10 - Identificar o conflito do enredo.",
    "Q13": "D11 - Estabelecer relação causa/consequência.", "Q14": "D13 - Identificar marcas linguísticas (locutor).",
    "Q15": "D15 - Estabelecer relações lógico-discursivas.", "Q16": "D16 - Identificar efeitos de ironia/humor.",
    "Q17": "D17 - Identificar efeito de pontuação.", "Q18": "D18 - Efeito de sentido (escolha de palavras).",
    "Q19": "D19 - Efeito de sentido (recursos gráficos).", "Q20": "D20 - Diferentes formas de tratar o tema.",
    "Q21": "D21 - Reconhecer posições distintas entre textos.", "Q22": "D22 - Identificar recursos ortográficos/estilísticos."
}

MATRIZ_MAT = {
    "Q01": "D1 - Identificar figuras bidimensionais.", "Q02": "D2 - Reconhecer propriedades de polígonos.",
    "Q03": "D3 - Identificar relações entre figuras espaciais.", "Q04": "D4 - Identificar polígonos regulares.",
    "Q05": "D5 - Reconhecer conservação de perímetro/área.", "Q06": "D6 - Reconhecer ângulos como mudança de direção.",
    "Q07": "D12 - Resolver problemas com medidas de grandeza.", "Q08": "D13 - Calcular área de figuras planas.",
    "Q09": "D14 - Resolver problema com noções de volume.", "Q10": "D16 - Identificar localização em mapas/malhas.",
    "Q11": "D17 - Identificar coordenadas no plano cartesiano.", "Q12": "D18 - Reconhecer expressão algébrica.",
    "Q13": "D19 - Resolver problema com inequações de 1º grau.", "Q14": "D20 - Analisar crescimento/decrescimento de função.",
    "Q15": "D21 - Resolver sistema de equações de 1º grau.", "Q16": "D22 - Identificar gráfico de funções de 1º grau.",
    "Q17": "D23 - Resolver problemas com porcentagem.", "Q18": "D24 - Resolver problemas com juros simples.",
    "Q19": "D25 - Resolver problemas com grandezas proporcionais.", "Q20": "D26 - Associar informações de tabelas/gráficos.",
    "Q21": "D27 - Calcular média aritmética de dados.", "Q22": "D28 - Resolver problema com probabilidade simples."
}

GABARITO = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']

def obter_nivel_escala(valor, disciplina):
    if disciplina == "Língua Portuguesa":
        if valor < 200: return "Muito Crítico", "#D32F2F"
        if valor < 250: return "Crítico", "#F57C00"
        if valor < 300: return "Intermediário", "#FBC02D"
        return "Adequado", "#388E3C"
    else:
        if valor < 225: return "Muito Crítico", "#D32F2F"
        if valor < 275: return "Crítico", "#F57C00"
        if valor < 325: return "Intermediário", "#FBC02D"
        return "Adequado", "#388E3C"

def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        b = np.linspace(-2.5, 2.5, 22)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    theta_final = thetas[np.argmax(verossimilhanca)]
    return (theta_final + 4) * 50

# --- 4. CONTROLE DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Portal de Inteligência Educacional</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.container(border=True):
            u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
            if st.button("Entrar no Sistema", use_container_width=True):
                if u == "12345" and s == "000":
                    st.session_state['autenticado'] = True; st.rerun()
                else: st.error("Acesso negado.")
else:
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "📝 Importar Dados", "📊 Painel Analítico", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state.clear(); st.rerun()

    elif menu == "🏠 Início":
        st.title("👋 Bem-vindo, Jardel Alves Vieira!")
        st.markdown("### 📊 Escalas de Proficiência (Referência SAEB)")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**Língua Portuguesa**")
            st.write("🔴 < 200: Muito Crítico | 🟠 < 250: Crítico | 🟡 < 300: Intermediário | 🟢 > 300: Adequado", unsafe_allow_html=True)
        with c2:
            st.success("**Matemática**")
            st.write("🔴 < 225: Muito Crítico | 🟠 < 275: Crítico | 🟡 < 325: Intermediário | 🟢 > 325: Adequado", unsafe_allow_html=True)

        st.markdown("### 🔬 Desvendando a Fórmula TRI")
        st.latex(r"P_i(\theta) = c_i + \frac{1 - c_i}{1 + e^{-1.7 \cdot a_i \cdot (\theta - b_i)}}")
        st.write("""
        Esta fórmula é o **Modelo Logístico de 3 Parâmetros**:
        - **Theta ($\theta$):** A habilidade do aluno.
        - **$b_i$:** Dificuldade do item.
        - **$a_i$:** Discriminação (qualidade pedagógica do item).
        - **$c_i$:** Probabilidade de acerto ao acaso (chute).
        """)

    elif menu == "📝 Importar Dados":
        st.header("📝 Importação de Dados")
        c1, c2, c3 = st.columns(3)
        disc = c1.selectbox("Disciplina:", ["Língua Portuguesa", "Matemática"])
        ano = c2.selectbox("Ano Escolar:", ["2º Ano", "5º Ano", "9º Ano"])
        arq = st.file_uploader("Arquivo Excel (.xlsx)", type="xlsx")

        if arq:
            df = pd.read_excel(arq).fillna("N/A")
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            for idx, row in df.iterrows():
                res_bin = {q: 1 if str(row[q]).upper() == GABARITO[i] else 0 for i, q in enumerate(cols_q)}
                df.at[idx, 'Prof_TRI'] = calcular_tri(res_bin)
            st.session_state['banco_dados'] = df
            st.session_state['mat_ativa'] = disc
            st.session_state['ano_ativo'] = ano
            st.success("✅ Dados processados!")

    elif menu == "📊 Painel Analítico":
        if st.session_state.get('banco_dados') is not None:
            df = st.session_state['banco_dados']
            matriz = MATRIZ_MAT if st.session_state['mat_ativa'] == "Matemática" else MATRIZ_LP
            media = df['Prof_TRI'].mean()
            nivel, cor = obter_nivel_escala(media, st.session_state['mat_ativa'])
            
            st.header(f"📊 {st.session_state['mat_ativa']} - {st.session_state['ano_ativo']}")
            st.markdown(f"<div style='padding:15px; border-radius:10px; background-color:{cor}; color:white; text-align:center; font-size:20px;'>Média: {media:.1f} | Nível: {nivel}</div>", unsafe_allow_html=True)
            
            st.divider()
            grid = st.columns(3)
            stats_list = []
            
            for i, q in enumerate([f'Q{i:02d}' for i in range(1, 23)]):
                counts = df[q].astype(str).str.upper().value_counts(normalize=True) * 100
                opts = ['A', 'B', 'C', 'D']; vals = [counts.get(o, 0) for o in opts]
                perc_acerto = counts.get(GABARITO[i], 0)
                stats_list.append({"Item": q, "Acerto": perc_acerto, "Hab": matriz.get(q), "Gab": GABARITO[i]})
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.write(f"**Questão {q}** (Gabarito: {GABARITO[i]})")
                        fig, ax = plt.subplots(figsize=(4, 2.5))
                        ax.bar(opts, vals, color=['#2ECC71' if o == GABARITO[i] else '#E74C3C' for o in opts])
                        ax.set_ylim(0, 100)
                        st.pyplot(fig); plt.close(fig)
                        st.caption(f"**Habilidade:** {matriz.get(q)}")

            # --- RELATÓRIO PDF COM DESCRIÇÕES ---
            if st.button("📄 Gerar Relatório Analítico Completo"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def f_txt(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                
                # Cabeçalho
                pdf.set_font('Arial', 'B', 20)
                pdf.cell(0, 15, f_txt(f"DIAGNÓSTICO MUNICIPAL: {st.session_state['mat_ativa']}"), ln=True, align='C')
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, f_txt(f"Ano: {st.session_state['ano_ativo']} | Proficiência Média: {media:.1f} ({nivel})"), ln=True, align='C')
                
                # Gráfico Geral
                df_res = pd.DataFrame(stats_list)
                fig_g, ax_g = plt.subplots(figsize=(12, 5))
                ax_g.bar(df_res['Item'], df_res['Acerto'], color='#1E3A8A')
                ax_g.set_title("Performance por Item (%)")
                ax_g.set_ylim(0, 105)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); plt.close(fig_g)
                    pdf.image(tmp.name, x=15, y=45, w=265)
                os.unlink(tmp.name)

                # Segunda Página - Detalhamento de Habilidades
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16); pdf.cell(0, 12, f_txt("📋 Mapeamento Pedagógico de Habilidades"), ln=True)
                
                df_rank = df_res.sort_values(by="Acerto")
                
                # Seção: Habilidades em Alerta (Baixo Desempenho)
                pdf.set_text_color(200, 0, 0) # Vermelho
                pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, f_txt("⚠️ ALERTA CRÍTICO: Habilidades com menor domínio"), ln=True)
                pdf.set_text_color(0, 0, 0) # Volta preto
                pdf.set_font('Arial', '', 9)
                for _, r in df_rank.head(6).iterrows():
                    pdf.multi_cell(0, 6, f_txt(f"Questão {r['Item']} (Acerto: {r['Acerto']:.1f}%) - {r['Hab']}"), border='B')
                
                pdf.ln(5)
                
                # Seção: Habilidades Consolidadas (Alto Desempenho)
                pdf.set_text_color(0, 128, 0) # Verde
                pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, f_txt("🏆 DESTAQUES: Habilidades consolidadas"), ln=True)
                pdf.set_text_color(0, 0, 0) # Volta preto
                pdf.set_font('Arial', '', 9)
                for _, r in df_rank.tail(6).iterrows():
                    pdf.multi_cell(0, 6, f_txt(f"Questão {r['Item']} (Acerto: {r['Acerto']:.1f}%) - {r['Hab']}"), border='B')

                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button(label="📥 Baixar Relatório Completo", data=pdf_bytes, file_name=f"Relatorio_{st.session_state['mat_ativa']}.pdf", mime="application/pdf")
