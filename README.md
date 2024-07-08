# Scrabble Query Language

A query language and query engine that looks up a given Scrabble position (letters on the board, open spaces, and crosswords) and produces matching words sorted by score.

The Scrabble query engine is just a tool. It does not play scrabble for you. That said, it is great at taking over the part of the game that involves knowing and forming words from the available letters (i.e. the boring part, sorry Scrabble fans), allowing you to focus on board state and positioning.

Once you are comfortable with the query language, you can quickly enter and compare different potential word locations to weed out promising positions from ones that are not feasible given your current letter set.

This tool was originally created for my own personal use as a result of my friends insisting that I play Scrabble with them. They deserve to be acknowledged as creating it was a great weekend project and it ended up working much better than I expected.

## Requirements
Python 3.12 or newer.
No other dependencies.

## Installation

Put the `scrabble` package somewhere in your PYTHONPATH. Then execute the package, e.g. 
```
python -m scrabble --help
```

## Usage

The scrabble query application uses a command-line interface.

Several query modes are available, however it is recommended to use the 'dynamic' query mode as it is the most ergonomic. The 'linear' and 'transverse' query modes are retained in the CLI for legacy purposes only.

To use the dynamic query mode, use the 'query' subcommand. e.g.
```
python -m scrabble -n 10 query deto*au /.!../ . . .A .LOFT
```
In the above example, the `-n` option is used to limit the number of results. Everything following the word "query" is the query string. The format of the query string is:
```
<LETTER POOL> <WORD SPEC> [<CROSSWORDS>...]
```

### Query Format

A query consists of at least two parts. Each query part is separated by whitespace.

#### Letter Pool

The first part is the letter pool specification. This tells the query engine which letters you
have available to make words. Valid letters are a-z and * for the wildcard. This part of the query is case-insensitive.

#### Word Specification

The second part of the query is the word specification. Each turn in Scrabble you may only place letters in a single line; this part tells the query engine about the constraints on that line. This is the heart of the query, as the engine will try to find matching words that satisfy the string inputted here. This is the only part of the query that is case-sensitive.

This part of the query consists of a sequence of characters:

* `.#!` indicate an open square on the line. `#` and `!` indicate double letter and triple letter bonus squares respectively. These are useful to include as they can affect the ordering of results.

* `A-Z` capital letters indicate a pre-existing letter tile that imposes a constraint on matching words.

* `a-z` lower case letters an open square where you want to constrain the tile placed there to a specific letter from your pool. If you do not actually have the necessary letters in your pool you will get an error message about your query being invalid. This feature was useful before crosswords were added but now it is kind of useless. I may remove it in the future so that query strings can be fully case-insensitive.

* `/` the word specification string can be optionally prefixed or postfixed with a forward slash to indicate that the word must end there. Otherwise the query engine will try to find a match anywhere inside potential words. This is very useful when examining positions close to the edge of a board or near crosswords that you know you can't make.

#### Crosswords

Crosswords may be optionally provided. If no crossword parts are provided then the search will not be constrained by any crosswords. If crossword parts are provided then a crossword part must be provided for every open space in the word specification part. Crossword parts are case-insensitive.

Each crossword part consists of a `.` optionally prefixed or postfixed by letters `a-z`. The letter characters indicate pre-existing letter tiles will constrain your search. The `.` indicates where the word matched by the word specification will cross through. For example:

```
F..
O..
xxx
.A.
.RA
```

Suppose you want to find a word that completely fills the line marked with x's (maybe the third x has a bonus square on it). The appropriate query would be:
```
<LETTER POOL> ... fo. .ar .
```

Note that the word spec has 3 open positions, so 3 crosswords need to be provided. A single `.` is used when there are no letters in the crossing direction that would constrain our query.


### Output
The application will output words that match the query strings, one result per line.
Each line will contain the matching word, followed by any newly formed crosswords, followed finally by the projected score value of the result. The `-n` option may be used to limit the number of result lines.
