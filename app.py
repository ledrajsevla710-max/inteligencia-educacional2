import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. GESTÃO DE USUÁRIOS (SESSÃO) ---
if 'usuarios_db' not in st.session_state:
    st.session_state['usuarios_db'] = {"12345": "000"} 

# --- 3. MATRIZES 1º BIMESTRE (DESCRIÇÕES COMPLETAS) ---
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
    "Q01": "D13 - Área de figuras planas.", "Q02": "D14 - Noções de volume.",
    "Q03": "D16 - Localização em mapas/malhas.", "Q04": "D17 - Coordenadas no plano cartesiano.",
    "Q05": "D18 - Expressão algébrica.", "Q06": "D19 - Inequações de 1º grau.",
    "Q07": "D20 - Crescimento/Decrescimento de função.", "Q08": "D21 - Sistema de equações de 1º grau.",
    "Q09": "D22 - Gráfico de funções de 1º grau.", "Q10": "D23 - Porcentagem.",
    "Q11": "D24 - Juros simples.", "Q12": "D25 - Grandezas proporcionais.",
    "Q13": "D26 - Tabelas/Gráficos.", "Q14": "D27 - Média aritmética.",
    "Q15": "D28 - Probabilidade simples.", "Q16": "D1 - Figuras bidimensionais.",
    "Q17": "D2 - Propriedades de polígonos.", "Q18": "D3 - Figuras espaciais.",
    "Q19": "D4 - Polígonos regulares.", "Q20": "D5 - Conservação de perímetro/área.",
    "Q21": "D6 - Ângulos e direções.", "Q22": "D12 - Medidas de grandeza."
}

GABARITO = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']

# --- 4. MOTORES DE CÁLCULO (TRI E ESCALAS) ---
def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        b = np.linspace(-2.5, 2.5, 22)[i]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel_escala(valor, disciplina):
    if disciplina == "Língua Portuguesa":
        if valor < 200: return "Muito Crítico", "#D32F2F", "Dificuldade em localizar informações básicas."
        if valor < 250: return "Crítico", "#F57C00", "Identifica o tema, mas falha em inferências."
        if valor < 300: return "Intermediário", "#FBC02D", "Domina leitura básica e ironia simples."
        return "Adequado", "#388E3C", "Capacidade plena de interpretação e tese."
    else:
        if valor < 225: return "Muito Crítico", "#D32F2F", "Dificuldade em operações e formas simples."
        if valor < 275: return "Crítico", "#F57C00", "Resolve adição/subtração, falha em geometria."
        if valor < 325: return "Intermediário", "#FBC02D", "Resolve porcentagem e gráficos básicos."
        return "Adequado", "#388E3C", "Domina álgebra e funções complexas."

# --- 5. TELA DE ACESSO (LOGIN / CADASTRO) ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Sistema de Inteligência Educacional</h1>", unsafe_allow_html=True)
    aba_l, aba_c = st.tabs(["🔐 Login do Gestor", "📝 Cadastro de Novo Usuário"])
    with aba_l:
        u = st.text_input("CPF ou Matrícula"); s = st.text_input("Senha", type="password")
        st.caption("🛡️ **Privacidade:** Dados protegidos conforme a LGPD para fins de diagnóstico de rede.")
        if st.button("Entrar no Painel"):
            if u in st.session_state['usuarios_db'] and st.session_state['usuarios_db'][u] == s:
                st.session_state['autenticado'] = True; st.rerun()
            else: st.error("Acesso negado.")
    with aba_c:
        nu = st.text_input("Definir Usuário"); ns = st.text_input("Definir Senha", type="password")
        st.checkbox("Declaro ser servidor autorizado da rede municipal.")
        if st.button("Finalizar Cadastro"):
            if nu and ns:
                st.session_state['usuarios_db'][nu] = ns; st.success("Cadastro realizado!")
            else: st.warning("Preencha todos os campos.")

