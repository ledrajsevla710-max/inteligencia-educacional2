import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, os

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Inteligência Educacional - José de Freitas", layout="wide", page_icon="📊")

# --- 2. GESTÃO DE USUÁRIOS E BANCO DE DADOS (SESSÃO) ---
if 'usuarios_db' not in st.session_state:
    st.session_state['usuarios_db'] = {"12345": "000"} 

if 'banco_geral' not in st.session_state:
    st.session_state['banco_geral'] = []

# --- 3. MATRIZES 1º BIMESTRE ---
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
        if valor < 200: return "Muito Crítico", "#D32F2F"
        if valor < 250: return "Crítico", "#F57C00"
        if valor < 300: return "Intermediário", "#FBC02D"
        return "Adequado", "#388E3C"
    else:
        if valor < 225: return "Muito Crítico", "#D32F2F"
        if valor < 275: return "Crítico", "#F57C00"
        if valor < 325: return "Intermediário", "#FBC02D"
        return "Adequado", "#388E3C"

# --- 5. LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Sistema de Inteligência Educacional</h1>", unsafe_allow_html=True)
    u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in st.session_state['usuarios_db'] and st.session_state['usuarios_db'][u] == s:
            st.session_state['autenticado'] = True; st.rerun()
else:
    # --- 6. MENU ---
    menu = st.sidebar.radio("Navegação", ["📝 Importar Dados", "📊 Painel Analítico", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False; st.rerun()

    elif menu == "📝 Importar Dados":
        st.header("📝 Importar Nova Planilha")
        c1, c2, c3, c4 = st.columns(4)
        esc = c1.text_input("Escola")
        ano = c2.selectbox("Ano", ["2º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano"])
        turma = c3.text_input("Turma")
        disc = c4.selectbox("Disciplina", ["Língua Portuguesa", "Matemática"])
        
        arq = st.file_uploader("Excel", type="xlsx")
        if arq:
            df = pd.read_excel(arq).fillna("N/A")
            num_ano = "".join(filter(str.isdigit, ano))
            if num_ano not in arq.name and not df.astype(str).apply(lambda x: x.str.contains(num_ano)).any().any():
                st.error("Planilha incompatível com o ano selecionado.")
            else:
                if st.button("Salvar Dados"):
                    for idx, row in df.iterrows():
                        res_bin = {f'Q{i:02d}': (1 if str(row[f'Q{i:02d}']).upper() == GABARITO[i-1] else 0) for i in range(1, 23)}
                        df.at[idx, 'Prof_TRI'] = calcular_tri(res_bin)
                    
                    # Salva metadados no DataFrame para filtros posteriores
                    df['Escola'] = esc
                    df['Ano'] = ano
                    df['Turma'] = turma
                    df['Disciplina'] = disc
                    
                    st.session_state['banco_geral'].append(df)
                    st.success("Dados salvos!")

    elif menu == "📊 Painel Analítico":
        if not st.session_state['banco_geral']:
            st.warning("Nenhum dado no banco.")
        else:
            # Consolida todo o banco em um único DataFrame
            df_total = pd.concat(st.session_state['banco_geral'], ignore_index=True)
            
            st.title("📊 Filtros de Resultado")
            # Opções de Filtro
            tipo_view = st.radio("Selecione o Nível de Visualização:", ["Geral (Rede)", "Por Escola", "Por Turma"], horizontal=True)
            
            df_filtrado = df_total.copy()
            titulo_analise = "Resultado Geral da Rede"

            if tipo_view == "Por Escola":
                lista_escolas = df_total['Escola'].unique()
                escolha_esc = st.selectbox("Selecione a Escola", lista_escolas)
                df_filtrado = df_total[df_total['Escola'] == escolha_esc]
                titulo_analise = f"Resultado: {escolha_esc}"
            
            elif tipo_view == "Por Turma":
                lista_escolas = df_total['Escola'].unique()
                escolha_esc = st.selectbox("Selecione a Escola", lista_escolas)
                turmas_da_escola = df_total[df_total['Escola'] == escolha_esc]['Turma'].unique()
                escolha_turma = st.selectbox("Selecione a Turma", turmas_da_escola)
                df_filtrado = df_total[(df_total['Escola'] == escolha_esc) & (df_total['Turma'] == escolha_turma)]
                titulo_analise = f"Resultado: {escolha_esc} - Turma {escolha_turma}"

            # --- EXIBIÇÃO DOS RESULTADOS ---
            st.divider()
            st.header(titulo_analise)
            
            # Média e Nível
            media_final = df_filtrado['Prof_TRI'].mean()
            disc_ref = df_filtrado['Disciplina'].iloc[0]
            nivel, cor = obter_nivel_escala(media_final, disc_ref)
            
            st.markdown(f"<div style='background:{cor}; color:white; padding:20px; border-radius:10px; text-align:center;'><h2>Média TRI: {media_final:.1f} | Nível: {nivel}</h2></div>", unsafe_allow_html=True)

            # --- GRÁFICOS (RESTURADOS) ---
            st.subheader("🎯 Desempenho por Item")
            matriz_ref = MATRIZ_MAT if disc_ref == "Matemática" else MATRIZ_LP
            cols = st.columns(3)
            
            for i in range(1, 23):
                q = f'Q{i:02d}'; gab = GABARITO[i-1]
                counts = df_filtrado[q].astype(str).str.upper().value_counts(normalize=True) * 100
                
                with cols[(i-1) % 3]:
                    with st.container(border=True):
                        st.write(f"**Questão {i}** (Gabarito: {gab})")
                        fig, ax = plt.subplots(figsize=(4, 3))
                        opc = ['A','B','C','D']
                        cores = ['#2ECC71' if o == gab else '#E74C3C' for o in opc]
                        ax.bar(opc, [counts.get(o, 0) for o in opc], color=cores)
                        ax.set_ylim(0, 100)
                        st.pyplot(fig)
                        plt.close()
                        st.caption(f"Habilidade: {matriz_ref[q]}")

            # --- PDF ---
            if st.button("Gerar PDF do Resultado Atual"):
                pdf = FPDF(orientation='L', unit='mm', format='A4'); pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f"RELATORIO - {titulo_analise}", ln=True, align='C')
                pdf.cell(0, 10, f"MEDIA: {media_final:.1f} - NIVEL: {nivel}", ln=True, align='C')
                
                # Gráfico Geral para o PDF
                fig_pdf, ax_pdf = plt.subplots(figsize=(10, 4))
                acertos_lista = [df_filtrado[f'Q{i:02d}'].astype(str).str.upper().value_counts(normalize=True).get(GABARITO[i-1], 0)*100 for i in range(1, 23)]
                ax_pdf.bar([f"Q{i}" for i in range(1, 23)], acertos_lista, color='#1E3A8A')
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); plt.close()
                    pdf.image(tmp.name, x=10, y=40, w=270)
                os.unlink(tmp.name)
                
                st.download_button("Baixar PDF", pdf.output(dest='S').encode('latin-1'), "Relatorio.pdf")
