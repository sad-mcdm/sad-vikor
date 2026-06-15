import numpy as np

# Saaty's Random Index (RI)
RANDOM_INDEX = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49
}

def map_ratio_to_saaty(val_i, val_j, is_benefit=True):
    """
    Intelligent helper to map consequences ratio to Saaty's 1-9 scale.
    Used to pre-fill pairwise comparison matrix of alternatives.
    """
    if val_i == val_j:
        return 1.0
        
    if not is_benefit:
        val_i, val_j = val_j, val_i
        
    # Prevent divide by zero
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
    # Linear interpolation between 1.2 and 3.0
    score = 2 + (ratio - 1.2) * (7.0 / 1.8)
    return int(round(score))

def calculate_geometric_mean_weights(matrix: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Calculates weights using the Row Geometric Mean method (RGM), which is
    highly robust and mathematically sound for AHP.
    Also returns the Consistency Ratio (CR).
    """
    n = matrix.shape[0]
    if n <= 2:
        weights = np.ones(n) / n
        return weights, 0.0
        
    # 1. Row geometric means
    geom_means = np.exp(np.mean(np.log(matrix), axis=1))
    
    # 2. Normalize weights
    weights = geom_means / np.sum(geom_means)
    
    # 3. Calculate Consistency Ratio (CR)
    # Principal eigenvalue lambda_max
    weighted_sum = np.dot(matrix, weights)
    eigenvalues = weighted_sum / weights
    lambda_max = np.mean(eigenvalues)
    
    # Consistency Index (CI)
    ci = (lambda_max - n) / (n - 1)
    
    # Consistency Ratio (CR)
    ri = RANDOM_INDEX.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0
    
    return weights, float(cr)

def solve_ahp(
    matrix_data: list[list[float]],         # Consequence matrix (m x n)
    criteria_types: list[str],             # 'benefit' or 'cost' (length n)
    preference_data: dict,                 # {'criteria_matrix': [[...]], 'alternatives_matrices': {crit_id: [[...]]}}
    criteria_ids: list[int],
    alternatives_ids: list[int]
) -> dict:
    """
    Solves AHP multicriteria decision problem.
    """
    m = len(alternatives_ids)
    n = len(criteria_ids)
    
    # 1. Elicit Criteria Weights
    crit_matrix = np.array(preference_data.get('criteria_matrix', np.ones((n, n))), dtype=float)
    # Ensure reciprocal property is enforced
    for i in range(n):
        crit_matrix[i, i] = 1.0
        for j in range(i + 1, n):
            if crit_matrix[i, j] == 0:
                crit_matrix[i, j] = 1.0
            crit_matrix[j, i] = 1.0 / crit_matrix[i, j]
            
    crit_weights, crit_cr = calculate_geometric_mean_weights(crit_matrix)
    
    # 2. Elicit Alternative Priorities for each criterion
    # norm_matrix stores alternative priorities, shape: m x n
    norm_matrix = np.zeros((m, n))
    alt_crs = {}
    
    # Retrieve alternative matrices
    alt_matrices_pref = preference_data.get('alternatives_matrices', {})
    
    for j, cid in enumerate(criteria_ids):
        # Check if user has a custom pairwise matrix for this criterion
        cid_str = str(cid)
        if cid_str in alt_matrices_pref:
            alt_matrix = np.array(alt_matrices_pref[cid_str], dtype=float)
        else:
            # If not provided, pre-fill based on consequence values ratio
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

    # 3. Compute global score: V(a_i) = Sum_j w_j * v_j(a_i)
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
        'criteria_cr': crit_cr,
        'alternatives_cr': alt_crs
    }
