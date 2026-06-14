import os
import importlib

import pandas as pd
import streamlit as st

import analysis
import charts
import pdf_report
importlib.reload(analysis)
importlib.reload(charts)
importlib.reload(pdf_report)

from analysis import (
    calcular_estatisticas,
    classificar_espessura,
    classificar_penetro,
    classificar_umidade,
    classificar_desvio_fase,
    classificar_umidade_valor,
    classificar_espessura_valor,
    classificar_perfil,
)
from charts import fig_mapa_espessura, fig_mapa_umidade, fig_penetrometro, fig_comparativa
from data import (
    assinatura_grade,
    carregar_csv,
    criar_grade,
    exportar_csv,
    extrair_df_editor,
    mesclar_grade,
    meta_padrao,
    normalizar_df_coleta,
    preparar_dados_analise,
)
from pdf_report import gerar_pdf

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
LAST_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_data.csv")
PASSOS = [
    "⚙️ 1. Configurar",
    "📝 2. Coletar",
    "📋 3. Diagnóstico",
    "📈 4. Gráficos",
    "📊 5. Análise Comparativa",
    "📋 6. Relatório de Diagnóstico"
]
HISTORICO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historico")
if not os.path.exists(HISTORICO_DIR):
    os.makedirs(HISTORICO_DIR)
EDITOR_KEY = "coleta_editor"
EDITOR_SIG_KEY = "coleta_editor_sig"


def salvar_estado_local():
    try:
        if "passo" in st.session_state:
            st.session_state.meta["passo"] = st.session_state.passo
        csv_bytes = exportar_csv(st.session_state.df_coleta, st.session_state.meta)
        with open(LAST_DATA_PATH, "wb") as f:
            f.write(csv_bytes)
            
        # Copiar para o diretório de histórico
        meta = st.session_state.meta
        if meta.get("fazenda") and meta.get("data"):
            nome = nome_arquivo("Levantamento", meta) + ".csv"
            caminho_hist = os.path.join(HISTORICO_DIR, nome)
            with open(caminho_hist, "wb") as f:
                f.write(csv_bytes)
    except Exception:
        pass


def init_session():
    if "meta" not in st.session_state or "df_coleta" not in st.session_state:
        carregou_sucesso = False
        if os.path.exists(LAST_DATA_PATH):
            try:
                with open(LAST_DATA_PATH, "rb") as f:
                    meta_carregada, df_carregado = carregar_csv(f)
                st.session_state.meta = meta_carregada
                st.session_state.df_coleta = df_carregado
                st.session_state.passo = int(meta_carregada.get("passo", 0))
                carregou_sucesso = True
            except Exception:
                pass
        
        if not carregou_sucesso:
            if "passo" not in st.session_state:
                st.session_state.passo = 0
            if "meta" not in st.session_state:
                st.session_state.meta = meta_padrao()
            if "df_coleta" not in st.session_state:
                meta = st.session_state.meta
                st.session_state.df_coleta = criar_grade(
                    meta["n_linhas"],
                    meta["n_pontos"],
                    meta["global_umi"],
                    meta["global_esp"],
                )
    
    if "passo" not in st.session_state:
        st.session_state.passo = 0


def reset_coleta_editor():
    st.session_state.pop(EDITOR_KEY, None)
    st.session_state.pop(EDITOR_SIG_KEY, None)


def sync_editor_to_coleta(editor_df=None):
    if isinstance(editor_df, pd.DataFrame):
        st.session_state.df_coleta = normalizar_df_coleta(editor_df)
        salvar_estado_local()
        return
    if EDITOR_KEY in st.session_state:
        bruto = st.session_state[EDITOR_KEY]
        df = extrair_df_editor(bruto, st.session_state.df_coleta)
        st.session_state.df_coleta = normalizar_df_coleta(df)
        salvar_estado_local()


def preparar_editor_coleta():
    meta = st.session_state.meta
    sig = assinatura_grade(meta)
    st.session_state.df_coleta = normalizar_df_coleta(st.session_state.df_coleta)

    if st.session_state.get(EDITOR_SIG_KEY) != sig:
        st.session_state[EDITOR_SIG_KEY] = sig
        st.session_state.pop(EDITOR_KEY, None)


def atualizar_grade():
    meta = st.session_state.meta
    st.session_state.df_coleta = mesclar_grade(
        st.session_state.df_coleta,
        int(meta["n_linhas"]),
        int(meta["n_pontos"]),
        meta["global_umi"],
        meta["global_esp"],
    )
    reset_coleta_editor()
    salvar_estado_local()


def nome_arquivo(prefixo, meta):
    fazenda = meta["fazenda"].replace(" ", "_")
    data = meta["data"].replace("/", "-")
    return f"{prefixo}_{fazenda}_{data}"


