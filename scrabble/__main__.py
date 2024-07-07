"""
| Author: Mike Werezak <mwerezak@gmail.com>
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

from scrabble import WORDLISTS, DEFAULT_WORDLIST, WordList
from scrabble.utils import (
    random_pool, 
    load_words_from_text_file_fast,
    load_words_from_text_file_safe,
)
from scrabble.query import LinearQuery, TransverseQuery, parse_letter_pool

if TYPE_CHECKING:
    pass


cli = ArgumentParser(
    description="Scrabble query tool.",
)
cli.set_defaults(action=None)

wordlist = cli.add_mutually_exclusive_group()
wordlist.add_argument(
    '--wordlist', default=DEFAULT_WORDLIST, dest='wordlist',
    help="Select the internal wordlist to use. Available lists: " + ", ".join(sorted(WORDLISTS.keys())),
    metavar="NAME",
)
wordlist.add_argument(
    '--wordfile', default=None, dest='ext_file',
    help="Load wordlist from a text file instead of using an internal wordlist.",
    metavar="FILE",
)
cmds = cli.add_subparsers()


def error_summary(error: BaseException) -> str:
    return f'({type(error).__name__}) {error}'

def load_wordlist_file(args: Namespace) -> WordList:
    print("Reading wordlist...")

    if args.ext_file is not None:
        filepath = args.ext_file
    else:
        filepath = WORDLISTS[args.wordlist]

    try:
        with open(filepath, 'rt') as file:
            wordlist = WordList.load_json(file)
    except Exception as err:
        print(f"Failed to load wordlist from file {filepath}!")
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

    wordlist = load_wordlist_file(args)

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


transverse_query = cmds.add_parser(
    'transverse',
    help="Perform a transverse query."
)
transverse_query.add_argument(
    'letter_pool',
    help="Letter pool specification string.",
    metavar="POOL",
)
transverse_query.add_argument(
    'linear_part',
    help="Linear part of the query.",
    metavar="QUERY"
)
transverse_query.add_argument(
    'context_parts', nargs='*',
    help=(
        "Context parts of the query. One context part must be provided for "
        "each open letter position present in the linear part of the query."
    ),
    metavar="CONTEXT",
)
transverse_query.add_argument(
    '-n', type=int, default=0, dest='max_results',
    help="Limit the query output to the top NUM results.",
    metavar="NUM",
)
transverse_query.set_defaults(action='transverse')


def exec_transverse_query(args: Namespace) -> None:
    try:
        pool = parse_letter_pool(args.letter_pool)
    except Exception as err:
        print(f"Invalid letter specification: {args.letter_pool}")
        print(error_summary(err))
        sys.exit(1)

    wordlist = load_wordlist_file(args)

    query = TransverseQuery(args.linear_part, args.context_parts, pool)

    results = list(query.execute(wordlist))
    results.sort(key=lambda m: (m.score, len(m.word)), reverse=True)

    extra_results = 0
    if args.max_results > 0:
        extra_results = len(results) - args.max_results
        results = results[:args.max_results]

    for match in results:
        print(match)

    if extra_results > 0:
        print(f"({extra_results} more result(s)...)")



def main(args: Namespace|None = None) -> None:
    if args is None:
        args = cli.parse_args()

    if args.wordlist is None:
        args.safe_load = False

    if args.action is None:
        print("No query method selected.")
        sys.exit(0)

    try:
        if args.action == 'linear':
            exec_linear_query(args)
        elif args.action == 'transverse':
            exec_transverse_query(args)
    except Exception as error:
        print(error_summary(error))
        raise
        sys.exit(1)


if __name__ == '__main__':
    main()
