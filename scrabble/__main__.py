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
from scrabble.query import LinearQuery, TransverseQuery, QueryMatch, parse_letter_pool

if TYPE_CHECKING:
    from collections.abc import Collection


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

cli.add_argument(
    '-n', type=int, default=0, dest='max_results',
    help="Limit the query output to the top NUM results.",
    metavar="NUM",
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


def print_query_results(results: Collection[QueryMatch], max_results: int) -> None:
    extra_results = 0
    if max_results > 0:
        extra_results = len(results) - max_results
        results = results[:max_results]

    for match in results:
        print(match)

    if extra_results > 0:
        print(f"({extra_results} more result(s)...)")


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
    'linear_part', nargs='?', default='',
    help="Query string. Omit to search using pool alone.",
    metavar="QUERY"
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

    query = LinearQuery(args.linear_part, pool)

    results = list(query.execute(wordlist))
    results.sort(key=lambda m: (m.score, len(m.word)), reverse=True)

    print_query_results(results, args.max_results)


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

    print_query_results(results, args.max_results)


dynamic_query = cmds.add_parser(
    'query',
    help="Perform a query."
)
dynamic_query.add_argument(
    'letter_pool',
    help="Letter pool specification string.",
    metavar="POOL",
)
dynamic_query.add_argument(
    'linear_part',
    help="Linear part of the query.",
    metavar="QUERY"
)
dynamic_query.add_argument(
    'context_parts', nargs='*',
    help=(
        "Context parts of the query. If no context is given, a linear query will be performed. "
        "Otherwise a transverse query will be performed."
    ),
    metavar="CONTEXT",
)
dynamic_query.set_defaults(action='dynamic')

def exec_dynamic_query(args: Namespace) -> None:
    if args.context_parts:
        exec_transverse_query(args)
    else:
        exec_linear_query(args)


def main(args: Namespace|None = None) -> None:
    if args is None:
        args = cli.parse_args()

    if args.wordlist is None:
        args.safe_load = False

    if args.action is None:
        print("No query method selected.")
        sys.exit(0)

    try:
        if args.action == 'dynamic':
            exec_dynamic_query(args)
        elif args.action == 'linear':
            exec_linear_query(args)
        elif args.action == 'transverse':
            exec_transverse_query(args)
    except Exception as error:
        print(error_summary(error))
        raise
        sys.exit(1)


if __name__ == '__main__':
    main()
