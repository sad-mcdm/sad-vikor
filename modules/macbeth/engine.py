import numpy as np
from scipy.optimize import linprog

# Categories mapping to minimum ordinal step multipliers
MACBETH_DIFFS = {
    0: 0,  # Null / Nula
    1: 1,  # Very Weak / Muito Fraca
    2: 2,  # Weak / Fraca
    3: 3,  # Moderate / Moderada
    4: 4,  # Strong / Forte
    5: 5,  # Very Strong / Muito Forte
    6: 6   # Extreme / Extrema
}

def solve_macbeth_lp(comparison_matrix: np.ndarray) -> tuple[np.ndarray, bool]:
    """
    Solves the MACBETH linear programming model to find cardinal weights/scores.
    Inputs:
        comparison_matrix: n x n matrix where cell (i, j) is:
            - positive integer (1 to 6) if i is more preferred than j
            - negative integer (-1 to -6) if j is more preferred than i
            - 0 if i and j are equivalent
            - None/NaN if no comparison is made
    Returns:
        weights: normalized array of size n (sum = 1.0)
        success: boolean indicating if LP was feasible
    """
    n = comparison_matrix.shape[0]
    if n <= 1:
        return np.ones(n), True
        
    # Variables: s_0, s_1, ..., s_{n-1}, delta
    # Total n + 1 variables
    # We want to maximize delta, which is equivalent to minimizing -delta
    c = np.zeros(n + 1)
    c[-1] = -1.0  # -1 for delta
    
    A_ub = []
    b_ub = []
    A_eq = []
    b_eq = []
    
    # Anchors: let's anchor the worst element to 0 and the best to 1.
    # To identify best/worst, we count row preferences.
    # A simple way: find elements with highest and lowest net preferences.
    net_pref = np.zeros(n)
    for i in range(n):
        for j in range(n):
            val = comparison_matrix[i, j]
            if val is not None and not np.isnan(val):
                if val > 0:
                    net_pref[i] += 1
                    net_pref[j] -= 1
                elif val < 0:
                    net_pref[i] -= 1
                    net_pref[j] += 1
                    
    best_idx = np.argmax(net_pref)
    worst_idx = np.argmin(net_pref)
    
    # If best and worst are the same (degenerate), force different indices
    if best_idx == worst_idx:
        worst_idx = (best_idx + 1) % n
        
    # Eq constraints: s[best_idx] = 1, s[worst_idx] = 0
    row_best = np.zeros(n + 1)
    row_best[best_idx] = 1.0
    A_eq.append(row_best)
    b_eq.append(1.0)
    
    row_worst = np.zeros(n + 1)
    row_worst[worst_idx] = 1.0
    A_eq.append(row_worst)
    b_eq.append(0.0)
    
    # Inequality constraints from comparisons
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            val = comparison_matrix[i, j]
            if val is None or np.isnan(val):
                continue
                
            if val == 0:
                # Equivalent: s_i - s_j = 0
                row = np.zeros(n + 1)
                row[i] = 1.0
                row[j] = -1.0
                A_eq.append(row)
                b_eq.append(0.0)
            elif val > 0:
                # i is more preferred than j: s_i - s_j >= val * delta -> s_j - s_i + val*delta <= 0
                step = MACBETH_DIFFS.get(int(val), 1)
                row = np.zeros(n + 1)
                row[i] = -1.0
                row[j] = 1.0
                row[-1] = step
                A_ub.append(row)
                b_ub.append(0.0)
                
    # Bounds: s_i in [0, 1], delta >= 0.001
    bounds = [(0.0, 1.0) for _ in range(n)] + [(0.001, 10.0)]
    
    # Solve LP
    A_ub = np.array(A_ub) if A_ub else None
    b_ub = np.array(b_ub) if b_ub else None
    A_eq = np.array(A_eq) if A_eq else None
    b_eq = np.array(b_eq) if b_eq else None
    
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    
    if res.success:
        scores = res.x[:n]
        # In case of negative values due to floating point precision, clip to 0
        scores = np.clip(scores, 0.0, 1.0)
        # Normalize weights to sum to 1.0
        total = np.sum(scores)
        if total > 0:
            weights = scores / total
        else:
            weights = np.ones(n) / n
        return weights, True
    else:
        # If infeasible (due to inconsistent judgments), return equal weights or simple heuristic
        # A simple fallback: convert net_pref to normalized ranks
        scores = net_pref - np.min(net_pref)
        total = np.sum(scores)
        if total > 0:
            weights = scores / total
        else:
            weights = np.ones(n) / n
        return weights, False

