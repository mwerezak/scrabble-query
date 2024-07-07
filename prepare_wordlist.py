"""
| Author: Mike Werezak <mwerezak@gmail.com>
"""

from __future__ import annotations

import sys
import os.path
import itertools
from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

from scrabble import WordList, WordListMeta, calc_checksum
from scrabble.letters import Letter, ALL_LETTERS

if TYPE_CHECKING:
    pass


cli = ArgumentParser(
    description="Wordlist tool."
)
cli.add_argument(
    'input',
    help = "Input file.",
    metavar = "INPUT",
)
cli.add_argument(
    'output', nargs='?', default=None,
    help = "Output file.",
    metavar = "OUTPUT",
)
cli.add_argument(
    '--skip', type=int, default=0, dest='skip',
    help = "Skip the first NUM header lines.",
    metavar = "NUM",
)
cli.add_argument(
    '--desc', default="", dest='desc',
    help = "Description text.",
    metavar = "TEXT",
)
cli.add_argument(
    '--date', default="", dest='date',
    help = "Date text.",
    metavar = "TEXT"
)

def error_summary(error: BaseException) -> str:
    return f'({type(error).__name__}) {error}'

def load_words_from_input_file(file: IO[str], args: Namespace) -> set[str]:
    allowed_chars = set(let.value for let in ALL_LETTERS)

    words = set()
    for raw_word in itertools.islice(file.readlines(), args.skip, None):
        # remove any definition parts
        word, *_ = raw_word.split(maxsplit=1)

        if not word:
            continue

        if not all(c in allowed_chars for c in word):
            raise ValueError(f'invalid word: {raw_word}')
        words.add(word)
    return words

def read_words_file(args: Namespace) -> set[str]:
    print("Reading wordlist...")
    try:
        with open(args.input, 'rt') as file:
            wordlist = load_words_from_input_file(file, args)
    except Exception as err:
        print(f"Failed to load input file {args.input}!")
        print(error_summary(err))
        sys.exit(1)

    print(f"Loaded {len(wordlist)} words.")

    return wordlist

def main(args: Namespace|None = None) -> None:
    if args is None:
        args = cli.parse_args()

    output = args.output
    if output is None:
        base, _ = os.path.splitext(args.input)
        output = base + '.json'

    if os.path.exists(output):
        print(f"File already exists: {output}")
        sys.exit(1)

    words = read_words_file(args)
    checksum = calc_checksum(words)
    print(f"Calculate checksum: {checksum}")

    meta = WordListMeta(
        date = args.date,
        description = args.desc,
        checksum = checksum,
    )
    wordlist = WordList(meta, words)

    with open(output, 'wt') as file:
        wordlist.write_json(file, indent=2)


if __name__ == '__main__':
    main()
