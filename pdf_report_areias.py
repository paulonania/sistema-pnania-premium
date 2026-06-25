# Paulo Nania - Gerador de Relatórios PDF para o App de Areias
import io
import os
from fpdf import FPDF
from blend_engine import SIEVES, mapear_para_usda

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
_TEMP_FILES = []


def _fig_para_bytes(fig, dpi=150):
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    fig.savefig(path, format="png", bbox_inches="tight", dpi=dpi)
    _TEMP_FILES.append(path)
    return path


def _texto_latin(texto):
    return str(texto).encode("latin-1", "replace").decode("latin-1")


def _adicionar_logo(pdf, largura=45):
    if not os.path.exists(LOGO_PATH):
        pdf.set_y(15)
        return
    logo_h = largura * (294 / 933)
    pdf.image(LOGO_PATH, x=10, y=10, w=largura)
    pdf.set_y(10 + logo_h + 4)


def limpar_arquivos_temporarios():
    global _TEMP_FILES
    for path in _TEMP_FILES:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
    _TEMP_FILES.clear()


def _gerar_bytes_pdf(pdf):
    pdf_output = pdf.output(dest='S')
    limpar_arquivos_temporarios()
    return bytes(pdf_output) if isinstance(pdf_output, (bytes, bytearray)) else pdf_output.encode("latin-1", errors="ignore")


