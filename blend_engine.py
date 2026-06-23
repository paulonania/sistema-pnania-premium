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
    "Paulo Nania Indoor": {
        "#10": (0.0, 0.0),
        "#14": (0.0, 0.5),
        "#18": (0.0, 0.5),
        "#35": (0.0, 2.0),
        "#40": (0.0, 2.0),
        "#60": (5.0, 15.0),
        "#100": (45.0, 60.0),
        "#140": (15.0, 25.0),
        "#200": (5.0, 10.0),
        "#270": (0.0, 2.0),
        "Finos": (0.0, 2.0),
        "AFS": (80.0, 83.7)
    },
    "Paulo Nania Outdoor": {
        "#10": (0.0, 0.0),
        "#14": (0.0, 0.5),
        "#18": (0.0, 0.5),
        "#35": (2.0, 5.0),
        "#40": (2.0, 5.0),
        "#60": (15.0, 20.0),
        "#100": (40.0, 50.0),
        "#140": (12.0, 18.0),
        "#200": (2.0, 5.0),
        "#270": (0.0, 2.0),
        "Finos": (0.0, 2.0),
        "AFS": (70.3, 76.5)
    },
    "RSTL / FEI": {
        "#10": (0.0, 0.0),
        "#14": (0.0, 0.0),
        "#18": (0.0, 1.0),
        "#35": (0.0, 2.0),
        "#40": (0.0, 5.0),
        "#60": (18.0, 24.0),
        "#100": (42.0, 52.0),
        "#140": (12.0, 22.0),
        "#200": (5.0, 15.0),
        "#270": (0.0, 2.0),
        "Finos": (0.0, 2.0),
        "AFS": (74.5, 82.7)
    },
    "Kentucky Horse Park (indoor)": {
        "#10": (0.0, 0.0),
        "#14": (0.0, 0.5),
        "#18": (0.0, 0.5),
        "#35": (0.0, 2.5),
        "#40": (0.0, 2.0),
        "#60": (12.2, 18.2),
        "#100": (48.7, 58.7),
        "#140": (11.7, 21.7),
        "#200": (4.6, 10.6),
        "#270": (0.0, 2.0),
        "Finos": (0.0, 2.0),
        "AFS": (75.6, 82.5)
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
    if faixa_alvo_name in FAIXAS_ALVO:
        faixa = FAIXAS_ALVO[faixa_alvo_name]
    elif "Hipismo (Imagens)" in FAIXAS_ALVO:
        faixa = FAIXAS_ALVO["Hipismo (Imagens)"]
    elif FAIXAS_ALVO:
        faixa = FAIXAS_ALVO[list(FAIXAS_ALVO.keys())[0]]
    else:
        # Fallback de segurança absoluto
        faixa = {s: (0.0, 100.0) for s in SIEVES}
        faixa["AFS"] = (0.0, 300.0)
    
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


def mapear_para_usda(record):
    """
    Agrega os resultados das peneiras conforme a norma USDA.
    """
    return {
        "Cascalho Grosso": 0.0,
        "Cascalho Fino": float(record.get("#10", 0.0)),
        "Muito Grossa": float(record.get("#14", 0.0)) + float(record.get("#18", 0.0)),
        "Grossa": float(record.get("#35", 0.0)),
        "Média": float(record.get("#40", 0.0)) + float(record.get("#60", 0.0)),
        "Fina": float(record.get("#100", 0.0)) + float(record.get("#140", 0.0)),
        "Muita Fina": float(record.get("#200", 0.0)) + float(record.get("#270", 0.0)),
        "Finos": float(record.get("Finos", 0.0))
    }
