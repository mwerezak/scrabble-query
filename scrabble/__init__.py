from __future__ import annotations

import json
import os
import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self, IO
    from collections.abc import Iterable, Set, Mapping


type LetterPool = Mapping[Letter, int]


WORDLIST_PATH = os.path.join(os.path.dirname(__file__), 'lists')

WORDLISTS = {
    fileparts[0] : os.path.join(WORDLIST_PATH, filename)
    for filename in os.listdir(WORDLIST_PATH)
    if (fileparts := os.path.splitext(filename))[1] == '.json'
}

DEFAULT_WORDLIST = 'NWL2023'

WORDLIST_VERSION = 1

def calc_checksum(words: Iterable[str]) -> str:
    h = hashlib.sha1()
    for word in sorted(words):
        h.update(word.encode('ascii'))
    return h.hexdigest()

class WordListError(Exception): pass

@dataclass(frozen=True)
class WordListMeta:
    date: str
    description: str
    checksum: str

class WordList(set[str]):
    def __init__(self, meta: WordListMeta, words: Iterable[str]):
        self.meta = meta
        super().__init__(words)

    def write_json(self, file: IO, *args, **kwargs) -> None:
        data = dict(
            version = WORDLIST_VERSION,
            description = self.meta.description,
            date = self.meta.date,
            checksum = self.meta.checksum,
            words = sorted(self),
        )
        json.dump(data, file, *args, **kwargs)

    @classmethod
    def load_json(cls, file: IO) -> Self:
        data = json.load(file)

        if data['version'] != WORDLIST_VERSION:
            raise WordListError('wordlist version mismatch')

        checksum = calc_checksum(data['words'])
        if checksum != data['checksum']:
            raise WordListError('wordlist checksum mismatch')

        meta = WordListMeta(
            date = data['date'],
            description = data['description'],
            checksum = checksum,
        )
        return cls(meta, data['words'])
