def classificar_penetro(valor):
    if valor <= 15.0:
        return "Ideal", "#2e7d32"
    elif valor <= 20.0:
        return "Alerta", "#f57c00"
    else:
        return "Crítico", "#c62828"


def classificar_umidade(valor):
    if valor <= 10.0:
        return "Ideal", "#2e7d32"
    elif valor <= 15.0:
        return "Alerta", "#f57c00"
    else:
        return "Crítico", "#c62828"


def classificar_espessura(valor):
    if valor <= 8.0:
        return "Ideal", "#2e7d32"
    elif valor <= 12.0:
        return "Alerta", "#f57c00"
    else:
        return "Crítico", "#c62828"


def calcular_io(serie):
    media = serie.mean()
    if media <= 0:
        return 0.0
    return (serie.std() / media) * 100


def calcular_estatisticas(df, meta):
    med_amort = df["1ª Queda"].mean()
    med_trans = df["2ª Queda"].mean()
    med_sup = df["3ª Queda"].mean()
    medicao_atual = [med_amort, med_trans, med_sup]

    # Risco Biomecânico
    n_pontos = len(df)

    tipo_pista = meta.get("tipo_pista", "Pista de Treinamento")
    if tipo_pista == "Pista de Competição":
        q1_min, q1_max = 3.0, 4.0
        q2_min, q2_max = 4.0, 5.0
        q3_min, q3_max = 5.0, 6.0
        ideal_q1 = "Alvo: 3.0 - 4.0 cm"
        ideal_q2 = "Alvo: 4.0 - 5.0 cm"
        ideal_q3 = "Alvo: 5.0 - 6.0 cm"
    else:
        q1_min, q1_max = 3.0, 5.0
        q2_min, q2_max = 5.0, 7.0
        q3_min, q3_max = 7.0, 9.0
        ideal_q1 = "Alvo: 3.0 - 5.0 cm"
        ideal_q2 = "Alvo: 5.0 - 7.0 cm"
        ideal_q3 = "Alvo: 7.0 - 9.0 cm"

    # 1ª Queda (Impacto)
    col_q1 = df["1ª Queda"]
    q1_abaixo = int((col_q1 < q1_min).sum())
    q1_acima = int((col_q1 > q1_max).sum())
    q1_falhas = q1_abaixo + q1_acima
    q1_risco = (q1_falhas / n_pontos * 100) if n_pontos > 0 else 0.0

    # 2ª Queda (Suporte)
    col_q2 = df["2ª Queda"]
    q2_abaixo = int((col_q2 < q2_min).sum())
    q2_acima = int((col_q2 > q2_max).sum())
    q2_falhas = q2_abaixo + q2_acima
    q2_risco = (q2_falhas / n_pontos * 100) if n_pontos > 0 else 0.0

    # 3ª Queda (Tração)
    col_q3 = df["3ª Queda"]
    q3_abaixo = int((col_q3 < q3_min).sum())
    q3_acima = int((col_q3 > q3_max).sum())
    q3_falhas = q3_abaixo + q3_acima
    q3_risco = (q3_falhas / n_pontos * 100) if n_pontos > 0 else 0.0

    total_falhas = q1_falhas + q2_falhas + q3_falhas
    total_medicoes = 3 * n_pontos

    if n_pontos == 0:
        q1_status, q1_cor = "IDEAL", "#2e7d32"
        q2_status, q2_cor = "IDEAL", "#2e7d32"
        q3_status, q3_cor = "IDEAL", "#2e7d32"
        geral_status, geral_cor = "IDEAL", "#2e7d32"
        risco_geral = 0.0
    else:
        # 1ª Queda (Impacto)
        if q1_min <= med_amort <= q1_max:
            q1_status, q1_cor = "IDEAL", "#2e7d32"
        elif (q1_min - 1.0) <= med_amort < q1_min or q1_max < med_amort <= (q1_max + 1.0):
            q1_status, q1_cor = "ALERTA", "#f57c00"
        else:
            q1_status, q1_cor = "CRÍTICO", "#c62828"

        # 2ª Queda (Suporte)
        if q2_min <= med_trans <= q2_max:
            q2_status, q2_cor = "IDEAL", "#2e7d32"
        elif (q2_min - 1.0) <= med_trans < q2_min or q2_max < med_trans <= (q2_max + 1.0):
            q2_status, q2_cor = "ALERTA", "#f57c00"
        else:
            q2_status, q2_cor = "CRÍTICO", "#c62828"

        # 3ª Queda (Tração)
        if q3_min <= med_sup <= q3_max:
            q3_status, q3_cor = "IDEAL", "#2e7d32"
        elif (q3_min - 1.0) <= med_sup < q3_min or q3_max < med_sup <= (q3_max + 1.0):
            q3_status, q3_cor = "ALERTA", "#f57c00"
        else:
            q3_status, q3_cor = "CRÍTICO", "#c62828"

        # Consolidação Geral (Regra de Pior Caso)
        risco_geral = (total_falhas / total_medicoes * 100)
        if q1_status == "CRÍTICO" or q2_status == "CRÍTICO" or q3_status == "CRÍTICO":
            geral_status, geral_cor = "CRÍTICO", "#c62828"
        elif q1_status == "ALERTA" or q2_status == "ALERTA" or q3_status == "ALERTA":
            geral_status, geral_cor = "ALERTA", "#f57c00"
        else:
            geral_status, geral_cor = "IDEAL", "#2e7d32"

    io_amort = calcular_io(df["1ª Queda"])
    io_trans = calcular_io(df["2ª Queda"])
    io_sup = calcular_io(df["3ª Queda"])

    coletou_umidade = meta["coletou_umidade"]
    coletou_espessura = meta["coletou_espessura"]

    io_umidade = calcular_io(df["Umidade"]) if coletou_umidade else 0.0
    io_espessura = calcular_io(df["Espessura"]) if coletou_espessura else 0.0

    umidade_media = df["Umidade"].mean() if coletou_umidade else meta["global_umi"]
    espessura_media = round(df["Espessura"].mean()) if coletou_espessura else meta["global_esp"]

    fases = [
        {
            "nome": "Impacto",
            "media": med_amort,
            "io": io_amort,
            "ideal": ideal_q1,
            "risco": q1_risco,
            "status": q1_status,
            "cor": q1_cor,
            "abaixo": q1_abaixo,
            "acima": q1_acima,
        },
        {
            "nome": "Suporte",
            "media": med_trans,
            "io": io_trans,
            "ideal": ideal_q2,
            "risco": q2_risco,
            "status": q2_status,
            "cor": q2_cor,
            "abaixo": q2_abaixo,
            "acima": q2_acima,
        },
        {
            "nome": "Tração",
            "media": med_sup,
            "io": io_sup,
            "ideal": ideal_q3,
            "risco": q3_risco,
            "status": q3_status,
            "cor": q3_cor,
            "abaixo": q3_abaixo,
            "acima": q3_acima,
        },
    ]

    io_geral = (io_amort + io_trans + io_sup) / 3
    w_pen = 0.4
    w_umi = 0.3 if coletou_umidade else 0.0
    w_esp = 0.3 if coletou_espessura else 0.0
    total_w = w_pen + w_umi + w_esp
    icg_val = (w_pen * io_geral + w_umi * io_umidade + w_esp * io_espessura) / total_w if total_w > 0 else 0.0

    return {
        "medicao_atual": medicao_atual,
        "io_amort": io_amort,
        "io_trans": io_trans,
        "io_supor": io_sup,
        "io_geral": io_geral,
        "io_umidade": io_umidade,
        "io_espessura": io_espessura,
        "umidade_media_geral": umidade_media,
        "espessura_media_geral": espessura_media,
        "fases": fases,
        "icg": icg_val,
        "risco_geral": risco_geral,
        "geral_status": geral_status,
        "geral_cor": geral_cor,
        "total_falhas": total_falhas,
        "total_medicoes": total_medicoes,
    }


