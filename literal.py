class Literals:
    """
    Static class for literal assignment.
    """

    def __init__(self, num_vars):
        """
        Initialize data structure.
        *: Assume that all variables are numbered > 0.
        """
        self.values = [0] * (num_vars + 1)
        self.levels = [0] * (num_vars + 1)
        self.reasons = [None] * (num_vars + 1)

    def assign(self, literal, level, reason):
        """
        Make an the assignment on the variable.
        """
        #assert self.values[abs(literal)] == 0
        lit = abs(literal)
        self.values[lit] = 1 if literal > 0 else -1
        self.levels[lit] = level
        self.reasons[lit] = reason

    def unassign(self, literal):
        """
        Cancel the assignment on the variable.
        """
        ret = (self.reasons[literal] != None)
        literal = abs(literal)
        #assert self.values[literal] != 0
        self.values[literal] = 0
        self.levels[literal] = 0
        self.reasons[literal] = None
        return ret

    def get(self, literal):
        """
        Get assigned value.
        Return value:
          1  : TRUE
          -1 : FALSE
          0  : UNASSIGNED
        """
        literal = abs(literal)
        return self.values[literal]

    def level(self, literal):
        literal = abs(literal)
        #assert Literal._values[literal] != 0
        return self.levels[literal]

    def ante(self, literal):
        """
        Get antecedent of the assignment.
        """
        literal = abs(literal)
        #assert Literal._values[literal] != 0
        ret = self.reasons[literal]
        if ret != None:
            while ret.subsumed != None:
                ret = ret.subsumed
        return ret

    def sat(self, literal):
        """
        Returns whether the assignment generates TRUE or not on the literal.
        For example, if variable of the literal is assigned TRUE and literal > 0, sat(literal) == TRUE
        """
        if literal == None:
            return False
        return self.values[abs(literal)] * literal > 0