def render_cabecalho():
    col_logo, col_titulo = st.columns([1, 3])
    with col_logo:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=180)
    with col_titulo:
        st.title("Relatório de Desempenho — Método Pnania")
        st.caption("Configure a pista, registre as medições e gere o laudo técnico.")


def render_passos():
    passo_anterior = st.session_state.passo
    passo = st.radio(
        "Etapas",
        PASSOS,
        index=st.session_state.passo,
        horizontal=True,
        label_visibility="collapsed",
    )
    novo_passo = PASSOS.index(passo)
    if passo_anterior == 1 and novo_passo != 1:
        sync_editor_to_coleta()
    st.session_state.passo = novo_passo
    salvar_estado_local()
    st.divider()


def render_configurar():
    meta = st.session_state.meta

    st.subheader("Identificação do levantamento")
    c1, c2 = st.columns(2)
    with c1:
        meta["fazenda"] = st.text_input("Fazenda / Haras", meta["fazenda"])
        meta["pista"] = st.text_input("Pista / Picadeiro", meta["pista"])
    with c2:
        meta["dimensao"] = st.text_input("Dimensão da pista", meta["dimensao"])
        meta["data"] = st.text_input("Data da coleta", meta["data"])
        
        tipo_atual = meta.get("tipo_pista", "Pista de Treinamento")
        lista_opcoes = ["Pista de Treinamento", "Pista de Competição"]
        try:
            index_opcao = lista_opcoes.index(tipo_atual)
        except ValueError:
            index_opcao = 0
        meta["tipo_pista"] = st.selectbox("Tipo de pista", lista_opcoes, index=index_opcao)

    st.subheader("Parâmetros ideais")
    c3, c4 = st.columns(2)
    with c3:
        umi_input = st.text_input("Faixa ideal de umidade", meta["ideal_umi"])
        if umi_input:
            val = umi_input.strip()
            if val and not val.endswith("%"):
                val = f"{val}%"
            meta["ideal_umi"] = val
        else:
            meta["ideal_umi"] = ""
    with c4:
        esp_input = st.text_input("Espessura ideal (cm)", meta["ideal_esp"])
        if esp_input:
            val = esp_input.strip()
            if val and not val.lower().endswith("cm"):
                val = f"{val} cm"
            meta["ideal_esp"] = val
        else:
            meta["ideal_esp"] = ""

    st.subheader("Grade de amostragem")
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        val_linhas = max(2, int(meta.get("n_linhas", 4)))
        max_linhas = max(50, val_linhas)
        meta["n_linhas"] = st.number_input("Linhas (eixo X)", 2, max_linhas, val_linhas, 1)
    with c6:
        val_pontos = max(2, int(meta.get("n_pontos", 5)))
        max_pontos = max(50, val_pontos)
        meta["n_pontos"] = st.number_input("Pontos por linha (eixo Y)", 2, max_pontos, val_pontos, 1)
    with c7:
        meta["coletou_umidade"] = st.checkbox("Umidade por ponto", meta["coletou_umidade"])
    with c8:
        meta["coletou_espessura"] = st.checkbox("Espessura por ponto", meta["coletou_espessura"])

    if not meta["coletou_umidade"] or not meta["coletou_espessura"]:
        st.markdown("**Valores gerais** (quando não coletados ponto a ponto)")
        g1, g2 = st.columns(2)
        with g1:
            if not meta["coletou_umidade"]:
                val_umi = max(0.0, min(100.0, float(meta.get("global_umi", 18.0))))
                meta["global_umi"] = st.number_input("Umidade geral (%)", 0.0, 100.0, val_umi, 0.1)
        with g2:
            if not meta["coletou_espessura"]:
                val_esp = max(0, min(50, int(float(meta.get("global_esp", 12)))))
                meta["global_esp"] = st.number_input("Espessura geral (cm)", 0, 50, val_esp, 1)


    st.subheader("Histórico")
    arquivo = st.file_uploader("Carregar levantamento anterior (CSV ou Excel)", type=["csv", "xlsx", "xls"])
    if arquivo is not None:
        try:
            meta_nova, df_nova = carregar_csv(arquivo)
            st.session_state.meta = meta_nova
            st.session_state.df_coleta = df_nova
            reset_coleta_editor()
            salvar_estado_local()
            st.success(f"Levantamento de {meta_nova['fazenda']} carregado.")
            st.rerun()
        except Exception as exc:
            st.error(f"Erro ao carregar arquivo: {exc}")

    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("🗑️ Limpar Todos os Dados", type="secondary", use_container_width=True):
            meta_limpa = {
                "fazenda": "",
                "pista": "",
                "dimensao": "",
                "data": "",
                "ideal_umi": "",
                "ideal_esp": "",
                "n_linhas": 4,
                "n_pontos": 5,
                "coletou_umidade": True,
                "coletou_espessura": True,
                "global_umi": 0.0,
                "global_esp": 0,
                "notas_gerais": "",
                "notas_manejo": "",
                "notas_parecer": "",
                "passo": 0,
            }
            st.session_state.meta = meta_limpa
            st.session_state.df_coleta = pd.DataFrame([
                {
                    "Linha": l,
                    "Ponto": p,
                    "1ª Queda": 0.0,
                    "2ª Queda": 0.0,
                    "3ª Queda": 0.0,
                    "Umidade": 0.0,
                    "Espessura": 0,
                }
                for l in range(1, 5)
                for p in range(1, 6)
            ])
            st.session_state.passo = 0
            reset_coleta_editor()
            salvar_estado_local()
            st.rerun()

    with c_btn2:
        if st.button("Continuar para coleta →", type="primary", use_container_width=True):
            atualizar_grade()
            st.session_state.passo = 1
            st.rerun()

    salvar_estado_local()


