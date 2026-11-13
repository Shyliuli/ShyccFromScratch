%option noyywrap nounput noinput nounistd never-interactive
%{
#include <stdlib.h>
#include "lexer.shyh"

#define YY_DECL Token scanner_next(void)

// 与 compiler/main.l 一样，直接用 fread 读取输入。
#define YY_INPUT(buf, result, max_size) \
    do { result = (int)fread(buf, 1, (size_t)max_size, yyin); } while (0)
%}

%%

[0-9]+       { return Token::Number(atoi(yytext)); }
[-+*/]       { return Token::Operator(yytext[0]); }
[()]         { return Token::Punct(yytext[0]); }
[ \t\r\n]+   { }
.            { return Token::Unknown(yytext[0]); }
<<EOF>>      { return Token::Eof; }

%%

void scanner_stop(void)
{
    yylex_destroy();
}
