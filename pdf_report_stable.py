import io
import os

from fpdf import FPDF
from data import preparar_dados_analise
from analysis import (
    calcular_estatisticas,
    classificar_umidade_valor,
    classificar_espessura_valor,
    classificar_penetro,
    classificar_umidade,
    classificar_espessura
)

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")


_TEMP_FILES = []

def _fig_para_bytes(fig, dpi=150):
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    fig.savefig(path, format="png", bbox_inches="tight", dpi=dpi)
    _TEMP_FILES.append(path)
    return path


def _adicionar_logo(pdf, largura=52):
    if not os.path.exists(LOGO_PATH):
        pdf.set_y(15)
        return
    logo_h = largura * (294 / 933)
    pdf.image(LOGO_PATH, x=10, y=10, w=largura)
    pdf.set_y(10 + logo_h + 4)


def _texto_latin(texto):
    return str(texto).encode("latin-1", "replace").decode("latin-1")


def criar_tabela_pnania(pdf, cabecalhos, dados, titulo):
    # Título da Tabela
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(15, 58, 97)  # Azul marinho corporativo
    pdf.cell(0, 8, _texto_latin(titulo), ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Calcula larguras das colunas
    if len(cabecalhos) == 4:
        larguras = [65, 42, 42, 41]
    elif len(cabecalhos) == 3:
        larguras = [75, 55, 60]
    else:
        larguras = [190 / len(cabecalhos)] * len(cabecalhos)
        
    # Cabeçalho da Tabela
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(15, 58, 97)  # Azul marinho corporativo
    pdf.set_text_color(255, 255, 255)  # Branco
    for col_idx, cab in enumerate(cabecalhos):
        align = "L" if col_idx == 0 else "C"
        pdf.cell(larguras[col_idx], 7, _texto_latin(cab), border=1, fill=True, align=align)
    pdf.ln()
    
    # Dados da Tabela
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    
    for idx_linha, linha in enumerate(dados):
        bg_alternado = (idx_linha % 2 == 1)
        if bg_alternado:
            pdf.set_fill_color(248, 250, 252)  # #f8fafc (Cinza claro alternado)
        else:
            pdf.set_fill_color(255, 255, 255)
            
        for col_idx, val in enumerate(linha):
            align = "L" if col_idx == 0 else "C"
            # Se for a última coluna (STATUS ou CLASSIFICAÇÃO), aplica cor de fundo condicional
            if col_idx == len(cabecalhos) - 1:
                val_upper = str(val).upper().strip()
                if "IDEAL" in val_upper or "EXCELENTE" in val_upper:
                    pdf.set_fill_color(27, 94, 32)  # Verde escuro #1b5e20
                    pdf.set_text_color(255, 255, 255)
                elif "BOA" in val_upper:
                    pdf.set_fill_color(165, 214, 167)  # Verde claro #a5d6a7
                    pdf.set_text_color(27, 94, 32)
                elif "SATISFATÓRIA" in val_upper or "SATISFATORIA" in val_upper or "ALERTA" in val_upper:
                    pdf.set_fill_color(255, 224, 130)  # Amarelo/laranja claro #ffe082
                    pdf.set_text_color(127, 95, 0)
                elif "CRÍTICO" in val_upper or "CRITICO" in val_upper or "CRÍTICA" in val_upper or "CRITICA" in val_upper:
                    pdf.set_fill_color(239, 154, 154)  # Vermelho claro #ef9a9a
                    pdf.set_text_color(183, 28, 28)
                else:
                    pdf.set_fill_color(245, 247, 250)
                    pdf.set_text_color(50, 50, 50)
                
                pdf.cell(larguras[col_idx], 7, _texto_latin(val), border=1, fill=True, align=align)
                pdf.set_text_color(50, 50, 50)
            else:
                pdf.cell(larguras[col_idx], 7, _texto_latin(val), border=1, fill=bg_alternado, align=align)
        pdf.ln()
    pdf.ln(3)


def _desenhar_tabelas_e_legenda(pdf, stats, meta):
    # Seção 1: Conformidade Biomecânica
    f_amort = stats["fases"][0]
    f_trans = stats["fases"][1]
    f_sup = stats["fases"][2]
    
    dados_biomecanica = [
        ["Amortecimento (1ª Queda)", f"{f_amort['media']:.1f} cm", "3.0 - 5.0 cm", f_amort["status"]],
        ["Transição (2ª Queda)", f"{f_trans['media']:.1f} cm", "5.0 - 7.0 cm", f_trans["status"]],
        ["Suporte (3ª Queda)", f"{f_sup['media']:.1f} cm", "7.0 - 9.0 cm", f_sup["status"]],
    ]
    criar_tabela_pnania(
        pdf,
        cabecalhos=["PARÂMETRO", "RESULTADO", "ALVO", "STATUS"],
        dados=dados_biomecanica,
        titulo="Seção 1: Conformidade Biomecânica"
    )
    
    # Seção 2: Parâmetros de Manejo
    dados_manejo = []
    if meta.get("coletou_umidade") or stats.get("umidade_media_geral", 0.0) > 0.0:
        rotulo_umi, _ = classificar_umidade_valor(stats["umidade_media_geral"], meta.get("ideal_umi", ""))
        ideal_umi_val = meta.get("ideal_umi") if meta.get("ideal_umi") else "18.0%"
        dados_manejo.append(["Umidade - TDR 250", f"{stats['umidade_media_geral']:.1f}%", ideal_umi_val, rotulo_umi])
    
    if meta.get("coletou_espessura") or stats.get("espessura_media_geral", 0) > 0:
        rotulo_esp, _ = classificar_espessura_valor(stats["espessura_media_geral"], meta.get("ideal_esp", ""))
        ideal_esp_val = meta.get("ideal_esp") if meta.get("ideal_esp") else "12 cm"
        dados_manejo.append(["Espessura da Camada", f"{stats['espessura_media_geral']} cm", ideal_esp_val, rotulo_esp])
        
    if dados_manejo:
        criar_tabela_pnania(
            pdf,
            cabecalhos=["PARÂMETRO", "VALOR MÉDIO", "ALVO", "STATUS"],
            dados=dados_manejo,
            titulo="Seção 2: Parâmetros de Manejo"
        )
        
    # Seção 3: Consistência (Uniformidade)
    label_icg, _ = classificar_penetro(stats["icg"])
    label_pen, _ = classificar_penetro(stats["io_geral"])
    
    dados_consistencia = [
        ["Consistência Geral (IUG)", f"{stats['icg']:.1f}%", label_icg],
        ["Penetrômetro", f"{stats['io_geral']:.1f}%", label_pen],
    ]
    
    if meta.get("coletou_umidade") or stats.get("umidade_media_geral", 0.0) > 0.0:
        label_umi, _ = classificar_umidade(stats["io_umidade"])
        dados_consistencia.append(["Umidade (CV%)", f"{stats['io_umidade']:.1f}%", label_umi])
        
    if meta.get("coletou_espessura") or stats.get("espessura_media_geral", 0) > 0:
        label_esp, _ = classificar_espessura(stats["io_espessura"])
        dados_consistencia.append(["Espessura (CV%)", f"{stats['io_espessura']:.1f}%", label_esp])
        
    criar_tabela_pnania(
        pdf,
        cabecalhos=["PARÂMETRO", "RESULTADO (CV%)", "CLASSIFICAÇÃO"],
        dados=dados_consistencia,
        titulo="Seção 3: Consistência (Uniformidade)"
    )
    
    # Legenda CV%
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 4, _texto_latin("Legenda de Classificação de Consistência (CV%):"), ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(45, 4, _texto_latin("  - EXCELENTE: CV < 5%"), ln=False)
    pdf.cell(45, 4, _texto_latin("  - BOA: 5% <= CV < 10%"), ln=False)
    pdf.cell(45, 4, _texto_latin("  - SATISFATÓRIA: 10% <= CV < 15%"), ln=False)
    pdf.cell(45, 4, _texto_latin("  - CRÍTICA: CV >= 15%"), ln=True)
    pdf.ln(4)


def gerar_pdf(meta, fig_penetro=None, fig_espessura=None, fig_umidade=None, apenas_tabelas=False):
    # Tenta carregar dados de coleta para calcular estatísticas
    df_coleta = None
    try:
        import streamlit as st
        if "df_coleta" in st.session_state:
            df_coleta = st.session_state.df_coleta
    except Exception:
        pass

    if df_coleta is None:
        try:
            caminho_last = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_data.csv")
            if os.path.exists(caminho_last):
                from data import carregar_csv
                _, df_coleta = carregar_csv(caminho_last)
        except Exception:
            pass

    stats = None
    if df_coleta is not None:
        try:
            df_analise = preparar_dados_analise(df_coleta, meta)
            stats = calcular_estatisticas(df_analise, meta)
        except Exception:
            pass

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- Página 1: Dados da propriedade ---
    pdf.add_page()
    _adicionar_logo(pdf)

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 58, 97)
    
    titulo_principal = "RELATÓRIO DE DIAGNÓSTICO" if apenas_tabelas else "RELATÓRIO DE DESEMPENHO"
    pdf.cell(0, 12, _texto_latin(titulo_principal), ln=True, align="C")
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_y(pdf.get_y() + 4)

    pdf.set_text_color(50, 50, 50)
    pdf.set_fill_color(245, 247, 250)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5, _texto_latin("  DADOS DA PROPRIEDADE E DA COLETA"), ln=True, fill=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 5, _texto_latin(" Fazenda / Haras: "), border="LT")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, _texto_latin(meta["fazenda"]), border="RT", ln=True)

    pdf.cell(40, 5, _texto_latin(" Pista / Picadeiro: "), border="L")
    pdf.cell(0, 5, _texto_latin(f"{meta['pista']} ({meta['dimensao']})"), border="R", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 5, _texto_latin(" Data da Coleta: "), border="LB")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, _texto_latin(meta["data"]), border="RB", ln=True)
    pdf.ln(4)

    if apenas_tabelas:
        # Modo Apenas Tabelas: Desenha as tabelas diretamente na Página 1
        if stats is not None:
            _desenhar_tabelas_e_legenda(pdf, stats, meta)
            
            # Desenha as notas logo em seguida na mesma página (ou quebrando se necessário)
            if meta.get("notas_gerais") or meta.get("notas_manejo") or meta.get("notas_parecer"):
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(15, 58, 97)
                pdf.cell(0, 6, _texto_latin("Parecer Técnico e Notas"), ln=True)
                pdf.ln(1)
                pdf.set_text_color(50, 50, 50)
                
                if meta.get("notas_gerais"):
                    pdf.set_font("Helvetica", "B", 9)
                    pdf.cell(0, 5, _texto_latin("Observações Gerais:"), ln=True)
                    pdf.set_font("Helvetica", "", 8.5)
                    pdf.multi_cell(0, 4.5, _texto_latin(meta["notas_gerais"]))
                    pdf.ln(3)

                if meta.get("notas_manejo"):
                    pdf.set_font("Helvetica", "B", 9)
                    pdf.cell(0, 5, _texto_latin("Manejo Recomendado:"), ln=True)
                    pdf.set_font("Helvetica", "", 8.5)
                    pdf.multi_cell(0, 4.5, _texto_latin(meta["notas_manejo"]))
                    pdf.ln(3)

                if meta.get("notas_parecer"):
                    pdf.set_font("Helvetica", "B", 9)
                    pdf.cell(0, 5, _texto_latin("Parecer Técnico:"), ln=True)
                    pdf.set_font("Helvetica", "", 8.5)
                    pdf.multi_cell(0, 4.5, _texto_latin(meta["notas_parecer"]))
                    pdf.ln(3)
    else:
        # Modo Completo com Gráficos
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 5, _texto_latin("1. Perfil de Compactação (Índice de Penetrômetro)"), ln=True)
        pdf.ln(1)
        pdf.image(_fig_para_bytes(fig_penetro), x=22, w=165)

        # Página 2: Tabelas de Indicadores
        if stats is not None:
            pdf.add_page()
            _adicionar_logo(pdf, largura=45)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.set_y(pdf.get_y() + 4)
            
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(15, 58, 97)
            pdf.cell(0, 6, _texto_latin("2. Indicadores de Desempenho e Diagnóstico"), ln=True)
            pdf.ln(3)
            pdf.set_text_color(0, 0, 0)
            
            _desenhar_tabelas_e_legenda(pdf, stats, meta)

        # Página 3: Distribuição Espacial e Mapas de Calor
        if fig_espessura is not None or fig_umidade is not None:
            pdf.add_page()
            _adicionar_logo(pdf, largura=45)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.set_text_color(50, 50, 50)
            pdf.set_y(pdf.get_y() + 4)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, _texto_latin("3. Distribuição Espacial e Mapas de Calor"), ln=True)
            pdf.ln(4)
            if fig_espessura is not None:
                pdf.image(_fig_para_bytes(fig_espessura), x=35, w=140)
                pdf.ln(10)
            if fig_umidade is not None:
                pdf.image(_fig_para_bytes(fig_umidade), x=35, w=140)

        # Página 4: Notas e Parecer Técnico
        if meta.get("notas_gerais") or meta.get("notas_manejo") or meta.get("notas_parecer"):
            pdf.add_page()
            _adicionar_logo(pdf, largura=45)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.set_y(pdf.get_y() + 4)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(15, 58, 97)
            pdf.cell(0, 6, _texto_latin("4. Notas e Parecer Técnico"), ln=True)
            pdf.ln(4)

            pdf.set_text_color(50, 50, 50)

            if meta.get("notas_gerais"):
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 5, _texto_latin("Observações Gerais:"), ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 4.5, _texto_latin(meta["notas_gerais"]))
                pdf.ln(4)

            if meta.get("notas_manejo"):
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 5, _texto_latin("Manejo:"), ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 4.5, _texto_latin(meta["notas_manejo"]))
                pdf.ln(4)

            if meta.get("notas_parecer"):
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 5, _texto_latin("Parecer Técnico:"), ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 4.5, _texto_latin(meta["notas_parecer"]))
                pdf.ln(4)

    pdf_output = pdf.output(dest='S')
    
    # Cleanup all temp files
    global _TEMP_FILES
    for path in _TEMP_FILES:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
    _TEMP_FILES.clear()
    
    return bytes(pdf_output) if isinstance(pdf_output, (bytes, bytearray)) else pdf_output.encode("latin-1", errors="ignore")