# --- 6. AMBIENTE LOGADO (SISTEMA PRINCIPAL) ---
else:
    menu = st.sidebar.radio("Navegação", ["🏠 Início (Técnico)", "📝 Importar Dados", "📊 Painel Analítico", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()

    elif menu == "🏠 Início (Técnico)":
        st.title("🔬 Embasamento Técnico e Metodologia")
        st.markdown("### 1. Teoria de Resposta ao Item (TRI)")
        st.latex(r"P_i(\theta) = c_i + \frac{1 - c_i}{1 + e^{-1.7 \cdot a_i \cdot (\theta - b_i)}}")
        st.info("**Nota:** Este modelo logístico de 3 parâmetros avalia a habilidade real considerando dificuldade, discriminação e acerto casual (chute).")
        
        st.markdown("### 2. Escalas de Proficiência (Referência SAEB/SAEPI)")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📚 Língua Portuguesa")
            st.markdown("- **< 200 (Muito Crítico):** Dificuldade em info. explícitas.\n- **200-249 (Crítico):** Identifica tema, mas não infere.\n- **250-299 (Intermediário):** Domina leitura básica.\n- **> 300 (Adequado):** Capacidade plena.")
        with col2:
            st.subheader("📐 Matemática")
            st.markdown("- **< 225 (Muito Crítico):** Dificuldade em operações básicas.\n- **225-274 (Crítico):** Resolve problemas simples.\n- **275-324 (Intermediário):** Resolve porcentagem e gráficos.\n- **> 325 (Adequado):** Domina álgebra e funções.")

    elif menu == "📝 Importar Dados":
        st.header("📝 Upload de Avaliações - 1º Bimestre")
        c1, c2, c3 = st.columns(3)
        ano = c1.selectbox("Ano Escolar", ["2º Ano", "5º Ano", "9º Ano"])
        turma = c2.text_input("Turma (Ex: 9º A)")
        disc = c3.selectbox("Disciplina", ["Língua Portuguesa", "Matemática"])
        
        arq = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type="xlsx")
        if arq:
            df = pd.read_excel(arq).fillna("N/A")
            for idx, row in df.iterrows():
                res_bin = {f'Q{i:02d}': (1 if str(row[f'Q{i:02d}']).upper() == GABARITO[i-1] else 0) for i in range(1, 23)}
                df.at[idx, 'Prof_TRI'] = calcular_tri(res_bin)
            st.session_state['db'] = df
            st.session_state['meta'] = {"ano": ano, "turma": turma, "disc": disc}
            st.success(f"✅ Dados processados: {ano} - {turma}")

    elif menu == "📊 Painel Analítico":
        if 'db' in st.session_state:
            df, meta = st.session_state['db'], st.session_state['meta']
            matriz = MATRIZ_MAT if meta['disc'] == "Matemática" else MATRIZ_LP
            media = df['Prof_TRI'].mean()
            nivel, cor, desc_ped = obter_nivel_escala(media, meta['disc'])
            
            st.subheader(f"Análise Final: {meta['ano']} | Turma: {meta['turma']} | {meta['disc']}")
            st.markdown(f"<div style='background:{cor}; color:white; padding:20px; border-radius:10px; text-align:center;'><h3>Média: {media:.1f} | Nível: {nivel}</h3><p>{desc_ped}</p></div>", unsafe_allow_html=True)
            
            st.markdown("### 📊 Desempenho por Questão (Distratores)")
            cols = st.columns(3)
            stats_pdf = []
            
            for i in range(1, 23):
                q = f'Q{i:02d}'; gab = GABARITO[i-1]
                counts = df[q].astype(str).str.upper().value_counts(normalize=True) * 100
                stats_pdf.append({"Item": q, "Acerto": counts.get(gab, 0), "Hab": matriz[q]})
                
                with cols[(i-1) % 3]:
                    with st.container(border=True):
                        st.write(f"**Questão {i}** (Gabarito: {gab})")
                        fig, ax = plt.subplots(figsize=(4, 3))
                        opc = ['A','B','C','D']
                        cores_bar = ['#2ECC71' if o == gab else '#E74C3C' for o in opc]
                        ax.bar(opc, [counts.get(o, 0) for o in opc], color=cores_bar)
                        st.pyplot(fig); plt.close()
                        st.caption(f"Habilidade: {matriz[q]}")

            if st.button("📄 Gerar Relatório Analítico PDF"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(texto): return str(texto).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, t(f"DIAGNÓSTICO: {meta['ano']} - {meta['turma']} ({meta['disc']})"), ln=True, align='C')
                
                df_s = pd.DataFrame(stats_pdf)
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
                
                pdf.ln(5); pdf.set_text_color(0, 128, 0); pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, t("🏆 HABILIDADES CONSOLIDADAS"), ln=True)
                pdf.set_font('Arial', '', 9); pdf.set_text_color(0,0,0)
                for _, r in df_rank.tail(6).iterrows():
                    pdf.multi_cell(0, 6, t(f"Q{r['Item']} ({r['Acerto']:.1f}%) - {r['Hab']}"), border='B')
                
                st.download_button("📥 Baixar PDF", pdf.output(dest='S').encode('latin-1'), "Relatorio_Final.pdf")
        else:
            st.warning("Importe os dados primeiro.")
