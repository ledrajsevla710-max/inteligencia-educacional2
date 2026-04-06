import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Sistema de Inteligência Educacional", layout="wide", page_icon="📊")

# --- 2. MATRIZES DE DESCRITORES E GABARITO ---
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
    theta_final = thetas[np.argmax(verossimilhanca)]
    return (theta_final + 4) * 50

# --- 4. GESTÃO DE SESSÃO E LOGIN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Portal de Inteligência Educacional</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.container(border=True):
            u = st.text_input("Usuário Administrativo")
            s = st.text_input("Senha de Acesso", type="password")
            if st.button("Entrar no Sistema", use_container_width=True):
                if u == "12345" and s == "000":
                    st.session_state['autenticado'] = True; st.rerun()
                else: st.error("Acesso Negado.")
else:
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "📝 Importar Dados", "📊 Painel Analítico", "🚪 Sair"])

    if menu == "🏠 Início":
        st.title("👋 Bem-vindo, Jardel Alves Vieira!")
        with st.container(border=True):
            st.subheader("📖 Como o sistema funciona?")
            st.write("""
            1. **Upload:** Envie a planilha Excel com as respostas dos alunos.
            2. **TRI:** O sistema calcula a proficiência baseada na consistência das respostas (Escala 0-400).
            3. **Distratores:** Analise quais alternativas erradas estão confundindo os estudantes.
            4. **Habilidades:** Cada questão é vinculada automaticamente aos Descritores da Matriz.
            """)
        
        with st.expander("🔬 Fundamentação Científica (Fórmula TRI)"):
            st.latex(r"P_i(\theta) = c_i + \frac{1 - c_i}{1 + e^{-1.7a_i(\theta - b_i)}}")
            st.write("Esta fórmula calcula a probabilidade de acerto considerando a habilidade ($\theta$), dificuldade ($b_i$) e o chute ($c_i$).")

    elif menu == "📝 Importar Dados":
        st.header("📝 Importação de Avaliações")
        c1, c2, c3 = st.columns(3)
        disc = c1.selectbox("Disciplina:", ["Língua Portuguesa", "Matemática"])
        ano = c2.selectbox("Ano Escolar:", ["2º Ano", "5º Ano", "9º Ano"])
        arq = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type="xlsx")

        if arq:
            df = pd.read_excel(arq).fillna("N/A")
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            with st.spinner("Calculando Proficiências..."):
                for idx, row in df.iterrows():
                    resps_bin = {q: 1 if str(row[q]).upper() == GABARITO[i] else 0 for i, q in enumerate(cols_q)}
                    df.at[idx, 'Prof_TRI'] = calcular_tri(resps_bin)
                st.session_state['banco_dados'] = df
                st.session_state['mat_ativa'] = disc
                st.session_state['ano_ativo'] = ano
                st.success("✅ Processamento concluído!")

    elif menu == "📊 Painel Analítico":
        if st.session_state['banco_dados'] is not None:
            df = st.session_state['banco_dados']
            matriz = MATRIZ_MAT if st.session_state['mat_ativa'] == "Matemática" else MATRIZ_LP
            
            st.header(f"📊 Painel: {st.session_state['mat_ativa']} ({st.session_state['ano_ativo']})")
            st.metric("Proficiência Média da Rede", f"{df['Prof_TRI'].mean():.1f}")
            
            st.divider()
            grid = st.columns(3)
            stats_relatorio = []
            
            for i, q in enumerate([f'Q{i:02d}' for i in range(1, 23)]):
                dist = df[q].astype(str).str.upper().value_counts(normalize=True) * 100
                alternativas = ['A', 'B', 'C', 'D']
                valores = [dist.get(alt, 0) for alt in alternativas]
                acerto_perc = dist.get(GABARITO[i], 0)
                stats_relatorio.append({"Item": q, "Acerto": acerto_perc, "Habilidade": matriz.get(q), "Gabarito": GABARITO[i]})
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.write(f"**Questão {q}** (Correta: **{GABARITO[i]}**)")
                        fig, ax = plt.subplots(figsize=(4, 2.5))
                        cores = ['#2ECC71' if alt == GABARITO[i] else '#E74C3C' for alt in alternativas]
                        ax.bar(alternativas, valores, color=cores)
                        ax.set_ylim(0, 100)
                        st.pyplot(fig); plt.close(fig)
                        st.info(f"**Habilidade:** {matriz.get(q)}")

            # --- RELATÓRIO PDF ---
            if st.button("📄 Gerar Relatório Técnico Completo"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, t(f"DIAGNÓSTICO PEDAGÓGICO - {st.session_state['mat_ativa']}"), ln=True, align='C')
                
                df_res = pd.DataFrame(stats_relatorio)
                fig_g, ax_g = plt.subplots(figsize=(12, 4))
                ax_g.bar(df_res['Item'], df_res['Acerto'], color='#1E3A8A')
                ax_g.set_title("Percentual de Acerto por Questao")
                ax_g.set_ylim(0, 105)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); pdf.image(tmp.name, x=10, y=35, w=275)
                plt.close(fig_g)

                pdf.add_page()
                pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, t("📋 Ranking de Habilidades"), ln=True)
                df_rank = df_res.sort_values(by="Acerto")
                
                pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, t("⚠️ Prioridades (Menor Acerto):"), ln=True)
                pdf.set_font('Arial', '', 10)
                for _, r in df_rank.head(4).iterrows():
                    pdf.cell(0, 6, t(f"- {r['Item']} ({r['Gabarito']}): {r['Habilidade']} ({r['Acerto']:.1f}%)"), ln=True)
                
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, t("🏆 Destaques (Maior Acerto):"), ln=True)
                pdf.set_font('Arial', '', 10)
                for _, r in df_rank.tail(4).iterrows():
                    pdf.cell(0, 6, t(f"- {r['Item']} ({r['Gabarito']}): {r['Habilidade']} ({r['Acerto']:.1f}%)"), ln=True)

                st.download_button("📥 Baixar Relatório", pdf.output(dest='S'), "Relatorio_Diagnostico.pdf")

    elif menu == "Sair":
        st.session_state['autenticado'] = False; st.rerun()
