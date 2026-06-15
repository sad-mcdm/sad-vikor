import numpy as np

def solve_electre(
    matrix_data: list[list[float]],
    criteria_types: list[str],
    preference_data: dict,  # {'weights': {...}, 'electre_version': 'I'|'IS'|'II'|'III'|'IV'|'TRI', ...}
    criteria_ids: list[int],
    alternatives_ids: list[int]
) -> dict:
    """
    Solves ELECTRE (I, IS, II, III, IV, TRI) for individual decision making.
    """
    matrix = np.array(matrix_data, dtype=float)
    m, n = matrix.shape
    
    # 1. Version and weights
    version = preference_data.get('electre_version', 'I')
    
    weights = np.zeros(n)
    if version != 'IV':  # ELECTRE IV does not use weights
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
    else:
        weights = np.ones(n) / n
        
    # 2. Get scale ranges for normalized discordance calculations
    ranges = np.zeros(n)
    for j in range(n):
        col = matrix[:, j]
        r = np.max(col) - np.min(col)
        ranges[j] = r if r > 0 else 1.0
        
    # 3. Read thresholds (q: indifference, p: preference, v: veto)
    q = np.zeros(n)
    p = np.full(n, 1e-9)
    v = np.full(n, np.inf)
    thresholds_pref = preference_data.get('thresholds', {})
    
    for j, cid in enumerate(criteria_ids):
        cid_str = str(cid)
        if cid_str in thresholds_pref:
            t = thresholds_pref[cid_str]
            q[j] = float(t.get('q', 0.0))
            p[j] = float(t.get('p', 1e-9))
            v[j] = float(t.get('v', np.inf))
            
    # Normalize matrix to [0,1] locally for cleaner distance/concordance calculations
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
            
    global_scores = np.zeros(m)
    ranks = np.ones(m, dtype=int)
    extra_data = {}
    
    # ------------------- ELECTRE I & IS -------------------
    if version in ['I', 'IS']:
        # Concordance matrix c(a,b)
        concordance = np.zeros((m, m))
        discordance = np.zeros((m, m))
        
        c_threshold = float(preference_data.get('concordance_threshold', 0.6))
        d_threshold = float(preference_data.get('discordance_threshold', 0.4))
        
        for a in range(m):
            for b in range(m):
                if a == b:
                    continue
                # Calculate Concordance
                c_sum = 0.0
                max_disc = 0.0
                vetoed = False
                
                for j in range(n):
                    diff = norm_matrix[a, j] - norm_matrix[b, j]
                    # Physical difference for veto
                    phys_diff = matrix[a, j] - matrix[b, j] if criteria_types[j] == 'benefit' else matrix[b, j] - matrix[a, j]
                    
                    if version == 'I':
                        if diff >= 0:
                            c_sum += weights[j]
                        else:
                            val = -diff
                            if val > max_disc:
                                max_disc = val
                    else:  # ELECTRE IS pseudo-criteria
                        # Scale thresholds to norm scale for consistency
                        norm_q = q[j] / ranges[j]
                        norm_p = p[j] / ranges[j]
                        norm_v = v[j] / ranges[j]
                        
                        # Concordance contribution
                        if diff >= -norm_q:
                            c_sum += weights[j]
                        elif diff < -norm_p:
                            c_sum += 0.0
                        else:
                            c_sum += weights[j] * (norm_p + diff) / (norm_p - norm_q)
                            
                        # Veto check
                        if diff < -norm_v:
                            vetoed = True
                            
                concordance[a, b] = c_sum
                if version == 'I':
                    discordance[a, b] = max_disc
                else:
                    discordance[a, b] = 1.0 if vetoed else 0.0
                    
        # Outranking Graph: a S b
        outranks = np.zeros((m, m), dtype=bool)
        for a in range(m):
            for b in range(m):
                if a != b:
                    if version == 'I':
                        outranks[a, b] = (concordance[a, b] >= c_threshold) and (discordance[a, b] <= d_threshold)
                    else:  # ELECTRE IS
                        outranks[a, b] = (concordance[a, b] >= c_threshold) and (discordance[a, b] == 0.0)
                        
        # Find Kernel
        # A kernel is a subset K of alternatives such that:
        # 1. No alternative in K outranks another in K.
        # 2. Every alternative outside K is outranked by at least one in K.
        kernel = []
        for i in range(m):
            # If not outranked by any other, it must be in the kernel
            outranked = False
            for j in range(m):
                if j != i and outranks[j, i]:
                    outranked = True
                    break
            if not outranked:
                kernel.append(i)
                
        # If kernel is empty (due to cycles), fallback to net outranking flows
        if not kernel:
            kernel = list(range(m))
            
        # Global scores can represent number of alternatives outranked
        global_scores = np.sum(outranks, axis=1).astype(float)
        sorted_indices = np.argsort(-global_scores)
        for rank_pos, idx in enumerate(sorted_indices):
            ranks[idx] = rank_pos + 1
            
        extra_data = {
            'concordance': concordance.tolist(),
            'discordance': discordance.tolist(),
            'kernel': [alternatives_ids[idx] for idx in kernel]
        }
        
    # ------------------- ELECTRE II -------------------
    elif version == 'II':
        # Strong and weak thresholds
        c_strong = float(preference_data.get('concordance_strong', 0.7))
        c_weak = float(preference_data.get('concordance_weak', 0.5))
        d_strong = float(preference_data.get('discordance_strong', 0.3))
        d_weak = float(preference_data.get('discordance_weak', 0.5))
        
        concordance = np.zeros((m, m))
        discordance = np.zeros((m, m))
        
        for a in range(m):
            for b in range(m):
                if a == b:
                    continue
                c_sum = 0.0
                max_disc = 0.0
                for j in range(n):
                    diff = norm_matrix[a, j] - norm_matrix[b, j]
                    if diff >= 0:
                        c_sum += weights[j]
                    else:
                        val = -diff
                        if val > max_disc:
                            max_disc = val
                concordance[a, b] = c_sum
                discordance[a, b] = max_disc
                
        # Strong and weak outranking relations
        S_strong = np.zeros((m, m), dtype=bool)
        S_weak = np.zeros((m, m), dtype=bool)
        for a in range(m):
            for b in range(m):
                if a == b:
                    continue
                S_strong[a, b] = (concordance[a, b] >= c_strong) and (discordance[a, b] <= d_strong)
                S_weak[a, b] = (concordance[a, b] >= c_weak) and (discordance[a, b] <= d_weak)
                
        # Distillation procedure (Forward & Backward)
        def distill(alternatives, is_forward=True):
            if not alternatives:
                return []
            
            # Subgraph outranking relationships
            sub_m = len(alternatives)
            deg = np.zeros(sub_m)
            for i, a in enumerate(alternatives):
                for j, b in enumerate(alternatives):
                    if i != j:
                        # Count strong dominance
                        if S_strong[a, b]:
                            deg[i] += 1
                        # If forward, count weak dominance
                        if is_forward and S_weak[a, b]:
                            deg[i] += 0.5
                            
            if is_forward:
                # Find maximum score
                max_val = np.max(deg)
                best_subset = [alternatives[i] for i in range(sub_m) if deg[i] == max_val]
            else:
                # Find minimum score (least dominated/backward)
                min_val = np.min(deg)
                best_subset = [alternatives[i] for i in range(sub_m) if deg[i] == min_val]
                
            if len(best_subset) == len(alternatives):
                return best_subset
            else:
                return distill(best_subset, is_forward)
                
        # Perform distillation to rank
        alts = list(range(m))
        ranking_order = []
        while alts:
            best_alts = distill(alts, is_forward=True)
            for ba in best_alts:
                ranking_order.append(ba)
                alts.remove(ba)
                
        for rank_pos, idx in enumerate(ranking_order):
            ranks[idx] = rank_pos + 1
            global_scores[idx] = float(m - rank_pos)
            
        extra_data = {
            'concordance': concordance.tolist(),
            'discordance': discordance.tolist()
        }
        
    # ------------------- ELECTRE III -------------------
    elif version in ['III', 'IV']:
        # Credibility matrix rho(a, b)
        credibility = np.zeros((m, m))
        
        for a in range(m):
            for b in range(m):
                if a == b:
                    continue
                
                # Concordance
                c_sum = 0.0
                for j in range(n):
                    diff = matrix[a, j] - matrix[b, j] if criteria_types[j] == 'benefit' else matrix[b, j] - matrix[a, j]
                    
                    if diff >= -q[j]:
                        c_sum += weights[j]
                    elif diff < -p[j]:
                        c_sum += 0.0
                    else:
                        c_sum += weights[j] * (p[j] + diff) / (p[j] - q[j])
                        
                # Discordance per criterion
                d_j = np.zeros(n)
                for j in range(n):
                    diff = matrix[a, j] - matrix[b, j] if criteria_types[j] == 'benefit' else matrix[b, j] - matrix[a, j]
                    if diff >= -p[j]:
                        d_j[j] = 0.0
                    elif diff < -v[j]:
                        d_j[j] = 1.0
                    else:
                        d_j[j] = (-diff - p[j]) / (v[j] - p[j])
                        
                # Credibility aggregation
                rho = c_sum
                for j in range(n):
                    if d_j[j] > c_sum:
                        rho *= (1.0 - d_j[j]) / (1.0 - c_sum)
                credibility[a, b] = rho
                
        # Distillation based on credibility matrix
        # Calculate thresholds: s(lambda) = 0.3 - 0.15 * lambda
        lambda_max = np.max(credibility)
        
        # Distillation algorithm
        def perform_distillation(active_alts, ascending=True):
            if not active_alts:
                return []
            
            lam = lambda_max
            # Iteratively find elite
            while lam > 0:
                s_lam = 0.3 - 0.15 * lam
                cutoff = lam - s_lam
                
                # Outranking relation at level lambda
                sub_out = np.zeros((len(active_alts), len(active_alts)), dtype=bool)
                for i, a in enumerate(active_alts):
                    for j, b in enumerate(active_alts):
                        if i != j:
                            sub_out[i, j] = (credibility[a, b] >= cutoff) and (credibility[a, b] > credibility[b, a] + 0.15)
                            
                # Net score
                strengths = np.sum(sub_out, axis=1)
                weaknesses = np.sum(sub_out, axis=0)
                net = strengths - weaknesses
                
                if ascending:
                    target = np.max(net)
                else:
                    target = np.min(net)
                    
                selected = [active_alts[idx] for idx, val in enumerate(net) if val == target]
                if len(selected) < len(active_alts):
                    return perform_distillation(selected, ascending)
                
                lam -= 0.1
                
            return active_alts
            
        # Rank by descending distillation
        alts_desc = list(range(m))
        order_desc = []
        while alts_desc:
            elite = perform_distillation(alts_desc, ascending=True)
            for el in elite:
                order_desc.append(el)
                alts_desc.remove(el)
                
        for rank_pos, idx in enumerate(order_desc):
            ranks[idx] = rank_pos + 1
            global_scores[idx] = float(m - rank_pos)
            
        extra_data = {
            'credibility': credibility.tolist()
        }
        
    # ------------------- ELECTRE TRI -------------------
    elif version == 'TRI':
        # Categories and boundaries mapping
        # preference_data['profiles'] contains matrix of boundaries b_k (shape: k x n)
        # Category indices 1 to K+1.
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
            
        profiles = np.array(profiles, dtype=float)  # shape: k x n (where k is number of boundary profiles)
        num_profiles = profiles.shape[0]
        
        # Calculate credibility degree rho(a, b_h) and rho(b_h, a)
        # Boundary profile indexing: b_1, b_2, ..., b_k
        rho_a_b = np.zeros((m, num_profiles))
        rho_b_a = np.zeros((num_profiles, m))
        
        lambda_t = float(preference_data.get('lambda_threshold', 0.6))
        
        for i in range(m):
            for h in range(num_profiles):
                # Compare a_i and b_h
                # Concordance a_i over b_h
                c_a_b = 0.0
                c_b_a = 0.0
                for j in range(n):
                    # Local values
                    val_a = matrix[i, j]
                    val_b = profiles[h, j]
                    
                    diff_a_b = val_a - val_b if criteria_types[j] == 'benefit' else val_b - val_a
                    diff_b_a = val_b - val_a if criteria_types[j] == 'benefit' else val_a - val_b
                    
                    # Concordance a S b
                    if diff_a_b >= -q[j]:
                        c_a_b += weights[j]
                    elif diff_a_b >= -p[j]:
                        c_a_b += weights[j] * (p[j] + diff_a_b) / (p[j] - q[j])
                        
                    # Concordance b S a
                    if diff_b_a >= -q[j]:
                        c_b_a += weights[j]
                    elif diff_b_a >= -p[j]:
                        c_b_a += weights[j] * (p[j] + diff_b_a) / (p[j] - q[j])
                        
                rho_a_b[i, h] = c_a_b
                rho_b_a[h, i] = c_b_a
                
        # Pessimistic alocation:
        # Compare alternative a_i with profiles b_h from h = num_profiles down to 1
        # find the first profile b_h such that a S b_h (i.e. rho_a_b >= lambda_t)
        # Alocate to category h+1 (where h ranges from 0 to num_profiles). Category 1 is worst, num_profiles+1 is best.
        allocations = np.zeros(m, dtype=int)
        for i in range(m):
            allocated = False
            for h in range(num_profiles - 1, -1, -1):
                if rho_a_b[i, h] >= lambda_t:
                    allocations[i] = h + 2  # Categories are 1-indexed (h+2 refers to category index)
                    allocated = True
                    break
            if not allocated:
                allocations[i] = 1
                
        # Ranks will represent sorted order of category (higher category is better)
        # For equal categories, secondary sort on net concordance over boundaries
        sorting_scores = np.zeros(m)
        for i in range(m):
            sorting_scores[i] = allocations[i] * 10.0 + np.mean(rho_a_b[i, :])
            
        sorted_indices = np.argsort(-sorting_scores)
        for rank_pos, idx in enumerate(sorted_indices):
            ranks[idx] = rank_pos + 1
            global_scores[idx] = float(allocations[idx])
            
        extra_data = {
            'allocations': allocations.tolist(),
            'num_categories': num_profiles + 1,
            'profiles': profiles.tolist()
        }
        
    return {
        'weights': weights.tolist(),
        'normalized_matrix': norm_matrix.tolist(),
        'global_scores': global_scores.tolist(),
        'ranks': ranks.tolist(),
        'version': version,
        'extra': extra_data
    }
