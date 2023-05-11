import math
import numpy as np


class MabAgent:
    def __init__(self, num_arms):
        self.num_arms = num_arms

    def run(self):
        raise NotImplementedError

    def reward(self, reward):
        raise NotImplementedError


class UCB(MabAgent):
    def __init__(self, num_arms, beta):
        super().__init__(num_arms)
        self.emp_means = np.zeros(self.num_arms)
        self.num_pulls = np.zeros(self.num_arms)
        self.beta = beta
        self.t = 0

    def run(self):
        if self.t < self.num_arms:
            arm = self.t
        else:
            ucb = [val + self.beta * math.sqrt(2 * math.log(self.t + 1) / self.num_pulls[a])
                   for a, val in enumerate(self.emp_means)]
            arm = np.argmax(ucb)
        self.last_pull = arm

        return arm

    def reward(self, reward):
        arm = self.last_pull
        self.emp_means[arm] *= self.num_pulls[arm] / (self.num_pulls[arm] + 1)
        self.emp_means[arm] += reward / (self.num_pulls[arm] + 1)
        self.num_pulls[arm] += 1
        self.t += 1
