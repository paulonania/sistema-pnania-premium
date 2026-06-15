import os
import sys

# Add project folder to sys.path
sys.path.append(r"c:\Users\paulo\Downloads\Sistema-Pnania-Premium (1)\Sistema-Pnania-Premium")

from analysis import (
    classificar_desvio_fase, 
    classificar_umidade_valor, 
    classificar_espessura_valor,
    classificar_penetro,
    classificar_umidade,
    classificar_espessura,
    calcular_estatisticas,
    classificar_perfil
)
import pandas as pd

def test_risco_biomecanico():
    print("Testing Block 1: Average-based phase classification and worst-of consolidation...")

    # Case A: All phases IDEAL
    # Impacto: mean 4.0 -> IDEAL
    # Suporte: mean 6.0 -> IDEAL
    # Tração: mean 8.0 -> IDEAL
    # Overall: IDEAL (worst of three IDEALs)
    df_a = pd.DataFrame({
        "Linha": [1]*10,
        "Ponto": list(range(1, 11)),
        "1ª Queda": [4.0]*10,
        "2ª Queda": [6.0]*10,
        "3ª Queda": [8.0]*10,
        "Umidade": [18.0]*10,
        "Espessura": [12]*10
    })
    meta = {
        "coletou_umidade": True,
        "coletou_espessura": True,
        "global_umi": 18.0,
        "global_esp": 12
    }
    stats_a = calcular_estatisticas(df_a, meta)
    assert stats_a["fases"][0]["status"] == "IDEAL", f"Impacto Status: {stats_a['fases'][0]['status']}"
    assert stats_a["fases"][1]["status"] == "IDEAL"
    assert stats_a["fases"][2]["status"] == "IDEAL"
    assert stats_a["geral_status"] == "IDEAL", f"Overall Status: {stats_a['geral_status']}"

    # Case B: At least one ALERTA, no CRÍTICO
    # Impacto: mean 2.8 -> ALERTA
    # Suporte: mean 6.0 -> IDEAL
    # Tração: mean 8.0 -> IDEAL
    # Overall: ALERTA (worst of ALERTA, IDEAL, IDEAL)
    df_b = pd.DataFrame({
        "Linha": [1]*10,
        "Ponto": list(range(1, 11)),
        "1ª Queda": [2.8]*10,
        "2ª Queda": [6.0]*10,
        "3ª Queda": [8.0]*10,
        "Umidade": [18.0]*10,
        "Espessura": [12]*10
    })
    stats_b = calcular_estatisticas(df_b, meta)
    assert stats_b["fases"][0]["status"] == "ALERTA", f"Impacto Status: {stats_b['fases'][0]['status']}"
    assert stats_b["fases"][1]["status"] == "IDEAL"
    assert stats_b["fases"][2]["status"] == "IDEAL"
    assert stats_b["geral_status"] == "ALERTA", f"Overall Status: {stats_b['geral_status']}"

    # Case C: At least one CRÍTICO
    # Impacto: mean 1.5 -> CRÍTICO
    # Suporte: mean 6.0 -> IDEAL
    # Tração: mean 6.8 -> ALERTA
    # Overall: CRÍTICO (worst of CRÍTICO, IDEAL, ALERTA)
    df_c = pd.DataFrame({
        "Linha": [1]*10,
        "Ponto": list(range(1, 11)),
        "1ª Queda": [1.5]*10,
        "2ª Queda": [6.0]*10,
        "3ª Queda": [6.8]*10,
        "Umidade": [18.0]*10,
        "Espessura": [12]*10
    })
    stats_c = calcular_estatisticas(df_c, meta)
    assert stats_c["fases"][0]["status"] == "CRÍTICO", f"Impacto Status: {stats_c['fases'][0]['status']}"
    assert stats_c["fases"][1]["status"] == "IDEAL"
    assert stats_c["fases"][2]["status"] == "ALERTA"
    assert stats_c["geral_status"] == "CRÍTICO", f"Overall Status: {stats_c['geral_status']}"

    # Test supporting sensors classifications (keep from previous desvio_absoluto tests)
    # Umidade (Center 18.0): Exc <= 0.5, Boa <= 1.5, Alerta <= 3.0, Crítica > 3.0
    lbl, _ = classificar_umidade_valor(17.9, "18.0%") # dev 0.1 -> Excelente
    assert lbl == "Excelente", f"Umidade Exc: {lbl}"
    
    # Espessura (Center 12.0): Exc <= 0.5, Boa <= 2.0, Alerta <= 4.0, Crítica > 4.0
    lbl, _ = classificar_espessura_valor(12.3, "12 cm") # dev 0.3 -> Excelente
    assert lbl == "Excelente", f"Espessura Exc: {lbl}"