def gerar_pdf_detalhes_areia(sand_rec, comparar_faixa=None, faixa_dict=None, fig_linha=None, fig_barras=None):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Cabeçalho
    _adicionar_logo(pdf, largura=45)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 10, _texto_latin("RELATÓRIO DETALHADO DA AREIA"), ln=True, align="C")
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Identificação da Areia
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("  DADOS DE IDENTIFICAÇÃO"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Helvetica", "", 9.5)
    # Linha 1
    pdf.cell(40, 6, _texto_latin(" Areia / Amostra:"), border="LT")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(sand_rec["Areia"]), border="T")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Mineradora:"), border="T")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(sand_rec.get("Mineradora", "Não Informado")), border="RT", ln=True)
    
    # Linha 2
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Cliente:"), border="L")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(sand_rec.get("Cliente", "Não Informado")), border="")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Teor de Fibra:"), border="")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(f"{sand_rec.get('Fibra', 0.0):.2f}%"), border="R", ln=True)
    
    # Linha 3
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Formato do Grão:"), border="LB")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(sand_rec.get("Formato", "Não Informado")), border="B")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" AFS (Granulometria):"), border="B")
    pdf.set_font("Helvetica", "B", 9.5)
    afs_val = sand_rec.get("AFS", 0.0)
    pdf.cell(55, 6, _texto_latin(f"{afs_val:.1f}"), border="RB", ln=True)
    
    pdf.ln(5)
    
    # Seção Granulometria
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("  ANÁLISE GRANULOMÉTRICA"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    # Se houver comparação
    comparar = (comparar_faixa and faixa_dict and comparar_faixa in faixa_dict)
    
    # Headers da tabela
    if comparar:
        headers = ["PENEIRA", "LÍM. MÍN ALVO", "LÍM. MÁX ALVO", "RESULTADO AREIA", "STATUS"]
        cols_w = [45, 35, 35, 40, 35]
    else:
        headers = ["DESCRIÇÃO AMOSTRA (PENEIRA)", "PERCENTUAL RETIDO (%)"]
        cols_w = [110, 80]
        
    # Desenhar headers
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(15, 58, 97)
    pdf.set_text_color(255, 255, 255)
    for col_idx, h in enumerate(headers):
        align = "L" if col_idx == 0 else "C"
        pdf.cell(cols_w[col_idx], 6, _texto_latin(h), border=1, fill=True, align=align)
    pdf.ln()
    
    # Desenhar linhas das peneiras
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    
    SIEVE_NAMES_CLEAN = {
        "#10": "NO. 10 (2,00 mm)",
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
    
    for idx_s, s in enumerate(SIEVES):
        val = float(sand_rec.get(s, 0.0))
        bg_alt = (idx_s % 2 == 1)
        pdf.set_fill_color(248, 250, 252) if bg_alt else pdf.set_fill_color(255, 255, 255)
        
        desc = SIEVE_NAMES_CLEAN.get(s, s)
        
        if comparar:
            faixa = faixa_dict[comparar_faixa]
            t_min, t_max = faixa[s]
            status = "DENTRO"
            pdf.set_text_color(50, 50, 50)
            status_color = (0, 0, 0)
            bg_cell = (255, 255, 255)
            
            if val < t_min:
                status = "ABAIXO"
                bg_cell = (254, 242, 242)
                status_color = (198, 40, 40)
            elif val > t_max:
                status = "ACIMA"
                bg_cell = (254, 242, 242)
                status_color = (198, 40, 40)
            else:
                status = "DENTRO"
                bg_cell = (226, 240, 217)
                status_color = (46, 125, 50)
                
            pdf.cell(cols_w[0], 5.5, _texto_latin(desc), border=1, fill=True, align="L")
            pdf.cell(cols_w[1], 5.5, _texto_latin(f"{t_min:.1f}%"), border=1, fill=True, align="C")
            pdf.cell(cols_w[2], 5.5, _texto_latin(f"{t_max:.1f}%"), border=1, fill=True, align="C")
            pdf.cell(cols_w[3], 5.5, _texto_latin(f"{val:.2f}%"), border=1, fill=True, align="C")
            
            # Status com cor
            pdf.set_fill_color(*bg_cell)
            pdf.set_text_color(*status_color)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(cols_w[4], 5.5, _texto_latin(status), border=1, fill=True, align="C")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(50, 50, 50)
        else:
            pdf.cell(cols_w[0], 5.5, _texto_latin(desc), border=1, fill=True, align="L")
            pdf.cell(cols_w[1], 5.5, _texto_latin(f"{val:.2f}%"), border=1, fill=True, align="C")
        pdf.ln()
        
    # Adicionar FUNDO + NO. 270 e AFS como rodapé da tabela
    fundo_val = float(sand_rec.get("Finos", 0.0))
    no270_val = float(sand_rec.get("#270", 0.0))
    soma_fundo_270 = fundo_val + no270_val
    pdf.set_fill_color(240, 244, 248)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(15, 58, 97)
    
    if comparar:
        pdf.cell(155, 5.5, _texto_latin("FUNDO + NO. 270"), border=1, fill=True, align="L")
        pdf.cell(35, 5.5, _texto_latin(f"{soma_fundo_270:.2f}%"), border=1, fill=True, align="C", ln=True)
        
        pdf.cell(155, 5.5, _texto_latin("AFS (Tamanho Médio de Grão)"), border=1, fill=True, align="L")
        pdf.cell(35, 5.5, _texto_latin(f"{afs_val:.1f}"), border=1, fill=True, align="C", ln=True)
    else:
        pdf.cell(cols_w[0], 5.5, _texto_latin("FUNDO + NO. 270"), border=1, fill=True, align="L")
        pdf.cell(cols_w[1], 5.5, _texto_latin(f"{soma_fundo_270:.2f}%"), border=1, fill=True, align="C", ln=True)
        
        pdf.cell(cols_w[0], 5.5, _texto_latin("AFS"), border=1, fill=True, align="L")
        pdf.cell(cols_w[1], 5.5, _texto_latin(f"{afs_val:.1f}"), border=1, fill=True, align="C", ln=True)
        
    pdf.ln(4)
    
    # Tabela USDA
    usda = mapear_para_usda(sand_rec)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("Classificação USDA (Distribuição de Partículas)"), ln=True)
    pdf.ln(1)
    
    # Headers USDA
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(34, 10, _texto_latin("AMOSTRA"), border=1, fill=True, align="C")
    pdf.cell(36, 5, _texto_latin("CASCALHO"), border=1, fill=True, align="C")
    pdf.cell(102, 5, _texto_latin("AREIA"), border=1, fill=True, align="C")
    pdf.cell(18, 10, _texto_latin("FINOS"), border=1, fill=True, align="C", ln=True)
    
    # Sub-headers USDA
    pdf.set_y(pdf.get_y() - 5)
    pdf.set_x(10 + 34)
    pdf.cell(18, 5, _texto_latin("Grosso"), border=1, fill=True, align="C")
    pdf.cell(18, 5, _texto_latin("Fino"), border=1, fill=True, align="C")
    pdf.cell(22, 5, _texto_latin("M. Grossa"), border=1, fill=True, align="C")
    pdf.cell(20, 5, _texto_latin("Grossa"), border=1, fill=True, align="C")
    pdf.cell(20, 5, _texto_latin("Média"), border=1, fill=True, align="C")
    pdf.cell(20, 5, _texto_latin("Fina"), border=1, fill=True, align="C")
    pdf.cell(20, 5, _texto_latin("M. Fina"), border=1, fill=True, align="C", ln=True)
    
    # Valores USDA
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(34, 5.5, _texto_latin(sand_rec["Areia"][:18]), border=1, align="L")
    pdf.cell(18, 5.5, _texto_latin("0.00%"), border=1, align="C")
    pdf.cell(18, 5.5, _texto_latin(f"{usda['Cascalho Fino']:.2f}%"), border=1, align="C")
    pdf.cell(22, 5.5, _texto_latin(f"{usda['Muito Grossa']:.2f}%"), border=1, align="C")
    pdf.cell(20, 5.5, _texto_latin(f"{usda['Grossa']:.2f}%"), border=1, align="C")
    pdf.cell(20, 5.5, _texto_latin(f"{usda['Média']:.2f}%"), border=1, align="C")
    pdf.cell(20, 5.5, _texto_latin(f"{usda['Fina']:.2f}%"), border=1, align="C")
    pdf.cell(20, 5.5, _texto_latin(f"{usda['Muita Fina']:.2f}%"), border=1, align="C")
    pdf.cell(18, 5.5, _texto_latin(f"{usda['Finos']:.2f}%"), border=1, align="C", ln=True)
    
    pdf.ln(5)
    
    # Comentários
    if sand_rec.get("Comentarios"):
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 5, _texto_latin("Observações Técnicas"), ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 4.5, _texto_latin(sand_rec["Comentarios"]))
        pdf.ln(4)
        
    # Adicionar gráficos
    if fig_linha or fig_barras:
        pdf.add_page()
        _adicionar_logo(pdf, largura=45)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 6, _texto_latin("Gráficos Analíticos Granulométricos"), ln=True)
        pdf.ln(4)
        
        if fig_linha:
            pdf.image(_fig_para_bytes(fig_linha), x=20, w=170)
            pdf.ln(6)
        if fig_barras:
            pdf.image(_fig_para_bytes(fig_barras), x=20, w=170)
            
    # Fotos de microscopia
    p_files = sand_rec.get("Foto", [])
    if isinstance(p_files, str):
        p_files = [p_files] if p_files else []
    p_files = [p for p in p_files if p]
    
    if p_files:
        pdf.add_page()
        _adicionar_logo(pdf, largura=45)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 6, _texto_latin("Microscopia e Textura Visual do Grão"), ln=True)
        pdf.ln(4)
        
        # Explicação morfológica
        formato = sand_rec.get("Formato", "Não Informado")
        expl = ""
        if formato == "Arredondado":
            expl = "Grãos arredondados. Menor atrito e estabilidade (tendência a rolar), baixo desgaste dos cascos e alta durabilidade das partículas."
        elif formato == "Sub-arredondado":
            expl = "Grãos sub-arredondados. Suporte moderado e resistência intermediária com baixo desgaste."
        elif formato == "Sub-angular":
            expl = "Grãos sub-angulares. Excelente equilíbrio: evita o rolamento/instabilidade e promove boa elasticidade da pista."
        elif formato == "Angular":
            expl = "Grãos angulares. Elevado atrito e resistência ao cisalhamento (pista firme), mas causa alto desgaste nos cascos e quebra facilmente gerando finos."
            
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 5, _texto_latin(f"Formato: {formato}"), ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 4.5, _texto_latin(expl))
        pdf.ln(5)
        
        # Inserir fotos
        for idx_p, p_file in enumerate(p_files):
            p_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fotos_graos", p_file)
            if os.path.exists(p_path):
                if pdf.get_y() > 180:
                    pdf.add_page()
                    _adicionar_logo(pdf, largura=45)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(5)
                pdf.image(p_path, x=45, w=120)
                pdf.set_font("Helvetica", "I", 8)
                pdf.cell(0, 4, _texto_latin(f"Foto {idx_p + 1}: Microscopia da areia {sand_rec['Areia']}"), ln=True, align="C")
                pdf.ln(5)
                
    return _gerar_bytes_pdf(pdf)