def solve_macbeth(
    matrix_data: list[list[float]],         # Consequence matrix (m x n)
    criteria_types: list[str],             # 'benefit' or 'cost' (length n)
    preference_data: dict,                 # {'criteria_matrix': [[...]], 'levels_matrices': {crit_id: [[...]]}}
    criteria_ids: list[int],
    alternatives_ids: list[int]
) -> dict:
    m = len(alternatives_ids)
    n = len(criteria_ids)
    
    # 1. Elicit Criteria Weights
    crit_matrix = np.array(preference_data.get('criteria_matrix', np.ones((n, n))), dtype=float)
    crit_weights, crit_success = solve_macbeth_lp(crit_matrix)
    
    # 2. Elicit Alternative Value Functions
    # For each criterion, we construct 5 reference levels spanning min to max consequence
    # and use the user's qualitative comparisons of these levels.
    norm_matrix = np.zeros((m, n))
    levels_success = {}
    
    levels_matrices_pref = preference_data.get('levels_matrices', {})
    
    for j, cid in enumerate(criteria_ids):
        cid_str = str(cid)
        col = [row[j] for row in matrix_data]
        col_min = min(col)
        col_max = max(col)
        
        # Define 5 reference levels
        levels = np.linspace(col_min, col_max, 5)
        
        # Get levels matrix
        if cid_str in levels_matrices_pref:
            levels_matrix = np.array(levels_matrices_pref[cid_str], dtype=float)
            # Solve LP for levels to get their cardianl scores [v(L_0), ..., v(L_4)]
            # Note: We want to make sure the scores are sorted according to criterion type (benefit vs cost)
            level_weights, success = solve_macbeth_lp(levels_matrix)
            levels_success[cid_str] = success
            
            # Macbeth returns normalized weights, but we need scores in [0, 1] scale
            # We scale level priorities such that the worst level is 0.0 and best level is 1.0
            # To reconstruct scores, solve LP again but just return the raw x[:5] from solve_macbeth_lp:
            # We can re-extract it from level_weights * n (approx) or by adjusting our solver
        else:
            # Default to linear scale
            level_weights = np.linspace(0, 1, 5) if criteria_types[j] == 'benefit' else np.linspace(1, 0, 5)
            levels_success[cid_str] = True
            
        # Re-solve levels explicitly to get scale values s in [0, 1]
        # Let's write a small helper to get the scores directly
        scores_levels = get_macbeth_scores(levels_matrix if cid_str in levels_matrices_pref else None, 5, criteria_types[j] == 'benefit')
        
        # Interpolate alternative values based on their consequence values
        for r in range(m):
            val = matrix_data[r][j]
            # Interpolate val among levels to get alternative value
            if col_max == col_min:
                norm_matrix[r, j] = 1.0
            else:
                norm_matrix[r, j] = float(np.interp(val, levels, scores_levels))
                
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
        'levels_success': levels_success
    }

def get_macbeth_scores(matrix: np.ndarray, n: int, is_benefit: bool) -> np.ndarray:
    """Helper to solve Macbeth and get raw scale scores in [0, 1] instead of normalized weights"""
    if matrix is None:
        return np.linspace(0, 1, n) if is_benefit else np.linspace(1, 0, n)
        
    c = np.zeros(n + 1)
    c[-1] = -1.0  # maximize delta
    
    A_ub = []
    b_ub = []
    A_eq = []
    b_eq = []
    
    # For scale levels, we know the natural ordering: L_0 < L_1 < L_2 < L_3 < L_4 (for benefit)
    # L_0 is worst, L_4 is best
    worst_idx = 0 if is_benefit else n - 1
    best_idx = n - 1 if is_benefit else 0
    
    row_best = np.zeros(n + 1)
    row_best[best_idx] = 1.0
    A_eq.append(row_best)
    b_eq.append(1.0)
    
    row_worst = np.zeros(n + 1)
    row_worst[worst_idx] = 1.0
    A_eq.append(row_worst)
    b_eq.append(0.0)
    
    for i in range(n):
        for j in range(n):
            if i == j: continue
            val = matrix[i, j]
            if val is None or np.isnan(val): continue
            
            if val == 0:
                row = np.zeros(n + 1)
                row[i] = 1.0
                row[j] = -1.0
                A_eq.append(row)
                b_eq.append(0.0)
            elif val > 0:
                step = MACBETH_DIFFS.get(int(val), 1)
                row = np.zeros(n + 1)
                row[i] = -1.0
                row[j] = 1.0
                row[-1] = step
                A_ub.append(row)
                b_ub.append(0.0)
                
    bounds = [(0.0, 1.0) for _ in range(n)] + [(0.001, 10.0)]
    
    A_ub = np.array(A_ub) if A_ub else None
    b_ub = np.array(b_ub) if b_ub else None
    A_eq = np.array(A_eq) if A_eq else None
    b_eq = np.array(b_eq) if b_eq else None
    
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    
    if res.success:
        scores = res.x[:n]
        return np.clip(scores, 0.0, 1.0)
    else:
        # Fallback to linear scale
        return np.linspace(0, 1, n) if is_benefit else np.linspace(1, 0, n)
