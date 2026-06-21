import os
import json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Import custom calculation engine
import blend_engine
from blend_engine import (
    SIEVES,
    FACTORS,
    FAIXAS_ALVO,
    calcular_afs,
    calcular_mistura,
    otimizar_proporcoes,
    dimensionar_insumos,
)

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
BANCO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banco_areias.json")

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
    {"Areia":"Areia Desclassificada","#10":0.46,"#14":0.15,"#18":0.1,"#35":0.85,"#40":0.41,"#60":5.78,"#100":39.39,"#140":9.27,"#200":7.12,"#270":5.81,"Finos":30.66,"AFS":153.62}
]


def carregar_banco():
    # 1. Carrega do JSON local se existir (contém inserções de novas areias)
    if os.path.exists(BANCO_FILE):
        try:
            with open(BANCO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    # 2. Carrega do arquivo original do Haras DOM no OneDrive se existir
    excel_path = r'c:\Users\paulo\OneDrive\Documentos\Haras DOM\Blend_Areia_Fibra_v5 (Haras Dom).xlsx'
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path, sheet_name='Banco_Areias')
            data = df.to_dict(orient='records')
            salvar_banco(data)
            return data
        except Exception:
            pass
            
    # 3. Fallback estático
    return DEFAULT_AREIAS


def salvar_banco(data):
    try:
        with open(BANCO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


def init_session():
    if "banco_areias" not in st.session_state:
        st.session_state.banco_areias = carregar_banco()
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


def plot_curva_comparativa(blend_result, target_profile):
    faixa = FAIXAS_ALVO[target_profile]
    
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = SIEVES
    y_res = [blend_result[s] for s in x]
    y_min = [faixa[s][0] for s in x]
    y_max = [faixa[s][1] for s in x]
    
    ax.plot(x, y_res, label="Mistura Resultante", color="#2e7d32", linewidth=2.5, marker="o", markersize=6)
    ax.plot(x, y_min, label="Limite Mínimo Alvo", color="#c62828", linestyle="--", linewidth=1.2)
    ax.plot(x, y_max, label="Limite Máximo Alvo", color="#c62828", linestyle="--", linewidth=1.2)
    
    ax.set_ylim(-1, max(max(y_res), max(y_max)) * 1.15)
    ax.set_title("Curva – Areia (blend) vs Alvo (Faixa_Alvo)", fontsize=11, fontweight="bold", pad=12, color="#0f3a61")
    ax.set_ylabel("% Retenção nas Peneiras", fontsize=9, fontweight="bold")
    ax.set_xlabel("Série de Peneiras", fontsize=9, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(frameon=True, facecolor="#f8fafc", edgecolor="none", loc="upper right")
    return fig


def plot_barras_mistura(blend_result):
    fig, ax = plt.subplots(figsize=(10, 3.8))
    x = SIEVES
    y = [blend_result[s] for s in x]
    
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
    ax.set_title("Distribuição de Retenção Granulométrica do Blend", fontsize=11, fontweight="bold", pad=12, color="#0f3a61")
    ax.set_ylabel("% Retida", fontsize=9, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    return fig


def main():
    st.set_page_config(page_title="Método Paulo Nania — Areias", layout="wide", page_icon="🏜️")
    init_session()
    render_cabecalho()
    
    tab1, tab2, tab3 = st.tabs(["🏜️ 1. Banco de Areias", "⚙️ 2. Motor de Blendagem", "📊 3. Dimensionador & Laudo"])
    
    # ----------------------------------------------------
    # TAB 1: BANCO DE AREIAS
    # ----------------------------------------------------
    with tab1:
        st.subheader("Base de Areias Cadastradas")
        st.write("Abaixo estão listadas as areias disponíveis para composição dos blends e análise técnica.")
        
        df_display = pd.DataFrame(st.session_state.banco_areias)
        
        # Formatar exibição do dataframe
        st.dataframe(
            df_display,
            column_config={
                "Areia": st.column_config.TextColumn("Nome da Areia", width="medium"),
                "AFS": st.column_config.NumberColumn("AFS", format="%.1f"),
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.divider()
        st.subheader("Cadastrar Nova Amostra")
        
        with st.form("nova_amostra_form", clear_on_submit=True):
            nome_amostra = st.text_input("Nome da Areia / Amostra", placeholder="Ex: Areia Fina Mogi")
            
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
                    nova_areia.update({s: sieve_inputs[s] for s in SIEVES})
                    nova_areia["AFS"] = afs_calc
                    
                    # Salvar na sessão e no arquivo local
                    st.session_state.banco_areias.append(nova_areia)
                    salvar_banco(st.session_state.banco_areias)
                    st.success(f"Areia '{nome_amostra.strip()}' cadastrada com sucesso! AFS calculado: {afs_calc}")
                    st.rerun()

    # ----------------------------------------------------
    # TAB 2: MOTOR DE BLENDAGEM
    # ----------------------------------------------------
    with tab2:
        st.subheader("Misturador & Otimizador Granulométrico")
        
        # Escolha da Faixa Alvo
        target_profile = st.selectbox("Selecione a Modalidade / Faixa Alvo da Superfície:", list(FAIXAS_ALVO.keys()))
        
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
            faixa = FAIXAS_ALVO[target_profile]
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

    # ----------------------------------------------------
    # TAB 3: DIMENSIONADOR & RELATÓRIO
    # ----------------------------------------------------
    with tab3:
        st.subheader("Gestão de Insumos da Pista")
        
        if "current_blend" not in st.session_state:
            st.info("Por favor, configure a mistura na aba '2. Motor de Blendagem' antes de prosseguir.")
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
                    fig_barras = plot_barras_mistura(st.session_state.current_blend)
                    st.pyplot(fig_barras)
                    
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                
                # Espaço para foto do formato da areia e nota final
                c_footer1, c_footer2 = st.columns(2)
                with c_footer1:
                    st.markdown("**Formato e Angularidade da Areia**")
                    st.info("[Inserir foto do formato da areia aqui]")
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