def gerar_pdf_dimensionamento(pista_nome, comprimento, largura, espessura, densidade, modo_fibra, dosagem_fibra, insumos, active_sands_with_props):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Cabeçalho
    _adicionar_logo(pdf, largura=45)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 10, _texto_latin("RELATÓRIO DE DIMENSIONAMENTO E INSUMOS"), ln=True, align="C")
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Identificação da Pista
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("  INFORMAÇÕES DA SUPERFÍCIE"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Identificação da Pista:"), border="LT")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(150, 6, _texto_latin(pista_nome), border="RT", ln=True)
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Comprimento (m):"), border="L")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(f"{comprimento:.1f} m"), border="")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Largura (m):"), border="")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(f"{largura:.1f} m"), border="R", ln=True)
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Espessura (cm):"), border="LB")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(f"{espessura:.1f} cm"), border="B")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Densidade (t/m³):"), border="B")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(f"{densidade:.2f} t/m³"), border="RB", ln=True)
    
    pdf.ln(5)
    
    # Insumos Necessários
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("  CÁLCULO DE INSUMOS E CONSOLIDAÇÃO"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    # Criar Tabela Consolidada de Insumos
    headers = ["PARÂMETRO", "VALOR CALCULADO"]
    cols_w = [110, 80]
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(15, 58, 97)
    pdf.set_text_color(255, 255, 255)
    for col_idx, h in enumerate(headers):
        align = "L" if col_idx == 0 else "C"
        pdf.cell(cols_w[col_idx], 6, _texto_latin(h), border=1, fill=True, align=align)
    pdf.ln()
    
    # Valores calculados
    calc_data = [
        ("Área da Pista (m²)", f"{insumos['area']:.2f} m²"),
        ("Volume de Areia (m³)", f"{insumos['volume']:.2f} m³"),
        ("Massa Total de Areia Requerida (t)", f"{insumos['sand_mass']:.1f} t"),
        ("Massa Total de Fibra Requerida (t)", f"{insumos['fiber_mass']:.3f} t"),
        ("Massa Total de Fibra Requerida (kg)", f"{insumos['fiber_mass']*1000:.1f} kg")
    ]
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    for idx_r, (p, val) in enumerate(calc_data):
        bg_alt = (idx_r % 2 == 1)
        pdf.set_fill_color(248, 250, 252) if bg_alt else pdf.set_fill_color(255, 255, 255)
        pdf.cell(cols_w[0], 6, _texto_latin(p), border=1, fill=True, align="L")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(cols_w[1], 6, _texto_latin(val), border=1, fill=True, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.ln()
        
    pdf.ln(5)
    
    # Detalhamento de Componentes (Blend)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("  DETALHAMENTO DE COMPONENTES DO BLEND"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    if active_sands_with_props:
        # Tabela com as areias do blend, porcentagens e peso em toneladas
        headers_b = ["COMPONENTE DO BLEND", "PARTICIPAÇÃO (%)", "MASSA EQUIVALENTE (TONELADAS)"]
        cols_wb = [85, 45, 60]
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(15, 58, 97)
        pdf.set_text_color(255, 255, 255)
        for col_idx, h in enumerate(headers_b):
            align = "L" if col_idx == 0 else "C"
            pdf.cell(cols_wb[col_idx], 6, _texto_latin(h), border=1, fill=True, align=align)
        pdf.ln()
        
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        
        for idx_c, (sand_rec, prop) in enumerate(active_sands_with_props):
            bg_alt = (idx_c % 2 == 1)
            pdf.set_fill_color(248, 250, 252) if bg_alt else pdf.set_fill_color(255, 255, 255)
            
            s_name = sand_rec["Areia"]
            p_val = prop
            mass_equiv = insumos['sand_mass'] * (prop / 100.0)
            
            pdf.cell(cols_wb[0], 6, _texto_latin(s_name), border=1, fill=True, align="L")
            pdf.cell(cols_wb[1], 6, _texto_latin(f"{p_val:.1f}%"), border=1, fill=True, align="C")
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(cols_wb[2], 6, _texto_latin(f"{mass_equiv:.1f} t"), border=1, fill=True, align="C")
            pdf.set_font("Helvetica", "", 9)
            pdf.ln()
            
        # Linha de totalização
        pdf.set_fill_color(240, 244, 248)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(cols_wb[0], 6, _texto_latin("TOTAL MISTURA"), border=1, fill=True, align="L")
        pdf.cell(cols_wb[1], 6, _texto_latin("100.0%"), border=1, fill=True, align="C")
        pdf.cell(cols_wb[2], 6, _texto_latin(f"{insumos['sand_mass']:.1f} t"), border=1, fill=True, align="C")
        pdf.ln()
    else:
        pdf.set_font("Helvetica", "I", 9.5)
        pdf.cell(0, 6, _texto_latin("Nenhum componente cadastrado no blend. Configure a mistura na aba '6. Blendagem'."), ln=True)
        
    pdf.ln(5)
    
    # Parâmetros de fibra
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("  DOSAGEM DE FIBRA TÊXTIL"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "", 9.5)
    fib_desc = "Porcentagem sobre a massa de areia" if modo_fibra == "A" else "Massa de fibra por metro quadrado de pista"
    pdf.cell(50, 6, _texto_latin("Método de Dosagem:"), border="L")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(140, 6, _texto_latin(fib_desc), border="R", ln=True)
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(50, 6, _texto_latin("Dosagem Definida:"), border="LB")
    pdf.set_font("Helvetica", "B", 9.5)
    unit_str = "%" if modo_fibra == "A" else " kg/m²"
    pdf.cell(140, 6, _texto_latin(f"{dosagem_fibra:.2f}{unit_str}"), border="RB", ln=True)
    
    pdf.ln(10)
    
    # Rodapé Técnico do Dimensionamento
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 5, _texto_latin("Método Paulo Nania — Engenharia de Superfícies Equestres"), ln=True, align="C")
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 4, _texto_latin("Dimensionamento granulométrico e volumétrico baseado no atrito dinâmico e retenção hídrica ideal."), ln=True, align="C")
    
    return _gerar_bytes_pdf(pdf)