def render_coletar():
    meta = st.session_state.meta
    total = int(meta["n_linhas"]) * int(meta["n_pontos"])

    st.subheader("Dados de campo")
    st.info(
        f"Grade **{meta['n_linhas']}×{meta['n_pontos']}** — {total} pontos. "
        "Preencha a tabela abaixo com as medições do penetrômetro."
    )

    preparar_editor_coleta()

    colunas = {
        "Linha": st.column_config.NumberColumn("Linha", disabled=True, format="%d"),
        "Ponto": st.column_config.NumberColumn("Ponto", disabled=True, format="%d"),
        "1ª Queda": st.column_config.NumberColumn("1ª Queda (cm)", min_value=0.0, max_value=25.0, step=0.1, format="%.1f"),
        "2ª Queda": st.column_config.NumberColumn("2ª Queda (cm)", min_value=0.0, max_value=25.0, step=0.1, format="%.1f"),
        "3ª Queda": st.column_config.NumberColumn("3ª Queda (cm)", min_value=0.0, max_value=25.0, step=0.1, format="%.1f"),
    }
    colunas_visiveis = ["Linha", "Ponto", "1ª Queda", "2ª Queda", "3ª Queda"]
    if meta["coletou_umidade"]:
        colunas["Umidade"] = st.column_config.NumberColumn("Umidade (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f")
        colunas_visiveis.append("Umidade")
    if meta["coletou_espessura"]:
        colunas["Espessura"] = st.column_config.NumberColumn("Espessura (cm)", min_value=0, max_value=50, step=1, format="%d")
        colunas_visiveis.append("Espessura")

    edited_df = st.data_editor(
        st.session_state.df_coleta,
        column_config=colunas,
        column_order=colunas_visiveis,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key=EDITOR_KEY,
    )


    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Voltar"):
            sync_editor_to_coleta(edited_df)
            st.session_state.passo = 0
            st.rerun()
    with c2:
        if st.button("Ver diagnóstico →", type="primary", use_container_width=True):
            sync_editor_to_coleta(edited_df)
            st.session_state.passo = 2
            st.rerun()


def render_card_html_unificado(titulo, valor_atual, classificacao, color_hex, ideal_txt=None, destaque=False, subtitulo=None):
    if color_hex == "#2e7d32":  # Green
        bg_color_hex = "#f0fdf4"
        border_color_hex = "#bbf7d0"
    elif color_hex == "#f57c00":  # Yellow/Orange
        bg_color_hex = "#fffbeb"
        border_color_hex = "#fde68a"
    else:  # Red
        bg_color_hex = "#fef2f2"
        border_color_hex = "#fecaca"
        
    shadow = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)" if destaque else "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)"
    border_style = f"border: 2px solid {color_hex};" if destaque else f"border: 1px solid {border_color_hex}; border-left: 6px solid {color_hex};"
    
    ideal_html = f'<span style="font-size: 11px; color: #64748b; font-weight: 500;">{ideal_txt}</span>' if ideal_txt else ''
    subtitulo_html = f'<div style="font-size: 9px; color: #64748b; font-weight: 500; margin-top: -2px; margin-bottom: 2px; text-transform: none; letter-spacing: 0px;">{subtitulo}</div>' if subtitulo else ''
    
    return f"""<div style="background-color: {bg_color_hex}; {border_style} border-radius: 10px; padding: 16px 20px; box-shadow: {shadow}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin-bottom: 15px; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px;">
<div>
<div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.75px; margin-bottom: 4px;">{titulo}</div>
{subtitulo_html}
</div>
<div style="font-size: 32px; font-weight: 800; color: #1e293b; margin: 4px 0;">{valor_atual}</div>
<div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px;">
<span style="background-color: {color_hex}; color: #ffffff; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 12px; text-transform: uppercase; letter-spacing: 0.5px; display: inline-block; white-space: nowrap;">{classificacao}</span>
{ideal_html}
</div>
</div>"""


