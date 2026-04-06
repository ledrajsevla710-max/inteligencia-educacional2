import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import io
import os

# --- 1. MAPA DE HABILIDADES (PROTÓTIPO 9º ANO - MATEMÁTICA) ---
MAPA_HABILIDADES = {
    "Matemática": {
        "Q01": "D6 - Reconhecer ângulos como mudança de direção ou giros de segmentos de reta.",
        "Q02": "EF06MA27 - Determinar medidas de ângulos (reto, agudo, obtuso) e utilizar transferidor.",
        "Q03": "EF06MA26 - Resolver problemas que envolvam a noção de ângulo em diferentes contextos.",
        "Q04": "D16 - Identificar a localização de números inteiros na reta numérica.",
        "Q05": "D20 - Resolver problemas com números inteiros envolvendo as operações fundamentais.",
        "Q06": "EF07MA04 - Resolver e elaborar problemas que envolvam operações com números inteiros.",
        "Q07": "D21 - Reconhecer as diferentes representações de um número racional (fração, decimal, %).",
        "Q08": "D23 - Identificar frações equivalentes a partir de representações gráficas ou numéricas.",
        "Q09": "D26 - Resolver problemas com números racionais envolvendo as operações fundamentais.",
        "Q10": "EF07MA10 - Comparar e ordenar números racionais em diferentes contextos e na reta.",
        "Q11": "EF07MA01.1PI - Calcular raiz quadrada exata de números naturais.",
        "Q12": "D19 - Resolver problemas com potenciação de números naturais (expoente inteiro).",
        "Q13": "D6/EF06MA25 - Reconhecer giros de uma volta completa (360°) em medidores e ponteiros.",
        "Q14": "D16/EF07MA03 - Comparar e ordenar números inteiros em situações de pontuação/saldo.",
        "Q15": "D21/EF06MA08 - Converter frações usuais (1/2, 1/4, 1/5) para sua representação decimal.",
        "Q16": "D23/EF06MA07 - Reconhecer frações equivalentes por simplificação ou amplificação.",
        "Q17": "D26/EF07MA12 - Operações combinadas entre frações e decimais no cotidiano.",
        "Q18": "D19/EF07MA01 - Resolver problemas envolvendo o Mínimo Múltiplo Comum (MMC).",
        "Q19": "D20/EF07MA04 - Aplicar regra de sinais na divisão de números inteiros.",
        "Q20": "EF06MA27 - Classificar ângulos obtusos (entre 90° e 180°) em figuras ou giros.",
        "Q21": "D21/EF07MA10 - Transformar números decimais finitos em frações decimais.",
        "Q22": "D26/EF06MA03 - Multiplicação de números decimais e posicionamento da vírgula."
    },
    "Língua Portuguesa": {
        "Q01": "D1 - Localizar informações explícitas em textos.",
        "Q02": "D3 - Inferir o sentido de palavra ou expressão.",
        # Adicione os descritores de Português conforme sua matriz