def test_regularidade_cv():
    print("Testing Block 2: CV Uniformity Classifications...")
    # Penetrômetro & ICG: Ideal <= 15%, Alerta 15-20%, Crítico > 20%
    lbl, _ = classificar_penetro(9.5)
    assert lbl == "Ideal", f"Penetro CV Ideal 1: {lbl}"
    lbl, _ = classificar_penetro(12.0)
    assert lbl == "Ideal", f"Penetro CV Ideal 2: {lbl}"
    lbl, _ = classificar_penetro(17.5)
    assert lbl == "Alerta", f"Penetro CV Alerta: {lbl}"
    lbl, _ = classificar_penetro(22.0)
    assert lbl == "Crítico", f"Penetro CV Crítico: {lbl}"

    # Umidade: Ideal <= 10%, Alerta 10-15%, Crítico > 15%
    lbl, _ = classificar_umidade(4.5)
    assert lbl == "Ideal", f"Umidade CV Ideal 1: {lbl}"
    lbl, _ = classificar_umidade(7.5)
    assert lbl == "Ideal", f"Umidade CV Ideal 2: {lbl}"
    lbl, _ = classificar_umidade(12.5)
    assert lbl == "Alerta", f"Umidade CV Alerta: {lbl}"
    lbl, _ = classificar_umidade(16.5)
    assert lbl == "Crítico", f"Umidade CV Crítico: {lbl}"

    # Espessura: Ideal <= 8%, Alerta 8-12%, Crítico > 12%
    lbl, _ = classificar_espessura(3.5)
    assert lbl == "Ideal", f"Espessura CV Ideal 1: {lbl}"
    lbl, _ = classificar_espessura(6.0)
    assert lbl == "Ideal", f"Espessura CV Ideal 2: {lbl}"
    lbl, _ = classificar_espessura(10.0)
    assert lbl == "Alerta", f"Espessura CV Alerta: {lbl}"
    lbl, _ = classificar_espessura(14.0)
    assert lbl == "Crítico", f"Espessura CV Crítico: {lbl}"


def test_icg_dinamico():
    print("Testing dynamic ICG calculation...")
    df = pd.DataFrame({
        "Linha": [1, 1, 2, 2],
        "Ponto": [1, 2, 1, 2],
        "1ª Queda": [4.0, 4.4, 3.8, 4.2], 
        "2ª Queda": [5.5, 6.0, 5.8, 5.9], 
        "3ª Queda": [7.2, 8.0, 7.5, 7.8], 
        "Umidade": [18.0, 18.5, 17.5, 18.0], 
        "Espessura": [12, 13, 11, 12] 
    })

    # Scenario A: All active
    meta = {
        "coletou_umidade": True,
        "coletou_espessura": True,
        "global_umi": 18.0,
        "global_esp": 12
    }
    stats = calcular_estatisticas(df, meta)
    icg_a = stats["icg"]
    
    io_gen = stats["io_geral"]
    io_umi = stats["io_umidade"]
    io_esp = stats["io_espessura"]
    expected_icg_a = (0.4 * io_gen + 0.3 * io_umi + 0.3 * io_esp) / 1.0
    assert abs(icg_a - expected_icg_a) < 1e-6, f"ICG All Active error. Got {icg_a}, expected {expected_icg_a}"

    # Scenario B: No moisture
    meta["coletou_umidade"] = False
    stats_b = calcular_estatisticas(df, meta)
    icg_b = stats_b["icg"]
    expected_icg_b = (0.4 * io_gen + 0.3 * io_esp) / 0.7
    assert abs(icg_b - expected_icg_b) < 1e-6, f"ICG No Moisture error. Got {icg_b}, expected {expected_icg_b}"

    # Scenario C: Only penetrometer
    meta["coletou_espessura"] = False
    stats_c = calcular_estatisticas(df, meta)
    icg_c = stats_c["icg"]
    expected_icg_c = io_gen
    assert abs(icg_c - expected_icg_c) < 1e-6, f"ICG Only Pen error. Got {icg_c}, expected {expected_icg_c}"


