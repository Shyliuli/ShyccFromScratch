#!/usr/bin/env python3
"""exp0 检查：工具链能运行，hello world 能以两种方式编译运行。"""
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
HELLO = HERE / "hello.c"


def run(cmd, cwd):
    """运行命令，返回 (退出码, 输出)。命令不存在时退出码为 None。"""
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return None, f"找不到命令: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return None, "超时（60 秒）"
    return p.returncode, p.stdout + p.stderr


def check_runs(cmd):
    """只要求命令能运行且退出码为 0。"""
    def test(cwd):
        code, out = run(cmd, cwd)
        if code == 0:
            return None
        return cmd, "退出码 0", "没有运行" if code is None else f"退出码 {code}", out
    return " ".join(cmd), test


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


TESTS = [
    check_runs(["shycc", "--version"]),
    check_runs(["shyc", "--version"]),
    check_runs(["shyasm", "--version"]),
    check_runs(["shyld", "--version"]),
    check_runs(["shyemu", "--version"]),
    check_runs(["clang", "--version"]),
    check_output(
        "hello world (shy)",
        [["shycc", str(HELLO), "-o", "hello.sfs"], ["shyemu", "hello.sfs"]],
        "hello world\n",
    ),
    check_output(
        "hello world (host)",
        [["shycc", "--target", "host", str(HELLO), "-o", "hello.elf"], ["./hello.elf"]],
        "hello world\n",
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
