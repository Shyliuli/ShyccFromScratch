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
