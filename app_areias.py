# Paulo Nania - Sistema de Areias
import os
import json
import re
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Import custom calculation engine
import blend_engine
from blend_engine import (
    SIEVES,
    FACTORS,
    calcular_afs,
    calcular_mistura,
    otimizar_proporcoes,
    dimensionar_insumos,
    mapear_para_usda,
)

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
BANCO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banco_areias.json")
FAIXAS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banco_faixas.json")
FOTOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fotos_graos")
os.makedirs(FOTOS_DIR, exist_ok=True)

SIEVE_DISPLAY_NAMES = {
    "#10": "NO. 10** (2,00 mm)",
    "#14": "NO. 14 (1,18 mm)",
    "#18": "NO. 18 (1,00 mm)",
    "#35": "NO. 35 (0,50 mm)",
    "#40": "NO. 40 (0,42 mm)",
    "#60": "NO. 60 (0,25 mm)",
    "#100": "NO. 100 (0,149 mm)",
    "#140": "NO. 140 (0,106 mm)",
    "#200": "NO. 200 (0,074 mm)",
    "#270": "NO. 270 (0,053 mm)",
    "Finos": "FUNDO (Silte+Argila)"
}

def sanitizar_nome_arquivo(nome):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', nome)


# Lista de areias padrão carregada estaticamente para garantir funcionamento offline
DEFAULT_AREIAS = [
    {"Areia":"Areia Jundu 1300","#10":0.0,"#14":0.0,"#18":0.0,"#35":0.0,"#40":0.0,"#60":0.0,"#100":11.7,"#140":53.8,"#200":26.5,"#270":5.7,"Finos":2.0,"AFS":116.84},
    {"Areia":"Areia Branca Bom Retiro","#10":0.0,"#14":0.0,"#18":0.0,"#35":0.2,"#40":0.6,"#60":1.3,"#100":78.2,"#140":16.7,"#200":1.0,"#270":1.8,"Finos":0.2,"AFS":77.91},
    {"Areia":"Areia Média Fina Caju 1","#10":0.3,"#14":0.5,"#18":1.5,"#35":12.9,"#40":15.4,"#60":21.1,"#100":38.0,"#140":6.4,"#200":2.3,"#270":1.3,"Finos":0.5,"AFS":58.13},
    {"Areia":"Areia 40–50 Darcy","#10":0.0,"#14":0.0,"#18":0.0,"#35":19.35,"#40":22.05,"#60":49.52,"#100":8.25,"#140":0.97,"#200":0.18,"#270":0.0,"Finos":0.0,"AFS":42.11},
    {"Areia":"Areia 50–60 Darcy","#10":0.0,"#14":0.0,"#18":0.0,"#35":15.16,"#40":12.0,"#60":40.11,"#100":28.31,"#140":4.09,"#200":0.33,"#270":0.0,"Finos":0.0,"AFS":51.06},
    {"Areia":"Areia 70–80 Darcy","#10":0.0,"#14":0.0,"#18":0.0,"#35":0.18,"#40":0.39,"#60":14.33,"#100":47.65,"#140":19.12,"#200":3.6,"#270":0.0,"Finos":0.0,"AFS":76.03},
    {"Areia":"Areia Fina Darcy","#10":0.0,"#14":0.0,"#18":0.0,"#35":0.0,"#40":0.0,"#60":0.63,"#100":26.83,"#140":46.87,"#200":22.34,"#270":3.33,"Finos":0.0,"AFS":103.9},
    {"Areia":"Areia Fina Mamede","#10":1.53,"#14":1.55,"#18":1.44,"#35":6.56,"#40":3.42,"#60":37.65,"#100":41.99,"#140":2.43,"#200":1.64,"#270":0.97,"Finos":0.82,"AFS":59.93},
    {"Areia":"Areia Fina Perisotto","#10":0.02,"#14":0.02,"#18":0.0,"#35":0.07,"#40":1.07,"#60":19.35,"#100":66.61,"#140":11.14,"#200":1.54,"#270":0.15,"Finos":0.03,"AFS":70.32},
    {"Areia":"Areia Jundu AA60","#10":0.02,"#14":0.02,"#18":0.0,"#35":1.9,"#40":7.5,"#60":41.2,"#100":37.7,"#140":10.1,"#200":1.1,"#270":0.5,"Finos":0.0,"AFS":62.24},
    {"Areia":"Areia Jundu BLEND","#10":0.02,"#14":0.02,"#18":0.0,"#35":7.6,"#40":9.5,"#60":29.1,"#100":40.0,"#140":11.45,"#200":1.8,"#270":0.4,"Finos":0.0,"AFS":61.76},
    {"Areia":"Areia Haras DOM","#10":0.02,"#14":0.54,"#18":0.46,"#35":1.35,"#40":0.42,"#60":20.61,"#100":60.09,"#140":6.67,"#200":3.32,"#270":0.8,"Finos":0.27,"AFS":70.4},
    {"Areia":"Fina Amarela Pedro","#10":0.84,"#14":0.29,"#18":0.18,"#35":3.48,"#40":5.38,"#60":31.57,"#100":39.89,"#140":8.53,"#200":5.58,"#270":1.25,"Finos":3.01,"AFS":73.94},
    {"Areia":"Areia Jundu 90/500","#10":0.0,"#14":0.0,"#18":0.0,"#35":0.0,"#40":0.0,"#60":3.1,"#100":49.3,"#140":33.9,"#200":9.9,"#270":3.3,"Finos":0.5,"AFS":91.92},
    {"Areia":"Itarena 4 - Hipismo","#10":0.01,"#14":0.02,"#18":0.2,"#35":3.54,"#40":1.76,"#60":17.08,"#100":45.71,"#140":17.04,"#200":9.58,"#270":3.86,"Finos":1.2,"AFS":83.57},
    {"Areia":"Itarena 3 - Areia Fina","#10":0.26,"#14":2.03,"#18":2.14,"#35":12.22,"#40":16.72,"#60":23.95,"#100":28.17,"#140":7.31,"#200":4.42,"#270":1.87,"Finos":0.9,"AFS":59.42},
    {"Areia":"Areia Desclassificada","#10":0.46,"#14":0.15,"#18":0.1,"#35":0.85,"#40":0.41,"#60":5.78,"#100":39.39,"#140":9.27,"#200":7.12,"#270":5.81,"Finos":30.66,"AFS":153.62},
    {"Areia":"Areia Kentucky #75 #100 (blend)","#10":0.0,"#14":0.34,"#18":0.25,"#35":1.94,"#40":0.86,"#60":15.16,"#100":53.71,"#140":16.75,"#200":7.61,"#270":1.98,"Finos":1.40,"AFS":81.43,"Mineradora":"Kentucky H. Park"},
    {"Areia":"Areia Kentucky #100","#10":0.0,"#14":0.0,"#18":0.01,"#35":0.09,"#40":0.04,"#60":0.55,"#100":10.45,"#140":41.11,"#200":32.78,"#270":10.92,"Finos":4.05,"AFS":128.61,"Mineradora":"Kentucky H. Park"},
    {"Areia":"Areia Kentucky #75","#10":0.0,"#14":0.40,"#18":0.29,"#35":2.27,"#40":1.00,"#60":17.74,"#100":61.35,"#140":12.45,"#200":3.17,"#270":0.40,"Finos":0.93,"AFS":73.10,"Mineradora":"Kentucky H. Park"}
]


