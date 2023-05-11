class SubsumptionEliminator:
    def __init__(self, cdcl, enabled=False):
        self.appearance = {}
        self.cdcl = cdcl
        if enabled:
            self.count_appearance()
        else:
            self.update_and_eliminate = self._nothing
            self.remove_appearance = self._nothing

    def count_appearance(self):
        num_vars = self.cdcl.num_vars
        for i in range(1, num_vars + 1):
            self.appearance[i] = set()
            self.appearance[-i] = set()
        for c in self.cdcl.clauses:
            for lit in c.literals:
                self.appearance[lit].add(c)

    def update_and_eliminate(self, new_clause):
        c = new_clause.literals
        subsumed = self.appearance[c[0]].copy()
        for lit in c:
            subsumed.intersection_update(self.appearance[lit])
            self.appearance[lit].add(new_clause)
        if len(subsumed) > 0:
            for sc in subsumed:
                #print(sc.literals, new_clause.literals)
                # assert(set(new_clause.literals).issubset(set(sc.literals)))
                sc.subsumed_by(new_clause)
                self.cdcl.eliminate_clause(sc)

    def remove_appearance(self, clause):
        for lit in clause.literals:
            self.appearance[lit].remove(clause)

    def _nothing(self, *args, **kwargs):
        pass