def classificar_desvio_fase(valor_medido, fase_nome, tipo_pista="Pista de Treinamento"):
    if tipo_pista == "Pista de Competição":
        if fase_nome == "Impacto":
            center = 3.5
            dev = abs(valor_medido - center)
            if dev <= 0.25:
                return "Excelente", "#2e7d32"
            elif dev <= 0.5:
                return "Boa", "#2e7d32"
            elif dev <= 1.5:
                return "Alerta", "#f57c00"
            else:
                return "Crítica", "#c62828"
        elif fase_nome == "Suporte":
            center = 4.5
            dev = abs(valor_medido - center)
            if dev <= 0.25:
                return "Excelente", "#2e7d32"
            elif dev <= 0.5:
                return "Boa", "#2e7d32"
            elif dev <= 1.5:
                return "Alerta", "#f57c00"
            else:
                return "Crítica", "#c62828"
        elif fase_nome == "Tração":
            center = 5.5
            dev = abs(valor_medido - center)
            if dev <= 0.25:
                return "Excelente", "#2e7d32"
            elif dev <= 0.5:
                return "Boa", "#2e7d32"
            elif dev <= 1.5:
                return "Alerta", "#f57c00"
            else:
                return "Crítica", "#c62828"
        else:
            return "Excelente", "#2e7d32"
    else:
        if fase_nome == "Impacto":
            center = 4.0
            dev = abs(valor_medido - center)
            if dev <= 0.5:
                return "Excelente", "#2e7d32"
            elif dev <= 1.0:
                return "Boa", "#2e7d32"
            elif dev <= 2.0:
                return "Alerta", "#f57c00"
            else:
                return "Crítica", "#c62828"
        elif fase_nome == "Suporte":
            center = 6.0
            dev = abs(valor_medido - center)
            if dev <= 0.5:
                return "Excelente", "#2e7d32"
            elif dev <= 1.5:
                return "Boa", "#2e7d32"
            elif dev <= 2.5:
                return "Alerta", "#f57c00"
            else:
                return "Crítica", "#c62828"
        elif fase_nome == "Tração":
            center = 8.0
            dev = abs(valor_medido - center)
            if dev <= 1.0:
                return "Excelente", "#2e7d32"
            elif dev <= 2.0:
                return "Boa", "#2e7d32"
            elif dev <= 3.5:
                return "Alerta", "#f57c00"
            else:
                return "Crítica", "#c62828"
        else:
            return "Excelente", "#2e7d32"


