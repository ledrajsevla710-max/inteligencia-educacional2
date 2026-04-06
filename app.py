import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Sistema de Inteligência Educacional", layout="wide", page_icon="📊")

# --- 2. GESTÃO DE USUÁRIOS (SESSÃO) ---
if 'usuarios_db' not in st.session_state:
    st.session_state['usuarios_db'] = {"12345": "000"} # Usuário padrão inicial

# --- 3. MATRIZES PEDAGÓGICAS - 1º BIMESTRE ---
# Língua Portuguesa: Foco em Localização, Inferência e Tema
MATRIZ_LP = {
    "Q01": "D1 - Localizar informações explícitas em textos.",
    "Q02": "D3 - Inferir o sentido de palavra ou expressão.",
    "Q03": "D4 - Inferir informação implícita em textos.",
    "Q04": "D6 - Identificar o tema de um texto.",
    "Q05": "D14 - Distinguir um fato da opinião relativa a esse fato.",
    "Q06": "D1 - Localizar informações explícitas em textos.",
    "Q07": "D4 - Inferir informação implícita em textos.",
    "Q08": "D5 - Interpretar texto com auxílio de material gráfico diverso.",
    "Q09": "D3 - Inferir o sentido de palavra ou expressão.",
    "Q10": "D6 - Identificar o tema de um texto.",
    "Q11": "D12 - Identificar a finalidade de textos de diferentes gêneros.",
    "Q12": "D1 - Localizar informações explícitas em textos.",
    "Q13": "D3 - Inferir o sentido de palavra ou expressão.",
    "Q14": "D4 - Inferir informação implícita em textos.",
    "Q15": "D6 - Identificar o tema de um texto.",
    "Q16": "D14 - Distinguir um fato da opinião relativa a esse fato.",
    "Q17": "D1 - Localizar informações explícitas em textos.",
    "Q18": "D4 - Inferir informação implícita em textos.",
    "Q19": "D5 - Interpretar texto com auxílio de material gráfico diverso.",
    "Q20": "D6 - Identificar o tema de um texto.",
    "Q21": "D3 - Inferir o sentido de palavra ou expressão.",
    "Q22": "D12 - Identificar a finalidade de textos de diferentes gêneros."
}

# Matemática: Foco em Espaço e Forma / Grandezas e Medidas
MATRIZ_MAT = {
    "Q01": "D1 - Identificar figuras bidimensionais.",
    "Q02": "D2 - Reconhecer propriedades comuns de polígonos.",
    "Q03": "D3 - Identificar relações entre figuras espaciais.",
    "Q04": "D4 - Identificar polígonos regulares.",
    "Q05": "D5 - Reconhecer conservação de perímetro/área.",
    "Q06": "D6 - Reconhecer ângulos como mudança de direção.",
    "Q07": "D12 - Resolver problemas com medidas de grandeza.",
    "Q08": "D13 - Calcular área de figuras planas.",
    "Q09": "D14 - Resolver problema com noções de volume.",
    "Q10": "D16 - Identificar localização em mapas/malhas.",
    "Q11": "D17 - Identificar coordenadas no plano cartesiano.",
    "Q12": "D18 - Reconhecer expressão algébrica.",
    "Q13": "D19 - Resolver problema com inequações de 1º grau.",
    "Q14": "D20 - Analisar crescimento/decrescimento de função.",
    "Q15": "D21 - Resolver sistema de equações de 1º grau.",
    "Q16": "D22 - Identificar gráfico de funções de 1º grau.",
    "Q17": "D23 - Resolver problemas com porcentagem.",
    "Q18": "D24 - Resolver problemas com juros simples.",
    "Q19": "D25 - Resolver problemas com grandezas proporcionais.",
    "Q20": "D26 - Associar informações de tabelas/gráficos.",
    "Q21": "D27 - Calcular média aritmética de dados.",
    "Q22": "D28 - Resolver problema com probabilidade simples."
}

# Gabarito Padrão (Exemplo para 22 questões)
GABARITO = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']

