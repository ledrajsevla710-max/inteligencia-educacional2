import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import os

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestão TRI Município", layout="wide", page_icon="🏛️")

# --- 2. MATRIZ DE REFERÊNCIA DETALHADA ---
MAPA_HABILIDADES = {
    "Matemática": {
        "Q01": {"desc": "D6 - Reconhecer ângulos como mudança de direção ou giros de segmentos de reta.", "sugestao": "Trabalhar com transferidor e giros de ponteiros de relógio."},
        "Q02": {"desc": "EF06MA27 - Determinar medidas de ângulos (reto, agudo, obtuso).", "sugestao": "Utilizar dobraduras de papel para identificar ângulos retos e agudos."},
        "Q03": {"desc": "EF06MA26 - Resolver problemas que envolvam a noção de ângulo em diferentes contextos.", "sugestao": "Aplicar em problemas de navegação e mapas (mudança de rota)."},
        "Q04": {"desc": "D16 - Identificar a localização de números inteiros na reta numérica.", "sugestao": "Usar termômetros e escalas de altitude (acima/abaixo de zero)."},
        "Q05": {"desc": "D20 - Resolver problemas com números inteiros (adição e subtração).", "sugestao": "Simular situações de extrato bancário (crédito e débito)."},
        "Q06": {"desc": "EF07MA04 - Operações com números inteiros (multiplicação e divisão).", "sugestao": "Trabalhar a regra de sinais com jogos de tabuleiro."},
        "Q07": {"desc": "D21 - Reconhecer diferentes representações de um número racional.", "sugestao": "Relacionar frações de pizza com números decimais e porcentagem."},
        "Q08": {"desc": "D23 - Identificar frações equivalentes.", "sugestao": "Usar barras de frações visuais para comparar tamanhos iguais."},
        "Q09": {"desc": "D26 - Resolver problemas com números racionais (decimais).", "sugestao": "Praticar cálculos com moedas e sistema monetário."},
        "Q10": {"desc": "EF07MA10 - Comparar e ordenar números racionais.", "sugestao": "Criar varais de números para ordenação física em sala."},
        "Q11": {"desc": "EF07MA01.1PI - Raiz quadrada exata de números naturais.", "sugestao": "Utilizar áreas de quadrados para visualizar a raiz."},
        "Q12": {"desc": "D19 - Potenciação de números naturais.", "sugestao": "Esquematizar reprodução bacteriana para entender o crescimento."},
        "Q13": {"desc": "D6/EF06MA25 - Ângulos em medidores e ponteiros.", "sugestao": "Analisar velocímetros e medidores de pressão."},
        "Q14": {"desc": "D16/EF07MA03 - Números inteiros em situações de saldo.", "sugestao": "Trabalhar tabelas de campeonatos de futebol (saldo de gols)."},
        "Q15": {"desc": "D21/EF06MA08 - Conversão de frações usuais para decimais.", "sugestao": "Memorizar frações padrão (1/2 = 0,5; 1/4 = 0,25)."},
        "Q16": {"desc": "D23/EF06MA07 - Simplificação de frações.", "sugestao": "Jogos de memória com frações equivalentes."},
        "Q17": {"desc": "D26/EF07MA12 - Operações combinadas com decimais.", "sugestao": "Simular compras em supermercado com descontos."},
        "Q18": {"desc": "D19/EF07MA01 - Problemas envolvendo MMC.", "sugestao": "Usar problemas de horários de ônibus que coincidem."},
        "Q19": {"desc": "D20/EF07MA04 - Regra de sinais na divisão de inteiros.", "sugestao": "Reforçar que sinais iguais resultam em positivo."},
        "Q20": {"desc": "EF06MA27 - Classificar ângulos obtusos.", "sugestao": "Identificar ângulos em telhados e estruturas arquitetônicas."},
        "Q21": {"desc": "D21/EF07MA10 - Transformar decimais em frações.", "sugestao": "Usar a leitura por extenso (ex: 0,5 = cinco décimos)."},
        "Q22": {"desc": "D26/EF06MA03 - Multiplicação de decimais.", "sugestao": "Atenção ao número de casas decimais no resultado final."}
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
    dados = [["Escola A", "9º A", "Exemplo"] + ["C"]*22]
    df_m = pd.DataFrame(dados, columns=colunas)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_m.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. INTERFACE ---
st.title("🏛️ Painel de Gestão Educacional - Município de José de Freitas")
st.sidebar.download_button("📂 Baixar Modelo Excel", gerar_modelo_excel(), "modelo.xlsx", use_container_width=True)

serie = st.sidebar.selectbox("Série:", ["2º Ano", "5º Ano", "9º Ano"])
uploaded_file = st.file_uploader("📥 Carregar Planilha de Resultados", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("X")
    cols_q = [f'Q{i:02d}' for i in range(1, 23)]
    gabarito = GABARITOS["Matemática"]

    # Cálculo Individual
    for idx, row
