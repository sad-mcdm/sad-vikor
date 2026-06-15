import numpy as np
from scipy.optimize import linprog

def calculate_geometric_mean_weights(matrix: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Local copy of Row Geometric Mean method for BWM intra-criteria evaluation,
    analogous to AHP alternative priority calculations.
    """
    n = matrix.shape[0]
    if n <= 2:
        weights = np.ones(n) / n
        return weights, 0.0
        
    geom_means = np.exp(np.mean(np.log(matrix), axis=1))
    weights = geom_means / np.sum(geom_means)
    
    # Simple principal eigenvalue CR calculation
    weighted_sum = np.dot(matrix, weights)
    eigenvalues = weighted_sum / weights
    lambda_max = np.mean(eigenvalues)
    ci = (lambda_max - n) / (n - 1)
    
    # Saaty Random Index
    ri_table = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
    ri = ri_table.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0
    return weights, float(cr)

def map_ratio_to_saaty(val_i, val_j, is_benefit=True):
    """
    Saaty ratio mapping for pre-filling BWM alternative comparisons.
    """
    if val_i == val_j:
        return 1.0
    if not is_benefit:
        val_i, val_j = val_j, val_i
    if val_j == 0:
        ratio = 9.0 if val_i > 0 else 1.0
    else:
        ratio = val_i / val_j
        
    if ratio < 1.0:
        inv_ratio = 1.0 / ratio
        score = map_ratio_to_score(inv_ratio)
        return 1.0 / score
    else:
        score = map_ratio_to_score(ratio)
        return float(score)

def map_ratio_to_score(ratio):
    if ratio <= 1.05: return 1
    if ratio <= 1.2: return 2
    if ratio >= 3.0: return 9
    score = 2 + (ratio - 1.2) * (7.0 / 1.8)
    return int(round(score))

def solve_bwm_weights_lp(
    n: int,
    best_idx: int,
    worst_idx: int,
    best_to_others: np.ndarray, # array of length n
    others_to_worst: np.ndarray # array of length n
) -> tuple[np.ndarray, float, bool]:
    """
    Solves the minimax Best-Worst Method (BWM) LP model to find criteria weights.
    Variables: [w_0, w_1, ..., w_{n-1}, xi]
    Objective: minimize xi (represented as x[-1])
    """
    # Variables: w_0, w_1, ..., w_{n-1}, xi (n + 1 variables)
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
    
    # Inequality constraints:
    # 1. |w_B - a_{Bj} * w_j| <= xi
    #    -> w_B - a_{Bj}*w_j - xi <= 0
    #    -> -w_B + a_{Bj}*w_j - xi <= 0
    # 2. |w_j - a_{jW} * w_W| <= xi
    #    -> w_j - a_{jW}*w_W - xi <= 0
    #    -> -w_j + a_{jW}*w_W - xi <= 0
    for j in range(n):
        a_Bj = float(best_to_others[j])
        a_jW = float(others_to_worst[j])
        
        if j != best_idx:
            # w_B - a_Bj * w_j - xi <= 0
            row1 = np.zeros(n + 1)
            row1[best_idx] = 1.0
            row1[j] = -a_Bj
            row1[-1] = -1.0
            A_ub.append(row1)
            b_ub.append(0.0)
            
            # -w_B + a_Bj * w_j - xi <= 0
            row2 = np.zeros(n + 1)
            row2[best_idx] = -1.0
            row2[j] = a_Bj
            row2[-1] = -1.0
            A_ub.append(row2)
            b_ub.append(0.0)
            
        if j != worst_idx:
            # w_j - a_jW * w_W - xi <= 0
            row3 = np.zeros(n + 1)
            row3[j] = 1.0
            row3[worst_idx] = -a_jW
            row3[-1] = -1.0
            A_ub.append(row3)
            b_ub.append(0.0)
            
            # -w_j + a_jW * w_W - xi <= 0
            row4 = np.zeros(n + 1)
            row4[j] = -1.0
            row4[worst_idx] = a_jW
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
        # Clean small negative values
        weights = np.clip(weights, 0.0, 1.0)
        weights = weights / np.sum(weights)
        return weights, float(xi), True
    else:
        # Fallback to equal weights
        return np.ones(n) / n, 0.0, False

def solve_bwm(
    matrix_data: list[list[float]],         # Consequence matrix (m x n)
    criteria_types: list[str],             # 'benefit' or 'cost' (length n)
    preference_data: dict,                 # {'best_idx': B, 'worst_idx': W, 'best_to_others': [...], 'others_to_worst': [...], 'alternatives_matrices': {crit_id: [[...]]}}
    criteria_ids: list[int],
    alternatives_ids: list[int]
) -> dict:
    m = len(alternatives_ids)
    n = len(criteria_ids)
    
    # 1. Elicit Criteria Weights (BWM LP)
    best_idx = int(preference_data.get('best_idx', 0))
    worst_idx = int(preference_data.get('worst_idx', n - 1))
    
    # BO and OW vectors
    best_to_others = np.array(preference_data.get('best_to_others', np.ones(n)), dtype=float)
    others_to_worst = np.array(preference_data.get('others_to_worst', np.ones(n)), dtype=float)
    
    crit_weights, xi, crit_success = solve_bwm_weights_lp(n, best_idx, worst_idx, best_to_others, others_to_worst)
    
    # 2. Elicit Alternative Priorities (BWM has SAME intra-criteria as AHP)
    norm_matrix = np.zeros((m, n))
    alt_crs = {}
    alt_matrices_pref = preference_data.get('alternatives_matrices', {})
    
    for j, cid in enumerate(criteria_ids):
        cid_str = str(cid)
        if cid_str in alt_matrices_pref:
            alt_matrix = np.array(alt_matrices_pref[cid_str], dtype=float)
        else:
            # Pre-fill AHP-style using ratio of consequences
            alt_matrix = np.ones((m, m))
            is_benefit = (criteria_types[j] == 'benefit')
            for r in range(m):
                val_r = matrix_data[r][j]
                for c in range(m):
                    val_c = matrix_data[c][j]
                    alt_matrix[r, c] = map_ratio_to_saaty(val_r, val_c, is_benefit)
                    
        # Enforce reciprocal
        for r in range(m):
            alt_matrix[r, r] = 1.0
            for c in range(r + 1, m):
                if alt_matrix[r, c] == 0:
                    alt_matrix[r, c] = 1.0
                alt_matrix[c, r] = 1.0 / alt_matrix[r, c]
                
        weights_alt, cr_alt = calculate_geometric_mean_weights(alt_matrix)
        norm_matrix[:, j] = weights_alt
        alt_crs[cid_str] = cr_alt
        
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
        'consistency_xi': xi,
        'alternatives_cr': alt_crs
    }
