import numpy as np
from modules.smarts_smarter.engine import normalize_linear
from modules.bwt.engine import interpolate_bisection
from modules.macbeth.engine import get_macbeth_scores
from modules.topsis.engine import solve_topsis
from modules.vikor.engine import solve_vikor
from modules.electre.engine import solve_electre
from modules.promethee.engine import solve_promethee

def run_monte_carlo(
    matrix_data: list[list[float]],         # Consequence matrix (m x n)
    criteria_types: list[str],             # 'benefit' or 'cost' (length n)
    weights: list[float],                  # Calculated criteria weights (length n)
    variations_pct: list[float],           # Perturbation percent per criterion (length n)
    num_simulations: int,                  # Number of iterations (e.g. 10000)
    method: str,                           # 'smarts', 'smarter', 'ahp', 'macbeth', 'bwm', 'bwt'
    preference_data: dict,                 # Preferences dictionary to retrieve bisection midpoints or levels
    criteria_ids: list[int]
) -> dict:
    """
    Runs Monte Carlo simulation by perturbing the consequence matrix.
    Recalculates scores and ranks at each iteration.
    """
    matrix = np.array(matrix_data, dtype=float)
    m, n = matrix.shape
    W = np.array(weights, dtype=float)
    
    # 1. Precalculate bounds and deltas
    col_maxs = np.max(matrix, axis=0)
    col_mins = np.min(matrix, axis=0)
    ranges = col_maxs - col_mins
    deltas = np.array(variations_pct, dtype=float) / 100.0 * ranges
    
    # 2. Extract specific elicitation helpers for value functions
    bisection_mids = {}
    macbeth_level_scores = {}
    
    if method == 'bwt':
        mids = preference_data.get('bisection_midpoints', {})
        for j, cid in enumerate(criteria_ids):
            cid_str = str(cid)
            default_mid = (col_mins[j] + col_maxs[j]) / 2.0
            bisection_mids[j] = float(mids.get(cid_str, default_mid))
            
    elif method == 'macbeth':
        levels_pref = preference_data.get('levels_matrices', {})
        for j, cid in enumerate(criteria_ids):
            cid_str = str(cid)
            is_benefit = (criteria_types[j] == 'benefit')
            if cid_str in levels_pref:
                levels_matrix = np.array(levels_pref[cid_str], dtype=float)
                macbeth_level_scores[j] = get_macbeth_scores(levels_matrix, 5, is_benefit)
            else:
                macbeth_level_scores[j] = np.linspace(0, 1, 5) if is_benefit else np.linspace(1, 0, 5)

    # 3. Counters
    winner_counts = np.zeros(m, dtype=int)
    rank_counts = np.zeros((m, m), dtype=int)  # rank_counts[i][r] = how many times alternative i was at rank r
    global_scores_sum = np.zeros(m, dtype=float)
    
    # Pre-generate random noise to vectorise or run loop efficiently
    # We run in batches of 1000 to save memory while utilizing vectorization
    batch_size = 1000
    remaining = num_simulations
    
    while remaining > 0:
        current_batch = min(batch_size, remaining)
        remaining -= current_batch
        
        for _ in range(current_batch):
            # Perturb consequences
            # Uniform noise in [-delta, delta]
            noise = np.random.uniform(-deltas, deltas, size=(m, n))
            perturbed = matrix + noise
            
            # Clip within original boundaries
            for j in range(n):
                perturbed[:, j] = np.clip(perturbed[:, j], col_mins[j], col_maxs[j])
                
            # Normalize based on the method's value function and calculate scores/ranks
            if method in ['topsis', 'vikor', 'electre', 'promethee']:
                # Run exact solver
                # Reconstruct weights dictionary for solver
                weights_dict = {str(criteria_ids[j]): W[j] * 100.0 for j in range(n)}
                pref_copy = preference_data.copy()
                pref_copy['weights'] = weights_dict
                
                if method == 'topsis':
                    res = solve_topsis(perturbed.tolist(), criteria_types, pref_copy, criteria_ids, list(range(m)))
                    scores = np.array(res['global_scores'])
                    ranks_iter = np.array(res['ranks']) - 1
                elif method == 'vikor':
                    res = solve_vikor(perturbed.tolist(), criteria_types, pref_copy, criteria_ids, list(range(m)))
                    scores = np.array(res['global_scores'])
                    ranks_iter = np.array(res['ranks']) - 1
                elif method == 'electre':
                    res = solve_electre(perturbed.tolist(), criteria_types, pref_copy, criteria_ids, list(range(m)))
                    scores = np.array(res['global_scores'])
                    ranks_iter = np.array(res['ranks']) - 1
                else:  # promethee
                    res = solve_promethee(perturbed.tolist(), criteria_types, pref_copy, criteria_ids, list(range(m)))
                    scores = np.array(res['global_scores'])
                    ranks_iter = np.array(res['ranks']) - 1
                    
                global_scores_sum += scores
                for idx in range(m):
                    r_pos = int(ranks_iter[idx])
                    r_pos = min(max(r_pos, 0), m - 1)
                    rank_counts[idx, r_pos] += 1
                    if r_pos == 0:
                        winner_counts[idx] += 1
            else:
                norm_perturbed = np.zeros_like(perturbed, dtype=float)
                
                if method == 'bwt':
                    # BWT: Piecewise linear bisection function
                    for j in range(n):
                        is_benefit = (criteria_types[j] == 'benefit')
                        x_05 = bisection_mids[j]
                        for i in range(m):
                            norm_perturbed[i, j] = interpolate_bisection(perturbed[i, j], col_mins[j], col_maxs[j], x_05, is_benefit)
                elif method == 'macbeth':
                    # MACBETH: Level-based interpolation
                    for j in range(n):
                        levels = np.linspace(col_mins[j], col_maxs[j], 5)
                        scores_levels = macbeth_level_scores[j]
                        for i in range(m):
                            if col_maxs[j] == col_mins[j]:
                                norm_perturbed[i, j] = 1.0
                            else:
                                norm_perturbed[i, j] = float(np.interp(perturbed[i, j], levels, scores_levels))
                else:
                    # SMARTS, SMARTER, AHP, BWM: Standard linear utility function
                    norm_perturbed = normalize_linear(perturbed, criteria_types)
                    
                # Calculate global scores: m x 1
                scores = np.dot(norm_perturbed, W)
                global_scores_sum += scores
                
                # Find ranks (descending order)
                # To handle ties, we use argsort twice
                sorted_indices = np.argsort(-scores)
                
                # Record ranks (0-indexed for positioning)
                for rank_pos, idx in enumerate(sorted_indices):
                    rank_counts[idx, rank_pos] += 1
                    if rank_pos == 0:
                        winner_counts[idx] += 1
                    
    # 4. Aggregate results
    probabilities_first = (winner_counts / num_simulations).tolist()
    rank_probabilities = (rank_counts / num_simulations).tolist()
    average_scores = (global_scores_sum / num_simulations).tolist()
    
    # Calculate average rank: 1-based
    # Sum_{r=0}^{m-1} (r + 1) * rank_counts[i][r] / num_simulations
    average_ranks = []
    for i in range(m):
        avg_r = sum((r + 1) * rank_counts[i, r] for r in range(m)) / num_simulations
        average_ranks.append(avg_r)
        
    return {
        'first_place_probabilities': probabilities_first,
        'rank_probabilities': rank_probabilities,
        'average_scores': average_scores,
        'average_ranks': average_ranks,
        'deltas': deltas.tolist()
    }
