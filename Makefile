.PHONY: build
build: build/mycc

build/mycc: compiler/main.l compiler/main.shyc compiler/lexer.shyh
	mkdir -p build
	# 使用flex生成scannner.c
	flex -L -o build/scanner.c compiler/main.l
	# -U__STDC_VERSION__只是为了避免ShyCC的实现问题
	shycc --target=host -U__STDC_VERSION__ -Icompiler -c build/scanner.c -o build/scanner.o
	shycc --target=host -Icompiler compiler/main.shyc build/scanner.o -o build/mycc
