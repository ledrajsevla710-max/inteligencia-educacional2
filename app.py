import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import io, tempfile, datetime

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestor Pedagógico - José de Freitas", layout="wide", page_icon="🏛️")

# --- 2. MATRIZES DE DESCRITORES ---
MATRIZ_LP = {f"Q{i:02d}": f"Descritor de Língua Portuguesa {i}" for i in range(1, 23)} # Simplificado para o exemplo
MATRIZ_MAT = {f"Q{i:02d}": f"Descritor de Matemática {i}" for i in range(1, 23)}

# --- 3. FUNÇÃO DE CÁLCULO TRI (ESTIMAÇÃO) ---
def calcular_proficiencia_tri(respostas_binarias):
    """
    Simula o cálculo TRI (Modelo de 3 Parâmetros simplificado).
    Transforma acertos em escala SAEB (0 a 500).
    """
    thetas = np.linspace(-4, 4, 100)
    verossimilhanca = np.ones_like(thetas)
    
    for q, acerto in respostas_binarias.items():
        # Parâmetro de dificuldade 'b' varia conforme a questão
        b = np.linspace(-2, 2, 22)[int(q[1:])-1]
        # Curva característica do item (Probabilidade de acerto)
        p = 0.2 + (0.8) / (1 + np.exp(-1.7 * 1.5 * (thetas - b)))
        if acerto == 1:
            verossimilhanca *= p
        else:
            verossimilhanca *= (1 - p)
    
    # Encontra o ponto de maior verossimilhança e converte para escala SAEB
    nota_estimada = thetas[np.argmax(verossimilhanca)]
    # Conversão linear para escala 0-500 (Média 250, DP 50)
    return (nota_estimada + 4) * 50

# --- 4. LÓGICA DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'banco_dados' not in st.session_state: st.session_state['banco_dados'] = None
if 'materia_selecionada' not in st.session_state: st.session_state['materia_selecionada'] = "Língua Portuguesa"

# --- 5. LOGIN ---
if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal de Avaliação Municipal</h1>", unsafe_allow_html=True)
    c1, col2, c3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            user = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.button("Acessar Painel", use_container_width=True):
                if user == "12345" and senha == "000":
                    st.session_state['autenticado'] = True
                    st.rerun()

else:
    st.sidebar.title("💎 Menu")
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "📝 Enviar Avaliações", "📊 Painel de Resultados", "🚪 Sair"])

    if menu == "🚪 Sair":
        st.session_state['autenticado'] = False
        st.rerun()

    elif menu == "🏠 Início":
        st.title(f"👋 Bem-vindo, Jardel Alves Vieira!")
        st.write("Sistema de Monitoramento de Proficiência TRI - José de Freitas.")
        if st.session_state['banco_dados'] is not None:
            st.success(f"✅ Dados de {st.session_state['materia_selecionada']} processados com TRI.")
        else:
            st.info("💡 Envie uma planilha para calcular a proficiência dos alunos.")

    elif menu == "📝 Enviar Avaliações":
        st.header("📝 Nova Importação com Cálculo TRI")
        if st.session_state['banco_dados'] is not None:
            if st.button("🗑️ EXCLUIR DADOS ATUAIS", type="primary"):
                st.session_state['banco_dados'] = None
                st.rerun()
        else:
            c1, c2 = st.columns(2)
            mat = c1.selectbox("Disciplina:", ["Língua Portuguesa", "Matemática"])
            ano = c2.selectbox("Ano Escolar:", ["9º Ano", "5º Ano", "2º Ano"])
            arq = st.file_uploader("Arquivo Excel:", type="xlsx")
            
            if arq:
                df = pd.read_excel(arq).fillna("X")
                cols_q = [f'Q{i:02d}' for i in range(1, 23)]
                gab = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']
                gab_dict = {f'Q{i:02d}': gab[i-1] for i in range(1, 23)}

                # CÁLCULO TRI POR ALUNO
                with st.spinner("Calculando Proficiência TRI..."):
                    for idx, row in df.iterrows():
                        binario = {q: 1 if str(row[q]).upper() == gab_dict[q] else 0 for q in cols_q}
                        df.at[idx, 'Proficiência_TRI'] = calcular_proficiencia_tri(binario)
                
                st.session_state['banco_dados'] = df
                st.session_state['materia_selecionada'] = mat
                st.success(f"✅ Notas TRI calculadas com sucesso para {mat}!")

    elif menu == "📊 Painel de Resultados":
        if st.session_state['banco_dados'] is None:
            st.error("Envie os dados primeiro.")
        else:
            df = st.session_state['banco_dados']
            matriz_ativa = MATRIZ_MAT if st.session_state['materia_selecionada'] == "Matemática" else MATRIZ_LP
            
            f_esc = st.sidebar.selectbox("Escola:", ["Visão Geral"] + list(df['Escola'].unique()))
            df_f = df if f_esc == "Visão Geral" else df[df['Escola'] == f_esc]

            st.header(f"📊 Painel TRI: {f_esc}")
            
            # CARDS DE MÉDIA
            media_tri = df_f['Proficiência_TRI'].mean()
            c1, c2 = st.columns(2)
            c1.metric("Média TRI do Grupo", f"{media_tri:.1f}")
            c2.metric("Total de Alunos", len(df_f))

            st.divider()
            
            # TABELA COM NOTA INDIVIDUAL
            st.subheader("📋 Lista de Alunos e Proficiência")
            st.dataframe(df_f[['Nome', 'Escola', 'Turma', 'Proficiência_TRI']].sort_values(by='Proficiência_TRI', ascending=False))

            # GRÁFICOS POR ITEM
            st.subheader("🎯 Desempenho por Habilidade")
            cols_q = [f'Q{i:02d}' for i in range(1, 23)]
            gab = ['A','B','C','D', 'A','B','C','D', 'C','A','A','B', 'C','D','C','C', 'C','A','C','A', 'A','B']
            grid = st.columns(4)
            for i, q in enumerate(cols_q):
                with grid[i % 4]:
                    with st.container(border=True):
                        st.caption(f"**{q}**: {matriz_ativa.get(q)[:35]}...")
                        freq = df_f[q].astype(str).str.upper().value_counts(normalize=True).reindex(['A','B','C','D'], fill_value=0) * 100
                        fig, ax = plt.subplots(figsize=(4, 3))
                        ax.bar(['A','B','C','D'], freq, color=['#2ECC71' if l == gab[i] else '#E74C3C' for l in ['A','B','C','D']])
                        st.pyplot(fig)

            # PDF COM MÉDIA TRI
            if st.button("📄 Gerar Relatório Oficial com TRI"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f'RELATÓRIO TÉCNICO TRI - {f_esc}', ln=True, align='C')
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, f'Média de Proficiência da Unidade: {media_tri:.1f} pontos na escala SAEB', ln=True, align='C')
                
                # Gráfico
                fig_p, ax_p = plt.subplots(figsize=(12, 4))
                resumo_acertos = [len(df_f[df_f[q].astype(str).str.upper() == gab[idx]])/len(df_f)*100 for idx, q in enumerate(cols_q)]
                ax_p.bar(cols_q, resumo_acertos, color='#1E3A8A')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    plt.savefig(tmp.name); pdf.image(tmp.name, x=10, y=45, w=275)
                
                st.download_button("Baixar PDF com TRI", pdf.output(dest='S').encode('latin-1'), "Relatorio_TRI.pdf")
