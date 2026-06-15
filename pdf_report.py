import io
import os

from fpdf import FPDF
from analysis import (
    calcular_estatisticas,
    classificar_umidade_valor,
    classificar_espessura_valor,
    classificar_penetro,
    classificar_umidade,
    classificar_espessura,
    classificar_perfil
)

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")


def _fig_para_bytes(fig, dpi=150):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=dpi)
    buffer.seek(0)
    return buffer


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
                elif "CRÍTICO" in val_upper or "CRITICO" in val_upper or "CRÍTICA" in val_upper or "CRITICA" in val_upper or "AJUSTES" in val_upper:
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


def _desenhar_card_pdf(pdf, x, y, w, h, titulo, valor_atual, classificacao, cor_hex, ideal_txt=None, destaque=False, subtitulo=None):
    # Converte cor_hex (#RRGGBB) para RGB
    hex_val = cor_hex.lstrip("#")
    r, g, b = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
    
    # Cores de fundo e bordas correspondentes
    if cor_hex == "#2e7d32":  # Verde
        bg_r, bg_g, bg_b = 240, 253, 244  # #f0fdf4
        border_r, border_g, border_b = 187, 247, 208  # #bbf7d0
    elif cor_hex == "#f57c00":  # Amarelo/Laranja
        bg_r, bg_g, bg_b = 255, 251, 235  # #fffbeb
        border_r, border_g, border_b = 253, 230, 138  # #fde68a
    elif cor_hex == "#c62828":  # Vermelho
        bg_r, bg_g, bg_b = 254, 242, 242  # #fef2f2
        border_r, border_g, border_b = 254, 202, 202  # #fecaca
    else:
        bg_r, bg_g, bg_b = 248, 250, 252  # #f8fafc
        border_r, border_g, border_b = 226, 232, 240  # #e2e8f0

    # Salva e configura parâmetros de desenho
    pdf.set_fill_color(bg_r, bg_g, bg_b)
    if destaque:
        pdf.set_draw_color(r, g, b)
        pdf.set_line_width(0.4)
    else:
        pdf.set_draw_color(border_r, border_g, border_b)
        pdf.set_line_width(0.25)
        
    # Desenha o retângulo do card
    pdf.rect(x, y, w, h, style="DF")
    
    # Faixa lateral se não for destaque
    if not destaque:
        pdf.set_fill_color(r, g, b)
        pdf.rect(x, y, 2.0, h, style="F")
        
    # Título (Cinza/Muted)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(100, 116, 139)  # #64748b
    pdf.set_xy(x + (4 if not destaque else 3), y + 2.5)
    pdf.cell(w - 6, 4, _texto_latin(titulo.upper()), border=0, ln=False)
    
    if subtitulo:
        # Subtítulo (Aplicação Técnica / Descrição)
        pdf.set_font("Helvetica", "", 5.2)
        pdf.set_text_color(120, 130, 140)
        pdf.set_xy(x + (4 if not destaque else 3), y + 5.8)
        pdf.cell(w - 6, 3.5, _texto_latin(subtitulo), border=0, ln=False)
        
        # Valor Principal (Grande e Escuro) - Reduzido e deslocado
        pdf.set_font("Helvetica", "B", 13.5)
        pdf.set_text_color(30, 41, 59)  # #1e293b
        pdf.set_xy(x + (4 if not destaque else 3), y + 8.8)
        pdf.cell(w - 6, 7, _texto_latin(valor_atual), border=0, ln=False)
    else:
        # Valor Principal (Grande e Escuro)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(30, 41, 59)  # #1e293b
        pdf.set_xy(x + (4 if not destaque else 3), y + 6.5)
        pdf.cell(w - 6, 8, _texto_latin(valor_atual), border=0, ln=False)
    
    # Classificação (Pill Badge)
    pdf.set_font("Helvetica", "B", 6.5)
    texto_badge = _texto_latin(classificacao.upper())
    largura_texto = pdf.get_string_width(texto_badge)
    badge_w = largura_texto + 4.0  # Adiciona 4mm de padding (2mm de cada lado)
    badge_h = 4.5
    badge_x = x + (4 if not destaque else 3)
    badge_y = y + h - 7
    
    pdf.set_fill_color(r, g, b)
    pdf.rect(badge_x, badge_y, badge_w, badge_h, style="F")
    
    # Texto da Classificação dentro do Badge
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(badge_x, badge_y)
    pdf.cell(badge_w, badge_h, texto_badge, border=0, ln=False, align="C")
    
    # Alvo/Ideal
    if ideal_txt:
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100, 116, 139)
        pdf.set_xy(x + w - 30, y + h - 7)
        pdf.cell(27, 4.5, _texto_latin(ideal_txt), border=0, ln=False, align="R")


