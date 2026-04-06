import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor TRI Municipal", layout="wide", page_icon="🏛️")

# --- 2. MATRIZ DE HABILIDADES (Edite os textos abaixo com sua matriz oficial) ---
MATRIZ_OFICIAL = {
    "Q01": "D1 - Localizar informações explícitas em um texto.",
    "Q02": "D3 - Inferir o sentido de uma palavra ou expressão.",
    "Q03": "D4 - Inferir uma informação implícita em um texto.",
    "Q04": "D6 - Identificar o tema de um texto.",
    "Q05": "D12 - Identificar a finalidade de textos de diferentes gêneros.",
    "Q06": "D2 - Estabelecer relações entre partes de um texto.",
    "Q07": "D5 - Interpretar texto com auxílio de material gráfico.",
    "Q08": "D7 - Identificar a tese de um texto.",
    "Q09": "D8 - Estabelecer relação entre a tese e os argumentos.",
    "Q10": "D9 - Diferenciar as partes principais das secundárias em um texto.",
    "Q11": "D10 - Identificar o conflito gerador do enredo.",
    "Q12": "D11 - Estabelecer relação de causa e consequência.",
    "Q13": "D13 - Identificar as marcas linguísticas de um locutor.",
    "Q14": "D14 - Distinguir um fato de uma opinião.",
    "Q15": "D15 - Estabelecer relações lógico-discursivas.",
    "Q16": "D16 - Identificar efeitos de ironia ou humor.",
    "Q17": "D17 - Identificar o efeito de sentido decorrente da pontuação.",
    "Q18": "D18 - Reconhecer o efeito de sentido decorrente de escolha de palavras.",
    "Q19": "D19 - Reconhecer o efeito de sentido decorrente de recursos gráficos.",
    "Q20": "D20 - Reconhecer diferentes formas de tratar uma informação.",
    "Q21": "D21 - Reconhecer posições distintas entre dois textos.",
    "Q22": "D22 - Identificar o efeito de sentido decorrente da exploração de recursos ortográficos."
}

# --- 3. LÓGICA DE ACESSO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None

if not st.session_state['autenticado']:
    st.title("🏛️ Portal TRI Municipal")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "12345" and senha == "000":
            st.session_state['autenticado'] = True
            st.rerun()
else:
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "⚙️ Importar Dados", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    # --- ABA: IMPORTAR DADOS (SEM TRAVA) ---
    elif menu == "⚙️ Importar Dados":
        st.header("⚙️ Importar Avaliações")
        materia = st.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
        serie_sistema = st.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])
        
        arquivo = st.file_uploader("Subir Excel", type="xlsx")
        if arquivo:
            # Lendo o arquivo sem travas de validação de série
            df_temp = pd.read_excel(arquivo).fillna("X")
            st.success(f"✅ Arquivo lido com sucesso! Processando dados de {materia}...")
            st.session_state['banco_dados'] = df_temp

    # --- ABA: DASHBOARD ---
    elif menu == "📊 Dashboard":
        if st.session_state['banco_dados'] is not None:
            df = st.session_state['banco_dados']
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            gab_dict = {f'Q{i:02d}': gab[i-1] for i in range(1, 23)}

            f_esc = st.sidebar.selectbox("Escola:", ["Geral Município"] + list(df['Escola'].unique()))
            df_f = df if f_esc == "Geral Município" else df[df['Escola'] == f_esc]

            st.header(f"📊 Análise: {f_esc}")

            # 1. TABELA DE ACERTOS COM DESCRIÇÃO DA HABILIDADE
            st.subheader("📋 Percentual de Acertos e Habilidades")
            dados_dashboard = []
            for q in cols_q:
                total = len(df_f)
                acertos = len(df_f[df_f[q].astype(str).str.upper() == gab_dict[q]])
                perc = (acertos / total) * 100
                dados_dashboard.append({
                    "Item": q,
                    "Acerto (%)": f"{perc:.1f}%",
                    "Erro (%)": f"{100 - perc:.1f}%",
                    "Habilidade/Descritor": MATRIZ_OFICIAL.get(q, "Não mapeada")
                })
            
            st.table(pd.DataFrame(dados_dashboard))

            # --- 2. RELATÓRIO PDF EM PAISAGEM ---
            st.divider()
            if st.button("📄 Gerar Relatório Profissional (Paisagem)"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Arial', 'B', 18)
                pdf.cell(0, 15, f'RELATÓRIO DE DESEMPENHO - {f_esc}', ln=True, align='C')
                
                # Gráfico Grande
                fig, ax = plt.subplots(figsize=(14, 5))
                questoes = [d['Item'] for d in dados_dashboard]
                valores = [float(d['Acerto (%)'].replace('%','')) for d in dados_dashboard]
                
                barras = ax.bar(questoes, valores, color='#3498DB', edgecolor='black')
                ax.set_ylabel('% de Acerto')
                ax.set_ylim(0, 110) # Margem para os rótulos
                
                # Adiciona o valor em cima de cada barra
                for barra in barras:
                    height = barra.get_height()
                    ax.annotate(f'{height:.0f}%', xy=(barra.get_x() + barra.get_width() / 2, height),
                                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name, bbox_inches='tight')
                    pdf.image(tmp.name, x=10, y=35, w=275)
                
                # Lista de Habilidades Críticas no PDF
                pdf.set_y(145)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "Diagnóstico das Habilidades Mais Críticas (Menor Acerto):", ln=True)
                pdf.set_font('Arial', '', 10)
                
                # Ordena pelas 5 piores para o relatório
                piores = sorted(dados_dashboard, key=lambda x: float(x['Acerto (%)'].replace('%','')))[:5]
                for p in piores:
                    txt = f"- {p['Item']}: {p['Habilidade/Descritor']} (Acerto: {p['Acerto (%)']})"
                    pdf.multi_cell(0, 7, txt.encode('latin-1', 'replace').decode('latin-1'))

                st.download_button("📥 Baixar PDF Paisagem", pdf.output(dest='S').encode('latin-1'), f"Relatorio_{f_esc}.pdf")
        else:
            st.info("⚠️ Aguardando envio da planilha para gerar o Dashboard.")
