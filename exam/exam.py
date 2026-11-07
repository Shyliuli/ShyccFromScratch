#!/usr/bin/env python3
"""exp1 检查：mycc 的 Token 输出、错误诊断和构建目标。"""
import subprocess
import sys
import tempfile
from pathlib import Path

GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
BOLD = "\033[1m"
RESET = "\033[0m"

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MYCC = ROOT / "build" / "mycc"
SHY_MYCC = ROOT / "build" / "mycc.sfs"
CASE_DIR = HERE / "case"
README_CASE = CASE_DIR / "shyc_subset.c"

README_OUTPUT = (
    "[Keyword(fn), Symbol(main), Punct('('), Punct(')'), Operator(->), "
    "Keyword(int), Punct('{'), Keyword(int), Symbol(a), Operator(=), Number(10), "
    "Punct(';'), Keyword(int), Symbol(b), Operator(=), Symbol(a), Operator(*), "
    "Number(10), Operator(+), Punct('('), Punct('('), Number(20), Punct(')'), "
    "Operator(-), Punct('('), Number(30), Operator(/), Number(3), Punct(')'), "
    "Punct(')'), Punct(';'), Symbol(println), Punct('!'), Punct('('), "
    "String(\"\\\"{}\\\"\"), Punct(','), Symbol(b), Punct(')'), Punct(';'), "
    "Keyword(return), Symbol(a), Punct(';'), Punct('}'), Eof]\n"
)

BLOCK_COMMENT_OUTPUT = (
    "[Keyword(fn), Symbol(main), Punct('('), Punct(')'), Operator(->), "
    "Keyword(int), Punct('{'), Keyword(return), Number(42), Punct(';'), "
    "Punct('}'), Eof]\n"
)

COMPARE_OUTPUT = (
    "[Keyword(fn), Symbol(main), Punct('('), Punct(')'), Operator(->), "
    "Keyword(int), Punct('{'), Keyword(int), Symbol(a), Operator(=), Number(1), "
    "Operator(<), Number(2), Punct(';'), Keyword(int), Symbol(b), Operator(=), "
    "Number(3), Operator(>), Number(2), Punct(';'), Keyword(int), Symbol(c), "
    "Operator(=), Symbol(a), Operator(==), Symbol(b), Punct(';'), Keyword(int), "
    "Symbol(d), Operator(=), Symbol(a), Operator(<=), Symbol(b), Punct(';'), "
    "Keyword(int), Symbol(e), Operator(=), Symbol(a), Operator(>=), Symbol(b), "
    "Punct(';'), Keyword(return), Symbol(e), Punct(';'), Punct('}'), Eof]\n"
)

INCDEC_OUTPUT = (
    "[Keyword(fn), Symbol(main), Punct('('), Punct(')'), Operator(->), "
    "Keyword(int), Punct('{'), Keyword(int), Symbol(a), Operator(=), Number(1), "
    "Punct(';'), Symbol(a), Operator(++), Punct(';'), Symbol(a), Operator(--), "
    "Punct(';'), Keyword(return), Symbol(a), Punct(';'), Punct('}'), Eof]\n"
)


def run(cmd, cwd):
    """运行命令，返回 (退出码, 输出)。命令不存在时退出码为 None。"""
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=60,
        )
    except FileNotFoundError:
        return None, f"找不到命令: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return None, "超时（60 秒）"
    return p.returncode, p.stdout + p.stderr


def check_output(name, steps, expected):
    """依次运行 steps，最后一步的输出应等于 expected。"""
    def test(cwd):
        for cmd in steps:
            code, out = run(cmd, cwd)
            if code != 0:
                return cmd, "退出码 0", "没有运行" if code is None else f"退出码 {code}", out
            if cmd is steps[-1] and out != expected:
                return cmd, repr(expected), repr(out), ""
        return None
    return name, test