def carregar_banco():
    data = []
    # 1. Carrega do JSON local se existir (contém inserções de novas areias)
    if os.path.exists(BANCO_FILE):
        try:
            with open(BANCO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    # 2. Carrega do arquivo original do Haras DOM no OneDrive se existir
    if not data:
        excel_path = r'c:\Users\paulo\OneDrive\Documentos\Haras DOM\Blend_Areia_Fibra_v5 (Haras Dom).xlsx'
        if os.path.exists(excel_path):
            try:
                df = pd.read_excel(excel_path, sheet_name='Banco_Areias')
                data = df.to_dict(orient='records')
                salvar_banco(data)
            except Exception:
                pass
            
    # 3. Fallback estático
    if not data:
        data = list(DEFAULT_AREIAS)
        
    # Normalização de campos de formato, foto, comentários e mineradora
    for item in data:
        if "Formato" not in item:
            item["Formato"] = "Não Informado"
        if "Foto" not in item:
            item["Foto"] = ""
        if "Comentarios" not in item:
            item["Comentarios"] = ""
        if "Mineradora" not in item:
            item["Mineradora"] = "Não Informado"
        if "Cliente" not in item:
            item["Cliente"] = "Não Informado"
        if "Fibra" not in item:
            item["Fibra"] = 0.0
            
    return data


def salvar_banco(data):
    try:
        with open(BANCO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


def carregar_faixas():
    if os.path.exists(FAIXAS_FILE):
        try:
            with open(FAIXAS_FILE, "r", encoding="utf-8") as f:
                raw_faixas = json.load(f)
            # Converter listas de limites para tuplas (min, max)
            faixas = {}
            for key, val in raw_faixas.items():
                faixas[key] = {sieve: tuple(limits) for sieve, limits in val.items()}
            return faixas
        except Exception:
            pass
            
    # Caso o arquivo nao exista ou falhe ao carregar, cria os padroes
    defaults = {
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
    salvar_faixas(defaults)
    return defaults


def salvar_faixas(faixas_dict):
    try:
        with open(FAIXAS_FILE, "w", encoding="utf-8") as f:
            json.dump(faixas_dict, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


def init_session():
    if "banco_areias" not in st.session_state:
        st.session_state.banco_areias = carregar_banco()
    if "faixas_alvo" not in st.session_state:
        st.session_state.faixas_alvo = carregar_faixas()
    # Rebind no modulo importado para refletir faixas dinamicas
    blend_engine.FAIXAS_ALVO = st.session_state.faixas_alvo
    
    if "pista_nome" not in st.session_state:
        st.session_state.pista_nome = "Pista Principal"
    if "pista_comprimento" not in st.session_state:
        st.session_state.pista_comprimento = 60.0
    if "pista_largura" not in st.session_state:
        st.session_state.pista_largura = 30.0
    if "pista_espessura" not in st.session_state:
        st.session_state.pista_espessura = 10.0
    if "pista_densidade" not in st.session_state:
        st.session_state.pista_densidade = 0.0




def render_cabecalho():
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=150)
    with col_titulo:
        st.title("Areia Método Paulo Nania")
        st.caption("Otimização Granulométrica de Misturas e Dimensionamento de Insumos")


def plot_curva_comparativa(blend_result, target_profile, label_result="Mistura Resultante"):
    faixa = blend_engine.FAIXAS_ALVO[target_profile]
    
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = SIEVES
    y_res = [blend_result[s] for s in x]
    y_min = [faixa[s][0] for s in x]
    y_max = [faixa[s][1] for s in x]
    
    ax.plot(x, y_res, label=label_result, color="#2e7d32", linewidth=2.5, marker="o", markersize=6)
    ax.plot(x, y_min, label="Limite Mínimo Alvo", color="#c62828", linestyle="--", linewidth=1.2)
    ax.plot(x, y_max, label="Limite Máximo Alvo", color="#c62828", linestyle="--", linewidth=1.2)
    
    ax.set_ylim(-1, max(max(y_res), max(y_max)) * 1.15)
    ax.set_title(f"Curva – {label_result} vs Alvo ({target_profile})", fontsize=11, fontweight="bold", pad=12, color="#0f3a61")
    ax.set_ylabel("% Retenção nas Peneiras", fontsize=9, fontweight="bold")
    ax.set_xlabel("Série de Peneiras", fontsize=9, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(frameon=True, facecolor="#f8fafc", edgecolor="none", loc="upper right")
    return fig


def plot_barras_mistura(blend_result, target_profile=None):
    fig, ax = plt.subplots(figsize=(10, 3.8))
    x = SIEVES
    y = [blend_result[s] for s in x]
    
    # Determinar a porção que está dentro do alvo (verde) e o excesso/falha (vermelho)
    green_heights = []
    red_heights = []
    red_bottoms = []
    
    if target_profile and target_profile in blend_engine.FAIXAS_ALVO:
        faixa = blend_engine.FAIXAS_ALVO[target_profile]
        for s in x:
            val = blend_result[s]
            l_min, l_max = faixa[s]
            if val > l_max:
                green_heights.append(l_max)
                red_heights.append(val - l_max)
                red_bottoms.append(l_max)
            elif val < l_min:
                green_heights.append(0.0)
                red_heights.append(val)
                red_bottoms.append(0.0)
            else:
                green_heights.append(val)
                red_heights.append(0.0)
                red_bottoms.append(0.0)
    else:
        green_heights = y
        red_heights = [0.0] * len(x)
        red_bottoms = [0.0] * len(x)

    # Plotar a barra base (verde se houver alvo, azul se não houver)
    main_color = "#2e7d32" if target_profile else "#0f3a61"
    main_edge = "#1b5e20" if target_profile else "#09253f"
    
    ax.bar(x, green_heights, color=main_color, alpha=0.85, edgecolor=main_edge, width=0.55)
    
    # Plotar o topo empilhado em vermelho para os excessos/falhas
    if target_profile:
        ax.bar(x, red_heights, bottom=red_bottoms, color="#c62828", alpha=0.85, edgecolor="#8b1c1c", width=0.55)
    
    # Adicionar legenda personalizada se houver comparação ativa
    if target_profile and target_profile in blend_engine.FAIXAS_ALVO:
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#2e7d32", edgecolor="#1b5e20", alpha=0.85, label="Dentro do Alvo"),
            Patch(facecolor="#c62828", edgecolor="#8b1c1c", alpha=0.85, label="Excesso/Fora do Alvo")
        ]
        ax.legend(handles=legend_elements, loc="upper right", frameon=True, facecolor="#f8fafc", edgecolor="none")
    
    # Adicionar o valor exato acima de cada barra
    for s, val in zip(x, y):
        ax.annotate(f"{val:.1f}%",
                    xy=(s, val),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, fontweight="bold", color="#334155")
                    
    ax.set_ylim(0, max(y) * 1.18 if max(y) > 0 else 10)
    ax.set_title("Distribuição de Retenção Granulométrica do Blend", fontsize=11, fontweight="bold", pad=12, color="#0f3a61")
    ax.set_ylabel("% Retida", fontsize=9, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    return fig


def plot_barras_areia(sand_record):
    fig, ax = plt.subplots(figsize=(10, 3.8))
    x = SIEVES
    y = [float(sand_record.get(s, 0.0)) for s in x]
    
    bars = ax.bar(x, y, color="#0f3a61", alpha=0.85, edgecolor="#09253f", width=0.55)
    
    # Adicionar o valor exato acima de cada barra
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, fontweight="bold", color="#334155")
                    
    ax.set_ylim(0, max(y) * 1.18 if max(y) > 0 else 10)
    ax.set_title(f"Distribuição Granulométrica – {sand_record['Areia']}", fontsize=11, fontweight="bold", pad=12, color="#0f3a61")
    ax.set_ylabel("% Retida", fontsize=9, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    return fig


def plot_linha_areia(sand_record):
    fig, ax = plt.subplots(figsize=(10, 3.8))
    x = SIEVES
    y = [float(sand_record.get(s, 0.0)) for s in x]
    
    ax.plot(x, y, color="#0f3a61", linewidth=2.5, marker="o", markersize=6, label="Retenção")
    
    ax.set_ylim(-1, max(y) * 1.18 if max(y) > 0 else 10)
    ax.set_title(f"Curva Granulométrica – {sand_record['Areia']}", fontsize=11, fontweight="bold", pad=12, color="#0f3a61")
    ax.set_ylabel("% Retenção nas Peneiras", fontsize=9, fontweight="bold")
    ax.set_xlabel("Série de Peneiras", fontsize=9, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5)
    return fig


def exibir_tabela_usda(sands_list, title="Classificação USDA (Distribuição de Partículas)"):
    st.markdown(f"##### {title}")
    
    html = "<style>" \
           ".usda-table {" \
           "width: 100%;" \
           "border-collapse: separate;" \
           "border-spacing: 0;" \
           "font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;" \
           "font-size: 14px;" \
           "color: #31333F;" \
           "margin-top: 10px;" \
           "margin-bottom: 10px;" \
           "border: 1px solid #EAEAEB;" \
           "border-radius: 4px;" \
           "overflow: hidden;" \
           "}" \
           ".usda-table th {" \
           "background-color: #F8F9FB;" \
           "border-bottom: 1px solid #EAEAEB;" \
           "border-right: 1px solid #EAEAEB;" \
           "text-align: center;" \
           "vertical-align: middle;" \
           "font-weight: 500;" \
           "color: rgba(49, 51, 63, 0.6);" \
           "padding: 8px 10px;" \
           "font-size: 12px;" \
           "text-transform: uppercase;" \
           "}" \
           ".usda-table th:last-child {" \
           "border-right: none;" \
           "}" \
           ".usda-table td {" \
           "border-bottom: 1px solid #EAEAEB;" \
           "border-right: 1px solid #EAEAEB;" \
           "padding: 8px 10px;" \
           "text-align: right;" \
           "color: #31333F;" \
           "font-size: 13px;" \
           "}" \
           ".usda-table td:last-child {" \
           "border-right: none;" \
           "}" \
           ".usda-table tr:last-child td {" \
           "border-bottom: none;" \
           "}" \
           ".usda-table td.desc {" \
           "text-align: left;" \
           "font-weight: normal;" \
           "padding-left: 12px;" \
           "color: #31333F;" \
           "}" \
           "</style>" \
           "<table class='usda-table'>" \
           "<thead>" \
           "<tr>" \
           "<th rowspan='2' style='text-align: center; vertical-align: middle;'>DESCRIÇÃO</th>" \
           "<th colspan='2'>Cascalho</th>" \
           "<th colspan='5'>Areia</th>" \
           "<th>Finos</th>" \
           "</tr>" \
           "<tr>" \
           "<th>Grosso<br><span style=\"white-space: nowrap;\">5-12 mm</span></th>" \
           "<th>Fino<br><span style=\"white-space: nowrap;\">2-5 mm</span></th>" \
           "<th>Muito Grossa<br><span style=\"white-space: nowrap;\">1-2 mm</span></th>" \
           "<th>Grossa<br><span style=\"white-space: nowrap;\">0.5-1 mm</span></th>" \
           "<th>Média<br><span style=\"white-space: nowrap;\">0.25-0.5 mm</span></th>" \
           "<th>Fina<br><span style=\"white-space: nowrap;\">0.1-0.25 mm</span></th>" \
           "<th>Muita Fina<br><span style=\"white-space: nowrap;\">0.05-0.1 mm</span></th>" \
           "<th>(silte+argila)<br><span style=\"white-space: nowrap;\">0.002-0.00 mm</span></th>" \
           "</tr>" \
           "</thead>" \
           "<tbody>"
    
    for sand in sands_list:
        usda = mapear_para_usda(sand)
        row_html = f"<tr><td class='desc'>{sand.get('Areia', 'Amostra')}</td>" \
                   f"<td>{usda['Cascalho Grosso']:.2f}%</td>" \
                   f"<td>{usda['Cascalho Fino']:.2f}%</td>" \
                   f"<td>{usda['Muito Grossa']:.2f}%</td>" \
                   f"<td>{usda['Grossa']:.2f}%</td>" \
                   f"<td>{usda['Média']:.2f}%</td>" \
                   f"<td>{usda['Fina']:.2f}%</td>" \
                   f"<td>{usda['Muita Fina']:.2f}%</td>" \
                   f"<td>{usda['Finos']:.2f}%</td></tr>"
        html += row_html
        
    html += "</tbody></table>" \
            "<div style='font-size: 11px; color: #8898AA; margin-top: 5px; font-family: sans-serif; font-style: italic;'>" \
            "Cascalho, Areia, Silte e Argila baseada na Classificação (USDA - United States Department of Agriculture)" \
            "</div>"
            
    st.markdown(html, unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Método Paulo Nania — Areias", layout="wide", page_icon="🏜️")
    init_session()
    render_cabecalho()
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📝 1. Cadastro de Areia",
        "📷 2. Formato do Grão",
        "🏜️ 3. Granulometria",
        "🔍 4. Detalhes da Areia",
        "🎯 5. Faixa Alvo",
        "⚙️ 6. Blendagem",
        "📊 7. Dimensionador & Laudo"
    ])
    
    # ----------------------------------------------------
    # TAB 1: CADASTRO DE AREIA
    # ----------------------------------------------------
    with tab1:
        st.subheader("Cadastrar Nova Amostra")
        st.write("Insira os dados granulométricos e de identificação da nova areia para registrá-la no banco de dados.")
        
        with st.form("nova_amostra_form", clear_on_submit=False):
            col_nome, col_mine = st.columns(2)
            with col_nome:
                nome_amostra = st.text_input("Nome da Areia / Amostra", placeholder="Ex: Areia Fina Mogi")
            with col_mine:
                mineradora_amostra = st.text_input("Mineradora / Origem", placeholder="Ex: Jundu")
                
            col_cli, col_fib = st.columns(2)
            with col_cli:
                cliente_amostra = st.text_input("Cliente", placeholder="Ex: Haras Primavera")
            with col_fib:
                fibra_amostra = st.number_input("Teor de Fibra (%)", 0.0, 100.0, 0.0, step=0.01, format="%.2f")
            
            c_s1, c_s2, c_s3, c_s4 = st.columns(4)
            sieve_inputs = {}
            
            with c_s1:
                sieve_inputs["#10"] = st.number_input("#10", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
                sieve_inputs["#14"] = st.number_input("#14", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
                sieve_inputs["#18"] = st.number_input("#18", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
            with c_s2:
                sieve_inputs["#35"] = st.number_input("#35", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
                sieve_inputs["#40"] = st.number_input("#40", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
                sieve_inputs["#60"] = st.number_input("#60", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
            with c_s3:
                sieve_inputs["#100"] = st.number_input("#100", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
                sieve_inputs["#140"] = st.number_input("#140", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
                sieve_inputs["#200"] = st.number_input("#200", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
            with c_s4:
                sieve_inputs["#270"] = st.number_input("#270", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
                sieve_inputs["Finos"] = st.number_input("Finos (Fundo)", 0.0, 100.0, 0.0, step=0.1, format="%.2f")
            submitted = st.form_submit_button("💾 Salvar Amostra no Banco", type="primary")
            
            if submitted:
                total_sum = sum(sieve_inputs.values())
                if not nome_amostra.strip():
                    st.error("Por favor, digite um nome válido para a amostra.")
                elif abs(total_sum - 100.0) > 1.0:
                    st.error(f"Erro: A soma das peneiras deve ser próxima de 100%. Soma atual: {total_sum:.2f}%")
                else:
                    # Ajusta as proporções levemente para fechar em exatamente 100%
                    if total_sum != 100.0:
                        factor = 100.0 / total_sum
                        for s in sieve_inputs:
                            sieve_inputs[s] = round(sieve_inputs[s] * factor, 2)
                    
                    # Calcular AFS
                    afs_calc = round(calcular_afs(sieve_inputs), 1)
                    
                    # Montar registro
                    nova_areia = {"Areia": nome_amostra.strip()}
                    nova_areia["Mineradora"] = mineradora_amostra.strip() if mineradora_amostra.strip() else "Não Informado"
                    nova_areia["Cliente"] = cliente_amostra.strip() if cliente_amostra.strip() else "Não Informado"
                    nova_areia["Fibra"] = fibra_amostra
                    nova_areia.update({s: sieve_inputs[s] for s in SIEVES})
                    nova_areia["AFS"] = afs_calc
                    nova_areia["Formato"] = "Não Informado"
                    nova_areia["Foto"] = []
                    nova_areia["Comentarios"] = ""
                    
                    # Salvar na sessão e no arquivo local
                    st.session_state.banco_areias.append(nova_areia)
                    salvar_banco(st.session_state.banco_areias)
                    st.success(f"Areia '{nome_amostra.strip()}' cadastrada com sucesso! AFS calculado: {afs_calc}")
                    st.rerun()

    # ----------------------------------------------------
    # TAB 3: GRANULOMETRIA (BASE DE AREIAS)
    # ----------------------------------------------------
    with tab3:
        st.subheader("Base de Areias Cadastradas")
        st.write("Abaixo estão listadas as areias disponíveis para composição dos blends e análise técnica.")
        
        df_display = pd.DataFrame(st.session_state.banco_areias)
        
        # Ocultar colunas não-granulométricas/de notas para manter a tabela limpa
        df_show = df_display.copy()
        for col_to_drop in ["Foto", "Comentarios"]:
            if col_to_drop in df_show.columns:
                df_show = df_show.drop(columns=[col_to_drop])
            
        # Reordenar colunas para manter visual consistente
        cols_order = ["Areia", "Mineradora", "Cliente", "Fibra"] + SIEVES + ["AFS", "Formato"]
        cols_order = [c for c in cols_order if c in df_show.columns]
        df_show = df_show[cols_order]
            
        column_config = {
            "Areia": st.column_config.TextColumn("Nome da Areia", width="medium"),
            "Mineradora": st.column_config.TextColumn("Mineradora", width="medium"),
            "Cliente": st.column_config.TextColumn("Cliente", width="medium"),
            "Fibra": st.column_config.NumberColumn("Teor de Fibra (%)", format="%.2f%%"),
            "Formato": st.column_config.TextColumn("Formato do Grão", width="small"),
            "AFS": st.column_config.NumberColumn("AFS", format="%.1f"),
        }
        for s in SIEVES:
            column_config[s] = st.column_config.NumberColumn(s, format="%.2f%%")
            
        st.dataframe(
            df_show,
            column_config=column_config,
            hide_index=True,
            use_container_width=True
        )
        
        st.divider()
        st.subheader("🎯 Base de Faixas Alvo (Alvos Granulométricos)")
        st.write("Abaixo estão listados os limites de faixa alvo (mínimos e máximos) para cada modalidade/disciplina cadastrada no banco de dados.")
        
        faixas_rows = []
        for name, data in st.session_state.faixas_alvo.items():
            row = {"Disciplina / Alvo": name}
            for s in SIEVES:
                limits = data.get(s, (0.0, 0.0))
                if limits[0] == limits[1]:
                    row[s] = f"{limits[0]:.1f}%"
                else:
                    row[s] = f"{limits[0]:.1f}% a {limits[1]:.1f}%"
            afs_limits = data.get("AFS", (0.0, 0.0))
            if afs_limits[0] == afs_limits[1]:
                row["AFS"] = f"{afs_limits[0]:.1f}"
            else:
                row["AFS"] = f"{afs_limits[0]:.1f} a {afs_limits[1]:.1f}"
            faixas_rows.append(row)
            
        df_faixas = pd.DataFrame(faixas_rows)
        st.dataframe(
            df_faixas,
            hide_index=True,
            use_container_width=True
        )
        
        # Seção de Edição e Exclusão na Aba 2
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.subheader("📝 Editar / Excluir Areia")
        areia_nomes_tab1 = [a["Areia"] for a in st.session_state.banco_areias]
        selected_edit_name = st.selectbox(
            "Selecione uma areia para editar o nome/mineradora ou excluir:",
            options=["-- Selecione --"] + areia_nomes_tab1,
            key="tab1_edit_select"
        )
        
        if selected_edit_name != "-- Selecione --":
            sand_rec = next(a for a in st.session_state.banco_areias if a["Areia"] == selected_edit_name)
            idx_to_update = next(i for i, a in enumerate(st.session_state.banco_areias) if a["Areia"] == selected_edit_name)
            
            col_edit_name, col_edit_mineradora = st.columns(2)
            with col_edit_name:
                novo_nome = st.text_input("Novo Nome da Areia:", value=sand_rec["Areia"], key=f"edit_name_val_{sand_rec['Areia']}")
            with col_edit_mineradora:
                nova_mineradora = st.text_input("Nova Mineradora:", value=sand_rec.get("Mineradora", "Não Informado"), key=f"edit_min_val_{sand_rec['Areia']}")
                
            col_edit_cliente, col_edit_fibra = st.columns(2)
            with col_edit_cliente:
                novo_cliente = st.text_input("Cliente:", value=sand_rec.get("Cliente", "Não Informado"), key=f"edit_cli_val_{sand_rec['Areia']}")
            with col_edit_fibra:
                nova_fibra = st.number_input("Teor de Fibra (%):", value=float(sand_rec.get("Fibra", 0.0)), step=0.01, format="%.2f", key=f"edit_fib_val_{sand_rec['Areia']}")
                
            st.markdown("##### Alterar Percentuais de Retenção nas Peneiras (%)")
            c_e1, c_e2, c_e3, c_e4 = st.columns(4)
            edit_sieve_inputs = {}
            
            with c_e1:
                edit_sieve_inputs["#10"] = st.number_input("#10", 0.0, 100.0, float(sand_rec.get("#10", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_10_{sand_rec['Areia']}")
                edit_sieve_inputs["#14"] = st.number_input("#14", 0.0, 100.0, float(sand_rec.get("#14", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_14_{sand_rec['Areia']}")
                edit_sieve_inputs["#18"] = st.number_input("#18", 0.0, 100.0, float(sand_rec.get("#18", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_18_{sand_rec['Areia']}")
            with c_e2:
                edit_sieve_inputs["#35"] = st.number_input("#35", 0.0, 100.0, float(sand_rec.get("#35", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_35_{sand_rec['Areia']}")
                edit_sieve_inputs["#40"] = st.number_input("#40", 0.0, 100.0, float(sand_rec.get("#40", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_40_{sand_rec['Areia']}")
                edit_sieve_inputs["#60"] = st.number_input("#60", 0.0, 100.0, float(sand_rec.get("#60", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_60_{sand_rec['Areia']}")
            with c_e3:
                edit_sieve_inputs["#100"] = st.number_input("#100", 0.0, 100.0, float(sand_rec.get("#100", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_100_{sand_rec['Areia']}")
                edit_sieve_inputs["#140"] = st.number_input("#140", 0.0, 100.0, float(sand_rec.get("#140", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_140_{sand_rec['Areia']}")
                edit_sieve_inputs["#200"] = st.number_input("#200", 0.0, 100.0, float(sand_rec.get("#200", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_200_{sand_rec['Areia']}")
            with c_e4:
                edit_sieve_inputs["#270"] = st.number_input("#270", 0.0, 100.0, float(sand_rec.get("#270", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_270_{sand_rec['Areia']}")
                edit_sieve_inputs["Finos"] = st.number_input("Finos (Fundo)", 0.0, 100.0, float(sand_rec.get("Finos", 0.0)), step=0.1, format="%.2f", key=f"edit_sieve_finos_{sand_rec['Areia']}")
                
            col_btn_save, col_btn_del = st.columns(2)
            with col_btn_save:
                if st.button("💾 Salvar Alterações", key=f"btn_save_tab1_{sand_rec['Areia']}", type="primary", use_container_width=True):
                    total_sum = sum(edit_sieve_inputs.values())
                    if not novo_nome.strip():
                        st.error("O nome da areia não pode ser vazio.")
                    elif abs(total_sum - 100.0) > 1.0:
                        st.error(f"Erro: A soma das peneiras deve ser próxima de 100%. Soma atual: {total_sum:.2f}%")
                    else:
                        # Ajusta as proporções levemente para fechar em exatamente 100%
                        if total_sum != 100.0:
                            factor = 100.0 / total_sum
                            for s in edit_sieve_inputs:
                                edit_sieve_inputs[s] = round(edit_sieve_inputs[s] * factor, 2)
                        
                        # Recalcular AFS
                        afs_calc = round(calcular_afs(edit_sieve_inputs), 1)
                        
                        st.session_state.banco_areias[idx_to_update]["Areia"] = novo_nome.strip()
                        st.session_state.banco_areias[idx_to_update]["Mineradora"] = nova_mineradora.strip() if nova_mineradora.strip() else "Não Informado"
                        st.session_state.banco_areias[idx_to_update]["Cliente"] = novo_cliente.strip() if novo_cliente.strip() else "Não Informado"
                        st.session_state.banco_areias[idx_to_update]["Fibra"] = nova_fibra
                        for s in edit_sieve_inputs:
                            st.session_state.banco_areias[idx_to_update][s] = edit_sieve_inputs[s]
                        st.session_state.banco_areias[idx_to_update]["AFS"] = afs_calc
                        
                        salvar_banco(st.session_state.banco_areias)
                        st.success("Areia atualizada com sucesso!")
                        st.rerun()
            with col_btn_del:
                if st.button("🗑️ Excluir esta Areia", key=f"btn_del_tab1_{sand_rec['Areia']}", type="secondary", use_container_width=True):
                    deleted_sand = st.session_state.banco_areias.pop(idx_to_update)
                    p_files = deleted_sand.get("Foto", [])
                    if isinstance(p_files, str):
                        p_files = [p_files] if p_files else []
                    for p_file in p_files:
                        if p_file:
                            p_path = os.path.join(FOTOS_DIR, p_file)
                            if os.path.exists(p_path):
                                try:
                                    os.remove(p_path)
                                except Exception:
                                    pass
                    salvar_banco(st.session_state.banco_areias)
                    st.success(f"Areia '{selected_edit_name}' excluída com sucesso!")
                    st.rerun()

    # ----------------------------------------------------
    # TAB 2: FORMATO DO GRÃO
    # ----------------------------------------------------
    with tab2:
        st.subheader("⚙️ Adicionar / Alterar Formato do Grão")
        st.write("Selecione uma areia para definir ou modificar a classificação morfológica de seus grãos:")
        
        areia_nomes_tab2 = [a["Areia"] for a in st.session_state.banco_areias]
        
        c_up1, c_up2, c_up3 = st.columns([2, 2, 1])
        with c_up1:
            nome_edit_tab2 = st.selectbox(
                "Escolha a Areia:",
                options=areia_nomes_tab2,
                key="tab2_edit_select"
            )
        with c_up2:
            current_sand_rec = next((a for a in st.session_state.banco_areias if a["Areia"] == nome_edit_tab2), None)
            current_format_val = current_sand_rec.get("Formato", "Não Informado") if current_sand_rec else "Não Informado"
            
            options_format_tab2 = ["Não Informado", "Arredondado", "Sub-arredondado", "Sub-angular", "Angular"]
            try:
                def_idx_tab2 = options_format_tab2.index(current_format_val)
            except ValueError:
                def_idx_tab2 = 0
                
            formato_edit_tab2 = st.selectbox(
                "Novo Formato do Grão:",
                options=options_format_tab2,
                index=def_idx_tab2,
                key="tab2_edit_format_selectbox"
            )
        with c_up3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("💾 Salvar Formato", key="tab2_edit_save_button", type="primary", use_container_width=True):
                idx_to_update = next((i for i, a in enumerate(st.session_state.banco_areias) if a["Areia"] == nome_edit_tab2), None)
                if idx_to_update is not None:
                    st.session_state.banco_areias[idx_to_update]["Formato"] = formato_edit_tab2
                    salvar_banco(st.session_state.banco_areias)
                    st.success(f"Formato da areia '{nome_edit_tab2}' atualizado para '{formato_edit_tab2}'!")
                    st.rerun()
                    
        st.divider()
        st.subheader("📷 Fotos de Microscopia do Grão")
        st.write("Gerencie, adicione e visualize múltiplas fotos de microscopia/lupa para as areias do banco de dados.")
        
        areia_nomes_img = [a["Areia"] for a in st.session_state.banco_areias]
        selected_img_name = st.selectbox("Selecione uma areia para gerenciar as imagens:", ["-- Selecione --"] + areia_nomes_img, key="foto_areia_select")
        
        if selected_img_name != "-- Selecione --":
            sand_rec = next(a for a in st.session_state.banco_areias if a["Areia"] == selected_img_name)
            
            # Normalizar se a foto for string (retrocompatibilidade)
            photo_list = sand_rec.get("Foto", [])
            if isinstance(photo_list, str):
                photo_list = [photo_list] if photo_list else []
            
            col_img_info, col_img_file = st.columns(2)
            with col_img_info:
                st.markdown(f"### Areia: **{sand_rec['Areia']}**")
                st.markdown(f"**Formato Cadastrado**: `{sand_rec.get('Formato', 'Não Informado')}`")
                
                # Uploader para múltiplas fotos
                uploaded_photos_tab3 = st.file_uploader(
                    "Fazer upload de fotos do grão (selecione uma ou mais imagens):",
                    type=["png", "jpg", "jpeg"],
                    accept_multiple_files=True,
                    key=f"upload_photos_tab3_{sand_rec['Areia']}"
                )
                
                if st.button("💾 Salvar Imagens Selecionadas", key=f"btn_save_photo_tab3_{sand_rec['Areia']}", type="primary"):
                    idx_to_update = next((i for i, a in enumerate(st.session_state.banco_areias) if a["Areia"] == selected_img_name), None)
                    if idx_to_update is not None and uploaded_photos_tab3:
                        sanitized = sanitizar_nome_arquivo(selected_img_name)
                        novas_fotos = list(photo_list)
                        
                        success_count = 0
                        for index, uploaded_file in enumerate(uploaded_photos_tab3):
                            ext = os.path.splitext(uploaded_file.name)[1] or ".png"
                            photo_filename = f"foto_{sanitized}_{int(pd.Timestamp.now().timestamp())}_{index}{ext}"
                            filepath = os.path.join(FOTOS_DIR, photo_filename)
                            try:
                                with open(filepath, "wb") as f:
                                    f.write(uploaded_file.getbuffer())
                                novas_fotos.append(photo_filename)
                                success_count += 1
                            except Exception as e:
                                st.error(f"Erro ao salvar a foto {uploaded_file.name}: {e}")
                        
                        if success_count > 0:
                            st.session_state.banco_areias[idx_to_update]["Foto"] = novas_fotos
                            salvar_banco(st.session_state.banco_areias)
                            st.success(f"{success_count} nova(s) imagem(ns) salva(s) com sucesso!")
                            st.rerun()
                    elif not uploaded_photos_tab3:
                        st.error("Por favor, selecione ao menos uma imagem antes de clicar em salvar.")
                        
            with col_img_file:
                st.markdown("#### Galeria de Imagens")
                if photo_list:
                    for idx_photo, photo_name in enumerate(photo_list):
                        if photo_name:
                            photo_path = os.path.join(FOTOS_DIR, photo_name)
                            if os.path.exists(photo_path):
                                st.image(photo_path, caption=f"Foto {idx_photo + 1}: {sand_rec['Areia']}", use_container_width=True)
                                
                                # Botão para remover esta imagem específica
                                if st.button(f"🗑️ Deletar Foto {idx_photo + 1}", key=f"btn_remove_photo_tab3_{sand_rec['Areia']}_{idx_photo}", type="secondary"):
                                    idx_to_update = next((i for i, a in enumerate(st.session_state.banco_areias) if a["Areia"] == selected_img_name), None)
                                    if idx_to_update is not None:
                                        # Remover o arquivo físico
                                        try:
                                            os.remove(photo_path)
                                        except Exception:
                                            pass
                                        # Atualizar a lista no banco
                                        photo_list.pop(idx_photo)
                                        st.session_state.banco_areias[idx_to_update]["Foto"] = photo_list
                                        salvar_banco(st.session_state.banco_areias)
                                        st.success("Imagem removida com sucesso!")
                                        st.rerun()
                                st.markdown("---")
                            else:
                                st.warning(f"📷 Arquivo {photo_name} não foi localizado no disco.")
                else:
                    st.info("📷 Nenhuma foto cadastrada para esta areia.")

    # ----------------------------------------------------
    # TAB 4: DETALHES DA AREIA
    # ----------------------------------------------------
    with tab4:
        st.subheader("🔍 Detalhes da Areia & Formato")
        st.write("Selecione uma areia cadastrada no banco de dados para inspecionar seus detalhes, propriedades físicas e granulometria.")
        
        areia_nomes = [a["Areia"] for a in st.session_state.banco_areias]
        selected_detail_name = st.selectbox("Selecione uma areia para ver detalhes:", ["-- Selecione --"] + areia_nomes, key="detalhes_areia_select")
        
        if selected_detail_name != "-- Selecione --":
            sand_rec = next(a for a in st.session_state.banco_areias if a["Areia"] == selected_detail_name)
            
            # Exibir cabeçalho com o nome, mineradora, cliente e teor de fibra abaixo
            st.markdown(f"### Areia: **{sand_rec['Areia']}**")
            col_det_1, col_det_2, col_det_3 = st.columns(3)
            with col_det_1:
                st.markdown(f"**Mineradora:** {sand_rec.get('Mineradora', 'Não Informado')}")
            with col_det_2:
                st.markdown(f"**Cliente:** {sand_rec.get('Cliente', 'Não Informado')}")
            with col_det_3:
                st.markdown(f"**Teor de Fibra:** {sand_rec.get('Fibra', 0.0):.2f}%")
            st.divider()
            
            # Arredondar o AFS para inteiro sem casas decimais
            afs_val = sand_rec.get('AFS', 0)
            try:
                afs_display = str(int(round(float(afs_val))))
            except Exception:
                afs_display = str(afs_val)
                
            # Seção de tabelas lado a lado
            col_tab1, col_tab2 = st.columns([1, 1.5])
            with col_tab1:
                st.markdown("#### 📊 Tamanho e Distribuição dos Grãos")
                # Tabela vertical clássica com milímetros das peneiras
                rows_vertical = []
                for s in SIEVES:
                    rows_vertical.append({
                        "DESCRIÇÃO AMOSTRA": SIEVE_DISPLAY_NAMES[s],
                        sand_rec["Areia"]: f"{sand_rec.get(s, 0.0):.2f}%"
                    })
                # Adicionar linha FUNDO + NO. 270
                fundo_val = float(sand_rec.get("Finos", 0.0))
                no270_val = float(sand_rec.get("#270", 0.0))
                soma_fundo_270 = fundo_val + no270_val
                rows_vertical.append({
                    "DESCRIÇÃO AMOSTRA": "FUNDO + NO. 270",
                    sand_rec["Areia"]: f"{soma_fundo_270:.2f}%"
                })
                # Adicionar linha AFS
                rows_vertical.append({
                    "DESCRIÇÃO AMOSTRA": "AFS",
                    sand_rec["Areia"]: afs_display
                })
                df_vertical = pd.DataFrame(rows_vertical)
                st.dataframe(df_vertical, hide_index=True, use_container_width=True)
                
            with col_tab2:
                # Tabela USDA horizontal
                exibir_tabela_usda([sand_rec], title=f"🌾 Classificação USDA — {sand_rec['Areia']}")
                
                st.markdown("#### 💬 Comentários / Notas da Areia")
                comentarios_val = sand_rec.get("Comentarios", "")
                comentarios = st.text_area(
                    "Anotações técnicas sobre esta areia:",
                    value=comentarios_val,
                    height=120,
                    key=f"comentarios_{sand_rec['Areia']}"
                )
                if st.button("💾 Salvar Comentários", key=f"btn_save_comments_{sand_rec['Areia']}", type="primary"):
                    idx_to_update = next((i for i, a in enumerate(st.session_state.banco_areias) if a["Areia"] == selected_detail_name), None)
                    if idx_to_update is not None:
                        st.session_state.banco_areias[idx_to_update]["Comentarios"] = comentarios
                        salvar_banco(st.session_state.banco_areias)
                        st.success("Comentários salvos com sucesso!")
                        st.rerun()
                        
            st.divider()
            
            # Seletor de Comparação com Faixas Alvo (Aba 5)
            col_comp_sel, _ = st.columns([1.5, 2])
            with col_comp_sel:
                comparar_faixa = st.selectbox(
                    "🎯 Comparar esta areia com uma Faixa Alvo (Opcional):",
                    options=["-- Sem Comparação --"] + list(st.session_state.faixas_alvo.keys()),
                    key=f"comparar_faixa_detalhes_{sand_rec['Areia']}"
                )
                
            if comparar_faixa != "-- Sem Comparação --":
                st.markdown(f"#### Comparativo Tabular: {sand_rec['Areia']} vs {comparar_faixa}")
                faixa = st.session_state.faixas_alvo[comparar_faixa]
                rows_comp = []
                for s in SIEVES:
                    target_min, target_max = faixa[s]
                    res_val = float(sand_rec.get(s, 0.0))
                    
                    if res_val < target_min:
                        status = "🔴 ABAIXO"
                    elif res_val > target_max:
                        status = "🔴 ACIMA"
                    else:
                        status = "🟢 DENTRO"
                        
                    rows_comp.append({
                        "Peneira": s,
                        "Ref. Mínima (%)": f"{target_min:.2f}%",
                        "Ref. Máxima (%)": f"{target_max:.2f}%",
                        "Resultado Areia (%)": f"{res_val:.2f}%",
                        "Status": status
                    })
                df_comp = pd.DataFrame(rows_comp)
                
                def style_status(val):
                    if "🟢" in val:
                        return "background-color: #e2f0d9; color: #2e7d32; font-weight: bold;"
                    else:
                        return "background-color: #fef2f2; color: #c62828; font-weight: bold;"
                        
                c_tab_comp, c_afs_comp = st.columns([3, 1])
                with c_tab_comp:
                    st.dataframe(
                        df_comp.style.map(style_status, subset=["Status"]),
                        use_container_width=True,
                        hide_index=True
                    )
                with c_afs_comp:
                    sand_afs = float(sand_rec.get("AFS", 0.0))
                    target_afs_min, target_afs_max = faixa.get("AFS", (0.0, 0.0))
                    st.markdown("#### AFS da Areia")
                    st.metric(sand_rec['Areia'], f"{sand_afs:.1f}")
                    st.markdown(f"**AFS Alvo da Disciplina:** `{target_afs_min:.1f} a {target_afs_max:.1f}`")
                    
                    if target_afs_min <= sand_afs <= target_afs_max:
                        st.success("✅ AFS dentro do intervalo ideal!")
                    else:
                        st.warning("⚠️ AFS fora do intervalo ideal de suporte.")
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            st.markdown("### 📈 Visualização Gráfica")
            col_graph1, col_graph2 = st.columns(2)
            with col_graph1:
                if comparar_faixa != "-- Sem Comparação --":
                    fig_linha = plot_curva_comparativa(sand_rec, comparar_faixa, label_result=sand_rec['Areia'])
                else:
                    fig_linha = plot_linha_areia(sand_rec)
                st.pyplot(fig_linha)
            with col_graph2:
                fig_barras = plot_barras_areia(sand_rec)
                st.pyplot(fig_barras)
                
            st.divider()
            st.markdown("### 📷 Formato e Microscopia do Grão")
            
            formato = sand_rec.get("Formato", "Não Informado")
            expl = ""
            if formato == "Arredondado":
                expl = " — Grãos arredondados. Menor atrito e estabilidade (tendência a rolar), baixo desgaste dos cascos e alta durabilidade das partículas."
            elif formato == "Sub-arredondado":
                expl = " — Grãos sub-arredondados. Suporte moderado e resistência intermediária com baixo desgaste."
            elif formato == "Sub-angular":
                expl = " — Grãos sub-angulares. Excelente equilíbrio: evita o rolamento/instabilidade e promove boa elasticidade da pista."
            elif formato == "Angular":
                expl = " — Grãos angulares. Elevado atrito e resistência ao cisalhamento (pista firme), mas causa alto desgaste nos cascos e quebra facilmente gerando finos."
            
            st.markdown(f"<div style='font-family: sans-serif; font-size: 14px; color: #000000; margin-bottom: 10px;'><strong>Formato do Grão:</strong> {formato}{expl}</div>", unsafe_allow_html=True)
            
            # Exibir fotos do formato do grão se houver
            p_files = sand_rec.get("Foto", [])
            if isinstance(p_files, str):
                p_files = [p_files] if p_files else []
            p_files = [p for p in p_files if p]
            
            if p_files:
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.markdown("**Fotos de Microscopia do Grão:**")
                n_photos = len(p_files)
                cols_photos = st.columns(min(n_photos, 3))
                for idx_p, p_file in enumerate(p_files):
                    p_path = os.path.join(FOTOS_DIR, p_file)
                    if os.path.exists(p_path):
                        with cols_photos[idx_p % min(n_photos, 3)]:
                            st.image(p_path, caption=f"Foto {idx_p + 1}: {sand_rec['Areia']}", use_container_width=True)
                            


    # ----------------------------------------------------
    # TAB 5: FAIXA ALVO
    # ----------------------------------------------------
    with tab5:
        st.subheader("🎯 Gerenciamento de Faixas Alvo (Disciplinas)")
        st.write("Visualize, crie, altere ou exclua os limites de tamanho de grãos por peneira e AFS para cada modalidade.")
        
        faixas_dict = st.session_state.faixas_alvo
        faixas_nomes = list(faixas_dict.keys())
        
        col_faixa_esq, col_faixa_dir = st.columns([1.2, 2.0])
        
        with col_faixa_esq:
            st.markdown("### Faixas Ativas")
            selected_faixa_manage = st.selectbox(
                "Selecione uma disciplina para visualizar ou gerenciar:",
                options=faixas_nomes,
                key="manage_faixa_select"
            )
            
            # Exibir limites atuais da faixa selecionada
            current_faixa = faixas_dict[selected_faixa_manage]
            
            st.markdown(f"#### Limites de: **{selected_faixa_manage}**")
            
            rows_faixa = []
            for s in SIEVES:
                l_min, l_max = current_faixa[s]
                rows_faixa.append({
                    "Peneira": SIEVE_DISPLAY_NAMES[s],
                    "Min (%)": f"{l_min:.2f}%",
                    "Max (%)": f"{l_max:.2f}%"
                })
            # AFS
            afs_min, afs_max = current_faixa["AFS"]
            rows_faixa.append({
                "Peneira": "AFS (Tamanho Médio)",
                "Min (%)": f"{afs_min:.1f}",
                "Max (%)": f"{afs_max:.1f}"
            })
            
            df_faixa_lim = pd.DataFrame(rows_faixa)
            st.dataframe(df_faixa_lim, hide_index=True, use_container_width=True)
            
            # Botão de exclusão da faixa selecionada
            st.markdown("---")
            st.markdown("#### 🗑️ Excluir Disciplina")
            if st.button("Excluir esta Faixa Alvo", key="btn_del_faixa", type="secondary", use_container_width=True):
                if len(faixas_dict) <= 1:
                    st.error("Não é possível excluir a única faixa alvo cadastrada no sistema.")
                else:
                    deleted = faixas_dict.pop(selected_faixa_manage)
                    salvar_faixas(faixas_dict)
                    st.success(f"Faixa alvo '{selected_faixa_manage}' excluída com sucesso!")
                    st.rerun()
                    
        with col_faixa_dir:
            # Abas internas para Editar e Adicionar
            tab_edit_faixa, tab_add_faixa = st.tabs(["📝 Editar Faixa Alvo", "➕ Cadastrar Nova Faixa Alvo"])
            
            with tab_edit_faixa:
                st.markdown(f"#### Alterar Limites de: **{selected_faixa_manage}**")
                
                with st.form("form_edit_faixa"):
                    nome_faixa_edit = st.text_input("Nome da Disciplina / Faixa Alvo", value=selected_faixa_manage)
                    
                    st.markdown("##### Limites Granulométricos nas Peneiras (%)")
                    
                    c_fe1, c_fe2, c_fe3 = st.columns(3)
                    edit_limits = {}
                    
                    # Dividir as 11 peneiras entre 3 colunas
                    for idx_s, s in enumerate(SIEVES):
                        val_min_default, val_max_default = current_faixa[s]
                        
                        target_col = c_fe1 if idx_s < 4 else (c_fe2 if idx_s < 8 else c_fe3)
                        
                        with target_col:
                            st.markdown(f"**{SIEVE_DISPLAY_NAMES.get(s, s)}**")
                            col_n1, col_n2 = st.columns(2)
                            with col_n1:
                                edit_limits[s + "_min"] = st.number_input(
                                    "Mín", 0.0, 100.0, float(val_min_default),
                                    step=0.1, format="%.2f",
                                    key=f"edit_min_{s}"
                                )
                            with col_n2:
                                edit_limits[s + "_max"] = st.number_input(
                                    "Máx", 0.0, 100.0, float(val_max_default),
                                    step=0.1, format="%.2f",
                                    key=f"edit_max_{s}"
                                )
                            st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
                            
                    btn_save_edit = st.form_submit_button("💾 Salvar Alterações", type="primary")
                    
                    if btn_save_edit:
                        # Validações
                        valido = True
                        for s in SIEVES:
                            s_min = edit_limits[s + "_min"]
                            s_max = edit_limits[s + "_max"]
                            if s_min > s_max:
                                st.error(f"Erro na peneira {s}: o limite mínimo ({s_min}) não pode ser maior que o máximo ({s_max}).")
                                valido = False
                                break
                                
                        if not nome_faixa_edit.strip():
                            st.error("O nome da disciplina não pode ser vazio.")
                            valido = False
                            
                        if valido:
                            # Monta o novo dicionário de limites
                            nova_faixa_data = {}
                            for s in SIEVES:
                                nova_faixa_data[s] = (edit_limits[s + "_min"], edit_limits[s + "_max"])
                                
                            # Calcular AFS automaticamente
                            sieve_mins = {s: edit_limits[s + "_min"] for s in SIEVES}
                            sieve_maxs = {s: edit_limits[s + "_max"] for s in SIEVES}
                            afs_min = round(calcular_afs(sieve_mins), 1)
                            afs_max = round(calcular_afs(sieve_maxs), 1)
                            nova_faixa_data["AFS"] = (afs_min, afs_max)
                            
                            # Se mudou o nome da faixa, remove a antiga
                            if nome_faixa_edit.strip() != selected_faixa_manage:
                                faixas_dict.pop(selected_faixa_manage)
                                
                            faixas_dict[nome_faixa_edit.strip()] = nova_faixa_data
                            salvar_faixas(faixas_dict)
                            st.session_state.faixas_alvo = faixas_dict
                            blend_engine.FAIXAS_ALVO = faixas_dict
                            st.success(f"Faixa alvo '{nome_faixa_edit.strip()}' salva com sucesso! AFS calculado automaticamente: {afs_min} a {afs_max}")
                            st.rerun()
                            
            with tab_add_faixa:
                st.markdown("#### Cadastrar Nova Disciplina / Faixa Alvo")
                
                with st.form("form_add_faixa"):
                    nome_faixa_new = st.text_input("Nome da Nova Disciplina", placeholder="Ex: Hipismo Salto")
                    modelo_base = st.selectbox(
                        "Usar limites de uma faixa existente como modelo:",
                        options=faixas_nomes
                    )
                    
                    st.markdown("##### Limites Granulométricos nas Peneiras (%)")
                    
                    c_fa1, c_fa2, c_fa3 = st.columns(3)
                    add_limits = {}
                    
                    model_faixa = faixas_dict[modelo_base]
                    
                    for idx_s, s in enumerate(SIEVES):
                        val_min_default, val_max_default = model_faixa[s]
                        
                        target_col = c_fa1 if idx_s < 4 else (c_fa2 if idx_s < 8 else c_fa3)
                        
                        with target_col:
                            st.markdown(f"**{SIEVE_DISPLAY_NAMES.get(s, s)}**")
                            col_n1, col_n2 = st.columns(2)
                            with col_n1:
                                add_limits[s + "_min"] = st.number_input(
                                    "Mín", 0.0, 100.0, float(val_min_default),
                                    step=0.1, format="%.2f",
                                    key=f"add_min_{s}"
                                )
                            with col_n2:
                                add_limits[s + "_max"] = st.number_input(
                                    "Máx", 0.0, 100.0, float(val_max_default),
                                    step=0.1, format="%.2f",
                                    key=f"add_max_{s}"
                                )
                            st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
                            
                    btn_save_add = st.form_submit_button("➕ Cadastrar Nova Faixa Alvo", type="primary")
                    
                    if btn_save_add:
                        valido = True
                        if not nome_faixa_new.strip():
                            st.error("Por favor, informe o nome da nova disciplina.")
                            valido = False
                        elif nome_faixa_new.strip() in faixas_dict:
                            st.error("Uma disciplina com esse nome já existe.")
                            valido = False
                            
                        if valido:
                            for s in SIEVES:
                                s_min = add_limits[s + "_min"]
                                s_max = add_limits[s + "_max"]
                                if s_min > s_max:
                                    st.error(f"Erro na peneira {s}: o limite mínimo ({s_min}) não pode ser maior que o máximo ({s_max}).")
                                    valido = False
                                    break
                                    
                        if valido:
                            nova_faixa_data = {}
                            for s in SIEVES:
                                nova_faixa_data[s] = (add_limits[s + "_min"], add_limits[s + "_max"])
                                
                            # Calcular AFS automaticamente
                            sieve_mins = {s: add_limits[s + "_min"] for s in SIEVES}
                            sieve_maxs = {s: add_limits[s + "_max"] for s in SIEVES}
                            afs_min = round(calcular_afs(sieve_mins), 1)
                            afs_max = round(calcular_afs(sieve_maxs), 1)
                            nova_faixa_data["AFS"] = (afs_min, afs_max)
                            
                            faixas_dict[nome_faixa_new.strip()] = nova_faixa_data
                            salvar_faixas(faixas_dict)
                            st.session_state.faixas_alvo = faixas_dict
                            blend_engine.FAIXAS_ALVO = faixas_dict
                            st.success(f"Nova faixa alvo '{nome_faixa_new.strip()}' cadastrada com sucesso! AFS calculado automaticamente: {afs_min} a {afs_max}")
                            st.rerun()

    # ----------------------------------------------------
    # TAB 6: BLENDAGEM
    # ----------------------------------------------------
    with tab6:
        st.subheader("Misturador & Otimizador Granulométrico")
        
        # Escolha da Faixa Alvo
        target_profile = st.selectbox("Selecione a Modalidade / Faixa Alvo da Superfície:", list(blend_engine.FAIXAS_ALVO.keys()))
        
        # Exibe os limites da faixa selecionada
        st.caption(f"Faixa Alvo Selecionada: {target_profile}")
        
        st.markdown("#### Seleção de Componentes da Mistura")
        col_sands = st.columns(4)
        selected_sands = []
        
        areia_nomes = [a["Areia"] for a in st.session_state.banco_areias]
        
        # Seleção de até 4 areias
        for i in range(4):
            with col_sands[i]:
                s_name = st.selectbox(
                    f"Componente {chr(65+i)} (Areia {chr(65+i)})",
                    ["-- Não Selecionado --"] + areia_nomes,
                    index=0 if i > 0 else (areia_nomes.index("Itarena 3 - Areia Fina") + 1 if "Itarena 3 - Areia Fina" in areia_nomes else 1),
                    key=f"blend_sand_{i}"
                )
                if s_name != "-- Não Selecionado --":
                    # Recupera o registro da areia do banco
                    sand_record = next(a for a in st.session_state.banco_areias if a["Areia"] == s_name)
                    selected_sands.append(sand_record)
        
        if not selected_sands:
            st.warning("Selecione pelo menos uma areia para iniciar o misturador.")
        else:
            N = len(selected_sands)
            st.divider()
            
            c_mode, c_vals = st.columns([1, 3])
            
            with c_mode:
                st.markdown("#### Ajuste do Blend")
                otimizar = st.checkbox("⚙️ Otimização Automática", value=True, help="Usa otimização linear para encontrar a melhor curva possível da faixa alvo.")
                
            proportions = []
            with c_vals:
                st.markdown("#### Proporções da Mistura (%)")
                c_props = st.columns(N)
                
                if otimizar:
                    # Roda o otimizador
                    opt_props = otimizar_proporcoes(selected_sands, target_profile)
                    for idx in range(N):
                        with c_props[idx]:
                            st.metric(label=f"Proporção {selected_sands[idx]['Areia']}", value=f"{opt_props[idx]:.1f}%")
                            proportions.append(opt_props[idx])
                else:
                    # Ajuste manual
                    for idx in range(N):
                        with c_props[idx]:
                            val = st.number_input(
                                f"{selected_sands[idx]['Areia']} (%)",
                                0.0, 100.0, 100.0 / N if idx == 0 else 0.0,
                                step=5.0,
                                key=f"manual_prop_{idx}"
                            )
                            proportions.append(val)
                    
                    sum_props = sum(proportions)
                    if abs(sum_props - 100.0) > 0.01:
                        st.error(f"A soma das proporções deve ser exatamente 100%. Soma atual: {sum_props:.1f}%")
            
            # Executar cálculo da mistura
            blend_result = calcular_mistura(selected_sands, proportions)
            blend_afs = round(calcular_afs(blend_result), 1)
            
            # Guardar o blend atual e faixas na session_state para a aba 3
            st.session_state.current_blend = blend_result
            st.session_state.current_blend_afs = blend_afs
            st.session_state.current_sands = selected_sands
            st.session_state.current_proportions = proportions
            st.session_state.current_profile = target_profile
            
            # Exibir Comparativo Granulométrico
            st.markdown("---")
            st.markdown("### Comparativo Granulométrico Detalhado")
            
            # Construir tabela comparativa
            faixa = blend_engine.FAIXAS_ALVO[target_profile]
            rows_comp = []
            
            for s in SIEVES:
                target_min, target_max = faixa[s]
                res_val = blend_result[s]
                
                # Definir status
                if res_val < target_min:
                    status = "🔴 ABAIXO"
                elif res_val > target_max:
                    status = "🔴 ACIMA"
                else:
                    status = "🟢 DENTRO"
                    
                row = {
                    "Peneira": s,
                    "Ref. Mínima (%)": f"{target_min:.1f}%",
                    "Ref. Máxima (%)": f"{target_max:.1f}%",
                    "Resultado Blend (%)": f"{res_val:.1f}%",
                    "Status": status
                }
                rows_comp.append(row)
                
            df_comp = pd.DataFrame(rows_comp)
            
            c_tab, c_afs_res = st.columns([3, 1])
            with c_tab:
                # Estilizar tabela comparativa
                def style_status(val):
                    if "🟢" in val:
                        return "background-color: #e2f0d9; color: #2e7d32; font-weight: bold;"
                    else:
                        return "background-color: #fef2f2; color: #c62828; font-weight: bold;"
                        
                st.dataframe(
                    df_comp.style.map(style_status, subset=["Status"]),
                    use_container_width=True,
                    hide_index=True
                )
                
            with c_afs_res:
                # Mostrar AFS
                target_afs_min, target_afs_max = faixa["AFS"]
                st.markdown("#### AFS do Blend")
                st.metric("AFS da Mistura", f"{blend_afs:.1f}")
                st.markdown(f"**AFS Alvo da Disciplina:** `{target_afs_min:.1f} a {target_afs_max:.1f}`")
                
                if target_afs_min <= blend_afs <= target_afs_max:
                    st.success("✅ AFS dentro do intervalo ideal!")
                else:
                    st.warning("⚠️ AFS fora do intervalo ideal de suporte.")
            
            # Exibir gráficos comparativos na aba Blendagem
            st.divider()
            col_blend_g1, col_blend_g2 = st.columns(2)
            with col_blend_g1:
                fig_blend_curva = plot_curva_comparativa(blend_result, target_profile)
                st.pyplot(fig_blend_curva)
            with col_blend_g2:
                fig_blend_barras = plot_barras_mistura(blend_result, target_profile)
                st.pyplot(fig_blend_barras)

    # ----------------------------------------------------
    # TAB 7: DIMENSIONADOR & LAUDO
    # ----------------------------------------------------
    with tab7:
        st.subheader("Gestão de Insumos da Pista")
        
        if "current_blend" not in st.session_state:
            st.info("Por favor, configure a mistura na aba '6. Blendagem' antes de prosseguir.")
        else:
            c_ins1, c_ins2 = st.columns(2)
            with c_ins1:
                st.markdown("#### Geometria da Pista")
                pista_nome = st.text_input("Identificação da Pista", value=st.session_state.pista_nome)
                st.session_state.pista_nome = pista_nome
                
                col_geom = st.columns(3)
                with col_geom[0]:
                    comprimento = st.number_input("Comprimento (m)", 1.0, 1000.0, value=st.session_state.pista_comprimento)
                    st.session_state.pista_comprimento = comprimento
                with col_geom[1]:
                    largura = st.number_input("Largura (m)", 1.0, 500.0, value=st.session_state.pista_largura)
                    st.session_state.pista_largura = largura
                with col_geom[2]:
                    espessura = st.number_input("Espessura (cm)", 1.0, 50.0, value=st.session_state.pista_espessura)
                    st.session_state.pista_espessura = espessura
                    
            with c_ins2:
                st.markdown("#### Parâmetros de Materiais")
                # Densidade como campo obrigatório antes do cálculo
                densidade = st.number_input(
                    "Densidade da Areia (t/m³)",
                    0.0, 3.0, value=st.session_state.pista_densidade,
                    step=0.05,
                    help="Obrigatório para cálculo de massa total em toneladas."
                )
                st.session_state.pista_densidade = densidade
                
                if densidade == 0.0:
                    st.warning("⚠️ DENSIDADE OBRIGATÓRIA: Insira o valor da densidade da areia para habilitar o cálculo de tonelagem.")
                
                col_fib = st.columns([2, 1])
                with col_fib[0]:
                    modo_fibra = st.radio("Dosagem de Fibra aplicada via:", ["% sobre a massa de areia (A)", "kg/m² de pista (B)"], index=0)
                    fib_mode_letter = "A" if "(A)" in modo_fibra else "B"
                with col_fib[1]:
                    dosagem_fibra = st.number_input("Valor da Dosagem", 0.0, 50.0, 0.3 if fib_mode_letter == "A" else 3.0, step=0.1)
            
            # Se densidade está preenchida, realiza cálculo e exibe laudo
            if densidade > 0.0:
                insumos = dimensionar_insumos(
                    comprimento, largura, espessura, densidade,
                    fib_mode_letter, dosagem_fibra
                )
                
                st.divider()
                st.subheader("Relatório Técnico & Consolidação")
                
                # Tabela Consolidada
                data_consolidado = [{
                    "Pista / Picadeiro": pista_nome,
                    "Disciplina": st.session_state.current_profile,
                    "Composição Utilizada": " + ".join([f"{p}% {s['Areia']}" for s, p in zip(st.session_state.current_sands, st.session_state.current_proportions) if p > 0]),
                    "Qtd. Areia (t)": f"{insumos['sand_mass']:.1f} t",
                    "Espessura (cm)": f"{espessura:.1f} cm",
                    "Dosagem de Fibra (t)": f"{insumos['fiber_mass']:.3f} t",
                    "AFS do Blend": f"{st.session_state.current_blend_afs:.1f}"
                }]
                
                df_consolidado = pd.DataFrame(data_consolidado)
                st.dataframe(df_consolidado, hide_index=True, use_container_width=True)
                
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                
                # Exibição dos gráficos lado a lado
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    fig_curva = plot_curva_comparativa(st.session_state.current_blend, st.session_state.current_profile)
                    st.pyplot(fig_curva)
                    
                with col_g2:
                    fig_barras = plot_barras_mistura(st.session_state.current_blend, st.session_state.current_profile)
                    st.pyplot(fig_barras)
                    
                # Tabela de classificação USDA do blend
                active_sands = [s for s, p in zip(st.session_state.current_sands, st.session_state.current_proportions) if p > 0]
                blend_rec = dict(st.session_state.current_blend)
                blend_rec["Areia"] = "MISTURA"
                
                exibir_tabela_usda(active_sands + [blend_rec], title="Classificação USDA — Componentes e Mistura")
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                
                # Espaço para foto do formato da areia e nota final
                c_footer1, c_footer2 = st.columns(2)
                with c_footer1:
                    st.markdown("**Formato e Angularidade da Areia (Componentes do Blend)**")
                    active_components = [
                        (sand, prop) for sand, prop in zip(st.session_state.current_sands, st.session_state.current_proportions)
                        if prop > 0
                    ]
                    if active_components:
                        for sand_rec, prop in active_components:
                            st.markdown(f"**{sand_rec['Areia']}** ({prop:.1f}%)")
                            formato = sand_rec.get("Formato", "Não Informado")
                            
                            # Explicações técnicas baseadas na classificação
                            expl = ""
                            if formato == "Arredondado":
                                expl = "Grãos arredondados. Menor atrito e estabilidade (tendência a rolar), baixo desgaste dos cascos e alta durabilidade das partículas."
                            elif formato == "Sub-arredondado":
                                expl = "Grãos sub-arredondados. Suporte moderado e resistência intermediária com baixo desgaste."
                            elif formato == "Sub-angular":
                                expl = "Grãos sub-angulares. Excelente equilíbrio: evita o rolamento/instabilidade e promove boa elasticidade da pista."
                            elif formato == "Angular":
                                expl = "Grãos angulares. Elevado atrito e resistência ao cisalhamento (pista firme), mas causa alto desgaste nos cascos e quebra facilmente gerando finos."
                            else:
                                expl = "Sem classificação morfológica cadastrada."
                                
                            st.markdown(f"*Formato*: {formato} — *{expl}*")
                            
                            p_files = sand_rec.get("Foto", [])
                            if isinstance(p_files, str):
                                p_files = [p_files] if p_files else []
                                
                            if p_files:
                                for idx_p, p_file in enumerate(p_files):
                                    if p_file:
                                        p_path = os.path.join(FOTOS_DIR, p_file)
                                        if os.path.exists(p_path):
                                            st.image(p_path, caption=f"Foto {idx_p + 1}: {sand_rec['Areia']}", use_container_width=True)
                                        else:
                                            st.caption(f"📷 Foto {idx_p + 1} cadastrada mas não localizada no disco.")
                            else:
                                st.caption("📷 Nenhuma foto anexada a esta areia.")
                            st.markdown("---")
                    else:
                        st.info("Nenhum componente ativo no blend atual.")
                        
                with c_footer2:
                    st.markdown("**Notas Adicionais do Laudo**")
                    st.caption(
                        "O Método Paulo Nania une a análise física dos materiais com o dimensionamento granulométrico ideal "
                        "para obter superfícies estáveis, garantindo o amortecimento de impacto, suporte e tração adequados para o esporte hípico."
                    )
            else:
                st.info("Insira a densidade acima para gerar a consolidação e os gráficos de laudo da pista.")


if __name__ == "__main__":
    main()