# --- 4. FUNÇÕES DE APOIO ---
def obter_nivel_escala(valor, disciplina):
    if disciplina == "Língua Portuguesa":
        if valor < 200: return "Muito Crítico", "#D32F2F"
        if valor < 250: return "Crítico", "#F57C00"
        if valor < 300: return "Intermediário", "#FBC02D"
        return "Adequado", "#388E3C"
    else: # Matemática
        if valor < 225: return "Muito Crítico", "#D32F2F"
        if valor < 275: return "Crítico", "#F57C00"
        if valor < 325: return "Intermediário", "#FBC02D"
        return "Adequado", "#388E3C"

def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for i, (q, acerto) in enumerate(respostas.items()):
        b = np.linspace(-2.5, 2.5, 22)[i] # Dificuldade simulada
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    theta_final = thetas[np.argmax(verossimilhanca)]
    return (theta_final + 4) * 50 # Conversão para escala SAEB (0-400)

# --- 5. LÓGICA DE ACESSO (LOGIN / CADASTRO) ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ Portal de Inteligência Educacional</h1>", unsafe_allow_html=True)
    
    aba_login, aba_cadastro = st.tabs(["🔐 Acessar Sistema", "📝 Criar Nova Conta"])
    
    with aba_login:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.container(border=True):
                u = st.text_input("Usuário (CPF ou Matrícula)")
                s = st.text_input("Senha", type="password")
                st.markdown("---")
                st.caption("🛡️ **Aviso de Privacidade:** Os dados aqui processados destinam-se exclusivamente ao diagnóstico pedagógico da rede municipal, em conformidade com a LGPD.")
                if st.button("Entrar no Sistema", use_container_width=True):
                    if u in st.session_state['usuarios_db'] and st.session_state['usuarios_db'][u] == s:
                        st.session_state['autenticado'] = True
                        st.rerun()
                    else: st.error("Acesso negado. Verifique suas credenciais.")

    with aba_cadastro:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.container(border=True):
                st.subheader("Cadastro de Novo Gestor")
                novo_u = st.text_input("Defina seu Usuário")
                nova_s = st.text_input("Defina sua Senha", type="password")
                conf_s = st.text_input("Confirme a Senha", type="password")
                aceite = st.checkbox("Li e aceito os termos de uso de dados educacionais.")
                if st.button("Finalizar Cadastro", use_container_width=True):
                    if novo_u == "" or nova_s == "": st.warning("Preencha todos os campos.")
                    elif nova_s != conf_s: st.error("As senhas não coincidem.")
                    elif not aceite: st.error("É necessário aceitar os termos de privacidade.")
                    else:
                        st.session_state['usuarios_db'][novo_u] = nova_s
                        st.success("✅ Conta criada com sucesso! Vá para a aba de Login.")

