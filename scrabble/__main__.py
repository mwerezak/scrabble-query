"""
| Author: Mike Werezak <mwerezak@gmail.com>
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

from scrabble import DEFAULT_WORDLIST
from scrabble.utils import load_words, random_pool
from scrabble.query import LinearQuery, parse_letter_pool

if TYPE_CHECKING:
    pass


cli = ArgumentParser(
    description="Scrabble query tool.",
)

cli.add_argument(
    'letter_pool',
    help="Letter pool specification string.",
    metavar="POOL",
)
cli.add_argument(
    'query_string', nargs='?', default='',
    help="Query string. Omit to search using pool alone.",
    metavar="QUERY"
)
cli.add_argument(
    '-n', type=int, default=0, dest='max_results',
    help="Limit the output to the top NUM results.",
    metavar="NUM",
)
cli.add_argument(
    '--wordlist', default=None, dest='wordlist',
    help="Optional path to external wordlist file.",
    metavar="FILE",
)


def error_summary(error: BaseException) -> str:
    return f'({type(error).__name__}) {error}'


def main(args: Namespace|None = None) -> None:
    if args is None:
        args = cli.parse_args()

    try:
        pool = parse_letter_pool(args.letter_pool)
    except Exception as err:
        print(f"Invalid letter specification: {args.letter_pool}")
        print(error_summary(err))
        sys.exit(1)

    print("Reading wordlist...")
    words_path = args.wordlist or DEFAULT_WORDLIST
    try:
        with open(words_path, 'rt') as file:
            wordlist = load_words(file)
    except Exception as err:
        print(f"Failed to load wordlist from file {words_path}!")
        print(error_summary(err))
        sys.exit(1)

    print(f"Loaded {len(wordlist)} words.")

    query = LinearQuery(args.query_string, pool)

    results = list(query.execute(wordlist))
    results.sort(key=lambda m: (m.score, len(m.word)), reverse=True)

    extra_results = None
    if args.max_results > 0:
        extra_results = len(results) - args.max_results
        results = results[:args.max_results]

    for match in results:
        print(match)

    if extra_results is not None:
        print(f"({extra_results} more result(s)...)")



if __name__ == '__main__':
    main()
