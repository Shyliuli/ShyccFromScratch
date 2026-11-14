%{
#include "lexer.shyh"
use std::io::*;
use std::fmt::*;

fn parser_lex(void) -> int;
fn parser_error(const char *message);

Vec<Token> *input_tokens;
int next_token = 0;
Str input_path;

/* 示例只有固定形状的树，先保存两个会变化的叶子。 */
struct Function {
    Str name;
    int value;
};
Function root;

impl Display for Function {
    fn display(const self *node, WriterRef *out) -> int {
        return write!(out, "(program (fn {} (params) int (block (return {}))))",
            node.name, node.value);
    }
}
%}

%define api.prefix {parser_}
%union {
    Str text;
    int number;
}
%token FN INT RETURN ARROW
%token <text> SYMBOL
%token <number> NUMBER

%%

program:
    FN SYMBOL '(' ')' ARROW INT '{' RETURN NUMBER ';' '}' {
        root.name = $2;
        root.value = $9;
    }
;

%%

fn parser_lex(void) -> int {
    let token = input_tokens->data[next_token++];
    switch (token) {
    case Token::Keyword: {
        let word = token.Keyword;
        if (word.eq(Str::from_cstr("fn"))) return FN;
        if (word.eq(Str::from_cstr("int"))) return INT;
        if (word.eq(Str::from_cstr("return"))) return RETURN;
        return PARSER_UNDEF;
    }
    case Token::Symbol:
        parser_lval.text = token.Symbol;
        return SYMBOL;
    case Token::Number:
        parser_lval.number = token.Number;
        return NUMBER;
    case Token::Operator:
        if (token.Operator.eq(Str::from_cstr("->"))) return ARROW;
        return PARSER_UNDEF;
    case Token::Punct:
        return token.Punct;
    case Token::Eof:
        return PARSER_EOF;
    default:
        return PARSER_UNDEF;
    }
}

fn parser_error(const char *message) {
    eprintln("{}: error: syntax error", input_path);
}

pub fn parse_program(Vec<Token> *tokens, Str input_file) -> int {
    input_tokens = tokens;
    next_token = 0;
    input_path = input_file;
    let status = parser_parse();
    if (status == 0) println("{}", root);
    return status == 0 ? 0 : 1;
}
