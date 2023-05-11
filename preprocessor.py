def simplify_sentence(sentence):
    """
    Remove already satisfied clauses.
    """
    simplified = []
    for s in sentence:
        ns = []
        for lit in s:
            if -lit in s:
                ns = []
                break
            if lit not in ns:
                ns.append(lit)
        if len(ns) > 0:
            simplified.append(ns)
    return simplified


def subsumption_eliminate(clauses, num_vars):
    appearance = {}
    for i in range(1, num_vars + 1):
        appearance[i] = set()
        appearance[-i] = set()
    for i, c in enumerate(clauses):
        for lit in c:
            appearance[lit].add(i)
    for i, c in enumerate(clauses):
        if c == None:
            continue
        subsumed = appearance[c[0]].copy()
        for lit in c:
            subsumed.intersection_update(appearance[lit])
        subsumed.remove(i)
        if len(subsumed) > 0:
            # This clause subsumes other
            for sc in subsumed:
                clauses[sc] = None
    ret = []
    for c in clauses:
        if c is not None:
            ret.append(c)
    return ret, appearance


def bounded_variable_eliminate(clauses, num_vars):
    """
    (
        clauses: the original clauses list
        num_vars
    )
    Do elimination at the very beginning only.
    Eliminate variables which had positively/negatively appeared only once.
    https://www.cs.cmu.edu/~mheule/publications/bve-paper.pdf
    """
    lc_map = [0] * (2 * num_vars + 1)
    tmp = [0] * (2 * num_vars + 1)
    # Count variable occurrence
    for c in clauses:
        for l in c:
            lc_map[l] += 1

    # A clause can only be used to eliminate one variable
    candidates = set()
    for c in clauses:
        x = {i: lc_map[-i] for i in c if lc_map[i] == 1}
        if len(x) == 0:
            continue
        # We eliminate the variable with the most occurrence
        l = max(x, key=x.get)
        t = set(c)
        t.remove(l)
        tmp[l] = t
        candidates.add(-l)

    # If both v and -v appear in candidates, we should remove one of them
    removed = set()
    for c in candidates:
        if -c in candidates:
            removed.add(-c)
    candidates.difference_update(removed)
    clauses_eliminated = {-l: tmp[-l] for l in candidates}

    ret = []

    for c in clauses:
        if c in clauses_eliminated.values():
            # c is to be eliminated
            continue
        set_c = set(c)
        itc = set_c.intersection(candidates)
        if len(itc) > 0:
            # c should be resolved
            lit = itc.pop()
            set_c.remove(lit)
            new_clause = set_c.union(tmp[-lit])
            cont = False
            for l in iter(new_clause):
                if -l in new_clause:
                    cont = True
                    break
            if cont:
                continue
            ret.append(list(new_clause))
        else:
            ret.append(c)

    return ret, clauses_eliminated

# GATE-BASED Elimination?
# http://fmv.jku.at/papers/EenBiere-SAT05.pdf

def preprocess(clauses, num_vars):
    size = len(clauses)
    clauses = simplify_sentence(clauses)
    #clauses, original_appearance = subsumption_eliminate(clauses, num_vars)
    clauses, bve_clauses = bounded_variable_eliminate(clauses, num_vars)
    clauses, _ = subsumption_eliminate(clauses, num_vars)
    print("Preprocessing completed. Eliminated", size - len(clauses), "clauses.")
    return clauses, bve_clauses