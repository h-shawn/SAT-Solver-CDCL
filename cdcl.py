import math

import checker
import preprocessor

from clause import Clause
from literal import Literals
from watchtable import WatchTable
from trail import Trail
from decider import *
from params import *
from mab import UCB
from restarter import *
from subsumption import SubsumptionEliminator


class CDCL:
    def __init__(self, sentence, num_vars):
        self.sentence = sentence
        sentence, self.clauses_eliminated = preprocessor.preprocess(
            sentence, num_vars)
        self.unsat = False
        self.level = 0
        self.num_vars = num_vars
        self.clauses = [Clause(clause) for clause in sentence]
        self.literals = Literals(num_vars)
        self.watchtable = WatchTable(self.clauses, num_vars)
        self.trail = Trail()
        self.conflict = None
        self.scores = [1] * (2 * num_vars + 1)
        self.scores[0] = 0
        self.subsumption_eliminator = SubsumptionEliminator(
            self, ENABLE_SUBSUMPTION_ON_THE_FLY)
        for clause in self.clauses:
            for lit in clause.literals:
                self.scores[lit] += 1

        vsids = VSIDS(self.scores, num_vars, PARAMS_VSIDS_DECAY)
        evsids = EVSIDS(self.scores, num_vars, PARAMS_EVSIDS_INCRE)
        lrb = LRB(num_vars, self.scores, alpha=PARAMS_LRB_ALPHA, alpha_lim=PARAMS_LRB_ALPHA_LIM,
                  epsilon=PARAMS_LRB_ALPHA_EPSILON, decay=PARAMS_LRB_DECAY, strategy=PARAMS_LRB_STRATEGY)
        chb = CHB(num_vars, self.trail, step_chb=PARAMS_CHB_STEP,
                  step_min_chb=PARAMS_CHB_STEP_MIN, step_dec_chb=PARAMS_CHB_STEP_DECAY)
        self.deciders = []
        if HEURISTIC_ENABLE_LRB:
            self.deciders.append(lrb)
        if HEURISTIC_ENABLE_CHB:
            self.deciders.append(chb)
        if HEURISTIC_ENABLE_VSIDS:
            self.deciders.append(vsids)
        if HEURISTIC_ENABLE_EVSIDS:
            self.deciders.append(evsids)
        self.decided_vars = 0
        self.decisions = 0
        self.mab_agent = UCB(len(self.deciders), PARAMS_UCB_BETA)
        self.active_decider = self.mab_agent.run()
        self.chosen = [0] * (2 * num_vars + 1)
        self.conflicts = 0
        self.reduce_lim = PARAMS_REDUCE_LIM
        self.reduces = 0
        if PARAMS_RESTARTER == "CADICAL":
            self.restarter = CadicalRestart(self)
        else:
            self.restarter = LubyRestart()

    def solve(self):
        assignment = self.cdcl_loop()
        if assignment is not None:
            assert checker.check(self.sentence, assignment, self.literals)
        return assignment

    def cdcl_loop(self):
        if not self.solve_unary_lits():
            return None

        while self.trail.len() < self.num_vars:
            if self.unsat:
                return None
            if not self.bcp():
                self.analyze()
            elif self.try_restart():
                self.restart()
            elif self.try_reduce():
                self.reduce()
            elif self.trail.len() < self.num_vars:
                self.decide()

        if self.unsat:
            return None

        return self.restore_eliminated_variables(self.trail.toDict(self.literals))

    def solve_unary_lits(self):
        for clause in self.clauses:
            if len(clause) == 1:
                lit = clause.literals[0]
                if self.literals.get(lit) == 0:
                    self.assign(lit, clause)
                elif not self.literals.sat(lit):
                    # UNSAT
                    self.unsat = True
                    return False

        return True

    def bcp(self):
        self.trail.start_bcp()
        while True:
            lit = self.trail.next()
            if lit == None:
                # Reached top of self.trail.stack. Exit.
                break
            # Check for clauses that might derive new assignments
            lit = -lit
            for clause in self.watchtable.l2c(lit).copy():
                # The watched literals does not sat
                if self.watchtable.sat(clause, self.literals):
                    # the watched literals sat, continue BCP
                    continue
                # Try to update watched literals
                if self.watchtable.update(clause, lit, self.literals):
                    # update success, continue BCP
                    continue
                # Update failed
                other = self.watchtable.get_other_watch(clause, lit)
                if self.literals.get(other) == 0:
                    # Derive a new assignment
                    self.assign(other, clause)
                else:
                    # UNSAT, Backtrack
                    self.conflict = clause
                    return False
        return True  # indicate no conflict; otherwise return the antecedent of the conflict

    def analyze(self):
        """
        Analyze the conflict with first-UIP clause learning.
        """
        self.conflicts += 1
        learned_clause = self.conflict.copy()
        d = self.conflict.deepest_level(self.literals)
        if d == 0:
            self.unsat = True
            return

        ptr = -1
        conflict_side = []
        while not learned_clause.one_lit_at_level(d, self.literals):
            literal = self.trail.stack[ptr]
            clause = self.literals.ante(literal)
            clause.recompute_glue(self.literals)
            ptr -= 1
            # First pop irrelevant assignments
            if -literal in learned_clause.literals:
                learned_clause.resolve(literal, clause)
                conflict_side.append(literal)

        backtrack_level = learned_clause.second_deepest_level(self.literals)
        if backtrack_level < 0:
            self.unsat = True
            return
        self.learn_clause(learned_clause)
        if PARAMS_RESTARTER == "CADICAL":
            self.restarter.update_glucose(learned_clause.glue)

        reasons = []
        for literal in learned_clause.literals:
            r = self.literals.ante(literal)
            if r is not None:
                reasons.append(r)
        if PARAMS_LRB_STRATEGY == LRB.Strategy.CONFLICT_SIDE:
            for d in self.deciders:
                d.update_scores(learned_clause, conflict_side, reasons)
        else:
            for d in self.deciders:
                d.update_scores(learned_clause, self.conflict.literals, reasons)

        self.backtrack(backtrack_level)
        # Immediately derive from the newly learned clause
        d1_lit = self.watchtable.c2l(learned_clause)[0]
        self.assign(d1_lit, learned_clause)

    def decide(self):
        self.decisions += 1
        lit = self.deciders[self.active_decider].decide()
        if self.chosen[lit] == 0:
            self.decided_vars += 1
            self.chosen[lit] = 1
        self.assign(lit, None)

    def learn_clause(self, clause):
        self.subsumption_eliminator.update_and_eliminate(clause)
        clause.compute_glue(self.literals)
        self.clauses.append(clause)
        self.watchtable.append(clause, self.literals)

    def backtrack(self, level):
        lit = self.trail.stack.pop()
        while self.literals.level(lit) > level and len(self.trail.stack) > 0:
            lit = self.unassign(lit)
        if self.literals.level(lit) == level:
            self.trail.stack.append(lit)
        else:
            # Special case if there is nothing in level 0
            # No need to push back.
            self.literals.unassign(lit)
            for d in self.deciders:
                d.on_unassign(lit)
        self.level = level

    def try_restart(self):
        if self.restarter.restart():
            print("Restarting...")
            reward = math.log2(self.decisions) / self.decided_vars
            self.chosen = [0] * (2 * self.num_vars + 1)
            self.decided_vars = 0
            self.decisions = 0
            self.mab_agent.reward(reward)
            self.active_decider = self.mab_agent.run()
            return True
        return False

    def restart(self):
        self.backtrack(0)

    def try_reduce(self):
        if self.conflicts > self.reduce_lim:
            print("Reducing...")
            self.reduces += 1
            delta = 300 * (self.reduces + 1)
            if len(self.sentence) > 1e5:
                delta *= math.log10(len(self.sentence) / 1e4)
            self.reduce_lim = self.conflicts + delta
            return True
        return False

    def reduce(self):
        for c in reversed(self.clauses):
            if c.used == 0:
                self.eliminate_clause(c)
            if c.used > 0:
                c.used -= 1

    def eagerly_subsume(self, clause):
        deleted = 0
        for c in reversed(self.clauses):
            if c.used > 0:
                length = len(clause.literals)
                for lit in c.literals:
                    if lit in clause.literals:
                        length -= 1
                    if length == 0:
                        self.clauses.remove(c)
                        for lit in self.watchtable.c2l(c):
                            self.watchtable.l2c(lit).remove(c)
                        self.watchtable.c2l_watch.pop(c)
                        deleted += 1
                        break
                if deleted == 20:
                    return

    def assign(self, lit, clause):
        if clause == None:
            self.level += 1
        self.trail.push(lit)
        self.literals.assign(lit, self.level, clause)
        for d in self.deciders:
            d.on_assign(lit)

    def unassign(self, lit):
        self.literals.unassign(lit)
        for d in self.deciders:
            d.on_unassign(lit)
        return self.trail.stack.pop()

    def eliminate_clause(self, clause):
        """
        Remove clause from clauses list, watchtable and appearance list.
        """
        if clause.subsuming:
            return
        self.clauses.remove(clause)
        for lit in self.watchtable.c2l(clause):
            self.watchtable.l2c(lit).remove(clause)
        self.watchtable.c2l_watch.pop(clause)
        self.subsumption_eliminator.remove_appearance(clause)

    def restore_eliminated_variables(self, assign):
        """
        Assign values for eliminated variables.
        """
        for l in self.clauses_eliminated:
            clause = list(self.clauses_eliminated[l])
            sat = False
            for lit in clause:
                if assign[abs(lit)] == (lit > 0):
                    sat = True
                    break
            if sat:
                if l > 0:
                    assign[l] = False
                else:
                    assign[-l] = True
            else:
                if l > 0:
                    assign[l] = True
                else:
                    assign[-l] = False
        return assign