def _desenhar_box_secao(pdf, y_start, y_end):
    pdf.set_draw_color(226, 232, 240)  # #e2e8f0 (Cinza claro, idêntico à borda da tela)
    pdf.set_line_width(0.3)
    pdf.rect(8, y_start, 194, y_end - y_start, style="D")


def _desenhar_tabelas_e_legenda(pdf, stats, meta):
    # Seção 1: Penetrômetro Longchamp
    f_amort = stats["fases"][0]
    f_trans = stats["fases"][1]
    f_sup = stats["fases"][2]
    media_fases = sum(stats["medicao_atual"]) / 3
    rotulo_perfil, cor_perfil, desc_perfil = classificar_perfil(media_fases, meta.get("tipo_pista", "Pista de Treinamento"))

    # Título Principal da Seção
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 8, _texto_latin("Análise Integrada da Pista"), ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(0, 6, _texto_latin("Penetrômetro Longchamp"), ln=True)
    pdf.ln(1)
    
    y_row1_top = pdf.get_y()
    # Desenha o card central (Penetrômetro)
    _desenhar_card_pdf(
        pdf, 
        x=75, 
        y=y_row1_top, 
        w=60, 
        h=24, 
        titulo="Penetrômetro", 
        valor_atual=f"{media_fases:.1f} cm", 
        classificacao=rotulo_perfil, 
        cor_hex=cor_perfil, 
        destaque=True,
        subtitulo=desc_perfil
    )
    
    y_row1_drops = y_row1_top + 24 + 3
    # Desenha as 3 quedas
    _desenhar_card_pdf(
        pdf, 
        x=10, 
        y=y_row1_drops, 
        w=60, 
        h=24, 
        titulo="Impacto (1ª Queda)", 
        valor_atual=f"{f_amort['media']:.1f} cm", 
        classificacao=f_amort["status"], 
        cor_hex=f_amort["cor"], 
        ideal_txt=f_amort["ideal"]
    )
    _desenhar_card_pdf(
        pdf, 
        x=75, 
        y=y_row1_drops, 
        w=60, 
        h=24, 
        titulo="Suporte (2ª Queda)", 
        valor_atual=f"{f_trans['media']:.1f} cm", 
        classificacao=f_trans["status"], 
        cor_hex=f_trans["cor"], 
        ideal_txt=f_trans["ideal"]
    )
    _desenhar_card_pdf(
        pdf, 
        x=140, 
        y=y_row1_drops, 
        w=60, 
        h=24, 
        titulo="Tração (3ª Queda)", 
        valor_atual=f"{f_sup['media']:.1f} cm", 
        classificacao=f_sup["status"], 
        cor_hex=f_sup["cor"], 
        ideal_txt=f_sup["ideal"]
    )
    
    # Desenha contorno (border container) da Seção 1
    _desenhar_box_secao(pdf, y_row1_top - 7, y_row1_drops + 24 + 2.5)
    
    # Seção 2: Parâmetros de Manejo
    show_umi = stats['umidade_media_geral'] > 0.0
    show_esp = stats['espessura_media_geral'] > 0
    
    y_next = y_row1_drops + 24 + 8
    if show_umi or show_esp:
        pdf.set_y(y_next)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 6, _texto_latin("Parâmetros de Apoio"), ln=True)
        pdf.ln(1)
        
        y_row2_top = pdf.get_y()
        if show_umi and show_esp:
            rotulo_umi, cor_umi = classificar_umidade_valor(stats['umidade_media_geral'], meta.get("ideal_umi", ""))
            ideal_umi_val = meta.get("ideal_umi") if meta.get("ideal_umi") else "18.0%"
            _desenhar_card_pdf(
                pdf, 
                x=40, 
                y=y_row2_top, 
                w=60, 
                h=24, 
                titulo="Umidade - TDR 250", 
                valor_atual=f"{stats['umidade_media_geral']:.1f}%", 
                classificacao=rotulo_umi, 
                cor_hex=cor_umi, 
                ideal_txt=f"Alvo: {ideal_umi_val}"
            )
            
            rotulo_esp, cor_esp = classificar_espessura_valor(stats['espessura_media_geral'], meta.get("ideal_esp", ""))
            ideal_esp_val = meta.get("ideal_esp") if meta.get("ideal_esp") else "12 cm"
            _desenhar_card_pdf(
                pdf, 
                x=110, 
                y=y_row2_top, 
                w=60, 
                h=24, 
                titulo="Espessura", 
                valor_atual=f"{stats['espessura_media_geral']} cm", 
                classificacao=rotulo_esp, 
                cor_hex=cor_esp, 
                ideal_txt=f"Alvo: {ideal_esp_val}"
            )
        else:
            if show_umi:
                rotulo_umi, cor_umi = classificar_umidade_valor(stats['umidade_media_geral'], meta.get("ideal_umi", ""))
                ideal_umi_val = meta.get("ideal_umi") if meta.get("ideal_umi") else "18.0%"
                _desenhar_card_pdf(
                    pdf, 
                    x=75, 
                    y=y_row2_top, 
                    w=60, 
                    h=24, 
                    titulo="Umidade - TDR 250", 
                    valor_atual=f"{stats['umidade_media_geral']:.1f}%", 
                    classificacao=rotulo_umi, 
                    cor_hex=cor_umi, 
                    ideal_txt=f"Alvo: {ideal_umi_val}"
                )
            else:
                rotulo_esp, cor_esp = classificar_espessura_valor(stats['espessura_media_geral'], meta.get("ideal_esp", ""))
                ideal_esp_val = meta.get("ideal_esp") if meta.get("ideal_esp") else "12 cm"
                _desenhar_card_pdf(
                    pdf, 
                    x=75, 
                    y=y_row2_top, 
                    w=60, 
                    h=24, 
                    titulo="Espessura", 
                    valor_atual=f"{stats['espessura_media_geral']} cm", 
                    classificacao=rotulo_esp, 
                    cor_hex=cor_esp, 
                    ideal_txt=f"Alvo: {ideal_esp_val}"
                )
        
        # Desenha contorno (border container) da Seção 2
        _desenhar_box_secao(pdf, y_row2_top - 7, y_row2_top + 24 + 2.5)
        y_next = y_row2_top + 24 + 8

    # Seção 3: Consistência
    pdf.set_y(y_next)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("Consistência"), ln=True)
    pdf.ln(1)
    
    y_row3_top = pdf.get_y()
    label_icg, color_icg = classificar_penetro(stats["icg"])
    _desenhar_card_pdf(
        pdf, 
        x=75, 
        y=y_row3_top, 
        w=60, 
        h=24, 
        titulo="Consistência Geral", 
        valor_atual=f"{stats['icg']:.1f}%", 
        classificacao=label_icg, 
        cor_hex=color_icg, 
        destaque=True
    )
    
    y_row3_cv = y_row3_top + 24 + 3
    cvs = []
    label_pen, color_pen = classificar_penetro(stats["io_geral"])
    cvs.append({"titulo": "CV Penetrômetro", "valor": f"{stats['io_geral']:.1f}%", "classif": label_pen, "cor": color_pen})
    
    if show_umi:
        label_umi_cv, color_umi_cv = classificar_umidade(stats["io_umidade"])
        cvs.append({"titulo": "CV Umidade", "valor": f"{stats['io_umidade']:.1f}%", "classif": label_umi_cv, "cor": color_umi_cv})
        
    if show_esp:
        label_esp_cv, color_esp_cv = classificar_espessura(stats["io_espessura"])
        cvs.append({"titulo": "CV Espessura", "valor": f"{stats['io_espessura']:.1f}%", "classif": label_esp_cv, "cor": color_esp_cv})
        
    if len(cvs) == 3:
        _desenhar_card_pdf(pdf, x=10, y=y_row3_cv, w=60, h=24, titulo=cvs[0]["titulo"], valor_atual=cvs[0]["valor"], classificacao=cvs[0]["classif"], cor_hex=cvs[0]["cor"])
        _desenhar_card_pdf(pdf, x=75, y=y_row3_cv, w=60, h=24, titulo=cvs[1]["titulo"], valor_atual=cvs[1]["valor"], classificacao=cvs[1]["classif"], cor_hex=cvs[1]["cor"])
        _desenhar_card_pdf(pdf, x=140, y=y_row3_cv, w=60, h=24, titulo=cvs[2]["titulo"], valor_atual=cvs[2]["valor"], classificacao=cvs[2]["classif"], cor_hex=cvs[2]["cor"])
    elif len(cvs) == 2:
        _desenhar_card_pdf(pdf, x=40, y=y_row3_cv, w=60, h=24, titulo=cvs[0]["titulo"], valor_atual=cvs[0]["valor"], classificacao=cvs[0]["classif"], cor_hex=cvs[0]["cor"])
        _desenhar_card_pdf(pdf, x=110, y=y_row3_cv, w=60, h=24, titulo=cvs[1]["titulo"], valor_atual=cvs[1]["valor"], classificacao=cvs[1]["classif"], cor_hex=cvs[1]["cor"])
    else:
        _desenhar_card_pdf(pdf, x=75, y=y_row3_cv, w=60, h=24, titulo=cvs[0]["titulo"], valor_atual=cvs[0]["valor"], classificacao=cvs[0]["classif"], cor_hex=cvs[0]["cor"])
        
    # Desenha contorno (border container) da Seção 3
    _desenhar_box_secao(pdf, y_row3_top - 7, y_row3_cv + 24 + 2.5)
    
    y_next = y_row3_cv + 24 + 6
    pdf.set_y(y_next)
    
    # Nota de rodapé explicativa logo abaixo da tabela/seção de Consistência Geral
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(100, 116, 139)  # #64748b (Cinza muted)
    nota_texto = (
        "Nota: O Coeficiente de Variação (CV%) mede a uniformidade da pista (quanto menor, "
        "mais consistente o terreno). A Consistência Geral é o indicador de comportamento da pista, "
        "unindo dados biomecânicos e de manejo para sinalizar a integridade da superfície."
    )
    pdf.multi_cell(0, 4.5, _texto_latin(nota_texto), border=0, align="L")
    pdf.ln(2)


