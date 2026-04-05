# Sistema de Inteligência Educacional - Escala SAEPI/SAEB
# Desenvolvido por Jardel Alves Vieira

def calcular_proficiencia(respostas, pesos):
    """
    Calcula a nota de 0 a 1000 baseada na Teoria Clássica dos Testes (TCT) 
    com pesos por dificuldade (Simulação de TRI).
    """
    pontuacao_maxima = sum(pesos)
    pontuacao_aluno = sum(r * p for r, p in zip(respostas, pesos))
    
    # Normaliza para a escala 0-1000
    nota_final = (pontuacao_aluno / pontuacao_maxima) * 1000
    return round(nota_final, 2)

def classificar_nivel(nota, serie):
    # Níveis de corte baseados nos padrões SAEB/SAEPI (Exemplo 9º Ano)
    if serie == 9:
        if nota < 250: return "Insuficiente"
        if nota < 300: return "Básico"
        if nota < 350: return "Proficiente"
        return "Avançado"
    # Adicionar lógica para 2º e 5º ano conforme necessário
    return "Em análise"

# Exemplo de uso para 1 aluno (22 questões)
# 1 = Acerto, 0 = Erro
respostas_joao = [1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1]
# Pesos: 1 (Fácil), 2 (Médio), 3 (Difícil)
pesos_prova = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3]

nota = calcular_proficiencia(respostas_joao, pesos_prova)
nivel = classificar_nivel(nota, 9)

print(f"Nota SAEPI: {nota} | Nível: {nivel}")
