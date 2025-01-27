from enum import Enum

import mmh3


class Treatment(Enum):
    C = 0
    T1 = 1


class Split(Enum):
    HALF_HALF = 2
    FOUR_WAY = 4
    FIVE_WAY = 5
    SEVEN_WAY = 7


class Experiment:
    """
    Represents a single A/B experiment. Assigns
    any user to one of the treatments based on
    experiment name and user ID.
    An example usage::
        experiment = Experiments.AA
        if experiment.assign(user) == Treatment.C:
            # do control actions
            ...
        elif experiment.assign(user) == Treatment.T1:
            # do treatment actions
            ...
    """

    def __init__(self, name: str, split: Split):
        self.name = name
        self.split = split
        self.hash = mmh3.hash(self.name)

    def assign(self, user: int) -> Treatment:
        user_hash = mmh3.hash(str(user), self.hash, False)
        return Treatment(user_hash % self.split.value)

    def __repr__(self):
        return f"{self.name}:{self.split}"


class Experiments:
    """
    A static container for all the existing experiments.
    """

    # TODO Seminar 6 step 5: Configure RECOMMENDERS A/B experiment
    ULTRA_POWER = Experiment("ULTRA_POWER", Split.HALF_HALF)
    CONTEXTUAL = Experiment("CONTEXTUAL", Split.HALF_HALF)

    def __init__(self):
        self.experiments = [Experiments.ULTRA_POWER]