def render_resumo_cards(stats, meta, df):
    # --- Bloco 1: Análise Integrada da Pista ---
    st.markdown("### Análise Integrada da Pista")
    
    # 1. Equipamento Longchamp (Container Único com cabeçalho, destaque e 3 quedas)
    with st.container(border=True):
        st.markdown("<h4 style='text-align: center; color: #0f3a61; margin-top: 5px; margin-bottom: 15px;'>Penetrômetro Longchamp</h4>", unsafe_allow_html=True)
        
        # Indicador de Topo (O Geral)
        col_gen = st.columns([1.3, 1.4, 1.3])
        with col_gen[1]:
            media_fases = sum(stats["medicao_atual"]) / 3
            rotulo_perfil, cor_perfil, desc_perfil = classificar_perfil(media_fases)
            st.markdown(
                render_card_html_unificado(
                    titulo="Penetrômetro",
                    valor_atual=f"{media_fases:.1f} cm",
                    classificacao=rotulo_perfil,
                    color_hex=cor_perfil,
                    ideal_txt=None,
                    destaque=True,
                    subtitulo=desc_perfil
                ),
                unsafe_allow_html=True
            )
            
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        # Linha de Detalhamento (As 3 Quedas)
        cols_drops = st.columns(3)
        
        # 1. Impacto (1ª Queda)
        f_amort = stats["fases"][0]
        with cols_drops[0]:
            st.markdown(
                render_card_html_unificado(
                    titulo="Impacto (1ª Queda)",
                    valor_atual=f"{f_amort['media']:.1f} cm",
                    classificacao=f_amort["status"],
                    color_hex=f_amort["cor"],
                    ideal_txt=f_amort["ideal"]
                ),
                unsafe_allow_html=True
            )
            
        # 2. Suporte (2ª Queda)
        f_trans = stats["fases"][1]
        with cols_drops[1]:
            st.markdown(
                render_card_html_unificado(
                    titulo="Suporte (2ª Queda)",
                    valor_atual=f"{f_trans['media']:.1f} cm",
                    classificacao=f_trans["status"],
                    color_hex=f_trans["cor"],
                    ideal_txt=f_trans["ideal"]
                ),
                unsafe_allow_html=True
            )
            
        # 3. Tração (3ª Queda)
        f_sup = stats["fases"][2]
        with cols_drops[2]:
            st.markdown(
                render_card_html_unificado(
                    titulo="Tração (3ª Queda)",
                    valor_atual=f"{f_sup['media']:.1f} cm",
                    classificacao=f_sup["status"],
                    color_hex=f_sup["cor"],
                    ideal_txt=f_sup["ideal"]
                ),
                unsafe_allow_html=True
            )
        
    # Linha 2: Sensores de Apoio (Simétricos e Centralizados)
    show_umi = stats['umidade_media_geral'] > 0.0
    show_esp = stats['espessura_media_geral'] > 0
    
    if show_umi or show_esp:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #0f3a61; margin-top: 5px; margin-bottom: 15px;'>Parâmetros de Apoio</h4>", unsafe_allow_html=True)
            
            if show_umi and show_esp:
                # Dois cartões ativos: Centralizados na linha usando 4 colunas
                cols_apoio = st.columns([1.0, 1.3, 1.3, 1.0])
                
                # Umidade - TDR 250
                rotulo_umi, cor_umi = classificar_umidade_valor(stats['umidade_media_geral'], meta["ideal_umi"])
                ideal_umi_val = meta["ideal_umi"] if meta["ideal_umi"] else "18.0%"
                with cols_apoio[1]:
                    st.markdown(
                        render_card_html_unificado(
                            titulo="Umidade - TDR 250",
                            valor_atual=f"{stats['umidade_media_geral']:.1f}%",
                            classificacao=rotulo_umi,
                            color_hex=cor_umi,
                            ideal_txt=f"Alvo: {ideal_umi_val}"
                        ),
                        unsafe_allow_html=True
                    )
                    
                # Espessura
                rotulo_esp, cor_esp = classificar_espessura_valor(stats['espessura_media_geral'], meta["ideal_esp"])
                ideal_esp_val = meta["ideal_esp"] if meta["ideal_esp"] else "12 cm"
                with cols_apoio[2]:
                    st.markdown(
                        render_card_html_unificado(
                            titulo="Espessura",
                            valor_atual=f"{stats['espessura_media_geral']} cm",
                            classificacao=rotulo_esp,
                            color_hex=cor_esp,
                            ideal_txt=f"Alvo: {ideal_esp_val}"
                        ),
                        unsafe_allow_html=True
                    )
            else:
                # Apenas um cartão ativo: Centralizado na linha usando 3 colunas
                cols_apoio = st.columns([1.3, 1.4, 1.3])
                with cols_apoio[1]:
                    if show_umi:
                        rotulo_umi, cor_umi = classificar_umidade_valor(stats['umidade_media_geral'], meta["ideal_umi"])
                        ideal_umi_val = meta["ideal_umi"] if meta["ideal_umi"] else "18.0%"
                        st.markdown(
                            render_card_html_unificado(
                                titulo="Umidade - TDR 250",
                                valor_atual=f"{stats['umidade_media_geral']:.1f}%",
                                classificacao=rotulo_umi,
                                color_hex=cor_umi,
                                ideal_txt=f"Alvo: {ideal_umi_val}"
                            ),
                            unsafe_allow_html=True
                        )
                    else:
                        rotulo_esp, cor_esp = classificar_espessura_valor(stats['espessura_media_geral'], meta["ideal_esp"])
                        ideal_esp_val = meta["ideal_esp"] if meta["ideal_esp"] else "12 cm"
                        st.markdown(
                            render_card_html_unificado(
                                titulo="Espessura",
                                valor_atual=f"{stats['espessura_media_geral']} cm",
                                classificacao=rotulo_esp,
                                color_hex=cor_esp,
                                ideal_txt=f"Alvo: {ideal_esp_val}"
                            ),
                            unsafe_allow_html=True
                        )
                        
    st.divider()
    
    # --- Bloco 2: Consistência ---
    with st.container(border=True):
        st.markdown("<h4 style='text-align: center; color: #0f3a61; margin-top: 5px; margin-bottom: 15px;'>Consistência</h4>", unsafe_allow_html=True)
        
        # Indicador de Topo (Resultado Geral)
        col_gen = st.columns([1.3, 1.4, 1.3])
        with col_gen[1]:
            label_icg, color_icg = classificar_penetro(stats["icg"])
            st.markdown(
                render_card_html_unificado(
                    titulo="Consistência Geral",
                    valor_atual=f"{stats['icg']:.1f}%",
                    classificacao=label_icg,
                    color_hex=color_icg,
                    ideal_txt=None,
                    destaque=True
                ),
                unsafe_allow_html=True
            )
            
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        # Linha de Coeficientes (Os Detalhes)
        cols_cv = st.columns(3)
        col_idx = 0
        
        # A. Penetrômetro (Sempre ativo)
        label_pen, color_pen = classificar_penetro(stats["io_geral"])
        with cols_cv[col_idx]:
            st.markdown(
                render_card_html_unificado(
                    titulo="Coeficiente Variação Penetrômetro",
                    valor_atual=f"{stats['io_geral']:.1f}%",
                    classificacao=label_pen,
                    color_hex=color_pen,
                    ideal_txt=None,
                    destaque=False
                ),
                unsafe_allow_html=True
            )
        col_idx += 1
        
        # B. Umidade
        if show_umi:
            label_umi, color_umi = classificar_umidade(stats["io_umidade"])
            with cols_cv[col_idx]:
                st.markdown(
                    render_card_html_unificado(
                        titulo="Coeficiente Variação Umidade",
                        valor_atual=f"{stats['io_umidade']:.1f}%",
                        classificacao=label_umi,
                        color_hex=color_umi,
                        ideal_txt=None,
                        destaque=False
                    ),
                    unsafe_allow_html=True
                )
            col_idx += 1
            
        # C. Espessura
        if show_esp:
            label_esp, color_esp = classificar_espessura(stats["io_espessura"])
            with cols_cv[col_idx]:
                st.markdown(
                    render_card_html_unificado(
                        titulo="Coeficiente Variação Espessura",
                        valor_atual=f"{stats['io_espessura']:.1f}%",
                        classificacao=label_esp,
                        color_hex=color_esp,
                        ideal_txt=None,
                        destaque=False
                    ),
                    unsafe_allow_html=True
                )
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size: 11.5px; color: #64748b; margin-top: 5px; margin-bottom: 0px; text-align: left; line-height: 1.4;'>"
            "<strong>Nota:</strong> O Coeficiente de Variação (CV%) mede a uniformidade da pista (quanto menor, "
            "mais consistente o terreno). A Consistência Geral é o indicador de comportamento da pista, "
            "unindo dados biomecânicos e de manejo para sinalizar a integridade da superfície."
            "</p>",
            unsafe_allow_html=True
        )


