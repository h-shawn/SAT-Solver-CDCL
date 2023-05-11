class Trail:
    """
    Static class for managing the assignment trail.
    Using a manager class is due to consideration of keeping consistency between assignment, trail and VSIDS score.
    The solver uses push() to assign a value, and backtrack() to revoke assignments.
    """

    def __init__(self):
        self.stack = []
        self.bcp_ptr = 0
        self.first_bcp = True

    def push(self, literal):
        """
        Push a new assignment to the stack
        """
        self.stack.append(literal)

    def start_bcp(self):
        if not self.first_bcp:
            self.bcp_ptr = len(self.stack) - 1
        else:
            self.first_bcp = False
            self.bcp_ptr = 0

    def next(self):
        """
        Move BCP pointer forward.
        """
        if self.bcp_ptr < len(self.stack) and self.bcp_ptr >= 0:
            ret = self.stack[self.bcp_ptr]
            self.bcp_ptr += 1
            return ret
        return None

    def len(self):
        return len(self.stack)

    def toDict(self, literals):
        return {abs(var): (literals.get(var) > 0) for var in self.stack}
