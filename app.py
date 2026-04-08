import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Sistema de Inteligência Educacional", layout="wide")

if 'usuarios_db' not in st.session_state:
    st.session_state['usuarios_db'] = {"12345": "000"} 

# --- 2. MATRIZES 1º BIMESTRE (SAEPI/SAEB) ---
MATRIZ_LP = {
    "Q01": "D1 - Localizar informações explícitas.", "Q02": "D3 - Inferir sentido de palavra/expressão.",
    "Q03": "D4 - Inferir informação implícita.", "Q04": "D6 - Identificar o tema do texto.",
    "Q05": "D14 - Distinguir fato de opinião.", "Q06": "D1 - Localizar informações explícitas.",
    "Q07": "D4 - Inferir informação implícita.", "Q08": "D5 - Interpretar texto com auxílio de imagem.",
    "Q09": "D3 - Inferir sentido de palavra/expressão.", "Q10": "D6 - Identificar o tema do texto.",
    "Q11": "D12 - Identificar finalidade do texto.", "Q12": "D1 - Localizar informações explícitas.",
    "Q13": "D3 - Inferir sentido de palavra/expressão.", "Q14": "D4 - Inferir informação implícita.",
    "Q15": "D6 - Identificar o tema do texto.", "Q16": "D14 - Distinguir fato de opinião.",
    "Q17": "D1 - Localizar informações explícitas.", "Q18": "D4 - Inferir informação implícita.",
    "Q19": "D5 - Interpretar texto com auxílio de imagem.", "Q20": "D6 - Identificar o tema do texto.",
    "Q21": "D3 - Inferir sentido de palavra/expressão.", "Q22": "D12 - Identificar finalidade do texto."
}

MATRIZ_MAT = {
    "Q01": "D13 - Calcular área de figuras planas.", "Q02": "D14 - Resolver problema com noções de volume.",
    "Q03": "D16 - Identificar localização em mapas/malhas.", "Q04": "D17 - Identificar coordenadas no plano cartesiano.",
    "Q05": "D18 - Reconhecer expressão algébrica.", "Q06": "D19 - Resolver problema com inequações de 1º grau.",
    "Q07": "D20 - Analisar crescimento/decrescimento de função.", "Q08": "D21 - Resolver sistema de equações de 1º grau.",
    "Q09": "D22 - Identificar gráfico de funções de 1º grau.", "Q10": "D23 - Resolver problemas com porcentagem.",
    "Q11": "D24 - Resolver problemas com juros simples.", "Q12": "D25 - Resolver problemas com grandezas proporcionais.",
    "Q13": "D26 - Associar informações de tabelas/gráficos.", "Q14": "D27 - Calcular média aritmética de dados.",
    "Q15": "D28 - Resolver problema com probabilidade simples.", "Q16": "D1 - Identificar figuras bidimensionais.",
    "Q17": "D2 - Reconhecer propriedades de polígonos.", "Q18": "D3 - Identificar relações entre figuras espaciais.",
    "Q19": "D4 - Identificar polígonos regulares.", "Q20": "D5 - Reconhecer conservação de perímetro/área.",
    "Q21": "D6 - Reconhecer ângulos como mudança de direção.", "Q22": "D12 - Resolver problemas com medidas de grandeza."
}

GABARITO = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']

# --- 3. MOTORES ---
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
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- 4. ACESSO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Sistema Educacional</h1>", unsafe_allow_html=True)
    aba_l, aba_c = st.tabs(["🔐 Login", "📝 Cadastro"])
    with aba_l:
        u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
        st.markdown("---")
        st.caption("🛡️ **Privacidade:** Dados tratados para fins pedagógicos (LGPD).")
        if st.button("Entrar"):
            if u in st.session_state['usuarios_db'] and st.session_state['usuarios_db'][u] == s:
                st.session_state['autenticado'] = True; st.rerun()
            else: st.error("Acesso negado.")
    with aba_c:
        nu = st.text_input("Novo Usuário"); ns = st.text_input("Nova Senha", type="password")
        st.checkbox("Aceito os termos de uso de dados educacionais.")
        if st.button("Cadastrar"):
            st.session_state['usuarios_db'][nu] = ns; st.success("Cadastro realizado!")

