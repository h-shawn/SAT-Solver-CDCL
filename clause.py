class Clause:
    """
    Utilities for clause operations.
    """

    def __init__(self, literals):
        self.literals = literals.copy()
        self.used = -1
        self.glue = 0
        self.subsumed = None
        self.subsuming = False

    def __len__(self):
        return len(self.literals)

    def deepest_literals(self, literals):
        """
        Get the literal with deepest/second deepest level.
        This is always called on a learned clause, so that there is only one deepest literal.
        """
        d1_level = -1
        d2_level = -1
        d1_lit = None
        d2_lit = None
        for lit in self.literals:
            if literals.level(lit) > d1_level:
                d2_level = d1_level
                d2_lit = d1_lit
                d1_level = literals.level(lit)
                d1_lit = lit
            elif literals.level(lit) > d2_level:
                d2_level = literals.level(lit)
                d2_lit = lit
        return d1_lit, d2_lit

    def deepest_level(self, literals):
        """
        Get the deepest level. For analyze_conflict().
        """
        return max([literals.level(lit) for lit in self.literals])

    def second_deepest_level(self, literals):
        """
        Get the second deepest level (or -1). For Trail.backtrack().
        """
        if len(self.literals) > 1:
            tmp = [literals.level(lit) for lit in self.literals]
            tmp.remove(max(tmp))
            return max(tmp)
        return 0

    def one_lit_at_level(self, level, literals):
        """
        Returns True if there is only one literal at the given level.
        """
        count = 0
        for lit in self.literals:
            if literals.level(lit) == level:
                count += 1
                if count > 1:
                    return False
        return count == 1

    def copy(self):
        return Clause(self.literals.copy())

    def resolve(self, lit, other):
        """
        Binary resolution.
        """
        #assert other != None
        self.literals = list(
            (set(self.literals) | set(other.literals)) - set((lit, -lit)))

    def recompute_glue(self, literals):
        """
        Recompute the glue (LBD) of each clause
        """
        # irredundant
        if self.used == -1:
            return
        levels = []
        for lit in self.literals:
            levels.append(literals.levels[lit])
        new_glue = len(set(levels))
        self.used = 1
        if new_glue < self.glue:
            if new_glue <= 2:
                self.used = -1
                self.glue = 0
            elif self.glue > 6 and new_glue <= 6:
                self.used = 2
            else:
                self.glue = new_glue
        elif self.glue <= 6:
            self.used = 2

    def compute_glue(self, literals):
        """
        Compute the glue (LBD) of each learned clause
        """
        levels = []
        for lit in self.literals:
            levels.append(literals.levels[lit])
        self.glue = len(set(levels))
        if self.glue <= 2:  # always keep
            self.used = -1
            self.glue = 0
        elif self.glue <= 6:
            self.used = 2
        else:
            self.used = 1

    def subsumed_by(self, clause):
        self.subsumed = clause
        clause.subsuming = True