def check_error(name, case_name, line, column, message):
    """词法错误应按 clang 格式写入 stderr，并以退出码 1 结束。"""
    expected = f"{CASE_DIR / case_name}:{line}:{column}: error: {message}\n"
    def test(cwd):
        cmd = [str(MYCC), str(CASE_DIR / case_name)]
        code, out = run(cmd, cwd)
        if code != 1:
            return cmd, "退出码 1", "没有运行" if code is None else f"退出码 {code}", out
        if out != expected:
            return cmd, repr(expected), repr(out), ""
        return None
    return name, test


def check_makefile():
    """shy_build 和 build 都应保留，并且两者运行结果一致。"""
    def test(_cwd):
        cmd = ["make", "-B", "shy_build"]
        code, out = run(cmd, ROOT)
        if code != 0:
            return cmd, "退出码 0", "没有运行" if code is None else f"退出码 {code}", out
        if not SHY_MYCC.exists():
            return cmd, str(SHY_MYCC), "文件不存在", out

        cmd = ["shyemu-user", str(SHY_MYCC), str(README_CASE)]
        code, out = run(cmd, ROOT)
        if code != 0:
            return cmd, "退出码 0", "没有运行" if code is None else f"退出码 {code}", out
        if out != README_OUTPUT:
            return cmd, repr(README_OUTPUT), repr(out), ""

        cmd = ["make", "-B", "build"]
        code, out = run(cmd, ROOT)
        if code != 0:
            return cmd, "退出码 0", "没有运行" if code is None else f"退出码 {code}", out

        cmd = [str(MYCC), str(README_CASE)]
        code, out = run(cmd, ROOT)
        if code != 0:
            return cmd, "退出码 0", "没有运行" if code is None else f"退出码 {code}", out
        if out != README_OUTPUT:
            return cmd, repr(README_OUTPUT), repr(out), ""

        cmd = ["make", "-B"]
        code, out = run(cmd, ROOT)
        if code != 0:
            return cmd, "退出码 0", "没有运行" if code is None else f"退出码 {code}", out
        return None
    return "Makefile targets", test


TESTS = [
    check_output(
        "README case (gift)",
        [[str(MYCC), str(README_CASE)]],
        README_OUTPUT,
    ),
    check_makefile(),
    check_output(
        "block comment",
        [[str(MYCC), str(CASE_DIR / "block_comment.c")]],
        BLOCK_COMMENT_OUTPUT,
    ),
    check_error("unclosed block comment", "unclosed_comment.c", 2, 5, "unclosed block comment"),
    check_error("illegal character", "illegal_char.c", 3, 5, "illegal character '@'"),
    check_output(
        "comparison operators",
        [[str(MYCC), str(CASE_DIR / "compare.c")]],
        COMPARE_OUTPUT,
    ),
    check_output(
        "increment and decrement",
        [[str(MYCC), str(CASE_DIR / "incdec.c")]],
        INCDEC_OUTPUT,
    ),
]


def report(index, name, failure):
    cmd, expected, got, output = failure
    print(f"{RED}{BOLD}error[test{index}]{RESET}{BOLD}: {name}{RESET}")
    print(f"  {BLUE}-->{RESET} {' '.join(cmd)}")
    print(f"   {BLUE}|{RESET}")
    print(f"   {BLUE}= 预期:{RESET} {expected}")
    print(f"   {BLUE}= 得到:{RESET} {got}")
    for line in output.rstrip().splitlines():
        print(f"   {BLUE}|{RESET} {line}")
    print()


def main():
    failures = []
    with tempfile.TemporaryDirectory() as cwd:
        for i, (name, test) in enumerate(TESTS, 1):
            failure = test(cwd)
            if failure is None:
                print(f"{GREEN}[test{i}] {name} Passed!{RESET}")
            else:
                print(f"{RED}[test{i}] {name} Failed!{RESET}")
                failures.append((i, name, failure))

    print()
    for i, name, failure in failures:
        report(i, name, failure)

    total = len(TESTS)
    if failures:
        passed = total - len(failures)
        print(f"{BOLD}{GREEN}{passed} test passed{RESET}{BOLD}, {RED}{len(failures)} test failed.{RESET}")
        sys.exit(1)
    print(f"{BOLD}{GREEN}All {total} test passed.{RESET}")


if __name__ == "__main__":
    main()
