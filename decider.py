import numpy as np
import math
from dpq import DynamicPriorityQueue


class decider:
    def update_scores(self):
        pass

    def on_assign(self):
        pass

    def on_unassign(self):
        pass

    def decide(self):
        pass


class VSIDS(decider):
    """
    VSIDS heuristic

    Using a list to store score of each variable. Using heap can possibly optimize handling with a lot of variables.
    """

    def __init__(self, scores, num_vars, decay=0.95):
        # Assign default score with 1.
        # Negative score means the literal has assignment.
        self.scores = scores
        self.num_vars = num_vars
        self.r_decay = 1 / decay
        self.one = 1

    def decide(self):
        """
        Decide the next literal to assign based on the max score.
        """
        ret = np.argmax(self.scores)
        # ret > self.num_vars: negative literal
        if ret > self.num_vars:
            return ret - (2 * self.num_vars + 1)
        return ret

    def on_assign(self, literal):
        """
        Change sign of the literal's score. (+ => -)
        """
        #assert self.scores[literal] > 0
        self.scores[literal] = -self.scores[literal]
        self.scores[-literal] = -self.scores[-literal]

    def on_unassign(self, literal):
        """
        Change sign of the literal's score. (- => +)
        """
        #assert self.scores[literal] < 0
        self.scores[literal] = -self.scores[literal]
        self.scores[-literal] = -self.scores[-literal]

    def update_scores(self, learned_clause, conflict, reasons):
        """
        +1 for literals in learned_clause. Apply decay on each literal.
        """
        mx = 0

        for lit in learned_clause.literals:
            if self.scores[lit] > 0:
                self.scores[lit] += self.one
            else:
                self.scores[lit] -= self.one
            mx = max(mx, abs(self.scores[lit]))

        self.one *= self.r_decay
        if mx > 1e6:
            for lit, _ in enumerate(self.scores):
                if abs(self.scores[lit]) > 1e-10:
                    self.scores[lit] = self.scores[lit] / self.one
            self.one = 1
        # for lit, _ in enumerate(self.scores):
        #    self.scores[lit] = self.scores[lit] * self.decay


class EVSIDS:
    def __init__(self, scores, num_vars, g=1.2):
        # Assign default score with 1.
        # Negative score means the literal has assignment.
        self.EXCEED_LIMIT = 10000
        self.scores = scores
        self.num_vars = num_vars
        self.g = g
        self.inc = g

    def decide(self):
        """
        Decide the next literal to assign based on the max score.
        """
        ret = np.argmax(self.scores)
        # ret > self.num_vars: negative literal
        if ret > self.num_vars:
            return ret - (2 * self.num_vars + 1)
        return ret

    def on_assign(self, literal):
        """
        Change sign of the literal's score. (+ => -)
        """
        self.scores[literal] = -self.scores[literal]
        self.scores[-literal] = -self.scores[-literal]

    def on_unassign(self, literal):
        """
        Change sign of the literal's score. (- => +)
        """
        self.scores[literal] = -self.scores[literal]
        self.scores[-literal] = -self.scores[-literal]

    def update_scores(self, learned_clause, conflict, reasons):
        """
        +1 for literals in learned_clause. Apply decay on each literal.
        """
        for lit in learned_clause.literals:
            if self.scores[lit] > 0:
                self.scores[lit] += self.inc
            else:
                self.scores[lit] -= self.inc

        self.inc *= self.g
        if self.inc > self.EXCEED_LIMIT:
            f = self.g / self.inc
            for lit, _ in enumerate(self.scores):
                if abs(self.scores[lit]) > 1e-10:
                    self.scores[lit] *= f
            self.inc = self.g