def is_streamlit_cloud():
    return os.path.exists("/mount/src") or "STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION" in os.environ


def gerar_pdf(meta, fig_penetro=None, fig_espessura=None, fig_umidade=None, apenas_tabelas=False, stats=None):
    # Tenta carregar dados de coleta para calcular estatísticas caso stats seja None
    if stats is None:
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

        if df_coleta is not None:
            try:
                df_analise = preparar_dados_analise(df_coleta, meta)
                stats = calcular_estatisticas(df_analise, meta)
            except Exception:
                pass

    media_fases = 0.0
    rotulo_perfil = "N/A"
    if stats is not None:
        media_fases = sum(stats["medicao_atual"]) / 3
        rotulo_perfil, _, _ = classificar_perfil(media_fases, meta.get("tipo_pista", "Pista de Treinamento"))

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- Página 1: Dados da propriedade + Cards de Diagnóstico ---
    pdf.add_page()
    _adicionar_logo(pdf)

    # Cabeçalho do Laudo no formato estrito: [Nome da Pista] | [Data] | [PR X - NOME TÉCNICO] | [ÓTIMO ou BOM]
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 58, 97)
    header_laudo = f"{meta['pista']} | {meta['data']} | {rotulo_perfil}"
    pdf.cell(0, 8, _texto_latin(header_laudo), ln=True, align="C")
    pdf.ln(1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_y(pdf.get_y() + 4)

    pdf.set_text_color(50, 50, 50)
    pdf.set_fill_color(245, 247, 250)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5, _texto_latin("  DADOS DA PROPRIEDADE"), ln=True, fill=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 5, _texto_latin(" Fazenda / Haras: "), border="LT")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, _texto_latin(meta["fazenda"]), border="RT", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 5, _texto_latin(" Pista / Picadeiro: "), border="L")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, _texto_latin(f"{meta['pista']} ({meta['dimensao']})"), border="R", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 5, _texto_latin(" Tipo de Pista: "), border="L")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, _texto_latin(meta.get("tipo_pista", "Pista de Treinamento")), border="R", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 5, _texto_latin(" Data da Coleta: "), border="LB")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, _texto_latin(meta["data"]), border="RB", ln=True)
    pdf.ln(4)

    # Desenha os cards de diagnóstico na Página 1
    if stats is not None:
        _desenhar_tabelas_e_legenda(pdf, stats, meta)

    if apenas_tabelas:
        # Se for apenas tabelas, desenha o Parecer Técnico na Página 1 logo após os cards
        if meta.get("notas_gerais") or meta.get("notas_manejo") or meta.get("notas_parecer"):
            pdf.set_y(pdf.get_y() + 5)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(15, 58, 97)
            pdf.cell(0, 6, _texto_latin("Parecer Técnico e Notas"), ln=True)
            pdf.ln(1)
            pdf.set_text_color(50, 50, 50)
            
            if meta.get("notas_gerais"):
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 5, _texto_latin("Observações Gerais:"), ln=True)
                pdf.set_font("Helvetica", "", 9.5)
                pdf.multi_cell(0, 4.5, _texto_latin(meta["notas_gerais"]))
                pdf.ln(2.5)

            if meta.get("notas_manejo"):
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 5, _texto_latin("Manejo Recomendado:"), ln=True)
                pdf.set_font("Helvetica", "", 9.5)
                pdf.multi_cell(0, 4.5, _texto_latin(meta["notas_manejo"]))
                pdf.ln(2.5)

            if meta.get("notas_parecer"):
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 5, _texto_latin("Parecer Técnico:"), ln=True)
                pdf.set_font("Helvetica", "", 9.5)
                pdf.multi_cell(0, 4.5, _texto_latin(meta["notas_parecer"]))
                pdf.ln(2.5)


    else:
        # Modo Completo: Página 2 contém Parecer Técnico (letra maior) e Gráficos de Análise
        pdf.add_page()
        _adicionar_logo(pdf, largura=45)
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 58, 97)
        header_laudo = f"{meta['pista']} | {meta['data']} | {rotulo_perfil}"
        pdf.cell(0, 8, _texto_latin(header_laudo), ln=True, align="C")
        pdf.ln(1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.set_y(pdf.get_y() + 4)

        # 1. Parecer Técnico e Notas (Tamanho de letra ampliado)
        if meta.get("notas_gerais") or meta.get("notas_manejo") or meta.get("notas_parecer"):
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(15, 58, 97)
            pdf.cell(0, 6, _texto_latin("Parecer Técnico e Notas"), ln=True)
            pdf.ln(1.5)
            pdf.set_text_color(50, 50, 50)
            
            if meta.get("notas_gerais"):
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 5, _texto_latin("Observações Gerais:"), ln=True)
                pdf.set_font("Helvetica", "", 10.5)
                pdf.multi_cell(0, 4.8, _texto_latin(meta["notas_gerais"]))
                pdf.ln(3)

            if meta.get("notas_manejo"):
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 5, _texto_latin("Manejo Recomendado:"), ln=True)
                pdf.set_font("Helvetica", "", 10.5)
                pdf.multi_cell(0, 4.8, _texto_latin(meta["notas_manejo"]))
                pdf.ln(3)

            if meta.get("notas_parecer"):
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 5, _texto_latin("Parecer Técnico:"), ln=True)
                pdf.set_font("Helvetica", "", 10.5)
                pdf.multi_cell(0, 4.8, _texto_latin(meta["notas_parecer"]))
                pdf.ln(3)
            pdf.ln(2)



        # 2. Gráficos de Análise
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 6, _texto_latin("Gráficos de Análise"), ln=True)
        pdf.ln(3)

        # Gráfico do Penetrômetro
        if fig_penetro is not None:
            pdf.image(_fig_para_bytes(fig_penetro), x=45, w=120)
            pdf.ln(4)

        # Mapas de Calor (Espessura e Umidade)
        if fig_espessura is not None or fig_umidade is not None:
            y_before_images = pdf.get_y()
            if fig_espessura is not None and fig_umidade is not None:
                # Plota lado a lado para economizar espaço vertical e manter a página limpa
                pdf.image(_fig_para_bytes(fig_espessura), x=15, y=y_before_images, w=85)
                pdf.image(_fig_para_bytes(fig_umidade), x=110, y=y_before_images, w=85)
                
                # Legenda de CV da Espessura
                label_esp_cv, _ = classificar_espessura(stats["io_espessura"])
                pdf.set_xy(15, y_before_images + 52.5)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(85, 4, _texto_latin(f"Coeficiente de Variação: {stats['io_espessura']:.1f}% ({label_esp_cv})"), border=0, align="C")
                
                # Legenda de CV da Umidade
                label_umi_cv, _ = classificar_umidade(stats["io_umidade"])
                pdf.set_xy(110, y_before_images + 52.5)
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(85, 4, _texto_latin(f"Coeficiente de Variação: {stats['io_umidade']:.1f}% ({label_umi_cv})"), border=0, align="C")
                
                pdf.set_y(y_before_images + 58)
            else:
                fig_active = fig_espessura if fig_espessura is not None else fig_umidade
                pdf.image(_fig_para_bytes(fig_active), x=50, y=y_before_images, w=110)
                
                # Legenda de CV único
                pdf.set_font("Helvetica", "B", 8.5)
                pdf.set_text_color(50, 50, 50)
                if fig_espessura is not None:
                    label_esp_cv, _ = classificar_espessura(stats["io_espessura"])
                    txt_cv = f"Coeficiente de Variação: {stats['io_espessura']:.1f}% ({label_esp_cv})"
                else:
                    label_umi_cv, _ = classificar_umidade(stats["io_umidade"])
                    txt_cv = f"Coeficiente de Variação: {stats['io_umidade']:.1f}% ({label_umi_cv})"
                
                pdf.set_xy(50, y_before_images + 67.5)
                pdf.cell(110, 4, _texto_latin(txt_cv), border=0, align="C")
                pdf.set_y(y_before_images + 73)

        # --- Página 3: Referência Técnica / Classificação da Pista ---
        pdf.add_page()
        _adicionar_logo(pdf, largura=45)
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 58, 97)
        header_laudo = f"{meta['pista']} | {meta['data']} | {rotulo_perfil}"
        pdf.cell(0, 8, _texto_latin(header_laudo), ln=True, align="C")
        pdf.ln(1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.set_y(pdf.get_y() + 4)

        # Título da Seção
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 6, _texto_latin("Classificação da Pista"), ln=True)
        pdf.ln(1.5)

        # Descrição
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(50, 50, 50)
        desc_txt = "A resistência da pista, medida pelo penetrômetro, é categorizada conforme a profundidade de penetração, indicando o comportamento da superfície para diferentes níveis de exigência:"
        pdf.multi_cell(0, 4.5, _texto_latin(desc_txt))
        pdf.ln(3)

        # Cabeçalhos da Tabela
        pdf.set_fill_color(240, 244, 248)
        pdf.set_draw_color(200, 210, 220)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(50, 6, _texto_latin("Faixa (cm)"), border=1, fill=True, align="C")
        pdf.cell(100, 6, _texto_latin("Classificação"), border=1, fill=True, align="C", ln=True)

        # Linhas da tabela
        linhas = [
            ("Abaixo de 3,0", "PR 1 - MUITO DURA"),
            ("3,0 a 4,0", "PR 2 - DURA"),
            ("4,0 a 5,0", "PR 3 - FIRME 1"),
            ("5,0 a 6,5", "PR 4 - FIRME 2"),
            ("6,5 a 7,0", "PR 5 - MACIA 1"),
            ("7,0 a 8,0", "PR 6 - MACIA 2"),
            ("Acima de 8,0", "PR 7 - PESADA"),
        ]
        
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        bg_alt = False
        for faixa, classif in linhas:
            pdf.set_fill_color(248, 250, 252)
            fill = 1 if bg_alt else 0
            pdf.cell(50, 6, _texto_latin(faixa), border=1, fill=fill, align="C")
            pdf.cell(100, 6, _texto_latin(classif), border=1, fill=fill, align="C", ln=True)
            bg_alt = not bg_alt
        
        pdf.ln(5)

        # Como a pista trabalha
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 6, _texto_latin("Como a pista trabalha (Fases de Desempenho):"), ln=True)
        pdf.ln(1.5)

        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 4.5, _texto_latin("Para oferecer segurança e performance ao cavalo, a superfície deve responder corretamente em três etapas:"))
        pdf.ln(3.0)

        # Fases
        fases_desc = [
            ("Impacto", "A capacidade do solo de absorver o choque inicial do casco."),
            ("Suporte", "A firmeza necessária para sustentar o peso do cavalo sem afundar excessivamente."),
            ("Tração", "A aderência adequada para garantir segurança na propulsão e nos giros."),
        ]

        for fase, desc in fases_desc:
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.set_text_color(15, 58, 97)
            pdf.cell(20, 5, _texto_latin(f"{fase}:"), ln=False)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 5, _texto_latin(desc), ln=True)
            pdf.ln(1)

        pdf.ln(5)

        # Nota Técnica final
        pdf.set_font("Helvetica", "I", 8.5)
        pdf.set_text_color(100, 116, 139)
        nota_tecnica_txt = "Nota Técnica: A ciência é um guia, não um absoluto. Nossa análise integra dados de precisão, inspeção visual e contexto ambiental para o diagnóstico final."
        pdf.multi_cell(0, 4.2, _texto_latin(nota_tecnica_txt), border=0, align="L")

    pdf_output = pdf.output()
    return bytes(pdf_output) if isinstance(pdf_output, (bytes, bytearray)) else pdf_output.encode("latin-1", errors="ignore")
