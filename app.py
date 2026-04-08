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

# --- 4. MOTORES DE CÁLCULO ---
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

# --- 5. TELA DE ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Sistema de Inteligência Educacional</h1>", unsafe_allow_html=True)
    aba_l, aba_c = st.tabs(["🔐 Login do Gestor", "📝 Cadastro de Novo Usuário"])
    with aba_l:
        u = st.text_input("CPF ou Matrícula"); s = st.text_input("Senha", type="password")
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

# --- 6. AMBIENTE LOGADO ---
else:
    menu = st.sidebar.radio("Navegação", ["🏠 Início (Técnico)", "📝 Importar Dados", "📊 Painel Analítico", "🏢 Relatório por Escola", "🏙️ Relatório Municipal", "🚪 Sair"])

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
        c1, c2, c3, c4 = st.columns(4)
        escola = c1.text_input("Nome da Escola")
        ano = c2.selectbox("Ano Escolar", ["2º Ano", "5º Ano", "9º Ano"])
        turma = c3.text_input("Turma (Ex: 9º A)")
        disc = c4.selectbox("Disciplina", ["Língua Portuguesa", "Matemática"])
        
        arq = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type="xlsx")
        if arq:
            df = pd.read_excel(arq).fillna("N/A")
            for idx, row in df.iterrows():
                res_bin = {f'Q{i:02d}': (1 if str(row[f'Q{i:02d}']).upper() == GABARITO[i-1] else 0) for i in range(1, 23)}
                df.at[idx, 'Prof_TRI'] = calcular_tri(res_bin)
            
            df['Escola'] = escola
            df['Ano_Escolar'] = ano
            df['Turma'] = turma
            df['Disciplina'] = disc
            
            if 'consolidado' not in st.session_state:
                st.session_state['consolidado'] = df
            else:
                st.session_state['consolidado'] = pd.concat([st.session_state['consolidado'], df]).drop_duplicates()
            
            st.session_state['db'] = df
            st.session_state['meta'] = {"ano": ano, "turma": turma, "disc": disc, "escola": escola}
            st.success(f"✅ Dados processados e salvos no banco consolidado!")

    elif menu == "📊 Painel Analítico":
        if 'db' in st.session_state:
            df, meta = st.session_state['db'], st.session_state['meta']
            matriz = MATRIZ_MAT if meta['disc'] == "Matemática" else MATRIZ_LP
            media = df['Prof_TRI'].mean()
            nivel, cor, desc_ped = obter_nivel_escala(media, meta['disc'])
            
            st.subheader(f"Análise: {meta['escola']} | {meta['ano']} | Turma: {meta['turma']}")
            st.markdown(f"<div style='background:{cor}; color:white; padding:20px; border-radius:10px; text-align:center;'><h3>Média: {media:.1f} | Nível: {nivel}</h3><p>{desc_ped}</p></div>", unsafe_allow_html=True)
            
            st.markdown("### 📊 Desempenho por Questão (Distratores)")
            cols = st.columns(3)
            for i in range(1, 23):
                q = f'Q{i:02d}'; gab = GABARITO[i-1]
                counts = df[q].astype(str).str.upper().value_counts(normalize=True) * 100
                with cols[(i-1) % 3]:
                    with st.container(border=True):
                        st.write(f"**Questão {i}** (Gabarito: {gab})")
                        fig, ax = plt.subplots(figsize=(4, 3))
                        ax.bar(['A','B','C','D'], [counts.get(o, 0) for o in ['A','B','C','D']], 
                               color=['#2ECC71' if o == gab else '#E74C3C' for o in ['A','B','C','D']])
                        st.pyplot(fig); plt.close()
                        st.caption(f"Habilidade: {matriz[q]}")

    elif menu in ["🏢 Relatório por Escola", "🏙️ Relatório Municipal"]:
        if 'consolidado' in st.session_state:
            df_geral = st.session_state['consolidado']
            tipo = "MUNICIPAL" if menu == "🏙️ Relatório Municipal" else "POR ESCOLA"
            
            if tipo == "POR ESCOLA":
                escolhas = df_geral['Escola'].unique()
                escolhida = st.selectbox("Selecione a Escola", escolhas)
                df_filtrado = df_geral[df_geral['Escola'] == escolhida]
                titulo_relatorio = f"RELATÓRIO ESCOLAR: {escolhida}"
            else:
                df_filtrado = df_geral
                titulo_relatorio = "RELATÓRIO ESTATÍSTICO MUNICIPAL"

            st.header(f"📈 Consolidação: {tipo}")
            
            disciplinas = df_filtrado['Disciplina'].unique()
            disc_alvo = st.selectbox("Escolha a Disciplina", disciplinas)
            df_final = df_filtrado[df_filtrado['Disciplina'] == disc_alvo]
            matriz = MATRIZ_MAT if disc_alvo == "Matemática" else MATRIZ_LP
            
            stats_list = []
            for i in range(1, 23):
                q = f'Q{i:02d}'; gab = GABARITO[i-1]
                acerto = (df_final[q].astype(str).str.upper() == gab).mean() * 100
                stats_list.append({"Item": q, "Acerto": acerto, "Habilidade": matriz[q]})
            
            df_stats = pd.DataFrame(stats_list)
            st.dataframe(df_stats, use_container_width=True)

            if st.button(f"📥 Gerar PDF {tipo}"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(text): return str(text).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, t(titulo_relatorio), ln=True, align='C')
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, t(f"Disciplina: {disc_alvo} | Amostra: {len(df_final)} alunos"), ln=True, align='C')
                
                fig_g, ax_g = plt.subplots(figsize=(10, 4))
                ax_g.bar(df_stats['Item'], df_stats['Acerto'], color='#1E3A8A')
                ax_g.set_title("Percentual de Acerto por Item")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); plt.close()
                    pdf.image(tmp.name, x=10, y=40, w=270)
                os.unlink(tmp.name)
                
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, t("📋 Detalhamento das Habilidades e Descritores"), ln=True)
                pdf.ln(5)
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(30, 8, "Item", 1); pdf.cell(30, 8, "% Acerto", 1); pdf.cell(0, 8, "Descritor / Habilidade", 1)
                pdf.ln()
                
                pdf.set_font('Arial', '', 9)
                for _, r in df_stats.iterrows():
                    cor_texto = (200, 0, 0) if r['Acerto'] < 50 else (0, 100, 0)
                    pdf.set_text_color(*cor_texto)
                    pdf.cell(30, 7, t(r['Item']), 1)
                    pdf.cell(30, 7, t(f"{r['Acerto']:.1f}%"), 1)
                    pdf.set_text_color(0,0,0)
                    pdf.cell(0, 7, t(r['Habilidade']), 1)
                    pdf.ln()
                
                st.download_button("Baixar Relatório PDF", pdf.output(dest='S').encode('latin-1'), "Relatorio_Consolidado.pdf")
        else:
            st.warning("Sem dados consolidados. Importe arquivos na aba 'Importar Dados'.")
