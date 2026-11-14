%{
#include "lexer.shyh"

use std::io::*;
use std::fmt::*;

fn yylex(void) -> int;
fn yyerror(const char *message);

int result = 0;
%}

/* 语义值是表达式的计算结果。 */
%define api.value.type {int}
%token NUMBER

%%

input: expr { result = $1; };

/* expr、term、factor 分层表达优先级；单符号规则默认执行 $$ = $1。 */
expr:
    term
  | expr '+' term { $$ = $1 + $3; }
  | expr '-' term { $$ = $1 - $3; }
;

term:
    factor
  | term '*' factor { $$ = $1 * $3; }
  | term '/' factor {
        if ($3 == 0) {
            yyerror("division by zero");
            YYABORT;
        }
        $$ = $1 / $3;
    }
;

factor:
    NUMBER
  | '(' expr ')' { $$ = $2; }
;

%%

fn yylex(void) -> int {
    let token = scanner_next();
    switch (token) {
    case Token::Number:
        /* 返回符号编号，通过 yylval 另传数字的实际值。 */
        yylval = token.Number;
        return NUMBER;
    case Token::Operator:
        return token.Operator;
    case Token::Punct:
        return token.Punct;
    case Token::Unknown:
        return YYUNDEF;
    case Token::Eof:
        return YYEOF;
    }
}

fn yyerror(const char *message) {
    eprintln("error: {}", Str::from_cstr(message));
}

fn main() -> int {
    let status = yyparse();
    scanner_stop();
    if (status != 0) {
        return 1;
    }
    println!("{}", result);
    return 0;
}