else:
    menu = st.sidebar.radio("Navegação", ["🏠 Início", "📝 Importar", "📊 Painel Analítico", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()

    elif menu == "🏠 Início":
        st.header("👋 Bem-vindo, Jardel!")
        st.markdown("### 🔬 Explicação da TRI")
        st.latex(r"P_i(\theta) = c_i + \frac{1 - c_i}{1 + e^{-1.7 \cdot a_i \cdot (\theta - b_i)}}")
        st.write("Este sistema utiliza o modelo logístico de 3 parâmetros para calcular a proficiência real do aluno, punindo o 'chute' e valorizando a consistência pedagógica.")

    elif menu == "📝 Importar":
        st.header("📝 Importar Excel")
        disc = st.selectbox("Disciplina", ["Língua Portuguesa", "Matemática"])
        arq = st.file_uploader("Arquivo (.xlsx)", type="xlsx")
        if arq:
            df = pd.read_excel(arq).fillna("N/A")
            for idx, row in df.iterrows():
                res = {f'Q{i:02d}': (1 if str(row[f'Q{i:02d}']).upper() == GABARITO[i-1] else 0) for i in range(1, 23)}
                df.at[idx, 'Prof_TRI'] = calcular_tri(res)
            st.session_state['db'], st.session_state['disc'] = df, disc
            st.success("Sucesso!")

    elif menu == "📊 Painel Analítico":
        if 'db' in st.session_state:
            df, disc = st.session_state['db'], st.session_state['disc']
            matriz = MATRIZ_MAT if disc == "Matemática" else MATRIZ_LP
            media = df['Prof_TRI'].mean()
            nivel, cor = obter_nivel_escala(media, disc)
            
            st.markdown(f"<div style='background:{cor}; color:white; padding:15px; border-radius:10px; text-align:center;'>Média: {media:.1f} | Nível: {nivel}</div>", unsafe_allow_html=True)
            
            stats = []
            grid = st.columns(3)
            for i in range(1, 23):
                q = f'Q{i:02d}'; gab = GABARITO[i-1]
                counts = df[q].astype(str).str.upper().value_counts(normalize=True) * 100
                stats.append({"Item": q, "Acerto": counts.get(gab, 0), "Hab": matriz[q]})
                
                with grid[(i-1) % 3]:
                    with st.container(border=True):
                        st.write(f"**Questão {q}**")
                        fig, ax = plt.subplots(figsize=(4, 3))
                        opcoes = ['A','B','C','D']
                        cores = ['#2ECC71' if o == gab else '#E74C3C' for o in opcoes]
                        ax.bar(opcoes, [counts.get(o, 0) for o in opcoes], color=cores)
                        st.pyplot(fig); plt.close()
                        st.caption(f"Habilidade: {matriz[q]}")

            if st.button("📄 Relatório PDF Completo"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(texto): return str(texto).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, t(f"RELATÓRIO: {disc}"), ln=True, align='C')
                
                df_s = pd.DataFrame(stats)
                fig_g, ax_g = plt.subplots(figsize=(10, 4))
                ax_g.bar(df_s['Item'], df_s['Acerto'], color='#1E3A8A')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); plt.close()
                    pdf.image(tmp.name, x=10, y=40, w=270)
                os.unlink(tmp.name)
                
                pdf.add_page()
                pdf.set_font('Arial', 'B', 12); df_rank = df_s.sort_values(by="Acerto")
                pdf.set_text_color(200, 0, 0); pdf.cell(0, 10, t("⚠️ HABILIDADES CRÍTICAS"), ln=True)
                pdf.set_font('Arial', '', 9); pdf.set_text_color(0,0,0)
                for _, r in df_rank.head(6).iterrows():
                    pdf.multi_cell(0, 6, t(f"Q{r['Item']} ({r['Acerto']:.1f}%) - {r['Hab']}"), border='B')
                
                pdf.ln(5); pdf.set_font('Arial', 'B', 12); pdf.set_text_color(0, 128, 0)
                pdf.cell(0, 10, t("🏆 HABILIDADES CONSOLIDADAS"), ln=True)
                pdf.set_font('Arial', '', 9); pdf.set_text_color(0,0,0)
                for _, r in df_rank.tail(6).iterrows():
                    pdf.multi_cell(0, 6, t(f"Q{r['Item']} ({r['Acerto']:.1f}%) - {r['Hab']}"), border='B')
                
                st.download_button("📥 Baixar PDF", pdf.output(dest='S').encode('latin-1'), "Relatorio.pdf")
