from __future__ import annotations

import os.path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Set, Mapping


type LetterPool = Mapping[Letter, int]
type WordList = Collection[str]


DEFAULT_WORDLIST = os.path.join(os.path.dirname(__file__), 'Collins-2019.txt')
