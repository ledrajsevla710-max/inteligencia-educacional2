import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor TRI Municipal", layout="wide", page_icon="🏛️")

# --- 2. DICIONÁRIO DE HABILIDADES (EXEMPLO) ---
# Aqui você deve preencher com a matriz oficial do SAEPI/SAEB
MATRIZ_HABILIDADES = {
    "Q01": "D1 - Localizar informações explícitas.",
    "Q02": "D3 - Inferir sentido de palavra.",
    "Q03": "D6 - Identificar o tema do texto.",
    # ... adicione as demais até a Q22
}

def obter_diagnostico(score):
    if score < 150: return {"nivel": "CRÍTICO", "cor": "#E74C3C", "sug": "Focar em base alfabética."}
    elif score < 250: return {"nivel": "BÁSICO", "cor": "#F1C40F", "sug": "Reforço em interpretação."}
    elif score < 350: return {"nivel": "PROFICIENTE", "cor": "#2ECC71", "sug": "Consolidar descritores."}
    else: return {"nivel": "AVANÇADO", "cor": "#3498DB", "sug": "Desafios de lógica."}

# --- 3. INTERFACE ---
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

    elif menu == "⚙️ Importar Dados":
        st.header("⚙️ Importar Avaliações")
        materia = st.selectbox("Disciplina:", ["Matemática", "Língua Portuguesa"])
        serie_sistema = st.selectbox("Série Selecionada no Sistema:", ["2º Ano", "5º Ano", "9º Ano"])
        
        arquivo = st.file_uploader("Subir Excel", type="xlsx")
        if arquivo:
            df_temp = pd.read_excel(arquivo)
            
            # --- VALIDAÇÃO DE SÉRIE ---
            serie_planilha = str(df_temp['Série'].iloc[0]) if 'Série' in df_temp.columns else ""
            
            if serie_sistema[:1] not in serie_planilha:
                st.error(f"❌ ERRO DE LEITURA: A planilha enviada é do '{serie_planilha}', mas você selecionou '{serie_sistema}'. Corrija a seleção para continuar.")
            else:
                st.success(f"✅ Validação concluída: Dados do {serie_sistema} lidos com sucesso.")
                # Lógica de cálculo TRI (omitida aqui por brevidade, mas mantida no seu código original)
                st.session_state['banco_dados'] = df_temp

    elif menu == "📊 Dashboard":
        if st.session_state['banco_dados'] is not None:
            df = st.session_state['banco_dados']
            
            st.sidebar.subheader("Filtros")
            f_esc = st.sidebar.selectbox("Escola:", ["Geral Município"] + list(df['Escola'].unique()))
            
            # --- LÓGICA DE CONTRASTE (MUNICÍPIO VS ESCOLA) ---
            # 1. Média de acertos por questão no Município
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D','A','B','C','D','C','A','A','B','C','D','C','C','C','A','C','A','A','B']
            gab_dict = {f'Q{i:02d}': gab[i-1] for i in range(1, 23)}

            def calc_acertos(data):
                acertos = {}
                for q in cols_q:
                    total = len(data)
                    certos = len(data[data[q].str.upper() == gab_dict[q]])
                    acertos[q] = (certos / total) * 100
                return acertos

            acertos_mun = calc_acertos(df)
            pior_q_mun = min(acertos_mun, key=acertos_mun.get)

            if f_esc == "Geral Município":
                st.header("🌍 Visão Geral do Município")
                st.metric("Pior Habilidade da Rede", pior_q_mun)
                st.info(f"**Descritor Crítico:** {MATRIZ_HABILIDADES.get(pior_q_mun, 'Habilidade não mapeada')}")
                
                # Gráfico Único Municipal
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(acertos_mun.keys(), acertos_mun.values(), color='#3498DB')
                ax.axhline(y=sum(acertos_mun.values())/22, color='red', linestyle='--', label='Média Rede')
                st.pyplot(fig)
            
            else:
                st.header(f"🏫 Visão: {f_esc}")
                df_esc = df[df['Escola'] == f_esc]
                acertos_esc = calc_acertos(df_esc)
                
                # Identificar onde a escola destoa do município
                diferenca = {q: acertos_esc[q] - acertos_mun[q] for q in cols_q}
                pior_q_esc = min(diferenca, key=diferenca.get)
                
                st.write(f"Comparado ao Município, sua escola teve maior dificuldade na **{pior_q_esc}**.")
                st.caption(f"Habilidade: {MATRIZ_HABILIDADES.get(pior_q_esc)}")

                # Gráfico de Contraste
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(acertos_mun.keys(), acertos_mun.values(), alpha=0.3, label='Município', color='gray')
                ax.bar(acertos_esc.keys(), acertos_esc.values(), alpha=0.8, label='Escola', color='#2ECC71')
                plt.legend()
                st.pyplot(fig)

            # --- BOTÃO PDF ÚNICO ---
            if st.button("📄 Gerar Relatório Sintético"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, f'RELATÓRIO DE INTERVENÇÃO - {f_esc}', ln=True, align='C')
                
                pdf.set_font('Arial', '', 11)
                pdf.ln(10)
                pdf.multi_cell(0, 7, f"A análise identificou que a habilidade mais crítica é a {pior_q_mun if f_esc == 'Geral Município' else pior_q_esc}.")
                
                # Salvar o gráfico atual para o PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name)
                    pdf.image(tmp.name, x=10, w=180)
                
                st.download_button("📥 Baixar Relatório", pdf.output(dest='S').encode('latin-1'), "Relatorio.pdf")

        else:
            st.warning("⚠️ Importe os dados primeiro.")
