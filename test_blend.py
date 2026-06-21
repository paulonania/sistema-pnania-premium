import sys
import os

# Import the blend engine
from blend_engine import calcular_afs, calcular_mistura, otimizar_proporcoes, dimensionar_insumos

def test_calcular_afs():
    print("Testing AFS calculation...")
    
    # Test with Itarena 3 data from sheet
    # Sieve values:
    itarena_3 = {
        "#10": 0.26,
        "#14": 2.03,
        "#18": 2.14,
        "#35": 12.22,
        "#40": 16.72,
        "#60": 23.95,
        "#100": 28.17,
        "#140": 7.31,
        "#200": 4.42,
        "#270": 1.87,
        "Finos": 0.90
    }
    
    afs_val = calcular_afs(itarena_3)
    # Expected is around 59.4
    print(f"Itarena 3 calculated AFS: {afs_val:.4f} (Expected: ~59.42)")
    assert abs(afs_val - 59.4186) < 0.01, f"AFS value mismatch: {afs_val}"
    
    # Test empty values
    assert calcular_afs({}) == 0.0
    print("calcular_afs tests passed successfully!")


def test_calcular_mistura():
    print("Testing blend mixing...")
    
    sand_a = {"#10": 10.0, "#60": 20.0, "Finos": 5.0}
    sand_b = {"#10": 0.0, "#60": 40.0, "Finos": 15.0}
    
    # 50/50 mix
    blend = calcular_mistura([sand_a, sand_b], [50.0, 50.0])
    assert blend["#10"] == 5.0
    assert blend["#60"] == 30.0
    assert blend["Finos"] == 10.0
    print("calcular_mistura tests passed successfully!")


def test_otimizar_proporcoes():
    print("Testing optimizer...")
    
    # If we optimize one sand, it should return 100%
    assert otimizar_proporcoes([{"#10": 1.0}], "Hipismo (Imagens)") == [100.0]
    
    # Let's test with a simulated two sands optimization
    # Sand A is very coarse, Sand B is very fine
    sand_a = {"#10": 100.0, "#35": 0.0, "#60": 0.0, "#100": 0.0, "#140": 0.0, "#200": 0.0, "#270": 0.0, "Finos": 0.0}
    sand_b = {"#10": 0.0, "#35": 0.0, "#60": 0.0, "#100": 100.0, "#140": 0.0, "#200": 0.0, "#270": 0.0, "Finos": 0.0}
    
    # Target range for #10 is 0-2% (mean 1%). Target for #100 is 25-35% (mean 30%).
    # The optimizer should give high proportion to Sand B and low to Sand A to match target.
    proportions = otimizar_proporcoes([sand_a, sand_b], "Hipismo (Imagens)")
    print(f"Optimized proportions for [Sand A (coarse), Sand B (fine)]: {proportions}")
    assert proportions[0] < proportions[1], "Sand B (fine) should have a higher proportion to match target range"
    assert abs(sum(proportions) - 100.0) < 0.1, f"Proportions must sum to 100%, got: {sum(proportions)}"
    print("otimizar_proporcoes tests passed successfully!")


def test_dimensionar_insumos():
    print("Testing material calculation...")
    
    # Dimensions: 30x60m, Thickness: 10cm, Density: 1.6 t/m3, Fiber: 0.3% of sand mass
    res_a = dimensionar_insumos(60.0, 30.0, 10.0, 1.6, "A", 0.3)
    assert res_a["area"] == 1800.0
    assert res_a["volume"] == 180.0
    assert res_a["sand_mass"] == 288.0
    assert res_a["fiber_mass"] == 0.864 # 288 * 0.003
    
    # Fiber: 3.0 kg/m2
    res_b = dimensionar_insumos(60.0, 30.0, 10.0, 1.6, "B", 3.0)
    assert res_b["fiber_mass"] == 5.4 # 1800 * 3 / 1000
    
    print("dimensionar_insumos tests passed successfully!")


if __name__ == "__main__":
    test_calcular_afs()
    test_calcular_mistura()
    test_otimizar_proporcoes()
    test_dimensionar_insumos()
    print("ALL TESTS PASSED SUCCESSFULLY!")
