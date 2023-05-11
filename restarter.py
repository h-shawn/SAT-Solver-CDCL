import math
from params import *

class RestartAlgo:
    def restart(self):
        pass


class LubyRestart(RestartAlgo):
    def __init__(self, base=PARAMS_RESTART_LUBY_BASE):
        self.counter = 0
        self.l = []
        self.mult = 1
        self.minu = 0
        self.base = base
        self.limit = self.base * self.gen()

    def restart(self):
        self.counter += 1
        if self.counter == self.limit:
            self.limit = self.base * self.gen()
            self.counter = 0
            return True
        return False

    def gen(self):
        size = len(self.l)
        to_fill = size+1
        if math.log2(to_fill+1).is_integer():
            self.l.append(self.mult)
            self.mult *= 2
            self.minu = size+1
        else:
            self.l.append(self.l[to_fill-self.minu-1])
        return self.l[size]

    def resetLuby(self):
        self.l = []
        self.mult = 1
        self.minu = 0

class CadicalRestart(RestartAlgo):
    """
    Simplified implementation of CaDiCaL's restarting policy. Not implementing its reuse_trail trick.
    """
    class Reluctant:
        def __init__(self):
            self.period = 0
            self.trigger = False
            self.u = 0
            self.v = 0
            self.limit = 0
            self.countdown = 0
            self.limited = False

        def tick(self):
            if self.period == 0:
                return
            if self.trigger:
                return
            self.countdown -= 1
            #print(self.countdown, self.period, self.trigger, (self.u & -self.u), self.v)
            if self.countdown > 0:
                return
            if (self.u & -self.u) == self.v:
                self.u += 1
                self.v = 1
            else:
                self.v *= 2
            if self.limited and self.v > self.limit:
                self.u = 1
                self.v = 1
            self.countdown = self.v * self.period
            self.trigger = True

        def triggered(self):
            if not self.trigger:
                return False
            self.trigger = False
            return True

        def enable(self, p, l):
            self.u = 1
            self.v = 1
            self.period = p
            self.countdown = p
            self.trigger = False
            if l <= 0:
                self.limited = False
            else:
                self.limited = True
                self.limit = l

        def disable(self):
            self.period = 0
            self.trigger = False


    def __init__(self, cdcl):
        self.cdcl = cdcl
        self.stable = True
        self.inc_stabilize = PARAMS_RESTART_CADICAL_STABLIZE_STABLIZEINT
        self.lim_stabilize = self.cdcl.conflicts + self.inc_stabilize
        self.ema_glucose_fast = 1
        self.ema_glucose_slow = 1
        self.ema_glucose_fast_saved = 1
        self.ema_glucose_slow_saved = 1
        self.lim_restart = PARAMS_RESTART_CADICAL_INTERVAL
        self.reluctant = self.Reluctant()
        if PARAMS_RESTART_CADICAL_STABLIZE and PARAMS_RESTART_CADICAL_RELUCTANT > 0:
            self.reluctant.enable(PARAMS_RESTART_CADICAL_RELUCTANT, PARAMS_RESTART_CADICAL_RELUCTANT_MAX)
        else:
            self.reluctant.disable()
        self.last_conflict = 0

    def swap_averages(self):
        self.ema_glucose_fast, self.ema_glucose_fast_saved = self.ema_glucose_fast_saved, self.ema_glucose_fast
        self.ema_glucose_slow, self.ema_glucose_slow_saved = self.ema_glucose_slow_saved, self.ema_glucose_slow

    def stabilizing(self):
        if not PARAMS_RESTART_CADICAL_STABLIZE: 
            return False
        if self.cdcl.conflicts >= self.lim_stabilize:
            self.stable = not self.stable
            self.inc_stabilize *= PARAMS_RESTART_CADICAL_STABLIZE_FACTOR
            if self.inc_stabilize > PARAMS_RESTART_CADICAL_STABLIZE_STABLIZEMAXINT:
                self.inc_stabilize = PARAMS_RESTART_CADICAL_STABLIZE_STABLIZEMAXINT
            self.lim_stabilize = self.cdcl.conflicts + self.inc_stabilize
            if self.lim_stabilize <= self.cdcl.conflicts:
                self.lim_stabilize = self.cdcl.conflicts + 1
            self.swap_averages()
        return self.stable

    def restart(self):
        if self.stabilizing():
            return self.reluctant.triggered()
        if self.cdcl.conflicts <= self.lim_restart:
            return False
        margin = 1.0 + PARAMS_RESTART_CADICAL_MARGIN
        r = (margin * self.ema_glucose_slow) <= self.ema_glucose_fast
        if r:
            self.lim_restart = self.cdcl.conflicts + PARAMS_RESTART_CADICAL_INTERVAL
            self.last_conflict = self.cdcl.conflicts
        return r

    def update_glucose(self, glue):
        if self.stable:
            self.reluctant.tick()
        self.ema_glucose_fast = (1 - PARAMS_RESTART_CADICAL_ALPHA_GLUCOSE_FAST) * self.ema_glucose_fast + PARAMS_RESTART_CADICAL_ALPHA_GLUCOSE_FAST * glue
        self.ema_glucose_slow = (1 - PARAMS_RESTART_CADICAL_ALPHA_GLUCOSE_SLOW) * self.ema_glucose_slow + PARAMS_RESTART_CADICAL_ALPHA_GLUCOSE_SLOW * glue
