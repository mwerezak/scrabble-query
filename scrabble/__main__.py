"""
| Author: Mike Werezak <mwerezak@gmail.com>
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

from scrabble import DEFAULT_WORDLIST
from scrabble.utils import (
    random_pool, 
    load_words_from_text_file_fast,
    load_words_from_text_file_safe,
)
from scrabble.query import LinearQuery, parse_letter_pool

if TYPE_CHECKING:
    pass


cli = ArgumentParser(
    description="Scrabble query tool.",
)
cli.add_argument(
    '--wordlist', default=None, dest='wordlist',
    help="Optional path to external wordlist file.",
    metavar="FILE",
)
cli.add_argument(
    '--unsafe-load', action='store_false', dest='safe_load',
    help=(
        "Use this to get a huge speedup if the wordlist file has already been sanitized. "
        "Always enabled when using the internal wordlist."
    )
)
cmds = cli.add_subparsers()


def error_summary(error: BaseException) -> str:
    return f'({type(error).__name__}) {error}'

def load_wordlist_file(filepath: str, safe: bool) -> WordList:
    print("Reading wordlist...")
    filepath = filepath or DEFAULT_WORDLIST
    try:
        with open(filepath, 'rt') as file:
            if safe:
                wordlist = load_words_from_text_file_safe(file)
            else:
                wordlist = load_words_from_text_file_fast(file)
    except Exception as err:
        print(f"Failed to load wordlist from text file {filepath}!")
        print(error_summary(err))
        sys.exit(1)

    print(f"Loaded {len(wordlist)} words.")

    return wordlist


linear_query = cmds.add_parser(
    'linear',
    help="Perform a linear query."
)
linear_query.add_argument(
    'letter_pool',
    help="Letter pool specification string.",
    metavar="POOL",
)
linear_query.add_argument(
    'query_string', nargs='?', default='',
    help="Query string. Omit to search using pool alone.",
    metavar="QUERY"
)
linear_query.add_argument(
    '-n', type=int, default=0, dest='max_results',
    help="Limit the query output to the top NUM results.",
    metavar="NUM",
)
linear_query.set_defaults(action='linear')


def exec_linear_query(args: Namespace) -> None:
    try:
        pool = parse_letter_pool(args.letter_pool)
    except Exception as err:
        print(f"Invalid letter specification: {args.letter_pool}")
        print(error_summary(err))
        sys.exit(1)

    wordlist = load_wordlist_file(args.wordlist, args.safe_load)

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



def main(args: Namespace|None = None) -> None:
    if args is None:
        args = cli.parse_args()

    if args.wordlist is None:
        args.safe_load = False

    if args.action == 'linear':
        exec_linear_query(args)



if __name__ == '__main__':
    main()
