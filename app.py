import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io

# --- 1. CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Gestão TRI José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. MATRIZ DE REFERÊNCIA DETALHADA ---
MAPA_HABILIDADES = {
    "Matemática": {
        "Q01": {"desc": "D6 - Reconhecer ângulos como mudança de direção ou giros.", "sugestao": "Praticar com ponteiros de relógio e transferidor."},
        "Q02": {"desc": "EF06MA27 - Determinar medidas de ângulos (reto, agudo, obtuso).", "sugestao": "Identificar ângulos em objetos do cotidiano."},
        "Q03": {"desc": "EF06MA26 - Resolver problemas com noção de ângulo.", "sugestao": "Trabalhar mudanças de direção em mapas."},
        "Q04": {"desc": "D16 - Localização de números inteiros na reta numérica.", "sugestao": "Usar termômetros e fita métrica para escalas negativas."},
        "Q05": {"desc": "D20 - Resolver problemas com números inteiros (+/-).", "sugestao": "Simular saldo bancário e extratos."},
        "Q06": {"desc": "EF07MA04 - Operações com números inteiros (x/:).", "sugestao": "Reforçar a regra de sinais com jogos."},
        "Q07": {"desc": "D21 - Diferentes representações de números racionais.", "sugestao": "Relacionar frações com decimais e porcentagem."},
        "Q08": {"desc": "D23 - Identificar frações equivalentes.", "sugestao": "Uso de material dourado ou barras de frações."},
        "Q09": {"desc": "D26 - Problemas com números racionais (decimais).", "sugestao": "Atividades com sistema monetário (dinheiro)."},
        "Q10": {"desc": "EF07MA10 - Comparar e ordenar números racionais.", "sugestao": "Exercícios de reta numérica com decimais."},
        "Q11": {"desc": "EF07MA01.1PI - Raiz quadrada exata.", "sugestao": "Desenhar quadrados para visualizar a área e o lado."},
        "Q12": {"desc": "D19 - Potenciação de números naturais.", "sugestao": "Explicar através de replicação (dobro do dobro)."},
        "Q13": {"desc": "D6/EF06MA25 - Ângulos em medidores e ponteiros.", "sugestao": "Análise de velocímetros e manômetros."},
        "Q14": {"desc": "D16/EF07MA03 - Números inteiros em situações de saldo.", "sugestao": "Tabelas de saldo de gols e campeonatos."},
        "Q15": {"desc": "D21/EF06MA08 - Conversão de frações para decimais.", "sugestao": "Praticar divisões sucessivas."},
        "Q16": {"desc": "D23/EF06MA07 - Simplificação de frações.", "sugestao": "Trabalhar o conceito de partes iguais menores."},
        "Q17": {"desc": "D26/EF07MA12 - Operações combinadas com decimais.", "sugestao": "Cálculos de compras com troco e descontos."},
        "Q18": {"desc": "D19/EF07MA01 - Problemas envolvendo MMC.", "sugestao": "Problemas de encontros de horários cíclicos."},
        "Q19": {"desc": "D20/EF07MA04 - Regra de sinais na divisão.", "sugestao": "Fixação de tabelas de sinais."},
        "Q20": {"desc": "EF06MA27 - Classificar ângulos obtusos.", "sugestao": "Identificar ângulos em telhados."},
        "Q21": {"desc": "D21/EF07MA10 - Transformar decimais em frações.", "sugestao": "Ler o número (cinco décimos = 5/10)."},
        "Q22": {"desc": "D26/EF06MA03 - Multiplicação de decimais.", "sugestao": "Atenção ao posicionamento da vírgula."}
    }
}

GABARITOS = {
    "Matemática": {f'Q{i:02d}': g for i, g in enumerate(['C','B','A','C','B','C','C','A','B','C','C','C','D','C','B','A','C','C','A','C','B','B'], 1)}
}

# --- 3. FUNÇÕES TÉCNICAS ---
def calcular_tri(respostas_binarias):
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    for q, acerto in respostas_binarias.items():
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        verossimilhanca *= p if acerto == 1 else (1 - p)
    return (thetas[np.argmax(verossimilhanca)] + 4) * 50

def obter_nivel(score):
    if score < 150: return "Abaixo do Básico", "#FF4B4B"
    if score < 200: return "Básico", "#FACA2E"
    if score < 250: return "Proficiente", "#00CC96"
    return "Avançado", "#1F77B4"

def gerar_modelo_excel():
    output = io.BytesIO()
    colunas = ["Escola", "Turma", "Nome"] + [f"Q{i:02d}" for i in range(1, 23)]
    dados = [["Escola Exemplo", "9º A", "Aluno Teste"] + ["C"]*22]
    df_m = pd.DataFrame(dados, columns=colunas)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_m.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. INTERFACE ---
st.title("🏛️ Gestão Municipal de Educação - TRI")

st.sidebar.header("Painel Administrativo")
st.sidebar.download_button("📥 Baixar Planilha Modelo", gerar_modelo_excel(), "modelo_gestao.xlsx", use_container_width=True)

serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])
uploaded_file = st.file_uploader("📥 Carregar Planilha Preenchida", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito = GABARITOS["Matemática"]

    # Processamento TRI
    for idx, row in df.iterrows():
        binario = {q: 1 if str(row[q]).upper() == gabarito[q] else 0 for q in cols_q}
        df.at[idx, 'Proficiência'] = calcular_tri(binario)

    # Visão Municipal
    st.subheader("📊 Panorama Geral do Município")
    media_mun = df['Proficiência'].mean()
    st.metric("Proficiência Média Municipal", f"{media_mun:.1f}")

    rank = df.groupby('Escola')['Proficiência'].mean().sort_values().reset_index()
    fig_mun, ax_mun = plt.subplots(figsize=(10, 3))
    ax_mun.barh(rank['Escola'], rank['Proficiência'], color='#1F77B4')
    ax_mun.axvline(media_mun, color='red', linestyle='--', label='Média Geral')
    ax