# --- 6. AMBIENTE LOGADO ---
else:
    menu = st.sidebar.radio("Navegação Principal:", ["🏠 Início", "📝 Importar Avaliações", "📊 Analisar Resultados", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "🏠 Início":
        st.title("👋 Bem-vindo, Jardel Alves Vieira!")
        st.markdown("### 📊 Escalas de Referência (SAEPI/SAEB)")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**Língua Portuguesa**")
            st.write("🔴 < 200: Muito Crítico | 🟠 < 250: Crítico | 🟡 < 300: Intermediário | 🟢 > 300: Adequado")
        with c2:
            st.success("**Matemática**")
            st.write("🔴 < 225: Muito Crítico | 🟠 < 275: Crítico | 🟡 < 325: Intermediário | 🟢 > 325: Adequado")
        
        st.markdown("### 🔬 Cálculo TRI")
        st.latex(r"P_i(\theta) = c_i + \frac{1 - c_i}{1 + e^{-1.7 \cdot a_i \cdot (\theta - b_i)}}")

    elif menu == "📝 Importar Avaliações":
        st.header("📝 Importação de Dados do 1º Bimestre")
        c1, c2, c3 = st.columns(3)
        disc = c1.selectbox("Disciplina:", ["Língua Portuguesa", "Matemática"])
        ano = c2.selectbox("Ano Escolar:", ["2º Ano", "5º Ano", "9º Ano"])
        arq = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type="xlsx")

        if arq:
            df = pd.read_excel(arq).fillna("N/A")
            for idx, row in df.iterrows():
                res_bin = {f'Q{i:02d}': (1 if str(row[f'Q{i:02d}']).upper() == GABARITO[i-1] else 0) for i in range(1, 23)}
                df.at[idx, 'Prof_TRI'] = calcular_tri(res_bin)
            st.session_state['dados_atuais'] = df
            st.session_state['disc_ativa'] = disc
            st.session_state['ano_ativo'] = ano
            st.success("✅ Dados processados com sucesso!")

    elif menu == "📊 Analisar Resultados":
        if 'dados_atuais' in st.session_state:
            df = st.session_state['dados_atuais']
            disc = st.session_state['disc_ativa']
            matriz = MATRIZ_MAT if disc == "Matemática" else MATRIZ_LP
            media = df['Prof_TRI'].mean()
            nivel, cor = obter_nivel_escala(media, disc)
            
            st.markdown(f"<div style='background:{cor}; color:white; padding:20px; text-align:center; border-radius:10px; font-size:24px;'>Média da Rede: {media:.1f} - Nível: {nivel}</div>", unsafe_allow_html=True)
            
            stats = []
            for i in range(1, 23):
                q = f'Q{i:02d}'
                perc = (df[q].astype(str).str.upper() == GABARITO[i-1]).mean() * 100
                stats.append({"Questao": q, "Acerto": perc, "Habilidade": matriz[q]})
            
            df_stats = pd.DataFrame(stats)
            st.subheader("Performance por Questão")
            st.bar_chart(df_stats.set_index("Questao")["Acerto"])

            if st.button("📄 Gerar Relatório Analítico (PDF)"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                def t(texto): return str(texto).encode('latin-1', 'replace').decode('latin-1')
                
                # Cabeçalho e Gráfico
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, t(f"DIAGNÓSTICO EDUCACIONAL: {disc} - {st.session_state['ano_ativo']}"), ln=True, align='C')
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, t(f"Proficiência Média: {media:.1f} ({nivel})"), ln=True, align='C')
                
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(df_stats['Questao'], df_stats['Acerto'], color='#1E3A8A')
                ax.set_ylim(0, 105)
                ax.set_ylabel("% de Acerto")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); plt.close()
                    pdf.image(tmp.name, x=10, y=40, w=270)
                os.unlink(tmp.name)
                
                # Página 2: Detalhamento Pedagógico
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, t("📋 Detalhamento por Habilidades"), ln=True)
                
                df_rank = df_stats.sort_values(by="Acerto")
                
                # Alerta Vermelho
                pdf.set_text_color(200, 0, 0); pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, t("⚠️ ALERTA: Habilidades com menor domínio (Intervenção Imediata)"), ln=True)
                pdf.set_font('Arial', '', 9); pdf.set_text_color(0,0,0)
                for _, r in df_rank.head(6).iterrows():
                    pdf.multi_cell(0, 6, t(f"Questão {r['Questao']} ({r['Acerto']:.1f}%) - {r['Habilidade']}"), border='B')
                
                # Destaques Verdes
                pdf.ln(5); pdf.set_text_color(0, 128, 0); pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, t("🏆 DESTAQUES: Habilidades Consolidadas"), ln=True)
                pdf.set_font('Arial', '', 9); pdf.set_text_color(0,0,0)
                for _, r in df_rank.tail(6).iterrows():
                    pdf.multi_cell(0, 6, t(f"Questão {r['Questao']} ({r['Acerto']:.1f}%) - {r['Habilidade']}"), border='B')

                st.download_button("📥 Baixar Relatório Completo", pdf.output(dest='S').encode('latin-1'), "Relatorio_Final.pdf", "application/pdf")
        else:
            st.warning("Por favor, importe os dados primeiro.")
