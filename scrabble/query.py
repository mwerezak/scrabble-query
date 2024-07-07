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


class QueryError(Exception): pass


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
            letter_pat = r'[A-Z]'  # allow any letter
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
            raise QueryError('query is not satisfiable using the available pool')

        self._regex = re.compile(''.join(regex_parts))

    def _validate_and_build_match(self, word: str, start_pos: int) -> LinearQueryMatch|None:
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
            score = score,
            start_pos = start_pos,
        )

    # check if word can match using pool alone
    def _match_empty_query(self, word: str) -> LinearQueryMatch|None:
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

        return LinearQueryMatch(
            word = word,
            score = score,
            start_pos = 0,
        )


    def execute(self, wordlist: WordList) -> Iterable[LinearQueryMatch]:
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

"""
TransverseQuery Syntax

..sAs       <- linear query
.           <- context for each position
asda.asdas
.
.
.


..A# asda. ss.sas 

"""

_context_re = re.compile(r'(?P<before>[a-z]*)\.(?P<after>[a-z]*)', flags=re.IGNORECASE)


@dataclass(frozen=True)
class TransverseQueryMatch(QueryMatch):
    start_pos: int
    extra_words: Sequence[QueryMatch]

    def total_score(self) -> int:
        return self.score + sum(extra.score for extra in self.extra_words)

    def __str__(self) -> str:
        words = " ".join([self.word, *(extra.word for extra in self.extra_words)])
        return f"{words} {self.total_score()}"


class TransverseQuery:
    def __init__(self, linear: str, context: Sequence[str], pool: LetterPool):
        self.pool = pool
        self.string = linear
        self.context = context

        self._open_letters = {}
        self._context_parts = {}
        self._multipliers = {}
        self._fixed_letters = {}
        self._letter_pool = Counter(pool)

        self._parse_query_str(linear)
        self._parse_context_parts(context)

    _start: bool
    _end: bool
    _multipliers: dict[int, int]
    _fixed_letters: dict[int, Letter]
    _open_letters: dict[int, set[Letter]]
    _context_parts: dict[int, tuple[str, str]]
    _eff_pool: LetterPool

    _letter_chars = set(letter.value for letter in ALL_LETTERS)
    def _parse_query_str(self, s: str) -> None:
        match = re.fullmatch(_query_re, s)
        if match is None:
            raise ValueError('invalid query string')

        captures = match.groupdict()
        self._start = captures['start'] is not None
        self._end = captures['end'] is not None
        spec = captures['spec']

        if Letter.WILD in self.pool.keys():
            letter_pat = r'[a-z]'  # allow any letter
        else:
            letters = ''.join(letter.value for letter in self.pool.keys())
            letter_pat = rf'[{letters}]'

        for pos, c in enumerate(spec):
            if c == '.':
                self._open_letters[pos] = set()
            elif c == '#':
                self._open_letters[pos] = set()
                self._multipliers[pos] = 2
            elif c == '!':
                self._open_letters[pos] = set()
                self._multipliers[pos] = 3
            elif c.upper() in self._letter_chars:
                letter = Letter(c.upper())
                self._fixed_letters[pos] = letter
                if c.islower():
                    self._letter_pool[letter] -= 1  # remove c from the pool
            else:
                raise ValueError('invalid query part at position {pos}: {c!r}')

        shortfall = sum(-c for c in self._letter_pool.values() if c < 0)
        if self._letter_pool[Letter.WILD] < shortfall:
            raise QueryError('query is not satisfiable using the available pool')


    def _parse_context_parts(self, context: Sequence[str]) -> None:
        if len(context) != len(self._open_letters):
            raise ValueError(
                "incorrect number of context parts: "
                f"query has {len(self._open_letters)} open letter positions, "
                f"but only {len(context)} context parts were provided"
            )

        open_pos = sorted(self._open_letters.keys())
        for pos, part in zip(open_pos, context, strict=True):
            match = _context_re.fullmatch(part)
            if match is None:
                raise ValueError(f'invalid context part: {part}')

            captures = match.groupdict()
            before, after = captures['before'], captures['after']
            if before or after:
                self._context_parts[pos] = before.upper(), after.upper()

    # for each open letter, 
    def _build_linear_query_regex(self, wordlist: WordList) -> Optional[Pattern]:
        if Letter.WILD in self.pool.keys():
            any_letter = r'[A-Z]'  # allow any letter
        else:
            letters = ''.join(letter.value for letter in self.pool.keys())
            any_letter = rf'[{letters}]'  # just letters from the pool


        letter_pos = {
            *self._open_letters.keys(),
            *self._fixed_letters.keys(),
        }
        assert len(letter_pos) == len(self._open_letters) + len(self._fixed_letters)
        letter_pos = sorted(letter_pos)

        regex_parts = []
        if self._start:
            regex_parts.append('^')

        for pos in letter_pos:
            if (letter := self._fixed_letters.get(pos)) is not None:
                regex_parts.append(letter.value)
            elif (pair := self._context_parts.get(pos)) is not None:
                before, after = pair

                allowed = self._get_allowed_letters_from_context(before, after, wordlist)
                if len(allowed) == 0:
                    return None  # no possible words

                letters = ''.join(letter.value for letter in allowed)
                regex_parts.append(rf'[{letters}]')
            else:
                regex_parts.append(any_letter)  # allow any letter

        if self._end:
            regex_parts.append('$')

        return re.compile(''.join(regex_parts))

    def _get_allowed_letters_from_context(self, before: str, after: str, wordlist: WordList) -> list[Letter]:
        """Return letter -> score"""
        if Letter.WILD in self.pool.keys():
            candidates = ALL_LETTERS
        else:
            candidates = self.pool.keys() # just letters from the pool

        allowed_letters = []
        for letter in candidates:
            candidate_word = before + letter.value + after
            if candidate_word in wordlist:
                allowed_letters.append(letter)
        return allowed_letters

    def _validate_and_build_match(self, word: str, start_pos: int) -> TransverseQueryMatch|None:
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

        extra_words = []
        for mult, pos, let in check_letters:
            # are there enough letters?
            if use_letters[let] >= self._letter_pool[let]:
                # can we use a wildcard?
                if use_letters[Letter.WILD] >= self._letter_pool[Letter.WILD]:
                    return None
                let = Letter.WILD

            use_letters[let] += 1
            score += let.score * mult

            # if a transverse word was formed in this position, add that to the score
            parts = self._context_parts.get(pos)
            if parts is not None:
                extra_score = score  # letter appears in both words
                for part in parts:
                    extra_score += sum(Letter(c).score for c in part)

                before, after = parts
                extra_match = QueryMatch(
                    word = before + let.value + after,
                    score = extra_score,
                )
                extra_words.append(extra_match)

        score += sum(let.score for let in self._fixed_letters.values())

        return TransverseQueryMatch(
            word = word,
            start_pos = start_pos,
            score = score,
            extra_words = extra_words,
        )

    def execute(self, wordlist: WordList) -> Iterable[TransverseQueryMatch]:
        regex = self._build_linear_query_regex(wordlist)
        if regex is None:
            return

        for word in wordlist:
            for re_match in regex.finditer(word):
                query_match = self._validate_and_build_match(word, re_match.start())
                if query_match is not None:
                    yield query_match
