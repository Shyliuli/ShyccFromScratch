%{
#include "lexer.shyh"
use std::io::*;
use std::fmt::*;

fn parser_lex(void) -> int;
fn parser_error(const char *message);

SourceManager *input;
int next_token = 0;

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
    let location = input->tokens.data[next_token++];
    let token = location.t;
    let text = input.token_text(location);
    if (token.type() == Token::Keyword) {
        if (text.eq_cstr("fn")) return FN;
        if (text.eq_cstr("int")) return INT;
        if (text.eq_cstr("return")) return RETURN;
        return PARSER_UNDEF;
    }
    if (token.type() == Token::Symbol) {
        parser_lval.text = text;
        return SYMBOL;
    }
    if (token.type() == Token::Number) {
        parser_lval.number = token.Number;
        return NUMBER;
    }
    if (token.type() == Token::Operator) {
        if (text.eq_cstr("->")) return ARROW;
        return PARSER_UNDEF;
    }
    if (token.type() == Token::Punct) {
        return token.Punct;
    }
    if (token.type() == Token::Eof) {
        return PARSER_EOF;
    }
    return PARSER_UNDEF;
}
fn parser_error(const char *message) {
    let location = input->tokens.data[next_token - 1];
    eprintln("{}:{}:{}: error: syntax error",
        input->input_path,
        input.get_line(location.from),
        input.get_col(location.from));
}

pub fn parse_program(SourceManager *source) -> int {
    input = source;
    next_token = 0;
    let status = parser_parse();
    if (status == 0) println("{}", root);
    return status == 0 ? 0 : 1;
}
