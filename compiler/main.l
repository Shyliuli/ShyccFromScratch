%option noyywrap nounput noinput nounistd
%{
// compiler/main.l
// #![disable_default_static]
#include <stdio.h>
#include <stdlib.h>
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

int current_line = 1;
int current_column = 1;
usize current_offset = 0;
usize token_from = 0;
usize token_to = 0;
/*对于块注释，我们希望定位块注释开始的地方，因此需要额外维护line和column*/
int comment_line = 1;
int comment_column = 1;

#define YY_USER_ACTION                            \
    do {                                          \
        token_from = current_offset;               \
        token_to = token_from + (usize)yyleng;     \
        current_offset = token_to;                 \
        for (int i = 0; i < yyleng; i++) {         \
            if (yytext[i] == '\n') {               \
                current_line++;                    \
                current_column = 1;                \
            } else {                               \
                current_column++;                  \
            }                                      \
        }                                          \
    } while (0);

int comment_start_line(void)
{
    return comment_line;
}

int comment_start_column(void)
{
    return comment_column;
}
int scanner_line(void)
{
    return current_line;
}
int scanner_column(void)
{
    return current_column;
}
%}

%x COMMENT

%%

\/\*                                {comment_line=current_line; comment_column=current_column-2; BEGIN(COMMENT); comment_start();}
<COMMENT>"*/"                       { BEGIN(INITIAL); comment_end();}
<COMMENT><<EOF>>                    { return Token::Eof(); }
<COMMENT>(.|\n)                     { }
"fn"|"int"|"void"|"return"|"let"|"mut"|"if"|"else"|"while"|"break"|"continue" { return Token::Keyword(); }
[a-zA-Z_][a-zA-Z0-9_]*              { return Token::Symbol(); }
[0-9]+                              { return Token::Number(atoi(yytext)); }
\"(\\.|[^\\"\n])*\"                 { return Token::String(); }
"->"|[-+*/=><]|[><=]=|"++"|"--"     { return Token::Operator(); }
[(){},;!]                           { return Token::Punct(yytext[0]); }

"//"[^\n]*                          { }
[ \t\r\n]+                          { }

.                                   { return Token::Unknown(); }

<<EOF>>                             { return Token::Eof(); }

%%

void scanner_start(const char *source)
{
    current_line = 1;
    current_column = 1;
    current_offset = 0;
    yy_scan_string(source);
}

Token scanner_next(void)
{
    return yylex();
}

TokenLoc scanner_next_loc(void)
{
    Token token = yylex();
    usize from = token.type() == Token::Eof ? current_offset : token_from;
    usize to = token.type() == Token::Eof ? current_offset : token_to;
    TokenLoc location = {token, from, to};
    return location;
}

void scanner_stop(void)
{
    yylex_destroy();
}
