import numpy as np

def solve_vikor(
    matrix_data: list[list[float]],
    criteria_types: list[str],
    preference_data: dict,  # {'weights': {crit_id: score}, 'v': float}
    criteria_ids: list[int],
    alternatives_ids: list[int]
) -> dict:
    """
    Solves VIKOR (Multicriteria Optimization and Compromise Solution).
    """
    matrix = np.array(matrix_data, dtype=float)
    m, n = matrix.shape
    
    # 1. Elicit and normalize weights
    weights = np.zeros(n)
    scores = preference_data.get('weights', {})
    total_score = 0.0
    for i, cid in enumerate(criteria_ids):
        score = float(scores.get(str(cid), 10.0))
        weights[i] = score
        total_score += score
        
    if total_score > 0:
        weights = weights / total_score
    else:
        weights = np.ones(n) / n
        
    # 2. Get v (majority of criteria weight, defaults to 0.5)
    v = float(preference_data.get('v', 0.5))
    
    # 3. Determine Best (f*) and Worst (f-) values for each criterion
    f_star = np.zeros(n)
    f_minus = np.zeros(n)
    for j in range(n):
        col = matrix[:, j]
        if criteria_types[j] == 'benefit':
            f_star[j] = np.max(col)
            f_minus[j] = np.min(col)
        else:
            f_star[j] = np.min(col)
            f_minus[j] = np.max(col)
            
    # 4. Calculate S_i (Utility) and R_i (Regret)
    S = np.zeros(m)
    R = np.zeros(m)
    for i in range(m):
        terms = []
        for j in range(n):
            denom = f_star[j] - f_minus[j]
            if denom == 0:
                term = 0.0
            else:
                term = weights[j] * (f_star[j] - matrix[i, j]) / denom
            terms.append(term)
        S[i] = np.sum(terms)
        R[i] = np.max(terms)
        
    # 5. Calculate Q_i
    S_star, S_minus = np.min(S), np.max(S)
    R_star, R_minus = np.min(R), np.max(R)
    
    Q = np.zeros(m)
    for i in range(m):
        s_term = 0.0
        if S_minus - S_star > 0:
            s_term = (S[i] - S_star) / (S_minus - S_star)
            
        r_term = 0.0
        if R_minus - R_star > 0:
            r_term = (R[i] - R_star) / (R_minus - R_star)
            
        Q[i] = v * s_term + (1 - v) * r_term
        
    # 6. Rank alternatives (ascending order of Q, smaller is better)
    sorted_indices = np.argsort(Q)
    ranks = np.zeros(m, dtype=int)
    for rank_pos, idx in enumerate(sorted_indices):
        ranks[idx] = rank_pos + 1
        
    # 7. Normalization for results viewing (Utility matrix representation)
    norm_matrix = np.zeros_like(matrix)
    for j in range(n):
        denom = f_star[j] - f_minus[j]
        if denom == 0:
            norm_matrix[:, j] = 1.0
        else:
            if criteria_types[j] == 'benefit':
                norm_matrix[:, j] = (matrix[:, j] - f_minus[j]) / denom
            else:
                norm_matrix[:, j] = (f_minus[j] - matrix[:, j]) / denom
                
    return {
        'weights': weights.tolist(),
        'normalized_matrix': norm_matrix.tolist(),
        'global_scores': Q.tolist(),  # The compromise index Q is the global score (smaller is better, we will handle in frontend)
        'ranks': ranks.tolist(),
        'S': S.tolist(),
        'R': R.tolist(),
        'v': v
    }
