import numpy as np
from scipy.optimize import linprog

def interpolate_bisection(val: float, col_min: float, col_max: float, x_05: float, is_benefit: bool) -> float:
    """
    Interpolates a value using the bisection method (piecewise linear value function).
    x_05 represents the value where the utility is 0.5.
    """
    if col_max == col_min:
        return 1.0
        
    # Safeguard bounds to prevent divide-by-zero
    x_05 = max(col_min + 1e-9, min(col_max - 1e-9, x_05))
    
    # Clip val to range [col_min, col_max]
    val = max(col_min, min(col_max, val))
    
    if is_benefit:
        if val <= x_05:
            # Linear segment from col_min (utility 0) to x_05 (utility 0.5)
            denom = x_05 - col_min
            return 0.5 * (val - col_min) / denom
        else:
            # Linear segment from x_05 (utility 0.5) to col_max (utility 1.0)
            denom = col_max - x_05
            return 0.5 + 0.5 * (val - x_05) / denom
    else:
        # Cost criterion (utility 1.0 at col_min, 0.0 at col_max, 0.5 at x_05)
        if val <= x_05:
            # Linear segment from col_min (utility 1.0) to x_05 (utility 0.5)
            denom = x_05 - col_min
            return 1.0 - 0.5 * (val - col_min) / denom
        else:
            # Linear segment from x_05 (utility 0.5) to col_max (utility 0.0)
            denom = col_max - x_05
            return 0.5 * (col_max - val) / denom

def solve_bwt_weights_lp(
    n: int,
    best_idx: int,
    worst_idx: int,
    best_to_others: np.ndarray, # array of floats
    others_to_worst: np.ndarray # array of floats
) -> tuple[np.ndarray, float, bool]:
    """
    Solves BWT minimax LP to find criteria weights.
    It has the same optimization structure as BWM, but uses float tradeoffs.
    """
    c = np.zeros(n + 1)
    c[-1] = 1.0  # minimize xi
    
    A_ub = []
    b_ub = []
    
    # Bounds: w_i in [0, 1], xi >= 0
    bounds = [(0.0, 1.0) for _ in range(n)] + [(0.0, 10.0)]
    
    # Eq constraints: Sum w_i = 1
    A_eq = [np.zeros(n + 1)]
    A_eq[0][:n] = 1.0
    b_eq = [1.0]
    
    for j in range(n):
        t_Bj = float(best_to_others[j])
        t_jW = float(others_to_worst[j])
        
        if j != best_idx:
            # w_B - t_Bj * w_j - xi <= 0
            row1 = np.zeros(n + 1)
            row1[best_idx] = 1.0
            row1[j] = -t_Bj
            row1[-1] = -1.0
            A_ub.append(row1)
            b_ub.append(0.0)
            
            # -w_B + t_Bj * w_j - xi <= 0
            row2 = np.zeros(n + 1)
            row2[best_idx] = -1.0
            row2[j] = t_Bj
            row2[-1] = -1.0
            A_ub.append(row2)
            b_ub.append(0.0)
            
        if j != worst_idx:
            # w_j - t_jW * w_W - xi <= 0
            row3 = np.zeros(n + 1)
            row3[j] = 1.0
            row3[worst_idx] = -t_jW
            row3[-1] = -1.0
            A_ub.append(row3)
            b_ub.append(0.0)
            
            # -w_j + t_jW * w_W - xi <= 0
            row4 = np.zeros(n + 1)
            row4[j] = -1.0
            row4[worst_idx] = t_jW
            row4[-1] = -1.0
            A_ub.append(row4)
            b_ub.append(0.0)
        
    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)
    A_eq = np.array(A_eq)
    b_eq = np.array(b_eq)
    
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    
    if res.success:
        weights = res.x[:n]
        xi = res.x[-1]
        weights = np.clip(weights, 0.0, 1.0)
        weights = weights / np.sum(weights)
        return weights, float(xi), True
    else:
        return np.ones(n) / n, 0.0, False

def solve_bwt(
    matrix_data: list[list[float]],         # Consequence matrix (m x n)
    criteria_types: list[str],             # 'benefit' or 'cost' (length n)
    preference_data: dict,                 # {'best_idx': B, 'worst_idx': W, 'best_to_others': [...], 'others_to_worst': [...], 'bisection_midpoints': {crit_id: float}}
    criteria_ids: list[int],
    alternatives_ids: list[int]
) -> dict:
    m = len(alternatives_ids)
    n = len(criteria_ids)
    
    # 1. Elicit Criteria Weights (BWT LP)
    best_idx = int(preference_data.get('best_idx', 0))
    worst_idx = int(preference_data.get('worst_idx', n - 1))
    
    best_to_others = np.array(preference_data.get('best_to_others', np.ones(n)), dtype=float)
    others_to_worst = np.array(preference_data.get('others_to_worst', np.ones(n)), dtype=float)
    
    crit_weights, xi, crit_success = solve_bwt_weights_lp(n, best_idx, worst_idx, best_to_others, others_to_worst)
    
    # 2. Elicit Alternative Value Functions (BWT Bisection Method)
    norm_matrix = np.zeros((m, n))
    bisection_midpoints = preference_data.get('bisection_midpoints', {})
    
    for j, cid in enumerate(criteria_ids):
        cid_str = str(cid)
        col = [row[j] for row in matrix_data]
        col_min = min(col)
        col_max = max(col)
        
        # User defined midpoint, defaults to arithmetic mean (linear)
        default_mid = (col_min + col_max) / 2.0
        x_05 = float(bisection_midpoints.get(cid_str, default_mid))
        
        is_benefit = (criteria_types[j] == 'benefit')
        
        for r in range(m):
            val = matrix_data[r][j]
            norm_matrix[r, j] = interpolate_bisection(val, col_min, col_max, x_05, is_benefit)
            
    # 3. Global values
    global_scores = np.dot(norm_matrix, crit_weights)
    
    # 4. Ranks
    sorted_indices = np.argsort(-global_scores)
    ranks = np.zeros(m, dtype=int)
    for rank_pos, idx in enumerate(sorted_indices):
        ranks[idx] = rank_pos + 1
        
    return {
        'weights': crit_weights.tolist(),
        'normalized_matrix': norm_matrix.tolist(),
        'global_scores': global_scores.tolist(),
        'ranks': ranks.tolist(),
        'criteria_success': crit_success,
        'consistency_xi': xi
    }
