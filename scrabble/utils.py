"""
| Author: Mike Werezak <mwerezak@gmail.com>
"""

from __future__ import annotations

import random
from collections import Counter
from typing import TYPE_CHECKING

from scrabble import WordList, LetterPool
from scrabble.letters import Letter, ALL_LETTERS, LETTER_COUNTS

if TYPE_CHECKING:
    pass


def load_words_from_text_file_safe(file: IO[str]) -> WordList:
    words = set()
    for word in file.readlines():
        word = word.strip().upper()
        if not all(Letter(c) in ALL_LETTERS for c in word):
            raise ValueError(f'invalid word: {word}')
        words.add(word)
    return words

def load_words_from_text_file_fast(file: IO[str]) -> WordList:
    return { word.strip().upper() for word in file.readlines() }


def random_pool() -> LetterPool:
    letters, counts = zip(*LETTER_COUNTS.items())
    pool = random.sample(letters, 7, counts=counts)
    return Counter(pool)