class LRB(decider):
    """
    Learn Rate Branch heuristic

    https://www.ac.tuwien.ac.at/files/pub/Liang2016.pdf
    """
    class Strategy:
        CONFLICT_SIDE = "CONFLICT_SIDE"
        CONFLICT_CLAUSE = "CONFLICT_CLAUSE"

    def __init__(self, num_vars, scores, alpha=0.4, alpha_lim=0.06, epsilon=1e-6, decay=0.95, strategy=Strategy.CONFLICT_SIDE):
        self.alpha = alpha
        self.beta = 1 - alpha
        self.alpha_lim = alpha_lim
        self.epsilon = epsilon
        self.learnt_counter = 1
        self.num_vars = num_vars
        self.ema = DynamicPriorityQueue()
        for v in range(1, num_vars + 1):
            self.ema.setVal(v, 1e-10)
        self.assigned = np.zeros(num_vars + 1)
        self.participated = np.zeros(num_vars + 1)
        # Extension: RSR
        self.reasoned = np.zeros(num_vars + 1)
        # Phase-saving, see: https://link.springer.com/content/pdf/10.1007/978-3-540-72788-0_28.pdf
        self.phase_saving = np.zeros(num_vars + 1, dtype=int)
        self.scores = scores
        self.decay = decay
        self.strategy = strategy

    def update_scores(self, clause, conflict, reasons):
        self.learnt_counter += 1
        clause_vars = set()
        for v in clause.literals:
            v = abs(v)
            self.participated[v] += 1
            self.reasoned[v] -= 1   # Extension: RSR
            clause_vars.add(v)
        for v in conflict:
            v = abs(v)
            if v not in clause_vars:
                self.participated[abs(v)] += 1
        if self.alpha > self.alpha_lim:
            self.alpha -= self.epsilon
        # Extension: RSR
        for lc in reasons:
            for v in lc.literals:
                v = abs(v)
                if v not in clause_vars:
                    self.reasoned[v] += 1
                    clause_vars.add(v)
        # Extension: Locality
        self.ema.decay(self.decay)

    def on_assign(self, v):
        v = abs(v)
        self.assigned[v] = self.learnt_counter
        self.participated[v] = 0
        orig_ema = self.ema.getVal(v)
        #assert orig_ema >= 0
        self.ema.setVal(v, -orig_ema)
        self.reasoned[v] = 0

    def on_unassign(self, v):
        self.phase_saving[abs(v)] = v
        v = abs(v)
        interval = self.learnt_counter - self.assigned[v]
        if interval > 0:
            r = self.participated[v] / interval
            orig_ema = -self.ema.getVal(v)
            #assert orig_ema >= 0
            rsr = self.reasoned[v] / interval
            self.ema.setVal(v, self.beta *
                            orig_ema + self.alpha * (r + rsr))
        else:
            orig_ema = -self.ema.getVal(v)
            #assert orig_ema >= 0
            self.ema.setVal(v, orig_ema)

    def decide(self):
        l = self.ema.top()
        if self.phase_saving[l] != 0:
            return self.phase_saving[l]
        if self.scores[l] > self.scores[-l]:
            return l
        return -l


class CHB:
    """
    Conflict History-based Branching heuristic
    """

    def __init__(self, num_vars, trail, step_chb=0.4, step_min_chb=0.06, step_dec_chb=1e-6):
        self.step_chb = step_chb
        self.step_dec_chb = step_dec_chb
        self.step_min_chb = step_min_chb
        self.num_vars = num_vars
        # scores close to 0
        self.scores = [1e-3] * (2 * num_vars + 1)
        self.scores[0] = 0
        self.trail = trail
        self.conflicts = 0
        self.last_conflict = [0] * (2 * num_vars + 1)

    def decide(self):
        """
        Decide the next literal to assign based on the max score.
        """
        ret = np.argmax(self.scores)

        # ret > self.num_vars: negative literal
        if ret > self.num_vars:
            return ret - (2 * self.num_vars + 1)

        return ret

    def on_assign(self, literal):
        """
        Change sign of the literal's score. (+ => -)
        """
        self.scores[literal] = -self.scores[literal]
        self.scores[-literal] = -self.scores[-literal]

    def on_unassign(self, literal):
        """
        Change sign of the literal's score. (- => +)
        """
        self.scores[literal] = -self.scores[literal]
        self.scores[-literal] = -self.scores[-literal]

    def update_scores(self, learned_clause, conflict, reasons):
        """
        +1 for literals in learned_clause. Apply decay on each literal.
        """
        self.conflicts += 1
        for lit in self.trail.stack:
            multiplier = 1
            if lit in conflict:
                multiplier = 0.9
            rew = multiplier / (self.conflicts - self.last_conflict[lit] + 1)

            if self.scores[lit] > 0:
                self.scores[lit] = (1 - self.step_chb) * \
                    self.scores[lit] + self.step_chb * rew
            else:
                self.scores[lit] = (1 - self.step_chb) * \
                    self.scores[lit] - self.step_chb * rew

        for c in reasons:
            for lit in c.literals:
                self.last_conflict[lit] = self.conflicts

        if self.step_chb > self.step_min_chb:
            self.step_chb -= self.step_dec_chb