def test_diagnostico_perfil():
    print("Testing Block 1: Diagnóstico de Perfil...")
    
    # --- Pista de Treinamento ---
    # PR 1 (< 3.0)
    lbl, color, app = classificar_perfil(2.5, "Pista de Treinamento")
    assert lbl == "Pista Muito Dura | BOM" and color == "#c62828", f"Treinamento PR 1 error: {lbl}, {color}"
    # PR 2 (3.0 <= media < 4.0)
    lbl, color, app = classificar_perfil(3.5, "Pista de Treinamento")
    assert lbl == "Pista Dura | BOM" and color == "#c62828", f"Treinamento PR 2 error: {lbl}, {color}"
    # PR 3 (4.0 <= media < 5.0)
    lbl, color, app = classificar_perfil(4.5, "Pista de Treinamento")
    assert lbl == "Pista Firme 1 | BOM" and color == "#f57c00", f"Treinamento PR 3 error: {lbl}, {color}"
    # PR 4 (Ótimo: 5.50 <= media <= 6.00)
    lbl, color, app = classificar_perfil(5.8, "Pista de Treinamento")
    assert lbl == "Pista Firme 2 | ÓTIMO" and color == "#2e7d32", f"Treinamento PR 4 error: {lbl}, {color}"
    # PR 4 (Bom: border 5.00 - 5.49)
    lbl, color, app = classificar_perfil(5.1, "Pista de Treinamento")
    assert lbl == "Pista Firme 2 | BOM" and color == "#2e7d32", f"Treinamento PR 4 border low error: {lbl}, {color}"
    # PR 4 (Bom: border 6.01 - 6.50)
    lbl, color, app = classificar_perfil(6.4, "Pista de Treinamento")
    assert lbl == "Pista Firme 2 | BOM" and color == "#2e7d32", f"Treinamento PR 4 border high error: {lbl}, {color}"
    # PR 5 (6.5 <= media < 7.0)
    lbl, color, app = classificar_perfil(6.8, "Pista de Treinamento")
    assert lbl == "Pista Macia 1 | BOM" and color == "#f57c00", f"Treinamento PR 5 error: {lbl}, {color}"
    # PR 6 (7.0 <= media < 8.0)
    lbl, color, app = classificar_perfil(7.5, "Pista de Treinamento")
    assert lbl == "Pista Macia 2 | BOM" and color == "#c62828", f"Treinamento PR 6 error: {lbl}, {color}"
    # PR 7 (media >= 8.0)
    lbl, color, app = classificar_perfil(8.5, "Pista de Treinamento")
    assert lbl == "Pista Pesada | BOM" and color == "#c62828", f"Treinamento PR 7 error: {lbl}, {color}"

    # --- Pista de Competição ---
    # PR 1
    lbl, color, app = classificar_perfil(2.5, "Pista de Competição")
    assert lbl == "Pista Muito Dura | BOM" and color == "#c62828", f"Competição PR 1 error: {lbl}, {color}"
    # PR 2
    lbl, color, app = classificar_perfil(3.5, "Pista de Competição")
    assert lbl == "Pista Dura | BOM" and color == "#f57c00", f"Competição PR 2 error: {lbl}, {color}"
    # PR 3 (Ideal/Alvo: PR 3)
    lbl, color, app = classificar_perfil(4.5, "Pista de Competição")
    assert lbl == "Pista Firme 1 | ÓTIMO" and color == "#2e7d32", f"Competição PR 3 error: {lbl}, {color}"
    # PR 4 (Ótimo: 5.50 <= media <= 6.00)
    lbl, color, app = classificar_perfil(5.8, "Pista de Competição")
    assert lbl == "Pista Firme 2 | ÓTIMO" and color == "#2e7d32", f"Competição PR 4 error: {lbl}, {color}"
    # PR 5
    lbl, color, app = classificar_perfil(6.8, "Pista de Competição")
    assert lbl == "Pista Macia 1 | BOM" and color == "#c62828", f"Competição PR 5 error: {lbl}, {color}"
    # PR 6
    lbl, color, app = classificar_perfil(7.5, "Pista de Competição")
    assert lbl == "Pista Macia 2 | BOM" and color == "#c62828", f"Competição PR 6 error: {lbl}, {color}"
    # PR 7
    lbl, color, app = classificar_perfil(8.5, "Pista de Competição")
    assert lbl == "Pista Pesada | BOM" and color == "#c62828", f"Competição PR 7 error: {lbl}, {color}"


