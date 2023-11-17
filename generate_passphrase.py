#!/usr/bin/env python3
from __future__ import annotations

import re
import secrets
import sys
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from io import TextIOBase
from pathlib import Path
from typing import Never, assert_never

import click

VALID_WORD_PATTERN = re.compile("(?P<word>[\w-]+)")


class InvalidWordlist(click.ClickException):
    file_path: Path
    file_format: WordlistFormat
    lineno: int

    def __init__(
        self, reason: str, *, lineno: int, file_path: Path, file_format: WordlistFormat
    ):
        assert lineno >= 1
        super().__init__(
            f"Invalid worldist not in {file_format.value} format: {reason} ({file_path}:{lineno})"
        )
        self.lineno = lineno
        self.file_path = file_path
        self.file_format = file_format


class WordlistFormat(Enum):
    PLAIN = "plain"
    DICELIST_EFF = "dicelist-eff"

    @cached_property
    def _line_pattern(self) -> re.Pattern[str]:
        match self:
            case WordlistFormat.PLAIN:
                return VALID_WORD_PATTERN
            case WordlistFormat.DICELIST_EFF:
                return re.compile("\d+\s*(?P<word>\S*)")
            case _ as unreachable:
                assert_never(unreachable)

    def parse(self, file: TextIOBase, *, file_path: Path) -> list[Word]:
        result: list[Word] = []
        pattern = self._line_pattern
        for lineno, line in enumerate(file, start=1):

            def bad_line(reason: str) -> Never:
                raise InvalidWordlist(
                    reason, lineno=lineno, file_path=file_path, file_format=self
                )

            line = line.strip()
            # Skip blank lines
            if not line:
                continue
            if (match := pattern.fullmatch(line)) is None:
                bad_line("Not a valid line")
            word = match["word"]
            assert word is not None
            if VALID_WORD_PATTERN.fullmatch(word) is None:
                bad_line(f"Invalid word {word!r}")
            result.append(Word(index=len(result), word=word))
        return result

    def __str__(self) -> str:
        return self.value


@dataclass
class Word:
    word: str
    index: int

    def __post_init__(self) -> None:
        if VALID_WORD_PATTERN.fullmatch(self.word) is None:
            raise ValueError(f"Invalid word: {self.word!r}")

    def describe(self) -> str:
        return f"index {self.index}: {self.word!r}"


@click.command
@click.option(
    "--wordlist-format",
    "wordlist_format_name",
    type=click.Choice([fmt.value for fmt in WordlistFormat]),
    help="The format of the wordlist file",
    required=True,
)
@click.option(
    "--wordlist",
    "wordlist_path",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    help="The file that contains the list of words to use",
    required=True,
)
@click.option(
    "--count",
    "-n",
    "word_count",
    type=click.IntRange(min=1),
    help="The number of words to use",
    prompt="Please specify the number of words to generate",
)
@click.option(
    "--join-char",
    "join_char",
    help="The character to join the words together",
    default=" ",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppresses the logging output",
)
def generate_passphrase(
    wordlist_format_name: str,
    wordlist_path: Path,
    word_count: int,
    quiet: bool,
    join_char: str,
) -> None:
    if len(join_char) != 1:
        raise click.ClickException(
            f"The join char must be a single character, but got {join_char!r}"
        )
    wordlist_format = WordlistFormat(wordlist_format_name)
    with open(wordlist_path) as wordlist_file:
        wordlist = wordlist_format.parse(wordlist_file, file_path=wordlist_path)
    result_words: list[str] = []
    for i in range(word_count):
        pick = secrets.choice(wordlist)
        if not quiet:
            print(f"{i:02} picked", pick.describe(), file=sys.stderr)
        result_words.append(pick.word)
    if not quiet:
        print(file=sys.stderr)
    assert len(result_words) == word_count > 0
    print(join_char.join(result_words))


if __name__ == "__main__":
    generate_passphrase()