def render_diagnostico():
    sync_editor_to_coleta()
    meta = st.session_state.meta
    df = preparar_dados_analise(st.session_state.df_coleta, meta)
    stats = calcular_estatisticas(df, meta)

    render_resumo_cards(stats, meta, df)

    fig1 = fig_penetrometro(df, meta, stats)
    
    # Só gera o gráfico de calor de espessura se habilitado E houver dados preenchidos (> 0)
    tem_espessura = meta["coletou_espessura"] and (df["Espessura"] > 0).any()
    fig2 = fig_mapa_espessura(df, int(meta["n_linhas"]), int(meta["n_pontos"])) if tem_espessura else None
    
    # Só gera o gráfico de calor de umidade se habilitado E houver dados preenchidos (> 0.0)
    tem_umidade = meta["coletou_umidade"] and (df["Umidade"] > 0.0).any()
    fig3 = fig_mapa_umidade(df, int(meta["n_linhas"]), int(meta["n_pontos"])) if tem_umidade else None

    st.markdown("### Parecer Técnico")
    
    val_gerais = st.text_area(
        "Observações Gerais", 
        value=meta.get("notas_gerais", ""),
        key="rep_notas_gerais",
        help="Digite observações gerais sobre a coleta, clima ou condições adicionais."
    )
    val_manejo = st.text_area(
        "Manejo Recomendado", 
        value=meta.get("notas_manejo", ""),
        key="rep_notas_manejo",
        help="Recomendações de manejo (Ex: irrigar, gradear, nivelar, etc.)"
    )
    val_parecer = st.text_area(
        "Parecer Técnico", 
        value=meta.get("notas_parecer", ""),
        key="rep_notas_parecer",
        help="Sua conclusão técnica e diagnóstico do picadeiro."
    )
    
    if (val_gerais != meta.get("notas_gerais", "") or 
        val_manejo != meta.get("notas_manejo", "") or 
        val_parecer != meta.get("notas_parecer", "")):
        meta["notas_gerais"] = val_gerais
        meta["notas_manejo"] = val_manejo
        meta["notas_parecer"] = val_parecer
        salvar_estado_local()
        st.rerun()
        
    st.divider()

    st.subheader("Exportar laudo")
    st.caption("Baixe os arquivos antes de fechar o navegador — os dados não são salvos automaticamente.")

    pdf_bytes = gerar_pdf(meta=meta, fig_penetro=fig1, fig_espessura=fig2, fig_umidade=fig3, stats=stats)
    csv_bytes = exportar_csv(st.session_state.df_coleta, meta)

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.download_button(
            "📥 Baixar PDF",
            pdf_bytes,
            file_name=f"{nome_arquivo('Relatorio', meta)}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "📥 Baixar CSV",
            csv_bytes,
            file_name=f"{nome_arquivo('Levantamento', meta)}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with d3:
        if st.button("← Editar dados", use_container_width=True):
            st.session_state.passo = 1
            st.rerun()
    with d4:
        if st.button("Ver gráficos →", type="primary", use_container_width=True):
            st.session_state.passo = 3
            st.rerun()


def render_graficos():
    sync_editor_to_coleta()
    meta = st.session_state.meta
    df = preparar_dados_analise(st.session_state.df_coleta, meta)
    stats = calcular_estatisticas(df, meta)

    st.subheader("Gráficos de Análise")
    
    fig1 = fig_penetrometro(df, meta, stats)
    tem_espessura = meta["coletou_espessura"] and (df["Espessura"] > 0).any()
    fig2 = fig_mapa_espessura(df, int(meta["n_linhas"]), int(meta["n_pontos"])) if tem_espessura else None
    tem_umidade = meta["coletou_umidade"] and (df["Umidade"] > 0.0).any()
    fig3 = fig_mapa_umidade(df, int(meta["n_linhas"]), int(meta["n_pontos"])) if tem_umidade else None

    col_g1, col_g2 = st.columns([1.2, 1.0])
    with col_g1:
        st.pyplot(fig1)
    with col_g2:
        if fig2:
            st.pyplot(fig2)
            label_esp_cv, _ = classificar_espessura(stats["io_espessura"])
            st.markdown(f"**Coeficiente de Variação:** {stats['io_espessura']:.1f}% ({label_esp_cv})")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if fig3:
            st.pyplot(fig3)
            label_umi_cv, _ = classificar_umidade(stats["io_umidade"])
            st.markdown(f"**Coeficiente de Variação:** {stats['io_umidade']:.1f}% ({label_umi_cv})")
            
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Voltar para diagnóstico", use_container_width=True):
            st.session_state.passo = 2
            st.rerun()


def render_comparativa():
    st.subheader("Análise Comparativa Histórica")
    st.caption("Compare múltiplos levantamentos acumulados na sessão.")

    # Inicializa a lista se não existir
    if "comparativo_lista" not in st.session_state:
        st.session_state["comparativo_lista"] = []

    # 1. Upload de novos arquivos para adicionar à lista
    arquivos_novos = st.file_uploader(
        "Carregar novos arquivos (CSV ou Excel) para a comparação",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="uploader_comparativa"
    )
    if arquivos_novos:
        adicionou = False
        for f in arquivos_novos:
            # Evita duplicados por nome do arquivo
            if any(item["name"] == f.name for item in st.session_state["comparativo_lista"]):
                continue
            try:
                meta_carregada, df_carregado = carregar_csv(f)
                df_analise = preparar_dados_analise(df_carregado, meta_carregada)
                stats_carregadas = calcular_estatisticas(df_analise, meta_carregada)
                
                st.session_state["comparativo_lista"].append({
                    "name": f.name,
                    "meta": meta_carregada,
                    "df": df_analise,
                    "stats": stats_carregadas
                })
                adicionou = True
            except Exception as e:
                st.error(f"Erro ao carregar '{f.name}': {e}")
        if adicionou:
            st.rerun()

    # 2. Exibir lista de arquivos selecionados com opção de remoção
    if st.session_state["comparativo_lista"]:
        st.write("---")
        st.markdown("#### Arquivos selecionados para comparação:")
        
        for idx, item in enumerate(st.session_state["comparativo_lista"]):
            c_name, c_btn = st.columns([4, 1])
            with c_name:
                st.markdown(f"🔹 **{item['name']}** (Data: `{item['meta']['data']}`) - Haras: *{item['meta']['fazenda']}*")
            with c_btn:
                if st.button("Remover", key=f"del_{idx}_{item['name']}", use_container_width=True):
                    st.session_state["comparativo_lista"].pop(idx)
                    st.rerun()
                    
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        # Feedback de Processamento: Mensagem indicando prontidão para plotagem
        st.success("✅ **Dados carregados e prontos para comparação!** Clique no botão abaixo para gerar o comparativo.")
        
        if st.button("🧹 Limpar Lista Completa", use_container_width=True):
            st.session_state["comparativo_lista"] = []
            st.session_state["comp_ativo"] = False
            st.rerun()
    else:
        st.info("Nenhum arquivo na lista de comparação. Faça o upload de arquivos CSV acima para começar.")
        return

    # 3. Botão Gerar Comparativo
    st.write("---")
    if st.button("Gerar Comparativo", type="primary", use_container_width=True) or st.session_state.get("comp_ativo"):
        if st.session_state["comparativo_lista"]:
            st.session_state["comp_ativo"] = True
            
            # Exibir cabeçalho de resumo
            st.markdown("### Resumo Consolidado")
            for item in st.session_state["comparativo_lista"]:
                meta_carregada = item["meta"]
                stats_carregadas = item["stats"]
                
                media_fases = sum(stats_carregadas["medicao_atual"]) / 3
                rotulo_perfil, _, _ = classificar_perfil(media_fases)
                
                risco_val = stats_carregadas.get("risco_geral", 0.0)
                risco_status = stats_carregadas.get("geral_status", "IDEAL")

                # Umidade (N/A se inativa ou zerada)
                if meta_carregada.get("coletou_umidade") or stats_carregadas.get("umidade_media_geral", 0.0) > 0.0:
                    umi_txt = f"{stats_carregadas['umidade_media_geral']:.1f} %"
                else:
                    umi_txt = "N/A"
                    
                # Espessura (N/A se inativa ou zerada)
                if meta_carregada.get("coletou_espessura") or stats_carregadas.get("espessura_media_geral", 0) > 0:
                    esp_txt = f"{stats_carregadas['espessura_media_geral']} cm"
                else:
                    esp_txt = "N/A"
                
                with st.container(border=True):
                    st.markdown(f"🗓️ **Medição - {meta_carregada['data']}** (Haras: *{meta_carregada['fazenda']}*)")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.markdown(f"**Penetrômetro:**\n`{media_fases:.1f} cm | {risco_status} ({risco_val:.1f}%)`")
                    with col_b:
                        st.markdown(f"**Umidade:**\n`{umi_txt}`")
                    with col_c:
                        st.markdown(f"**Espessura:**\n`{esp_txt}`")
            
            st.markdown("### Gráfico Comparativo")
            fig_comp = fig_comparativa(st.session_state["comparativo_lista"], meta=st.session_state.meta)
            st.pyplot(fig_comp)
        else:
            st.session_state["comp_ativo"] = False
            st.warning("A lista de comparação está vazia.")

def render_streamlit_tabela(titulo, cabecalhos, dados):
    html = f"""
    <div style="margin-top: 15px; margin-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <h4 style="color: #0f3a61; margin-bottom: 8px; font-weight: 700; font-size: 15px;">{titulo}</h4>
        <table style="width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <thead>
                <tr style="background-color: #0f3a61; color: white; text-align: left; font-size: 13px;">
    """
    for col_idx, cab in enumerate(cabecalhos):
        align = "left" if col_idx == 0 else "center"
        html += f'<th style="padding: 10px 12px; font-weight: 600; text-align: {align};">{cab}</th>'
    
    html += """
                </tr>
            </thead>
            <tbody>
    """
    
    for idx_linha, linha in enumerate(dados):
        bg = "#f8fafc" if idx_linha % 2 == 1 else "#ffffff"
        html += f'<tr style="background-color: {bg}; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #334155;">'
        
        for col_idx, val in enumerate(linha):
            align = "left" if col_idx == 0 else "center"
            if col_idx == len(cabecalhos) - 1:
                val_upper = str(val).upper().strip()
                if "IDEAL" in val_upper or "EXCELENTE" in val_upper:
                    bg_cell = "#1b5e20"
                    color_cell = "#ffffff"
                elif "BOA" in val_upper:
                    bg_cell = "#a5d6a7"
                    color_cell = "#1b5e20"
                elif "SATISFATÓRIA" in val_upper or "SATISFATORIA" in val_upper or "ALERTA" in val_upper:
                    bg_cell = "#ffe082"
                    color_cell = "#7f5f00"
                elif "CRÍTICO" in val_upper or "CRITICO" in val_upper or "CRÍTICA" in val_upper or "CRITICA" in val_upper or "AJUSTES" in val_upper:
                    bg_cell = "#ef9a9a"
                    color_cell = "#b71c1c"
                else:
                    bg_cell = "transparent"
                    color_cell = "#334155"
                
                html += f'<td style="padding: 8px 12px; text-align: {align}; font-weight: 700; background-color: {bg_cell}; color: {color_cell};">{val}</td>'
            else:
                html += f'<td style="padding: 8px 12px; text-align: {align};">{val}</td>'
                
        html += '</tr>'
        
    html += """
            </tbody>
        </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_relatorio_pdf():
    sync_editor_to_coleta()
    meta = st.session_state.meta
    df = preparar_dados_analise(st.session_state.df_coleta, meta)
    stats = calcular_estatisticas(df, meta)

    # Gerar gráficos para exibição na tela e inserção no PDF
    fig1 = fig_penetrometro(df, meta, stats)
    tem_espessura = meta["coletou_espessura"] and (df["Espessura"] > 0).any()
    fig2 = fig_mapa_espessura(df, int(meta["n_linhas"]), int(meta["n_pontos"])) if tem_espessura else None
    tem_umidade = meta["coletou_umidade"] and (df["Umidade"] > 0.0).any()
    fig3 = fig_mapa_umidade(df, int(meta["n_linhas"]), int(meta["n_pontos"])) if tem_umidade else None

    # Comando único de geração de PDF completo
    pdf_bytes = gerar_pdf(meta=meta, fig_penetro=fig1, fig_espessura=fig2, fig_umidade=fig3, stats=stats)

    st.subheader("Relatório de Diagnóstico")
    
    col_download, col_dummy = st.columns([1.2, 3])
    with col_download:
        st.download_button(
            "📥 Exportar Laudo Completo (PDF)",
            pdf_bytes,
            file_name=f"{nome_arquivo('Relatorio_Completo', meta)}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        
    st.divider()
    
    # 1. Dados da página do diagnóstico (Cards de Resumo)
    render_resumo_cards(stats, meta, df)
    
    st.divider()
    
    # 2. Dados da página de gráficos (Exibição dos gráficos)
    st.markdown("### Gráficos de Análise")
    
    # Gráfico de Penetrômetro
    st.pyplot(fig1)
    
    # Mapa de calor de espessura
    if fig2 is not None:
        st.markdown("#### Mapa de Espessura da Pista")
        st.pyplot(fig2)
        label_esp_cv, _ = classificar_espessura(stats["io_espessura"])
        st.markdown(f"**Coeficiente de Variação:** {stats['io_espessura']:.1f}% ({label_esp_cv})")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
    # Mapa de calor de umidade
    if fig3 is not None:
        st.markdown("#### Distribuição Espacial de Umidade")
        st.pyplot(fig3)
        label_umi_cv, _ = classificar_umidade(stats["io_umidade"])
        st.markdown(f"**Coeficiente de Variação:** {stats['io_umidade']:.1f}% ({label_umi_cv})")

    # 3. Parecer Técnico e Notas
    if meta.get("notas_gerais") or meta.get("notas_manejo") or meta.get("notas_parecer"):
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.subheader("Parecer Técnico e Notas")
        
        if meta.get("notas_gerais"):
            with st.container(border=True):
                st.markdown("**Observações Gerais**")
                st.write(meta["notas_gerais"])
                
        if meta.get("notas_manejo"):
            with st.container(border=True):
                st.markdown("**Manejo Recomendado**")
                st.write(meta["notas_manejo"])
                
        if meta.get("notas_parecer"):
            with st.container(border=True):
                st.markdown("**Parecer Técnico**")
                st.write(meta["notas_parecer"])


def main():
    st.set_page_config(page_title="Sistema Pnania Premium", layout="wide", page_icon="📊")
    init_session()
    render_cabecalho()
    render_passos()

    if st.session_state.passo == 0:
        render_configurar()
    elif st.session_state.passo == 1:
        render_coletar()
    elif st.session_state.passo == 2:
        render_diagnostico()
    elif st.session_state.passo == 3:
        render_graficos()
    elif st.session_state.passo == 4:
        render_comparativa()
    elif st.session_state.passo == 5:
        render_relatorio_pdf()


if __name__ == "__main__":
    main()
