# exp1 词法分析

本节我们实现一个词法分析器。我们选择ShyC的一个子集，它基本上是C。完成本章节后，你将能够对下面的代码进行词法分析:
```c
//exam/case/shyc_subset.c 
fn main()->int{
    int a=10;
    int b=a*10+((20)-(30/3));
    println!("{}",b);
    return a;
}
```

## 1. 为什么需要词法分析器
因为字符串太复杂了！比如说对于下面的题目：

### 加法
输入：x+y=

输出：计算结果

保证x和y都是1~100的整数

示例输入：
```
1+2=
```
输出:
```
3
```

我们可能会写出这样的代码:
```
// playground/example1.c
// btw，你可以试试shycc编译这个文件...很神奇吧，ShyC是C的不严格超集
#include<stdio.h>

int main(void) {
    int x = 0;
    int y = 0;
    int plus = 0;
    int c;

    while ((c = getchar()) != '=' && c != EOF) {
        if (c == '+') {
            plus = 1;
        } else if (c >= '0' && c <= '9') {
            if (plus) {
                y = y * 10 + c - '0';
            } else {
                x = x * 10 + c - '0';
            }
        }
    }

    printf("%d\n", x + y);
    return 0;
}

```
其中有一个很复杂的`while{....}`(相对于1+1=2这种计算);它其实只做了一个事情，把字符串解析为计算机可以看得懂的形式。
词法分析器做的就是这样的事情！只不过，它面对的程序还要复杂的多，多到不能“一拍脑门”就想清楚。
好在在那个还没有AI的时代，已经有代码仙人总结出了通用的词法分析算法，相信同学们在编译原理课上已经学过了。

可能会有同学问为什么不用`scanf("%d+%d=",&x,&y)`?实际上`scanf`内部(某种角度来说)就是一个小型的词法分析器，做了相同的事情。

## 正规式
词法分析本质上就是将一串字符串按照特定的规则且分成一个个词(Token)，其中正规式(Regular Expression,又叫正则表达式)是描述这些规则的形式化工具。
它本质上可以用来描述一个词张什么样，比如数字就是1或多个范围在`0`~`9`的字符.下面是本实验会用到的最小化的正规式：
```
a: 一个字符a
ab: 先a后b
a|b: a或b
a*: 任意多个a
a+ 1个或多个a
a? 1个或0个a
(ab)* 任意多个`ab`组合
[a-z] `a`到`z`中的任意一个字符
[a-z0-9] `a`到`z`或`0`到`9`中的任意一个字符
[a-zA-Z0-9_] `a`到`z`、`A`到`Z`、`0`到`9`或`_`中的任意一个字符
. 任意一个字符
[^ab]任何不是a或b的字符
\  转义字符，例如 `\.` 表示一个点号`\\`表示一个`\`
```

例如，对于c语言变量名，可以用`[a-zA-Z_][a-zA-Z0-9_]*` 来描述。即开头为以字母或下划线开头，后跟任意多个字母、数字或下划线。

对于我们本节实验课要分析的代码，我们只需要识别出以下几类 Token：

| Token 类型 | 正规式 / 匹配内容 | 示例 |
| --- | --- | --- |
| 关键字 `Keyword` | `fn`、`int`、`return` | `fn`、`int`、`return` |
| 符号 `Symbol` | `[a-zA-Z_][a-zA-Z0-9_]*` | `main`、`a`、`b`、`println` |
| 整数 `Number` | `[0-9]+` | `10`、`20`、`30`、`3` |
| 字符串 `String` | `"((\\.)|[^"\\])*"` | `"{}"` |
| 运算符 `Operator` | `+`、`-`、`*`、`/`、`=`、`->` | `+`、`*`、`->` |
| 标点 `Punct` | `(`、`)`、`{`、`}`、`;`、`,`、`!` | `(`、`{`、`;` |
| 文件结束 `EOF` | 输入结束 | — |
| 注释 | `//[^\n]*`| `// exam/case/shyc_subset.c` |
| 块注释 | `/* ... */` | `/* ignored */` |
| 空白 |`[ \t\r\n]+` | 空格、换行 |
| Eof  | 手动添加到最后| 文件结束 |

其中可能引起困惑的：
1. String 实际上它的意思是: “”包裹的，内部有无数多个`\`+任意字符或者非非`"`非`\`的字符。
2. 注释： //开头的，后续无数个非换行字符。

## flex

怎么把上面的正规式变成实际可跑的代码？我们可以使用使用 `flex` 工具，把正规式写成规则文件（`.l`），再生成 C 代码。
flex的安装：

Debian / Ubuntu：

```sh
sudo apt update
sudo apt install flex
```

Arch Linux：

```sh
sudo pacman -S flex
```

安装后确认：

```sh
flex --version
```

能输出版本号就说明安装成功。

## 构建

在仓库根目录执行：

```sh
make
```

生成的可执行文件是 `build/mycc`。用它对示例代码做词法分析：

```sh
./build/mycc exam/case/shyc_subset.c
```

## 编写第一个flex文件

有关flex的语法，请参考[utsc编译原理](https://ustc-compiler-principles.github.io/2023/lab1/Flex)
我们在这里将上面的正规式写入flex文件的第二部分，并按需返回。

```lex
%option noyywrap nounput noinput nounistd
// compiler/main.l
%{
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

<<EOF>>                             { return Token::Eof; }

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
```

## 运行
我们提供了一个简单的`main.shyc`.它读取文件，并循环调用scanner_next()直到EOF，然后打印每个token。
运行make build，然后随意使用playground/下的代码测试!

## exam
为了检验你的理解，我们增加了以下exam，运行 `python3 exam/exam.py` 以检查。
### 1. run it
第一个exam仅仅会检查你是否成功编译程序了并输出正确的token序列。
### 2. makefile
作为第一个练习，我们会检查你对基础工具的理解。请修改`Makefile`，增加目标"shy_build"，
它应该产生shyISA的mycc.sfs.提示:使用 --target=shy-user 来生成目标。
ShyISA 目标的对象文件扩展名是 `.sobj`，例如 `build/scanner.sobj`。
我们还会检查make build的默认行为是否被破坏.
### 3. 词法报错与块注释
尝试让编译器能够处理块注释(返回空)。
并处理以下两种词法错误:
    1. 未闭合的块注释
    2. 非法字符(比如@)

### 4. 实现比较符号
实现 > < == >= <=的识别。
### 5. 实现自增自减。
实现++和--的识别。

### 输出约定

- 块注释 `/* ... */` 不产生 Token。
- 比较运算符和自增自减都作为 `Operator` 输出：`Operator(>)`、`Operator(<)`、`Operator(==)`、`Operator(>=)`、`Operator(<=)`、`Operator(++)`、`Operator(--)`。
- 词法错误不进入 Token 数组，写入 stderr：`<file>:<line>:<column>: error: <message>`(你可以使用eprintln("...",...))。
  - 非法字符 `@` 的消息是 `illegal character '@'`。
  - 未闭合块注释的位置指向 `/*` 起点，消息是 `unclosed block comment`。
- 有词法错误时不向 stdout 输出 Token 数组，进程退出码为 1。
- `make shy_build` 生成 `build/mycc.sfs`；`shyemu-user build/mycc.sfs <case>` 的输出应与 `build/mycc <case>` 一致。
