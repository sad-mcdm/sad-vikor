import numpy as np
import math

# Import solvers directly from packages
from modules.smarts_smarter.engine import calculate_roc_weights, normalize_linear, solve_smarts_smarter
from modules.ahp.engine import calculate_geometric_mean_weights, solve_ahp
from modules.macbeth.engine import solve_macbeth_lp, get_macbeth_scores, solve_macbeth
from modules.bwm.engine import solve_bwm_weights_lp, solve_bwm
from modules.bwt.engine import solve_bwt_weights_lp, interpolate_bisection, solve_bwt
from modules.topsis.engine import solve_topsis
from modules.vikor.engine import solve_vikor
from modules.electre.engine import solve_electre
from modules.promethee.engine import solve_promethee
from services.monte_carlo import run_monte_carlo

def test_smarter_weights():
    print("Testing SMARTER weights...")
    weights = calculate_roc_weights(3)
    assert len(weights) == 3
    # w_1 = (1/3)*(1 + 1/2 + 1/3) = (1/3)*(11/6) = 11/18 = 0.6111
    # w_2 = (1/3)*(1/2 + 1/3) = (1/3)*(5/6) = 5/18 = 0.2777
    # w_3 = (1/3)*(1/3) = 1/9 = 2/18 = 0.1111
    assert math.isclose(weights[0], 11/18, rel_tol=1e-4)
    assert math.isclose(weights[1], 5/18, rel_tol=1e-4)
    assert math.isclose(weights[2], 2/18, rel_tol=1e-4)
    print("SMARTER weights: Success!")

def test_linear_normalization():
    print("Testing linear normalization...")
    matrix = np.array([
        [10.0, 100.0],
        [20.0, 50.0],
        [30.0, 0.0]
    ])
    types = ['benefit', 'cost']
    norm = normalize_linear(matrix, types)
    
    # Benefit column: min=10, max=30, range=20
    # norm = [[0, 1], [0.5, 0.5], [1, 0]]
    # Cost column: min=0, max=100, range=100
    # norm = [[0, 0], [0.5, 0.5], [1, 1]]
    assert math.isclose(norm[0, 0], 0.0)
    assert math.isclose(norm[1, 0], 0.5)
    assert math.isclose(norm[2, 0], 1.0)
    assert math.isclose(norm[0, 1], 0.0)
    assert math.isclose(norm[1, 1], 0.5)
    assert math.isclose(norm[2, 1], 1.0)
    print("Linear normalization: Success!")

def test_ahp_weights():
    print("Testing AHP weights...")
    # Consistent 3x3 comparison matrix
    # C1 over C2: 3, C1 over C3: 9, C2 over C3: 3
    matrix = np.array([
        [1.0, 3.0, 9.0],
        [1/3, 1.0, 3.0],
        [1/9, 1/3, 1.0]
    ])
    weights, cr = calculate_geometric_mean_weights(matrix)
    # Weights should be normalized geometric mean
    # Row 1 product = 27 -> GM = 3
    # Row 2 product = 1 -> GM = 1
    # Row 3 product = 1/27 -> GM = 1/3
    # Sum = 4.3333
    # w_1 = 3 / 4.333 = 9/13 = 0.6923
    # w_2 = 1 / 4.333 = 3/13 = 0.2307
    # w_3 = 0.333 / 4.333 = 1/13 = 0.0769
    assert math.isclose(weights[0], 9/13, rel_tol=1e-4)
    assert math.isclose(weights[1], 3/13, rel_tol=1e-4)
    assert math.isclose(weights[2], 1/13, rel_tol=1e-4)
    assert cr < 0.01  # Perfectly consistent matrix has CR close to 0
    print("AHP weights: Success!")

def test_bwm_weights():
    print("Testing BWM weights solver...")
    # 3 criteria: Best is C0, Worst is C2
    # Best-to-Others (BO): [1, 3, 9] (Best is C0, it is 3x more important than C1, 9x than C2)
    # Others-to-Worst (OW): [9, 3, 1] (C0 is 9x than C2, C1 is 3x than C2, C2 is 1x than C2)
    best_to_others = np.array([1, 3, 9])
    others_to_worst = np.array([9, 3, 1])
    weights, xi, success = solve_bwm_weights_lp(3, 0, 2, best_to_others, others_to_worst)
    
    assert success
    # Expected: w_0 = 9/13, w_1 = 3/13, w_2 = 1/13
    assert math.isclose(weights[0], 9/13, rel_tol=1e-3)
    assert math.isclose(weights[1], 3/13, rel_tol=1e-3)
    assert math.isclose(weights[2], 1/13, rel_tol=1e-3)
    assert xi < 1e-4
    print("BWM weights: Success!")