def test_pista_competicao():
    print("Testing Block 5: Pista de Competição alvos...")
    df = pd.DataFrame({
        "Linha": [1]*5,
        "Ponto": list(range(1, 6)),
        "1ª Queda": [3.5]*5,  # mean 3.5 -> IDEAL for Competição (3.0 to 4.0)
        "2ª Queda": [5.0]*5,  # mean 5.0 -> IDEAL for Competição (4.0 to 5.0)
        "3ª Queda": [5.5]*5,  # mean 5.5 -> IDEAL for Competição (5.0 to 6.0)
        "Umidade": [18.0]*5,
        "Espessura": [12]*5
    })
    meta = {
        "coletou_umidade": True,
        "coletou_espessura": True,
        "global_umi": 18.0,
        "global_esp": 12,
        "tipo_pista": "Pista de Competição"
    }
    stats = calcular_estatisticas(df, meta)
    assert stats["fases"][0]["status"] == "IDEAL", f"Impacto Status: {stats['fases'][0]['status']}"
    assert stats["fases"][1]["status"] == "IDEAL", f"Suporte Status: {stats['fases'][1]['status']}"
    assert stats["fases"][2]["status"] == "IDEAL", f"Tração Status: {stats['fases'][2]['status']}"
    assert stats["geral_status"] == "IDEAL", f"Overall Status: {stats['geral_status']}"

    # Test failure counts with value out of range for Competição (e.g. 4.5 in 1ª queda)
    df_fail = pd.DataFrame({
        "Linha": [1],
        "Ponto": [1],
        "1ª Queda": [4.5],  # 4.5 -> ALERTA for Competição (4.0 < med <= 5.0)
        "2ª Queda": [5.0],
        "3ª Queda": [5.5],
        "Umidade": [18.0],
        "Espessura": [12]
    })
    stats_fail = calcular_estatisticas(df_fail, meta)
    assert stats_fail["fases"][0]["status"] == "ALERTA", f"Impacto Status Fail: {stats_fail['fases'][0]['status']}"


def test_tracao_desvio_limite():
    print("Testing Block 6: Tração desvio limite (Treinamento)...")
    # Tração in Treinamento (Center 8.0, Target 7-9):
    # dev <= 1.0 (7.0 - 9.0): Excelente / Boa
    # dev <= 2.0 (6.0 - 10.0): Boa
    # dev <= 3.5 (4.5 - 11.5): Alerta
    # dev > 3.5 (< 4.5 or > 11.5): Crítica

    lbl, color = classificar_desvio_fase(8.5, "Tração", "Pista de Treinamento")
    assert lbl == "Excelente", f"Tração 8.5: {lbl}"

    lbl, color = classificar_desvio_fase(6.5, "Tração", "Pista de Treinamento")
    assert lbl == "Boa", f"Tração 6.5: {lbl}"

    lbl, color = classificar_desvio_fase(5.5, "Tração", "Pista de Treinamento")
    assert lbl == "Alerta", f"Tração 5.5: {lbl}"

    lbl, color = classificar_desvio_fase(11.0, "Tração", "Pista de Treinamento")
    assert lbl == "Alerta", f"Tração 11.0: {lbl}"

    lbl, color = classificar_desvio_fase(4.0, "Tração", "Pista de Treinamento")
    assert lbl == "Crítica", f"Tração 4.0: {lbl}"

    lbl, color = classificar_desvio_fase(12.0, "Tração", "Pista de Treinamento")
    assert lbl == "Crítica", f"Tração 12.0: {lbl}"


def main():
    test_risco_biomecanico()
    test_regularidade_cv()
    test_icg_dinamico()
    test_diagnostico_perfil()
    test_pista_competicao()
    test_tracao_desvio_limite()
    print("\nSUCCESS: All dashboard architecture logic and tests passed successfully!")

if __name__ == "__main__":
    main()
