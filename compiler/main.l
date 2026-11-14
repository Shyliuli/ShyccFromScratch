%option noyywrap nounput noinput nounistd
%{
// compiler/main.l
// #![disable_default_static]
#include <stdio.h>
#include <stdlib.h>
#include <alloc/string.shyh>
#include <lexer.shyh>
//一些shycc libshy暂时不稳定的妥协
//shycc暂时不支持的函数，但是我们也用不到
#define isatty(fd) 0
#define fileno(file) 0
//替换默认的输入宏
#define YY_INPUT(buf, result, max_size) \
    do { result = (int)fread(buf, 1, (size_t)max_size, yyin); } while (0)
//让yylex返回Token类型
#define YY_DECL Token yylex(void)

Str token_text(const char *text)
{
    String copy = String::from_cstr(text);
    return copy.as_str();
}
%}

%%

"fn"|"int"|"return"                 { return Token::Keyword(token_text(yytext)); }
[a-zA-Z_][a-zA-Z0-9_]*              { return Token::Symbol(token_text(yytext)); }
[0-9]+                              { return Token::Number(atoi(yytext)); }
\"(\\.|[^\\"\n])*\"                 { return Token::String(token_text(yytext)); }
"->"|[-+*/=]                        { return Token::Operator(token_text(yytext)); }
[(){},;!]                           { return Token::Punct(yytext[0]); }

"//"[^\n]*                          { }
[ \t\r\n]+                          { }

.                                   { }

<<EOF>>                             { return Token::Eof(); }

%%

void scanner_start(const char *source)
{
    yy_scan_string(source);
}

Token scanner_next(void)
{
    return yylex();
}

void scanner_stop(void)
{
    yylex_destroy();
}
