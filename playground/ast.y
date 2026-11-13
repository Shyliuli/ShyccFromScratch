%{
#include "lexer.shyh"

use std::io::*;
use std::fmt::*;
use alloc::vec::*;

fn yylex(void) -> int;
fn yyerror(const char *message);

struct Binary {
    char op;
    int left;
    int right;
};

enum Node {
    Number(int),
    Binary(Binary),
};

/* 节点统一存放，左右孩子和根节点都用数组下标表示。 */
Vec<Node> nodes = {0};
int root = 0;

fn binary(char op, int left, int right) -> int {
    Binary children = {op, left, right};
    nodes.push(Node::Binary(children));
    return nodes.len - 1;
}

/* 子树递归写入同一个 Writer，不生成中间字符串。 */
impl Display for Node {
    fn display(const self *node, WriterRef *out) -> int {
        switch (*node) {
        case Node::Number:
            return write!(out, "{}", node.payload.Number);
        case Node::Binary:
            return write!(out, "({} {} {})", node.payload.Binary.op,
                nodes.data[node.payload.Binary.left],
                nodes.data[node.payload.Binary.right]);
        }
    }
}
%}

/* NUMBER 的语义值是数字本身，expr、term、factor 的语义值是节点下标。 */
%define api.value.type {int}
%token NUMBER

%%

input: expr { root = $1; };

expr:
    term
  | expr '+' term { $$ = binary('+', $1, $3); }
  | expr '-' term { $$ = binary('-', $1, $3); }
;

term:
    factor
  | term '*' factor { $$ = binary('*', $1, $3); }
  | term '/' factor { $$ = binary('/', $1, $3); }
;

factor:
    NUMBER {
        nodes.push(Node::Number($1));
        $$ = nodes.len - 1;
    }
  /* 括号只影响树的形状，直接传递内部节点，不创建新节点。 */
  | '(' expr ')' { $$ = $2; }
;

%%

fn yylex(void) -> int {
    let token = scanner_next();
    switch (token) {
    case Token::Number:
        yylval = token.payload.Number;
        return NUMBER;
    case Token::Operator:
        return token.payload.Operator;
    case Token::Punct:
        return token.payload.Punct;
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
    if (status == 0) {
        println!("{}", nodes.data[root]);
    }
    nodes.drop();
    return status == 0 ? 0 : 1;
}
