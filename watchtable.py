class WatchTable:
    """
    Static class for managing literal watch.
    Considering consistency of l2c and c2l,
      using a static class to handle that seems to be better than manually keeping consistency in the solver logic.
    """

    def __init__(self, clauses, num_vars):
        """
        Initialize watch with the first one or two literals.
        """
        self.l2c_watch = [[] for _ in range(2 * num_vars + 1)]
        self.c2l_watch = {}
        for clause in clauses:
            if len(clause) > 1:
                self.c2l_watch[clause] = [
                    clause.literals[0], clause.literals[1]]
                self.l2c_watch[clause.literals[0]].append(clause)
                self.l2c_watch[clause.literals[1]].append(clause)
            # else:
            #     # assert len(clause) == 1
            #     self.c2l_watch[clause] = [clause.literals[0], None]
            #     self.l2c_watch[clause.literals[0]].append(clause)
            # we directly assign unary lits and do not watch them.

    def l2c(self, literal):
        return self.l2c_watch[literal]

    def c2l(self, clause):
        return self.c2l_watch[clause]

    def update(self, clause, assigned_lit, literals):
        other = self.get_other_watch(clause, assigned_lit)

        # if other == None:
        #     return False

        # Find unassigned literal or satisfied literal
        for lit in clause.literals:
            if lit == assigned_lit or lit == other:
                continue
            # This literal satisfies the clause or is not assigned
            if literals.sat(lit) or literals.get(lit) == 0:
                c2l = self.c2l_watch[clause]
                # assert lit_old in c2l
                # assert lit_new not in c2l
                c2l.remove(assigned_lit)
                c2l.append(lit)
                self.l2c_watch[assigned_lit].remove(clause)
                self.l2c_watch[lit].append(clause)
                return True
        # Cann't find a literal to watch
        return False

    def append(self, clause, literals):
        """
        Append LEARNED clause to the watch table.
        """
        # assert len(clause) > 0
        # We watch the two deepest literals.
        # When backtrack happens, they are the first literals to be unassigned in the clause.
        # Then they can be included in the BCP process.
        d1_lit, d2_lit = clause.deepest_literals(literals)
        self.c2l_watch[clause] = [d1_lit, d2_lit]
        self.l2c_watch[d1_lit].append(clause)
        if d2_lit != None:
            self.l2c_watch[d2_lit].append(clause)

    def sat(self, clause, literals):
        """
        Returns True if the clause is satisfied by assignment on watched literals.
        """
        watch = self.c2l(clause)
        return literals.sat(watch[0]) or literals.sat(watch[1])

    def get_other_watch(self, clause, lit):
        watch = self.c2l(clause)
        return watch[1] if watch[0] == lit else watch[0]
