import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Sistema de Inteligência Educacional", layout="wide", page_icon="📊")

# --- 2. MATRIZES DE DESCRITORES (GABARITO E HABILIDADES) ---
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
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Portal de Avaliação</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True; st.rerun()
else:
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📝 Importar Dados", "📊 Painel Analítico", "🚪 Sair"])

    if menu == "🏠 Início":
        st.title("👋 Bem-vindo, Jardel!")
        st.write("Sistema Profissional de Monitoramento Pedagógico.")
        
        with st.expander("📚 Como o sistema funciona?", expanded=True):
            st.write("""
            Este sistema utiliza a **Teoria de Resposta ao Item (TRI)**, a mesma metodologia do SAEB e ENEM.
            1. **Coleta:** Você envia as respostas dos alunos via Excel.
            2. **Processamento:** O sistema compara com o gabarito e calcula a probabilidade de acerto.
            3. **Escalonamento:** As notas são convertidas para uma escala de 0 a 400.
            """)
        
        with st.expander("🔢 A Fórmula da TRI explicada"):
            st.latex(r"P_i(\theta) = c_i + \frac{1 - c_i}{1 + e^{-1.7a_i(\theta - b_i)}}")
            st.write("""
            - **$\theta$ (Theta):** Habilidade real do aluno.
            - **$b_i$:** Dificuldade da questão (parâmetro de dificuldade).
            - **$c_i$:** Probabilidade de acerto ao acaso (chute).
            """)

    elif menu == "📝 Importar Dados":
        st.header("📝 Upload de Avaliações")
        c1, c2, c3 = st.columns(3)
        disc = c1.selectbox("Disciplina", ["Língua Portuguesa", "Matemática"])
        ano = c2.selectbox("Ano", ["2º Ano", "5º Ano", "9º Ano"])
        arq = st.file_uploader("Excel (.xlsx)", type="xlsx")
        
        if arq:
            df = pd.read_excel(arq).fillna("BRANCO")
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            for idx, row in df.iterrows():
                resps = {q: 1 if str(row[q]).upper() == GABARITO[i] else 0 for i, q in enumerate(cols_q)}
                df.at[idx, 'Prof_TRI'] = calcular_tri(resps)
            st.session_state['banco_dados'] = df
            st.session_state['mat_ativa'] = disc
            st.session_state['ano_ativo'] = ano
            st.success("✅ Dados processados!")

    elif menu == "📊 Painel Analítico":
        if st.session_state['banco_dados'] is not None:
            df = st.session_state['banco_dados']
            matriz = MATRIZ_MAT if st.session_state['mat_ativa'] == "Matemática" else MATRIZ_LP
            
            st.header(f"📊 {st.session_state['mat_ativa']} - {st.session_state['ano_ativo']}")
            st.metric("Média de Proficiência da Rede", f"{df['Prof_TRI'].mean():.1f}")
            
            st.divider()
            st.subheader("🎯 Análise de Distratores e Habilidades")
            
            grid = st.columns(3)
            stats_list = []
            
            for i, q in enumerate([f'Q{i:02d}' for i in range(1, 23)]):
                # Cálculo de Distratores
                counts = df[q].astype(str).str.upper().value_counts(normalize=True) * 100
                options = ['A', 'B', 'C', 'D']
                values = [counts.get(opt, 0) for opt in options]
                acerto_perc = counts.get(GABARITO[i], 0)
                
                stats_list.append({"Item": q, "Acerto": acerto_perc, "Habilidade": matriz.get(q)})
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.write(f"**Questão {q}** (Correta: **{GABARITO[i]}**)")
                        fig, ax = plt.subplots(figsize=(4, 2.5))
                        colors = ['#2ECC71' if opt == GABARITO[i] else '#E74C3C' for opt in options]
                        ax.bar(options, values, color=colors)
                        ax.set_ylim(0, 100)
                        st.pyplot(fig)
                        plt.close(fig)
                        st.caption(f"**Habilidade:** {matriz.get(q)}")
            
            # --- RELATÓRIO PDF COM MELHORES/PIORES ---
            st.divider()
            if st.button("📄 Gerar Relatório Gerencial Completo"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def f_pdf(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f_pdf(f"RELATÓRIO GERAL - {st.session_state['mat_ativa']} ({st.session_state['ano_ativo']})"), ln=True, align='C')
                
                # Ranking para o relatório
                df_rank = pd.DataFrame(stats_list).sort_values(by="Acerto")
                
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, f_pdf("⚠️ HABILIDADES CRÍTICAS (MENOR ACERTO):"), ln=True)
                pdf.set_font('Arial', '', 10)
                for _, r in df_rank.head(3).iterrows():
                    pdf.cell(0, 6, f_pdf(f"- {r['Item']}: {r['Habilidade']} ({r['Acerto']:.1f}% acerto)"), ln=True)
                
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, f_pdf("🏆 HABILIDADES CONSOLIDADAS (MAIOR ACERTO):"), ln=True)
                pdf.set_font('Arial', '', 1
