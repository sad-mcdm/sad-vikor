import numpy as np

def calculate_roc_weights(n: int) -> list[float]:
    """
    Computes ROC (Rank-Order Centroid) weights for n criteria.
    Formula: w_i = (1/n) * sum_{j=i}^{n} (1/j)
    """
    if n <= 0:
        return []
    weights = []
    for i in range(1, n + 1):
        w_i = (1.0 / n) * sum(1.0 / j for j in range(i, n + 1))
        weights.append(w_i)
    return weights

def normalize_linear(matrix: np.ndarray, criteria_types: list[str]) -> np.ndarray:
    """
    Normalizes consequence matrix using standard linear value functions.
    For benefit: (x - x_min) / (x_max - x_min)
    For cost: (x_max - x) / (x_max - x_min)
    """
    m, n = matrix.shape
    norm_matrix = np.zeros_like(matrix, dtype=float)
    
    for j in range(n):
        col = matrix[:, j]
        col_max = np.max(col)
        col_min = np.min(col)
        denom = col_max - col_min
        if denom == 0:
            denom = 1.0  # Avoid division by zero, all values get same utility
            
        if criteria_types[j] == 'benefit':
            norm_matrix[:, j] = (col - col_min) / denom
        else:
            norm_matrix[:, j] = (col_max - col) / denom
            
    return norm_matrix

def solve_smarts_smarter(
    matrix_data: list[list[float]],
    criteria_types: list[str],
    preference_data: dict,  # For smarts: {'weights': {crit_id: score}}, for smarter: {'ranks': [crit_ids_ordered]}
    criteria_ids: list[int],
    method: str
) -> dict:
    """
    Calculates final scores and weights for SMARTS or SMARTER.
    """
    matrix = np.array(matrix_data, dtype=float)
    m, n = matrix.shape
    
    # 1. Calculate weights
    weights = np.zeros(n)
    if method == 'smarts':
        # SMARTS: Direct weights (scores) normalized to sum to 1.0
        scores = preference_data.get('weights', {})
        total_score = 0.0
        for i, cid in enumerate(criteria_ids):
            score = float(scores.get(str(cid), 10.0))  # Default score 10 if missing
            weights[i] = score
            total_score += score
            
        if total_score > 0:
            weights = weights / total_score
        else:
            weights = np.ones(n) / n
            
    elif method == 'smarter':
        # SMARTER: ROC weights based on rank order
        # preference_data['ranks'] contains list of criteria IDs in descending order of importance
        ranks_order = preference_data.get('ranks', [])
        roc_w = calculate_roc_weights(n)
        
        # Map criteria IDs to their ranks
        for i, cid in enumerate(criteria_ids):
            try:
                # Find rank position (0-indexed, where 0 is most important)
                rank_idx = ranks_order.index(cid)
            except ValueError:
                # If not found, put it at the end
                rank_idx = n - 1
            weights[i] = roc_w[rank_idx]
            
    else:
        # Fallback to equal weights
        weights = np.ones(n) / n

    # 2. Normalize consequence matrix (linear utility)
    norm_matrix = normalize_linear(matrix, criteria_types)
    
    # 3. Compute global scores: V(a_i) = Sum_j w_j * v_j(a_i)
    global_scores = np.dot(norm_matrix, weights)
    
    # 4. Determine ranks (descending order of score)
    sorted_indices = np.argsort(-global_scores)
    ranks = np.zeros(m, dtype=int)
    for rank_pos, idx in enumerate(sorted_indices):
        ranks[idx] = rank_pos + 1  # 1-based ranking
        
    return {
        'weights': weights.tolist(),
        'normalized_matrix': norm_matrix.tolist(),
        'global_scores': global_scores.tolist(),
        'ranks': ranks.tolist()
    }
