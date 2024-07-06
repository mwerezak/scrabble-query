"""
| Author: Mike Werezak <mwerezak@gmail.com>
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Letter(Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'
    F = 'F'
    G = 'G'
    H = 'H'
    I = 'I'
    J = 'J'
    K = 'K'
    L = 'L'
    M = 'M'
    N = 'N'
    O = 'O'
    P = 'P'
    Q = 'Q'
    R = 'R'
    S = 'S'
    T = 'T'
    U = 'U'
    V = 'V'
    W = 'W'
    X = 'X'
    Y = 'Y'
    Z = 'Z'
    WILD = '*'

    def __str__(self) -> str:
        return self.value.upper()

    @property
    def score(self) -> int:
        return LETTER_SCORES[self]


# set of all letters (not wild)
ALL_LETTERS = set(letter for letter in Letter if letter is not Letter.WILD)


LETTER_SCORES = {
    Letter.A : 1,
    Letter.B : 3,
    Letter.C : 3,
    Letter.D : 2,
    Letter.E : 1,
    Letter.F : 4,
    Letter.G : 2,
    Letter.H : 4,
    Letter.I : 1,
    Letter.J : 8,
    Letter.K : 5,
    Letter.L : 1,
    Letter.M : 3,
    Letter.N : 1,
    Letter.O : 1,
    Letter.P : 3,
    Letter.Q : 10,
    Letter.R : 1,
    Letter.S : 1,
    Letter.T : 1,
    Letter.U : 1,
    Letter.V : 4,
    Letter.W : 4,
    Letter.X : 8,
    Letter.Y : 4,
    Letter.Z : 10,
    Letter.WILD : 0,
}


LETTER_COUNTS = {
    Letter.A: 9,
    Letter.B: 2,
    Letter.C: 2,
    Letter.D: 4,
    Letter.E: 12,
    Letter.F: 2,
    Letter.G: 3,
    Letter.H: 2,
    Letter.I: 9,
    Letter.J: 1,
    Letter.K: 1,
    Letter.L: 4,
    Letter.M: 2,
    Letter.N: 6,
    Letter.O: 8,
    Letter.P: 2,
    Letter.Q: 1,
    Letter.R: 6,
    Letter.S: 4,
    Letter.T: 6,
    Letter.U: 4,
    Letter.V: 2,
    Letter.W: 2,
    Letter.X: 1,
    Letter.Y: 2,
    Letter.Z: 1,
    Letter.WILD: 2
}
