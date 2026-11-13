.PHONY: build shy_build playground
build: build/mycc

build/mycc: compiler/main.l compiler/main.shyc compiler/lexer.shyh
	mkdir -p build
	# 使用flex生成scannner.c
	flex -L -o build/scanner.c compiler/main.l
	# -U__STDC_VERSION__只是为了避免ShyCC的实现问题
	shycc --target=host -U__STDC_VERSION__ -Icompiler -c build/scanner.c -o build/scanner.o
	shycc --target=host -Icompiler compiler/main.shyc build/scanner.o -o build/mycc
shy_build: build/mycc.sfs

build/mycc.sfs: compiler/main.l compiler/main.shyc compiler/lexer.shyh
	mkdir -p build
	# 使用flex生成scannner.c
	flex -L -o build/scanner.c compiler/main.l
	# -U__STDC_VERSION__只是为了避免ShyCC的实现问题
	shycc --target=shy-user -U__STDC_VERSION__ -Icompiler -c build/scanner.c -o build/scanner-shy.sobj
	shycc --target=shy-user -Icompiler compiler/main.shyc build/scanner-shy.sobj -o build/mycc.sfs

playground: build/calc/main build/ast/main

build/calc/main: playground/calc.y playground/arithmetic.l playground/lexer.shyh
	mkdir -p build/calc
	bison -Wall --no-lines --defines=build/calc/parser.shyh -o build/calc/parser.shyc playground/calc.y
	flex -L -o build/calc/scanner.shyc playground/arithmetic.l
	shycc --target=host -U__STDC_VERSION__ -Iplayground -Ibuild/calc -c build/calc/scanner.shyc -o build/calc/scanner.o
	shycc --target=host -Iplayground -Ibuild/calc build/calc/parser.shyc build/calc/scanner.o -o build/calc/main

build/ast/main: playground/ast.y playground/arithmetic.l playground/lexer.shyh
	mkdir -p build/ast
	bison -Wall --no-lines --defines=build/ast/parser.shyh -o build/ast/parser.shyc playground/ast.y
	flex -L -o build/ast/scanner.shyc playground/arithmetic.l
	shycc --target=host -U__STDC_VERSION__ -Iplayground -Ibuild/ast -c build/ast/scanner.shyc -o build/ast/scanner.o
	shycc --target=host -Iplayground -Ibuild/ast build/ast/parser.shyc build/ast/scanner.o -o build/ast/main
