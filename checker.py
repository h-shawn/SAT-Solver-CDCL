def check(sentence, assign, literals):
    """
    Checks whether the assignment is correct.
    """
    for s in sentence:
        sat = False
        for lit in s:
            if assign[abs(lit)] == (lit > 0):
                sat = True
                break
        if sat == False:
            return False
    return True