def classificar_umidade_valor(valor_medido, ideal_str):
    if not ideal_str:
        center = 18.0
    else:
        import re
        numeros = [float(s) for s in re.findall(r"[-+]?\d*\.\d+|\d+", ideal_str)]
        if len(numeros) >= 2:
            center = sum(numeros) / len(numeros)
        elif len(numeros) == 1:
            center = numeros[0]
        else:
            center = 18.0
        
    dev = abs(valor_medido - center)
    if dev <= 0.5:
        return "Excelente", "#2e7d32"
    elif dev <= 1.5:
        return "Boa", "#2e7d32"
    elif dev <= 3.0:
        return "Alerta", "#f57c00"
    else:
        return "Crítica", "#c62828"


def classificar_espessura_valor(valor_medido, ideal_str):
    if not ideal_str:
        center = 12.0
    else:
        import re
        numeros = [float(s) for s in re.findall(r"[-+]?\d*\.\d+|\d+", ideal_str)]
        if len(numeros) >= 2:
            center = sum(numeros) / len(numeros)
        elif len(numeros) == 1:
            center = numeros[0]
        else:
            center = 12.0
        
    dev = abs(valor_medido - center)
    if dev <= 0.5:
        return "Excelente", "#2e7d32"
    elif dev <= 2.0:
        return "Boa", "#2e7d32"
    elif dev <= 4.0:
        return "Alerta", "#f57c00"
    else:
        return "Crítica", "#c62828"


def classificar_perfil(media, tipo_pista="Pista de Treinamento"):
    if tipo_pista == "Pista de Competição":
        # Target is PR 3: Pista Firme 1 (4.0 <= media < 5.0)
        if media < 3.0:
            return "PR 1 - MUITO DURA | BOM", "#c62828", ""
        elif media < 4.0:
            return "PR 2 - DURA | BOM", "#f57c00", ""
        elif media < 5.0:
            return "PR 3 - FIRME 1 | ÓTIMO", "#2e7d32", ""
        elif media < 6.5:
            if 5.50 <= media <= 6.00:
                return "PR 4 - FIRME 2 | ÓTIMO", "#2e7d32", ""
            else:
                return "PR 4 - FIRME 2 | BOM", "#f57c00", ""
        elif media < 7.0:
            return "PR 5 - MACIA 1 | BOM", "#c62828", ""
        elif media < 8.0:
            return "PR 6 - MACIA 2 | BOM", "#c62828", ""
        else:
            return "PR 7 - PESADA | BOM", "#c62828", ""
    else:
        # Pista de Treinamento: Target is PR 4: Pista Firme 2 (5.0 <= media < 6.5)
        if media < 3.0:
            return "PR 1 - MUITO DURA | BOM", "#c62828", ""
        elif media < 4.0:
            return "PR 2 - DURA | BOM", "#c62828", ""
        elif media < 5.0:
            return "PR 3 - FIRME 1 | BOM", "#f57c00", ""
        elif media < 6.5:
            if 5.50 <= media <= 6.00:
                return "PR 4 - FIRME 2 | ÓTIMO", "#2e7d32", ""
            else:
                return "PR 4 - FIRME 2 | BOM", "#f57c00", ""
        elif media < 7.0:
            return "PR 5 - MACIA 1 | BOM", "#f57c00", ""
        elif media < 8.0:
            return "PR 6 - MACIA 2 | BOM", "#c62828", ""
        else:
            return "PR 7 - PESADA | BOM", "#c62828", ""
