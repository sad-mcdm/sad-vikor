import numpy as np

def solve_topsis(
    matrix_data: list[list[float]],
    criteria_types: list[str],
    preference_data: dict,  # {'weights': {crit_id: score}}
    criteria_ids: list[int],
    alternatives_ids: list[int]
) -> dict:
    """
    Solves TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution).
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
        
    # 2. Vector Normalization
    # r_ij = x_ij / sqrt(sum_k x_kj^2)
    norm_matrix = np.zeros_like(matrix, dtype=float)
    for j in range(n):
        col = matrix[:, j]
        norm_factor = np.sqrt(np.sum(col ** 2))
        if norm_factor == 0:
            norm_factor = 1.0
        norm_matrix[:, j] = col / norm_factor
        
    # 3. Weighted Normalized Matrix
    weighted_matrix = norm_matrix * weights
    
    # 4. Determine Ideal and Anti-Ideal Solutions
    ideal_positive = np.zeros(n)
    ideal_negative = np.zeros(n)
    for j in range(n):
        col = weighted_matrix[:, j]
        if criteria_types[j] == 'benefit':
            ideal_positive[j] = np.max(col)
            ideal_negative[j] = np.min(col)
        else:
            ideal_positive[j] = np.min(col)
            ideal_negative[j] = np.max(col)
            
    # 5. Calculate Euclidean Distances
    distance_positive = np.zeros(m)
    distance_negative = np.zeros(m)
    for i in range(m):
        row = weighted_matrix[i, :]
        distance_positive[i] = np.sqrt(np.sum((row - ideal_positive) ** 2))
        distance_negative[i] = np.sqrt(np.sum((row - ideal_negative) ** 2))
        
    # 6. Calculate Closeness Coefficient
    # C_i = S_i^- / (S_i^+ + S_i^-)
    closeness = np.zeros(m)
    for i in range(m):
        denom = distance_positive[i] + distance_negative[i]
        if denom == 0:
            closeness[i] = 0.5
        else:
            closeness[i] = distance_negative[i] / denom
            
    # 7. Rank alternatives (descending order of closeness)
    sorted_indices = np.argsort(-closeness)
    ranks = np.zeros(m, dtype=int)
    for rank_pos, idx in enumerate(sorted_indices):
        ranks[idx] = rank_pos + 1
        
    return {
        'weights': weights.tolist(),
        'normalized_matrix': norm_matrix.tolist(),  # Return normalized matrix for viewing
        'global_scores': closeness.tolist(),
        'ranks': ranks.tolist(),
        'distance_positive': distance_positive.tolist(),
        'distance_negative': distance_negative.tolist()
    }
