"""
Scrabble query language
| Author: Mike Werezak <mwerezak@gmail.com>
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, IO

from scrabble import LetterPool, WordList
from scrabble.letters import Letter, ALL_LETTERS

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence, Set, Mapping
    from re import Pattern


# Letter Pool Specification Syntax
# e.g. 5!abcc3eqz2n
_letter_re = re.compile(r'(?P<count>\d+)?(?P<letter>[a-z*])', flags=re.IGNORECASE)

def parse_letter_pool(spec: str) -> LetterPool:
    counter = Counter()
    for match in re.finditer(_letter_re, spec):
        captures = match.groupdict()
        letter = Letter(captures['letter'].upper())
        count = int(s) if (s := captures.get('count')) is not None else 1
        counter[letter] += count
    return counter



"""
Word Query Syntax

e.g. |..A..#!s.

. denotes any word from the pool
# denotes any word from the pool, and it will be scored x2
! denotes any word from the pool, and it will be scored x3
A (capital letter) denotes a letter already on the board
a (lowercase letter) denotes a specific letter from the pool which must be used in that position

| denotes the start or end of word. If not present on both ends, the word length is unconstrained
"""

_query_re = re.compile(r'(?P<start>/)?(?P<spec>[a-zA-Z.#!]*)(?P<end>/)?')


@dataclass(frozen=True)
class QueryMatch:
    word: str
    score: int

    def __str__(self) -> str:
        return f'{self.word} {self.score}'


@dataclass(frozen=True)
class LinearQueryMatch(QueryMatch):
    start_pos: int


class LinearQuery:
    def __init__(self, query_string: str, pool: LetterPool):
        self.pool = pool
        self.string = query_string
        self._regex = None
        self._multipliers = {}
        self._fixed_letters = {}
        self._letter_pool = Counter(pool)
        self._parse_query_str(query_string)

    _regex: Pattern | None
    _multipliers: dict[int, int]
    _fixed_letters: dict[int, Letter]
    _eff_pool: LetterPool

    _letter_chars = set(letter.value for letter in ALL_LETTERS)
    def _parse_query_str(self, s: str) -> None:
        match = re.fullmatch(_query_re, s)
        if match is None:
            raise ValueError('invalid query string')

        captures = match.groupdict()
        start = captures['start'] is not None
        end = captures['end'] is not None
        spec = captures['spec']

        if len(spec) == 0:
            return # empty query

        if Letter.WILD in self.pool.keys():
            letter_pat = r'[a-z]'  # allow any letter
        else:
            letters = ''.join(letter.value for letter in self.pool.keys())
            letter_pat = rf'[{letters}]'

        regex_parts = []

        if start:
            regex_parts.append('^')

        for pos, c in enumerate(spec):
            if c == '.':
                regex_parts.append(letter_pat)
            elif c == '#':
                regex_parts.append(letter_pat)
                self._multipliers[pos] = 2
            elif c == '!':
                regex_parts.append(letter_pat)
                self._multipliers[pos] = 3
            elif c.upper() in self._letter_chars:
                letter = Letter(c.upper())
                regex_parts.append(letter.value)
                self._fixed_letters[pos] = letter
                if c.islower():
                    self._letter_pool[letter] -= 1  # remove c from the pool
            else:
                raise ValueError('invalid query part at position {pos}: {c!r}')

        if end:
            regex_parts.append('$')

        shortfall = sum(-c for c in self._letter_pool.values() if c < 0)
        if self._letter_pool[Letter.WILD] < shortfall:
            raise ValueError('query is not satisfiable using the available pool')

        self._regex = re.compile(''.join(regex_parts))

    def _validate_and_build_match(self, word: str, start_pos: int) -> QueryMatch|None:
        # quick check based on word length
        required_letters = len(word) - len(self._fixed_letters)
        if required_letters > self._letter_pool.total():
            return None

        score = 0
        use_letters = Counter()

        check_letters = [
            (self._multipliers.get(pos, 1), pos, Letter(c))
            for idx, c in enumerate(word)
            if (pos := idx - start_pos) not in self._fixed_letters.keys()
        ]

        # process positions with multipliers first
        check_letters.sort(reverse=True)

        for mult, pos, let in check_letters:
            # are there enough letters?
            if use_letters[let] >= self._letter_pool[let]:
                # can we use a wildcard?
                if use_letters[Letter.WILD] >= self._letter_pool[Letter.WILD]:
                    return None
                let = Letter.WILD

            use_letters[let] += 1
            score += let.score * mult

        score += sum(let.score for let in self._fixed_letters.values())

        return LinearQueryMatch(
            word = word,
            start_pos = start_pos,
            score = score,
        )

    # check if word can match using pool alone
    def _match_empty_query(self, word: str) -> QueryMatch|None:
        if len(word) > self._letter_pool.total():
            return None

        score = 0
        use_letters = Counter()
        required_letters = Counter(Letter(c) for c in word)
        for let in sorted(required_letters, key = lambda let: let.score, reverse=True):
            for _ in range(required_letters[let]):
                # are there enough letters?
                if use_letters[let] >= self._letter_pool[let]:
                    # can we use a wildcard?
                    if use_letters[Letter.WILD] >= self._letter_pool[Letter.WILD]:
                        return None
                    let = Letter.WILD

                use_letters[let] += 1
                score += let.score

        return QueryMatch(
            word = word,
            score = score,
        )


    def execute(self, wordlist: WordList) -> Iterable[QueryMatch]:
        if self._regex is None:
            for word in wordlist:
                query_match = self._match_empty_query(word)
                if query_match is not None:
                    yield query_match
            return

        for word in wordlist:
            for re_match in self._regex.finditer(word):
                query_match = self._validate_and_build_match(word, re_match.start())
                if query_match is not None:
                    yield query_match