def test_bwt_bisection():
    print("Testing BWT bisection value function...")
    # Min = 10, Max = 30, Midpoint (x_05) = 15
    # If benefit:
    # v(10) = 0.0, v(15) = 0.5, v(30) = 1.0
    # v(12.5) = 0.25 (linear midpoint between 10 and 15)
    # v(22.5) = 0.75 (linear midpoint between 15 and 30)
    v1 = interpolate_bisection(10.0, 10.0, 30.0, 15.0, True)
    v2 = interpolate_bisection(12.5, 10.0, 30.0, 15.0, True)
    v3 = interpolate_bisection(15.0, 10.0, 30.0, 15.0, True)
    v4 = interpolate_bisection(22.5, 10.0, 30.0, 15.0, True)
    v5 = interpolate_bisection(30.0, 10.0, 30.0, 15.0, True)
    
    assert math.isclose(v1, 0.0)
    assert math.isclose(v2, 0.25)
    assert math.isclose(v3, 0.5)
    assert math.isclose(v4, 0.75)
    assert math.isclose(v5, 1.0)
    print("BWT bisection: Success!")

def test_macbeth_lp():
    print("Testing MACBETH LP solver...")
    # 3 criteria: C0 > C1 > C2
    # C0 vs C1: 3 (Moderate), C1 vs C2: 2 (Weak)
    # C0 vs C2: 5 (Very Strong)
    matrix = np.array([
        [0.0, 3.0, 5.0],
        [-3.0, 0.0, 2.0],
        [-5.0, -2.0, 0.0]
    ])
    weights, success = solve_macbeth_lp(matrix)
    assert success
    assert weights[0] > weights[1] > weights[2]
    print("MACBETH solver: Success!")

if __name__ == "__main__":
    print("Running solver mathematical test suite...")
    test_smarter_weights()
    test_linear_normalization()
    test_ahp_weights()
    test_bwm_weights()
    test_bwt_bisection()
    test_macbeth_lp()
    
    # New solver tests
    def test_topsis():
        print("Testing TOPSIS solver...")
        matrix = [[10.0, 100.0], [20.0, 50.0], [30.0, 0.0]]
        types = ['benefit', 'cost']
        pref = {'weights': {'1': 10.0, '2': 10.0}}
        res = solve_topsis(matrix, types, pref, [1, 2], [1, 2, 3])
        assert res['ranks'][2] == 1
        assert res['ranks'][0] == 3
        print("TOPSIS solver: Success!")
        
    def test_vikor():
        print("Testing VIKOR solver...")
        matrix = [[10.0, 100.0], [20.0, 50.0], [30.0, 0.0]]
        types = ['benefit', 'cost']
        pref = {'weights': {'1': 10.0, '2': 10.0}, 'v': 0.5}
        res = solve_vikor(matrix, types, pref, [1, 2], [1, 2, 3])
        assert res['ranks'][2] == 1
        assert res['ranks'][0] == 3
        print("VIKOR solver: Success!")
        
    def test_electre():
        print("Testing ELECTRE solvers...")
        matrix = [[10.0, 100.0], [20.0, 50.0], [30.0, 0.0]]
        types = ['benefit', 'cost']
        pref = {'weights': {'1': 10.0, '2': 10.0}, 'electre_version': 'I', 'concordance_threshold': 0.5, 'discordance_threshold': 0.5}
        res = solve_electre(matrix, types, pref, [1, 2], [1, 2, 3])
        assert 'kernel' in res['extra']
        print("ELECTRE solvers: Success!")
        
    def test_promethee():
        print("Testing PROMETHEE solvers...")
        matrix = [[10.0, 100.0], [20.0, 50.0], [30.0, 0.0]]
        types = ['benefit', 'cost']
        pref = {'weights': {'1': 10.0, '2': 10.0}, 'promethee_version': 'II'}
        res = solve_promethee(matrix, types, pref, [1, 2], [1, 2, 3])
        assert res['ranks'][2] == 1
        assert res['ranks'][0] == 3
        print("PROMETHEE solvers: Success!")
        
    test_topsis()
    test_vikor()
    test_electre()
    test_promethee()
    
    print("All solver tests passed successfully!")
