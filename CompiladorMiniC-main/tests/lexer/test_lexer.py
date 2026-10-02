"""Pruebas unitarias para el analizador léxico de Mini C."""

import pytest

from minic.lexer import Lexer, Token, TokenType
from minic.output import format_diagnostic, format_token


def test_empty_source() -> None:
    tokens, diagnostics = Lexer("").scan()
    assert len(diagnostics) == 0
    assert len(tokens) == 1
    assert tokens[0] == Token(TokenType.EOF, "", None, 1, 1)


def test_single_tokens() -> None:
    source = "int while x 42 = + - == != ( ) { } ;"
    tokens, diagnostics = Lexer(source).scan()
    assert len(diagnostics) == 0
    expected_types = [
        TokenType.KW_INT,
        TokenType.KW_WHILE,
        TokenType.IDENTIFIER,
        TokenType.INTEGER_LITERAL,
        TokenType.ASSIGN,
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.EQUAL_EQUAL,
        TokenType.NOT_EQUAL,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected_types
    assert tokens[3].literal == 42


def test_keywords_vs_identifiers() -> None:
    source = "int int2 while whilex _int _while"
    tokens, _ = Lexer(source).scan()
    assert tokens[0].type == TokenType.KW_INT
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[2].type == TokenType.KW_WHILE
    assert tokens[3].type == TokenType.IDENTIFIER
    assert tokens[4].type == TokenType.IDENTIFIER
    assert tokens[5].type == TokenType.IDENTIFIER


def test_integer_literal_values() -> None:
    source = "0 007 12345"
    tokens, _ = Lexer(source).scan()
    assert tokens[0].literal == 0
    assert tokens[1].literal == 7
    assert tokens[1].lexeme == "007"
    assert tokens[2].literal == 12345


def test_max_munch_operators() -> None:
    source = "== = != !"
    tokens, diagnostics = Lexer(source).scan()
    assert tokens[0].type == TokenType.EQUAL_EQUAL
    assert tokens[1].type == TokenType.ASSIGN
    assert tokens[2].type == TokenType.NOT_EQUAL
    # '!' alone is not an operator in SINGLE, produces LEX001
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "LEX001"
    assert diagnostics[0].line == 1
    assert diagnostics[0].column == 9


def test_number_followed_by_letters() -> None:
    source = "12abc"
    tokens, _ = Lexer(source).scan()
    assert len(tokens) == 3  # 12, abc, EOF
    assert tokens[0].type == TokenType.INTEGER_LITERAL
    assert tokens[0].lexeme == "12"
    assert tokens[0].literal == 12
    assert (tokens[0].line, tokens[0].column) == (1, 1)
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].lexeme == "abc"
    assert (tokens[1].line, tokens[1].column) == (1, 3)


def test_negative_number_separation() -> None:
    source = "-5"
    tokens, _ = Lexer(source).scan()
    assert len(tokens) == 3
    assert tokens[0].type == TokenType.MINUS
    assert tokens[0].lexeme == "-"
    assert tokens[1].type == TokenType.INTEGER_LITERAL
    assert tokens[1].lexeme == "5"
    assert tokens[1].literal == 5


def test_positions_and_whitespace() -> None:
    source = "  \t \r\n  x"
    tokens, _ = Lexer(source).scan()
    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].lexeme == "x"
    assert tokens[0].line == 2
    assert tokens[0].column == 3


def test_section_7_case_1() -> None:
    source = "int2 = 12abc;\nwhilex == -5"
    tokens, diagnostics = Lexer(source).scan()
    assert len(diagnostics) == 0

    expected_output = [
        "IDENTIFIER 'int2' 1 1",
        "ASSIGN '=' 1 6",
        "INTEGER_LITERAL '12' 1 8",
        "IDENTIFIER 'abc' 1 10",
        "SEMICOLON ';' 1 13",
        "IDENTIFIER 'whilex' 2 1",
        "EQUAL_EQUAL '==' 2 8",
        "MINUS '-' 2 11",
        "INTEGER_LITERAL '5' 2 12",
        "EOF '' 2 13",
    ]
    actual_output = [format_token(t) for t in tokens]
    assert actual_output == expected_output


def test_section_7_case_2() -> None:
    source = "int x = @;\nx ! = 0; // fin"
    tokens, diagnostics = Lexer(source).scan()

    expected_tokens = [
        "KW_INT 'int' 1 1",
        "IDENTIFIER 'x' 1 5",
        "ASSIGN '=' 1 7",
        "SEMICOLON ';' 1 10",
        "IDENTIFIER 'x' 2 1",
        "ASSIGN '=' 2 5",
        "INTEGER_LITERAL '0' 2 7",
        "SEMICOLON ';' 2 8",
        "IDENTIFIER 'fin' 2 13",
        "EOF '' 2 16",
    ]
    expected_diagnostics = [
        "LEX001 error 1:9 Carácter no reconocido: '@'",
        "LEX001 error 2:3 Carácter no reconocido: '!'",
        "LEX001 error 2:10 Carácter no reconocido: '/'",
        "LEX001 error 2:11 Carácter no reconocido: '/'",
    ]

    actual_tokens = [format_token(t) for t in tokens]
    actual_diagnostics = [format_diagnostic(d) for d in diagnostics]

    assert actual_tokens == expected_tokens
    assert actual_diagnostics == expected_diagnostics
