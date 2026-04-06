import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor Pedagógico - José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. MATRIZES DE DESCRITORES REAIS ---
MATRIZ_LP = {
    "Q01": "D1 - Localizar informações explícitas.",
    "Q02": "D3 - Inferir o sentido de palavra/expressão.",
    "Q03": "D4 - Inferir informação implícita.",
    "Q04": "D6 - Identificar o tema do texto.",
    "Q05": "D14 - Distinguir fato de opinião.",
    "Q06": "D12 - Identificar finalidade do texto.",
    "Q07": "D2 - Estabelecer relações entre partes do texto.",
    "Q08": "D5 - Interpretar texto com auxílio de imagem.",
    "Q09": "D7 - Identificar a tese do texto.",
    "Q10": "D8 - Estabelecer relação tese/argumentos.",
    "Q11": "D9 - Diferenciar partes principais/secundárias.",
    "Q12": "D10 - Identificar o conflito do enredo.",
    "Q13": "D11 - Estabelecer relação causa/consequência.",
    "Q14": "D13 - Identificar marcas linguísticas (locutor).",
    "Q15": "D15 - Estabelecer relações lógico-discursivas.",
    "Q16": "D16 - Identificar efeitos de ironia/humor.",
    "Q17": "D17 - Identificar efeito de pontuação.",
    "Q18": "D18 - Efeito de sentido (escolha de palavras).",
    "Q19": "D19 - Efeito de sentido (recursos gráficos).",
    "Q20": "D20 - Diferentes formas de tratar o tema.",
    "Q21": "D21 - Reconhecer posições distintas entre textos.",
    "Q22": "D22 - Identificar recursos ortográficos/estilísticos."
}

MATRIZ_MAT = {
    "Q01": "D1 - Identificar figuras bidimensionais.",
    "Q02": "D2 - Reconhecer propriedades de polígonos.",
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

# --- 3. LÓGICA DE INTERVENÇÃO ---
def sugerir_intervencao(item, matriz):
    desc = matriz.get(item, "")
    if "D1" in desc or "D4" in desc: return "Oficinas de sublinhar palavras-chave."
    elif "D14" in desc or "D13" in desc: return "Debate sobre Fato vs Opinião com notícias."
    elif "D23" in desc or "D24" in desc: return "Resolução de problemas do cotidiano financeiro."
    return "Reforço teórico e exercícios práticos em grupo."

# --- 4. MOTOR TRI ---
def calcular_tri(respostas):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

# --- 5. SESSÃO E LOGIN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal de Avaliação Municipal</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if u == "12345" and s == "000":
                st.session_state['autenticado'] = True; st.rerun()
else:
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "📝 Enviar Avaliações", "📊 Painel de Resultados", "🚪 Sair"])

    if menu == "🏠 Início":
        st.title(f"👋 Bem-vindo, Jardel Alves Vieira!")
        st.write("Sistema de Monitoramento de Proficiência TRI.")

    elif menu == "📝 Enviar Avaliações":
        st.header("📝 Nova Importação")
        if st.session_state['banco_dados'] is not None:
            if st.button("🗑️ LIMPAR DADOS", type="primary"): st.session_state['banco_dados'] = None; st.rerun()
        else:
            c1, c2 = st.columns(2)
            mat = c1.selectbox("Disciplina:", ["Língua Portuguesa", "Matemática"])
            arq = st.file_uploader("Arquivo Excel:", type="xlsx")
            if arq:
                df = pd.read_excel(arq).fillna("X")
                cols_q = [f'Q{i:02d}' for i in range(1, 23)]
                gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
                for idx, row in df.iterrows():
                    binario = {q: 1 if str(row[q]).upper() == gab[int(q[1:])-1] else 0 for q in cols_q}
                    df.at[idx, 'Proficiência_TRI'] = calcular_tri(binario)
                st.session_state['banco_dados'] = df
                st.session_state['mat_ativa'] = mat
                st.success("Dados processados!")

    elif menu == "📊 Painel de Resultados":
        if st.session_state['banco_dados'] is not None:
            df = st.session_state['banco_dados']
            matriz = MATRIZ_MAT if st.session_state['mat_ativa'] == "Matemática" else MATRIZ_LP
            f_esc = st.sidebar.selectbox("Escola:", ["Visão Geral"] + list(df['Escola'].unique()))
            df_f = df if f_esc == "Visão Geral" else df[df['Escola'] == f_esc]

            st.header(f"📊 Análise: {f_esc} ({st.session_state['mat_ativa']})")
            
            # Ranking de Acertos para o Relatório
            stats = []
            for q in [f'Q{i:02d}' for i in range(1, 23)]:
                gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
                idx = int(q[1:])-1
                perc = (len(df_f[df_f[q].astype(str).str.upper() == gab[idx]]) / len(df_f)) * 100
                stats.append({"Item": q, "Acerto": perc, "Habilidade": matriz[q]})
            
            df_stats = pd.DataFrame(stats).sort_values(by="Acerto", ascending=False)

            # Botão PDF Robusto
            if st.button("📄 Gerar Relatório Técnico com Plano de Ação"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f'RELATÓRIO DE DESEMPENHO - {f_esc} ({st.session_state["mat_ativa"]})', ln=True, align='C')
                
                # Gráfico
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.bar(df_stats['Item'], df_stats['Acerto'], color='#1E3A8A')
                ax.set_ylim(0, 105); ax.set_ylabel('% de Acerto')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); pdf.image(tmp.name, x=10, y=30, w=275)
                
                # Segunda Página: Descrições e Intervenção
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "🏆 PONTOS FORTES (Melhores Resultados):", ln=True)
                pdf.set_font('Arial', '', 10)
                for _, r in df_stats.head(3).iterrows():
                    pdf.cell(0, 7, f"- {r['Item']}: {r['Habilidade']} (Acerto: {r['Acerto']:.1f}%)", ln=True)

                pdf.ln(5)
                pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "⚠️ PONTOS DE ATENÇÃO E