def gerar_pdf_laudo(pista_nome, target_profile, composition_str, insumos, df_comp_data, blend_afs, target_afs, fig_curva, fig_barras, usda_sands_list, active_sands_with_props, comments_notes):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- Página 1 ---
    pdf.add_page()
    _adicionar_logo(pdf, largura=45)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 10, _texto_latin("LAUDO TÉCNICO DE ESTABILIZAÇÃO DE PISTA"), ln=True, align="C")
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Consolidação Geral da Superfície
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("  DADOS DE CONSOLIDAÇÃO DA PISTA"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Identificação da Pista:"), border="LT")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(pista_nome), border="T")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Disciplina / Faixa Alvo:"), border="T")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(target_profile), border="RT", ln=True)
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Espessura da Camada:"), border="L")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(f"{insumos.get('thickness', 10.0):.1f} cm"), border="")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" AFS do Blend:"), border="")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(f"{blend_afs:.1f}"), border="R", ln=True)
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Teor de Areia Total:"), border="L")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(f"{insumos['sand_mass']:.1f} t"), border="")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Dosagem de Fibra:"), border="")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(55, 6, _texto_latin(f"{insumos['fiber_mass']:.3f} t ({insumos['fiber_mass']*1000:.1f} kg)"), border="R", ln=True)
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(40, 6, _texto_latin(" Composição do Blend:"), border="LMB")
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(150, 6, _texto_latin(composition_str), border="RMB", ln=True)
    
    pdf.ln(5)
    
    # Comparativo Tabular
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("  ANÁLISE COMPARATIVA GRANULOMÉTRICA"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    headers = ["PENEIRA", "REF. MÍNIMA (%)", "REF. MÁXIMA (%)", "RESULTADO BLEND (%)", "STATUS"]
    cols_w = [45, 35, 35, 40, 35]
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(15, 58, 97)
    pdf.set_text_color(255, 255, 255)
    for col_idx, h in enumerate(headers):
        align = "L" if col_idx == 0 else "C"
        pdf.cell(cols_w[col_idx], 6, _texto_latin(h), border=1, fill=True, align=align)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    
    SIEVE_NAMES_CLEAN = {
        "#10": "NO. 10 (2,00 mm)",
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
    
    for idx_row, row in enumerate(df_comp_data):
        bg_alt = (idx_row % 2 == 1)
        pdf.set_fill_color(248, 250, 252) if bg_alt else pdf.set_fill_color(255, 255, 255)
        
        peneira = row["Peneira"]
        desc = SIEVE_NAMES_CLEAN.get(peneira, peneira)
        
        pdf.cell(cols_w[0], 5.5, _texto_latin(desc), border=1, fill=True, align="L")
        pdf.cell(cols_w[1], 5.5, _texto_latin(row["Ref. Mínima (%)"]), border=1, fill=True, align="C")
        pdf.cell(cols_w[2], 5.5, _texto_latin(row["Ref. Máxima (%)"]), border=1, fill=True, align="C")
        pdf.cell(cols_w[3], 5.5, _texto_latin(row["Resultado Blend (%)"]), border=1, fill=True, align="C")
        
        status = row["Status"]
        bg_cell = (255, 255, 255)
        text_color = (0, 0, 0)
        
        if "DENTRO" in status:
            bg_cell = (226, 240, 217)
            text_color = (46, 125, 50)
        else:
            bg_cell = (254, 242, 242)
            text_color = (198, 40, 40)
            
        pdf.set_fill_color(*bg_cell)
        pdf.set_text_color(*text_color)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(cols_w[4], 5.5, _texto_latin(status), border=1, fill=True, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.ln()
        
    # Linha do AFS
    pdf.set_fill_color(240, 244, 248)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(15, 58, 97)
    
    pdf.cell(155, 5.5, _texto_latin("AFS da Mistura (Tamanho Médio Alvo: " + f"{target_afs[0]:.1f} a {target_afs[1]:.1f})"), border=1, fill=True, align="L")
    
    if target_afs[0] <= blend_afs <= target_afs[1]:
        bg_cell = (226, 240, 217)
        text_color = (46, 125, 50)
        afs_status_text = f"{blend_afs:.1f} (OK)"
    else:
        bg_cell = (254, 242, 242)
        text_color = (198, 40, 40)
        afs_status_text = f"{blend_afs:.1f} (FORA)"
        
    pdf.set_fill_color(*bg_cell)
    pdf.set_text_color(*text_color)
    pdf.cell(35, 5.5, _texto_latin(afs_status_text), border=1, fill=True, align="C", ln=True)
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Helvetica", "", 9)
    
    # --- Página 2: Gráficos ---
    pdf.add_page()
    _adicionar_logo(pdf, largura=45)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("Gráficos de Ajuste Granulométrico do Blend"), ln=True)
    pdf.ln(4)
    
    if fig_curva:
        pdf.image(_fig_para_bytes(fig_curva), x=20, w=170)
        pdf.ln(6)
    if fig_barras:
        pdf.image(_fig_para_bytes(fig_barras), x=20, w=170)
        
    # --- Página 3: Classificação USDA e Morfologia ---
    pdf.add_page()
    _adicionar_logo(pdf, largura=45)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Tabela USDA
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("Classificação USDA da Mistura e Componentes"), ln=True)
    pdf.ln(2)
    
    # Headers USDA
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(34, 10, _texto_latin("DESCRIÇÃO"), border=1, fill=True, align="C")
    pdf.cell(36, 5, _texto_latin("CASCALHO"), border=1, fill=True, align="C")
    pdf.cell(102, 5, _texto_latin("AREIA"), border=1, fill=True, align="C")
    pdf.cell(18, 10, _texto_latin("FINOS"), border=1, fill=True, align="C", ln=True)
    
    # Sub-headers USDA
    pdf.set_y(pdf.get_y() - 5)
    pdf.set_x(10 + 34)
    pdf.cell(18, 5, _texto_latin("Grosso"), border=1, fill=True, align="C")
    pdf.cell(18, 5, _texto_latin("Fino"), border=1, fill=True, align="C")
    pdf.cell(22, 5, _texto_latin("M. Grossa"), border=1, fill=True, align="C")
    pdf.cell(20, 5, _texto_latin("Grossa"), border=1, fill=True, align="C")
    pdf.cell(20, 5, _texto_latin("Média"), border=1, fill=True, align="C")
    pdf.cell(20, 5, _texto_latin("Fina"), border=1, fill=True, align="C")
    pdf.cell(20, 5, _texto_latin("M. Fina"), border=1, fill=True, align="C", ln=True)
    
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(50, 50, 50)
    
    for sand in usda_sands_list:
        usda = mapear_para_usda(sand)
        
        is_mistura = sand.get("Areia", "") in ["MISTURA", "MISTURA RESULTANTE", "MISTURA (MISTURA)"]
        if is_mistura:
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_fill_color(240, 244, 248)
            pdf.set_text_color(15, 58, 97)
            fill_row = True
        else:
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(50, 50, 50)
            fill_row = False
            
        pdf.cell(34, 5.5, _texto_latin(sand.get("Areia", "Amostra")[:18]), border=1, fill=fill_row, align="L")
        pdf.cell(18, 5.5, _texto_latin("0.00%"), border=1, fill=fill_row, align="C")
        pdf.cell(18, 5.5, _texto_latin(f"{usda['Cascalho Fino']:.2f}%"), border=1, fill=fill_row, align="C")
        pdf.cell(22, 5.5, _texto_latin(f"{usda['Muito Grossa']:.2f}%"), border=1, fill=fill_row, align="C")
        pdf.cell(20, 5.5, _texto_latin(f"{usda['Grossa']:.2f}%"), border=1, fill=fill_row, align="C")
        pdf.cell(20, 5.5, _texto_latin(f"{usda['Média']:.2f}%"), border=1, fill=fill_row, align="C")
        pdf.cell(20, 5.5, _texto_latin(f"{usda['Fina']:.2f}%"), border=1, fill=fill_row, align="C")
        pdf.cell(20, 5.5, _texto_latin(f"{usda['Muita Fina']:.2f}%"), border=1, fill=fill_row, align="C")
        pdf.cell(18, 5.5, _texto_latin(f"{usda['Finos']:.2f}%"), border=1, fill=fill_row, align="C", ln=True)
        
    pdf.ln(5)
    
    # Morfologia
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 58, 97)
    pdf.cell(0, 6, _texto_latin("Morfologia e Angularidade dos Componentes"), ln=True)
    pdf.ln(2)
    
    for sand_rec, prop in active_sands_with_props:
        formato = sand_rec.get("Formato", "Não Informado")
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
            
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 5, _texto_latin(f"{sand_rec['Areia']} ({prop:.1f}%): Formato {formato}"), ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 4.5, _texto_latin(expl))
        pdf.ln(3)
        
    # Coletar fotos para galeria
    fotos_encontradas = []
    for sand_rec, prop in active_sands_with_props:
        p_files = sand_rec.get("Foto", [])
        if isinstance(p_files, str):
            p_files = [p_files] if p_files else []
        for pf in p_files:
            if pf:
                p_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fotos_graos", pf)
                if os.path.exists(p_path):
                    fotos_encontradas.append((sand_rec["Areia"], p_path))
                    
    if fotos_encontradas:
        pdf.add_page()
        _adicionar_logo(pdf, largura=45)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 6, _texto_latin("Galeria de Microscopia dos Grãos"), ln=True)
        pdf.ln(4)
        
        for idx_f, (sand_name, f_path) in enumerate(fotos_encontradas):
            if pdf.get_y() > 190:
                pdf.add_page()
                _adicionar_logo(pdf, largura=45)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
            pdf.image(f_path, x=45, w=120)
            pdf.set_font("Helvetica", "I", 8)
            pdf.cell(0, 4, _texto_latin(f"Microscopia: {sand_name}"), ln=True, align="C")
            pdf.ln(5)
            
    # Notas do Laudo
    if comments_notes:
        pdf.add_page()
        _adicionar_logo(pdf, largura=45)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 58, 97)
        pdf.cell(0, 6, _texto_latin("Notas Técnicas e Parecer Técnico"), ln=True)
        pdf.ln(4)
        
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 4.8, _texto_latin(comments_notes))
        
    return _gerar_bytes_pdf(pdf)
