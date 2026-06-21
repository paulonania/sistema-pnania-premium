import numpy as np
from scipy.optimize import minimize

# Coeficientes multiplicadores oficiais para o cálculo de AFS
FACTORS = {
    "#10": 2,
    "#14": 5,
    "#18": 10,
    "#35": 20,
    "#40": 30,
    "#60": 50,
    "#100": 70,
    "#140": 100,
    "#200": 140,
    "#270": 200,
    "Finos": 300
}

SIEVES = ["#10", "#14", "#18", "#35", "#40", "#60", "#100", "#140", "#200", "#270", "Finos"]

# Faixas Alvo Padrão do Sistema
FAIXAS_ALVO = {
    "Geral (v5)": {
        "#10": (0.0, 2.0),
        "#14": (0.0, 2.0),
        "#18": (0.0, 2.0),
        "#35": (5.0, 15.0),
        "#40": (5.0, 10.0),
        "#60": (20.0, 35.0),
        "#100": (25.0, 35.0),
        "#140": (8.0, 12.0),
        "#200": (2.0, 5.0),
        "#270": (0.0, 2.0),
        "Finos": (0.0, 2.0),
        "AFS": (62.8, 63.4),
    },
    "Hipismo (Imagens)": {
        "#10": (0.0, 2.0),
        "#14": (0.0, 2.0),
        "#18": (0.0, 2.0),
        "#35": (3.0, 8.0),
        "#40": (5.0, 10.0),
        "#60": (20.0, 35.0),
        "#100": (25.0, 35.0),
        "#140": (8.0, 12.0),
        "#200": (2.0, 5.0),
        "#270": (0.0, 2.0),
        "Finos": (0.0, 2.0),
        "AFS": (64.1, 66.0),
    }
}


def calcular_afs(sieve_values):
    """
    Calcula o AFS de uma amostra de areia com base nos valores retidos (%).
    sieve_values: dicionário mapeando nome da peneira para o percentual retido (%)
    """
    total_percent = 0.0
    weighted_sum = 0.0
    for s in SIEVES:
        val = float(sieve_values.get(s, 0.0))
        weighted_sum += val * FACTORS[s]
        total_percent += val
    
    if total_percent == 0.0:
        return 0.0
    return weighted_sum / total_percent


def calcular_mistura(sands_data, proportions):
    """
    Calcula a distribuição granulométrica resultante da mistura de areias.
    sands_data: lista de dicionários contendo os dados das areias selecionadas.
    proportions: lista de proporções (%) de cada areia na mistura.
    """
    blend = {}
    for s in SIEVES:
        val = 0.0
        for i, sand in enumerate(sands_data):
            p = float(proportions[i]) / 100.0
            val += float(sand.get(s, 0.0)) * p
        blend[s] = round(val, 2)
    return blend


def otimizar_proporcoes(sands_data, faixa_alvo_name):
    """
    Encontra as proporções ideais de areias (até 4) para atingir a faixa-alvo desejada.
    Retorna uma lista de proporções (%) arredondadas que somam 100%.
    """
    N = len(sands_data)
    if N == 0:
        return []
    if N == 1:
        return [100.0]

    # Obter os limites da faixa alvo
    faixa = FAIXAS_ALVO.get(faixa_alvo_name, FAIXAS_ALVO["Hipismo (Imagens)"])
    
    # Construir vetor alvo (ponto médio de cada peneira)
    target = np.array([(faixa[s][0] + faixa[s][1]) / 2.0 for s in SIEVES])
    
    # Construir matriz de areias (11 x N)
    sand_matrix = np.zeros((len(SIEVES), N))
    for i, sand in enumerate(sands_data):
        for j, s in enumerate(SIEVES):
            sand_matrix[j, i] = float(sand.get(s, 0.0))

    # Função objetivo: minimizar soma dos quadrados dos desvios
    def objective(w):
        blend = sand_matrix @ w
        return np.sum((blend - target) ** 2)

    # Restrições: w >= 0 e sum(w) = 1
    bounds = [(0.0, 1.0) for _ in range(N)]
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    
    # Palpite inicial: distribuição uniforme
    w0 = np.ones(N) / N
    
    res = minimize(objective, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    
    if res.success:
        # Converter para percentuais
        proportions = res.x * 100.0
        # Ajustar para garantir que a soma seja exatamente 100.0% após arredondamento
        proportions = np.round(proportions, 1)
        diff = 100.0 - np.sum(proportions)
        proportions[0] += diff
        return [round(float(p), 1) for p in proportions]
    else:
        # Fallback uniforme em caso de falha na otimização
        return [round(100.0 / N, 1)] * N


def dimensionar_insumos(length, width, thickness, density, fiber_mode, fiber_value):
    """
    Calcula as quantidades de areia e fibra necessárias para a pista.
    length, width: dimensões em metros (m)
    thickness: espessura da camada de areia em centímetros (cm)
    density: densidade do material em toneladas por metro cúbico (t/m³)
    fiber_mode: 'A' (porcentagem sobre massa de areia) ou 'B' (kg/m²)
    fiber_value: dosagem correspondente (ex: 0.3 para 0.3%, ou 3.0 para 3 kg/m²)
    """
    area = length * width
    volume = area * (thickness / 100.0)
    sand_mass = volume * density
    
    if fiber_mode == "A":
        # % sobre a massa da areia
        fiber_mass = sand_mass * (fiber_value / 100.0)
    else:
        # kg por metro quadrado (convertido para toneladas)
        fiber_mass = (area * fiber_value) / 1000.0
        
    return {
        "area": round(area, 2),
        "volume": round(volume, 2),
        "sand_mass": round(sand_mass, 2),
        "fiber_mass": round(fiber_mass, 3)
    }
