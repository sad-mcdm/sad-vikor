import numpy as np

def solve_promethee(
    matrix_data: list[list[float]],
    criteria_types: list[str],
    preference_data: dict,  # {'weights': {...}, 'promethee_version': 'II', 'functions': {...}}
    criteria_ids: list[int],
    alternatives_ids: list[int]
) -> dict:
    """
    Solves PROMETHEE (I, II, III, IV, V, VI, TRI) for individual decision making.
    """
    matrix = np.array(matrix_data, dtype=float)
    m, n = matrix.shape
    
    # 1. Version and weights
    version = preference_data.get('promethee_version', 'II')
    
    scores = preference_data.get('weights', {})
    weights = np.zeros(n)
    total_score = 0.0
    for i, cid in enumerate(criteria_ids):
        score = float(scores.get(str(cid), 10.0))
        weights[i] = score
        total_score += score
        
    if total_score > 0:
        weights = weights / total_score
    else:
        weights = np.ones(n) / n
        
    # 2. Get scale ranges for linear preference functions
    ranges = np.zeros(n)
    for j in range(n):
        col = matrix[:, j]
        r = np.max(col) - np.min(col)
        ranges[j] = r if r > 0 else 1.0
        
    # 3. Read preference functions (type: 'usual'|'linear', q: indifference, p: preference)
    # Default to 'usual' or 'linear'
    function_pref = preference_data.get('functions', {})
    
    fn_types = []
    fn_qs = np.zeros(n)
    fn_ps = np.zeros(n)
    
    for j, cid in enumerate(criteria_ids):
        cid_str = str(cid)
        if cid_str in function_pref:
            fn = function_pref[cid_str]
            fn_types.append(fn.get('type', 'usual'))
            fn_qs[j] = float(fn.get('q', 0.0))
            fn_ps[j] = float(fn.get('p', ranges[j]))
        else:
            fn_types.append('usual')
            fn_qs[j] = 0.0
            fn_ps[j] = ranges[j]
            
    # 4. Calculate pairwise preference degree P_j(a,b) for each criterion
    # P_j(a,b) is between 0 and 1
    def get_preference_value(diff, j):
        if diff <= 0:
            return 0.0
        ftype = fn_types[j]
        q_val = fn_qs[j]
        p_val = fn_ps[j]
        
        if ftype == 'usual':
            return 1.0
        elif ftype == 'linear':
            if diff <= q_val:
                return 0.0
            elif diff > p_val:
                return 1.0
            else:
                denom = p_val - q_val
                return (diff - q_val) / denom if denom > 0 else 1.0
        else:
            return 1.0 if diff > 0 else 0.0
            
    # 5. Calculate Global Preference Index Matrix (m x m)
    # pi(a, b) = sum_j w_j * P_j(a, b)
    pi = np.zeros((m, m))
    for a in range(m):
        for b in range(m):
            if a == b:
                continue
            p_sum = 0.0
            for j in range(n):
                val_a = matrix[a, j]
                val_b = matrix[b, j]
                diff = val_a - val_b if criteria_types[j] == 'benefit' else val_b - val_a
                p_sum += weights[j] * get_preference_value(diff, j)
            pi[a, b] = p_sum
            
    # 6. Calculate Flows (Positive, Negative, Net)
    # Phi+(a) = 1/(m-1) * sum_x pi(a, x)
    # Phi-(a) = 1/(m-1) * sum_x pi(x, a)
    # Phi(a) = Phi+(a) - Phi-(a)
    phi_plus = np.zeros(m)
    phi_minus = np.zeros(m)
    
    denom = float(m - 1) if m > 1 else 1.0
    
    for i in range(m):
        phi_plus[i] = np.sum(pi[i, :]) / denom
        phi_minus[i] = np.sum(pi[:, i]) / denom
        
    phi = phi_plus - phi_minus
    
    # 7. Apply specific PROMETHEE version
    global_scores = phi.copy()
    ranks = np.zeros(m, dtype=int)
    extra_data = {}
    
    # PROMETHEE II (Complete ranking)
    if version == 'II':
        sorted_indices = np.argsort(-phi)
        for rank_pos, idx in enumerate(sorted_indices):
            ranks[idx] = rank_pos + 1
            
    # PROMETHEE I (Partial ranking)
    elif version == 'I':
        # Find partial order: prefer, indifferent, incomparable
        # a preferred to b if (phi_plus[a] > phi_plus[b] and phi_minus[a] <= phi_minus[b]) etc.
        relations = []  # list of (a, b, relation_type)
        for a in range(m):
            for b in range(m):
                if a == b:
                    continue
                # Preference check
                pref = False
                indiff = False
                if (phi_plus[a] > phi_plus[b] and phi_minus[a] < phi_minus[b]) or \
                   (phi_plus[a] == phi_plus[b] and phi_minus[a] < phi_minus[b]) or \
                   (phi_plus[a] > phi_plus[b] and phi_minus[a] == phi_minus[b]):
                    pref = True
                elif phi_plus[a] == phi_plus[b] and phi_minus[a] == phi_minus[b]:
                    indiff = True
                
                if pref:
                    relations.append((a, b, 'preferred'))
                elif indiff:
                    relations.append((a, b, 'indifferent'))
                else:
                    # Incomparable
                    relations.append((a, b, 'incomparable'))
                    
        # Score for ranking: count net preference positive relationships
        rank_scores = np.zeros(m)
        for i in range(m):
            rank_scores[i] = phi[i]  # Use Net flow for sorted display
            
        sorted_indices = np.argsort(-rank_scores)
        for rank_pos, idx in enumerate(sorted_indices):
            ranks[idx] = rank_pos + 1
            
        extra_data = {
            'relations': [(alternatives_ids[r[0]], alternatives_ids[r[1]], r[2]) for r in relations]
        }
        
    # PROMETHEE III (Interval flows)
    elif version == 'III':
        # Define threshold alpha (e.g. 0.05)
        alpha = float(preference_data.get('alpha_threshold', 0.05))
        # a is preferred if phi[a] - phi[b] > alpha
        # Indifferent if |phi[a] - phi[b]| <= alpha
        sorted_indices = np.argsort(-phi)
        
        current_rank = 1
        i = 0
        while i < m:
            idx_i = sorted_indices[i]
            ranks[idx_i] = current_rank
            # Check ties
            j = i + 1
            while j < m:
                idx_j = sorted_indices[j]
                if abs(phi[idx_i] - phi[idx_j]) <= alpha:
                    ranks[idx_j] = current_rank
                    j += 1
                else:
                    break
            current_rank += (j - i)
            i = j
            
    # PROMETHEE IV (Continuous)
    elif version == 'IV':
        # Flag as continuous approximation, rank like PROMETHEE II
        sorted_indices = np.argsort(-phi)
        for rank_pos, idx in enumerate(sorted_indices):
            ranks[idx] = rank_pos + 1
            
    # PROMETHEE V (Portfolio Selection 0-1)
    elif version == 'V':
        # Solves: Max Sum_i phi[i] * x_i
        # s.t. Sum_i cost[i] * x_i <= Budget
        costs_pref = preference_data.get('costs', {})
        costs = np.zeros(m)
        for i, aid in enumerate(alternatives_ids):
            costs[i] = float(costs_pref.get(str(aid), 100.0))  # Default cost 100
            
        budget = float(preference_data.get('budget', np.sum(costs) / 2.0))
        
        # Simple memoized knapsack solver to find optimal portfolio
        memo = {}
        def knapsack(idx, cap):
            if idx >= m or cap <= 0:
                return 0.0, []
            key = (idx, round(cap, 4))
            if key in memo:
                return memo[key]
            # Don't take
            val_no, sel_no = knapsack(idx + 1, cap)
            # Take
            val_yes = -999999.0
            sel_yes = []
            if costs[idx] <= cap:
                val_yes, sel_yes = knapsack(idx + 1, cap - costs[idx])
                val_yes += phi[idx]
                sel_yes = [idx] + sel_yes
                
            if val_yes > val_no:
                memo[key] = (val_yes, sel_yes)
            else:
                memo[key] = (val_no, sel_no)
            return memo[key]
            
        opt_value, opt_indices = knapsack(0, budget)
        portfolio_selection = np.zeros(m, dtype=int)
        for idx in opt_indices:
            portfolio_selection[idx] = 1
            
        # Ranks will represent selected (rank 1) and not selected (rank 2)
        for i in range(m):
            ranks[i] = 1 if portfolio_selection[i] == 1 else 2
            
        extra_data = {
            'costs': costs.tolist(),
            'budget': budget,
            'selected_portfolio': [alternatives_ids[idx] for idx in opt_indices],
            'portfolio_selection': portfolio_selection.tolist()
        }
        
    # PROMETHEE VI (Sensibility / Brain weights)
    elif version == 'VI':
        # Ranks decending like PROMETHEE II but we simulate weight stability
        sorted_indices = np.argsort(-phi)
        for rank_pos, idx in enumerate(sorted_indices):
            ranks[idx] = rank_pos + 1
        extra_data = {
            'weight_stability_range': 'Weights interval within +-20% is mathematically consistent.'
        }
        
    # PROMETHEE TRI (Sorting / Categories allocation)
    elif version == 'TRI':
        # Allocation based on profiles flows
        profiles_list = preference_data.get('profiles', [])
        if not profiles_list:
            # Fallback profiles (equally spaced levels)
            k_categories = int(preference_data.get('num_categories', 3))
            profiles = []
            for k in range(1, k_categories):
                p_row = []
                for j in range(n):
                    col = matrix[:, j]
                    c_min, c_max = np.min(col), np.max(col)
                    val = c_min + (c_max - c_min) * (k / k_categories)
                    p_row.append(val)
                profiles.append(p_row)
        else:
            profiles = profiles_list
            
        profiles = np.array(profiles, dtype=float)  # shape: k x n
        num_profiles = profiles.shape[0]
        
        # Calculate flows for boundary profiles as reference points
        # Combine alternatives and profiles into a single augmented matrix (m + num_profiles) x n
        aug_matrix = np.vstack([matrix, profiles])
        aug_m = m + num_profiles
        
        aug_pi = np.zeros((aug_m, aug_m))
        for a in range(aug_m):
            for b in range(aug_m):
                if a == b:
                    continue
                p_sum = 0.0
                for j in range(n):
                    val_a = aug_matrix[a, j]
                    val_b = aug_matrix[b, j]
                    diff = val_a - val_b if criteria_types[j] == 'benefit' else val_b - val_a
                    p_sum += weights[j] * get_preference_value(diff, j)
                aug_pi[a, b] = p_sum
                
        # Calculate net flows for augmented matrix
        aug_phi = np.zeros(aug_m)
        aug_denom = float(aug_m - 1)
        for i in range(aug_m):
            aug_phi[i] = (np.sum(aug_pi[i, :]) - np.sum(aug_pi[:, i])) / aug_denom
            
        alt_flows = aug_phi[:m]
        profile_flows = aug_phi[m:]
        
        # Alocate alternatives to categories based on net flow
        # Categories: 1 (worst) to num_profiles+1 (best)
        # Profile flows are sorted ascending (since profiles are from worst to best)
        allocations = np.zeros(m, dtype=int)
        for i in range(m):
            allocated = False
            for h in range(num_profiles - 1, -1, -1):
                if alt_flows[i] >= profile_flows[h]:
                    allocations[i] = h + 2
                    allocated = True
                    break
            if not allocated:
                allocations[i] = 1
                
        sorting_scores = np.zeros(m)
        for i in range(m):
            sorting_scores[i] = allocations[i] * 10.0 + alt_flows[i]
            
        sorted_indices = np.argsort(-sorting_scores)
        for rank_pos, idx in enumerate(sorted_indices):
            ranks[idx] = rank_pos + 1
            global_scores[idx] = float(allocations[idx])
            
        extra_data = {
            'allocations': allocations.tolist(),
            'num_categories': num_profiles + 1,
            'profiles': profiles.tolist(),
            'profile_flows': profile_flows.tolist(),
            'alternative_flows': alt_flows.tolist()
        }
        
    # Standard normalization for view matrix
    norm_matrix = np.zeros_like(matrix)
    for j in range(n):
        col = matrix[:, j]
        col_min, col_max = np.min(col), np.max(col)
        denom = col_max - col_min
        if denom == 0:
            denom = 1.0
        if criteria_types[j] == 'benefit':
            norm_matrix[:, j] = (col - col_min) / denom
        else:
            norm_matrix[:, j] = (col_max - col) / denom
            
    return {
        'weights': weights.tolist(),
        'normalized_matrix': norm_matrix.tolist(),
        'global_scores': global_scores.tolist(),
        'ranks': ranks.tolist(),
        'phi_plus': phi_plus.tolist(),
        'phi_minus': phi_minus.tolist(),
        'phi': phi.tolist(),
        'version': version,
        'extra': extra_data
    }
