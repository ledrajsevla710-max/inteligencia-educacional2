import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Sistema de Inteligência Educacional", layout="wide", page_icon="📊")

# --- 2. MATRIZES E DEFINIÇÕES ---
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
    "Q11": "D17 - Identificar coordenadas no plano cartesiano.", "Q12": "D18 - Reconecedor expressão algébrica.",
    "Q13": "D19 - Resolver problema com inequações de 1º grau.", "Q14": "D20 - Analisar crescimento/decrescimento de função.",
    "Q15": "D21 - Resolver sistema de equações de 1º grau.", "Q16": "D22 - Identificar gráfico de funções de 1º grau.",
    "Q17": "D23 - Resolver problemas com porcentagem.", "Q18": "D24 - Resolver problemas com juros simples.",
    "Q19": "D25 - Resolver problemas com grandezas proporcionais.", "Q20": "D26 - Associar informações de tabelas/gráficos.",
    "Q21": "D27 - Calcular média aritmética de dados.", "Q22": "D28 - Resolver problema com probabilidade simples."
}

GABARITO = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']

def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        b = np.linspace(-2.5, 2.5, 22)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- 3. GESTÃO DE USUÁRIOS (SESSÃO) ---
if 'usuarios_db' not in st.session_state:
    st.session_state['usuarios_db'] = {"12345": "000"} # Usuário padrão
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# --- 4. TELA DE ACESSO (LOGIN / CADASTRO) ---
if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Inteligência Educacional</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
    
    with tab1:
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c2:
            with st.container(border=True):
                u_login = st.text_input("Usuário (CPF ou Matrícula)")
                s_login = st.text_input("Senha ", type="password")
                if st.button("Acessar Painel", use_container_width=True):
                    if u_login in st.session_state['usuarios_db'] and st.session_state['usuarios_db'][u_login] == s_login:
                        st.session_state['autenticado'] = True
                        st.rerun()
                    else: st.error("Usuário ou senha incorretos.")

    with tab2:
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c2:
            with st.container(border=True):
                st.subheader("Novo Cadastro")
                novo_u = st.text_input("Definir Usuário")
                nova_s = st.text_input("Definir Senha", type="password")
                conf_s = st.text_input("Confirmar Senha", type="password")
                
                st.markdown("---")
                st.warning("⚠️ **Política de Privacidade**")
                st.caption("""Ao se cadastrar, você concorda que os dados de avaliações submetidos serão utilizados exclusivamente para fins de diagnóstico pedagógico e melhoria do ensino municipal, em conformidade com a LGPD.""")
                concordo = st.checkbox("Li e aceito os termos de uso de dados educacionais.")
                
                if st.button("Finalizar Cadastro", use_container_width=True):
                    if not concordo:
                        st.error("Você precisa aceitar a Política de Privacidade.")
                    elif nova_s != conf_s:
                        st.error("As senhas não coincidem.")
                    elif novo_u == "" or nova_s == "":
                        st.error("Preencha todos os campos.")
                    else:
                        st.session_state['usuarios_db'][novo_u] = nova_s
                        st.success("Cadastro realizado! Use a aba 'Entrar'.")

else:
    # --- 5. SISTEMA LOGADO ---
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "📝 Importar Dados", "📊 Painel Analítico", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "🏠 Início":
        st.title("👋 Bem-vindo ao Sistema de Diagnóstico!")
        st.markdown("### 🔬 A Teoria de Resposta ao Item (TRI)")
        st.latex(r"P_i(\theta) = c_i + \frac{1 - c_i}{1 + e^{-1.7 \cdot a_i \cdot (\theta - b_i)}}")
        st.info("**Nota Técnica:** A proficiência ($\theta$) avalia a consistência do aprendizado. Acertos em questões difíceis sem base nas fáceis são calibrados para evitar distorções por 'chute'.")

    elif menu == "📝 Importar Dados":
        st.header("📝 Importação")
        c1, c2 = st.columns(2)
        disc = c1.selectbox("Disciplina:", ["Língua Portuguesa", "Matemática"])
        arq = st.file_uploader("Excel (.xlsx)", type="xlsx")
        if arq:
            df = pd.read_excel(arq).fillna("N/A")
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            for idx, row in df.iterrows():
                res_bin = {q: 1 if str(row[q]).upper() == GABARITO[i] else 0 for i, q in enumerate(cols_q)}
                df.at[idx, 'Prof_TRI'] = calcular_tri(res_bin)
            st.session_state['banco_dados'] = df
            st.session_state['mat_ativa'] = disc
            st.success("✅ Processamento concluído!")

    elif menu == "📊 Painel Analítico":
        if st.session_state.get('banco_dados') is not None:
            df = st.session_state['banco_dados']
            matriz = MATRIZ_MAT if st.session_state['mat_ativa'] == "Matemática" else MATRIZ_LP
            stats_list = []
            
            st.header(f"📊 Painel Analítico - {st.session_state['mat_ativa']}")
            grid = st.columns(3)
            for i, q in enumerate([f'Q{i:02d}' for i in range(1, 23)]):
                counts = df[q].astype(str).str.upper().value_counts(normalize=True) * 100
                perc_acerto = counts.get(GABARITO[i], 0)
                stats_list.append({"Item": q, "Acerto": perc_acerto, "Hab": matriz.get(q), "Gab": GABARITO[i]})
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.write(f"Questão {q}")
                        fig, ax = plt.subplots(figsize=(4, 2))
                        ax.bar(['A','B','C','D'], [counts.get(o, 0) for o in ['A','B','C','D']], 
                               color=['#2ECC71' if o == GABARITO[i] else '#E74C3C' for o in ['A','B','C','D']])
                        st.pyplot(fig); plt.close(fig)
                        st.caption(matriz.get(q))

            # --- RELATÓRIO PDF COM DESTAQUES ---
            if st.button("📄 Gerar Relatório Técnico Completo"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def f_txt(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font('Arial', 'B', 18)
                pdf.cell(0, 15, f_txt(f"RELATÓRIO PEDAGÓGICO: {st.session_state['mat_ativa']}"), ln=True, align='C')
                
                df_res = pd.DataFrame(stats_list).sort_values(by="Acerto")
                
                # Gráfico Geral
                fig_g, ax_g = plt.subplots(figsize=(10, 4))
                ax_g.bar(df_res['Item'], df_res['Acerto'], color='#1E3A8A')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); plt.close(fig_g)
                    pdf.image(tmp.name, x=15, y=40, w=265)
                os.unlink(tmp.name)

                pdf.add_page()
                pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, f_txt("📋 Prioridades e Destaques"), ln=True)
                
                pdf.set_text_color(200, 0, 0)
                pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, f_txt("⚠️ ALERTA: Habilidades Críticas"), ln=True)
                pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
                for _, r in df_res.head(5).iterrows():
                    pdf.multi_cell(0, 6, f_txt(f"{r['Item']}: {r['Acerto']:.1f}% - {r['Hab']}"), border='B')
                
                pdf.ln(5)
                pdf.set_text_color(0, 128, 0)
                pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, f_txt("🏆 SUCESSO: Habilidades Consolidadas"), ln=True)
                pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
                for _, r in df_res.tail(5).iterrows():
                    pdf.multi_cell(0, 6, f_txt(f"{r['Item']}: {r['Acerto']:.1f}% - {r['Hab']}"), border='B')

                st.download_button("📥 Baixar PDF", pdf.output(dest='S').encode('latin-1'), "Diagnostico.pdf")
