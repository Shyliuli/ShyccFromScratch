#!/usr/bin/env python3
"""检查 exp2 的小型 ShyC 子集；指定层名时，检查到该层为止。"""
import argparse
import subprocess
from pathlib import Path

GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
BOLD = "\033[1m"
RESET = "\033[0m"

ROOT = Path(__file__).resolve().parent.parent
MYCC = ROOT / "build" / "mycc"
CASES = ROOT / "exam" / "case"
STAGES = ("minimal", "expr", "variable", "call", "control", "function", "program", "error")

# 每项是：所属层、输入文件、完整的预期 AST。最小层已经由示例实现。
EXAMPLES = [
    ("minimal", "minimal.shyc",
     "(program (fn main (params) int (block (return 42))))"),
    ("minimal", "renamed.shyc",
     "(program (fn answer (params) int (block (return 7))))"),
    ("expr", "expr.shyc",
     "(program (fn main (params) int (block (return (+ (* (+ 1 2) 3) 4)))))"),
    ("expr", "precedence.shyc",
     "(program (fn main (params) int (block (return (+ 1 (* 2 3))))))"),
    ("variable", "associativity.shyc",
     "(program (fn main (params) int (block (return (- (- 10 3) 2)) "
     "(return (/ (/ 24 4) 2)) (return (/ 24 (/ 4 2))))))"),
    ("variable", "variable.shyc",
     "(program (fn main (params) int (block "
     "(decl int (var a 10)) (decl int (var b (+ a 2))) (return b))))"),
    ("variable", "unary.shyc",
     "(program (fn main (params) int (block (decl int (var a 3)) "
     "(return (+ (* (- a) (+ 2)) (! 0))))))"),
    ("variable", "assignment.shyc",
     "(program (fn main (params) int (block (decl int (var a 0) (var b)) "
     "(expr (= a (= b 3))) (return (, (, (= a 1) (= b 2)) (+ a b))))))"),
    ("variable", "inferred.shyc",
     "(program (fn main (params) int (block (let a 1) (let-mut b (+ a 2)) "
     "(expr (= b (+ b 1))) (return b))))"),
    ("variable", "compare.shyc",
     "(program (fn main (params) int (block (decl int (var a 1)) "
     "(expr (pre++ a)) (expr (post-- a)) (return (== a (< (+ 1 (* 2 3)) 8))))))"),
    ("variable", "comparisons.shyc",
     "(program (fn main (params) int (block (decl int (var a 1)) "
     "(expr (= a (> a 0))) (expr (= a (<= a 2))) (expr (= a (>= a 0))) "
     "(expr (pre-- a)) (expr (post++ a)) (return a))))"),
    ("call", "calls.shyc",
     "(program (fn main (params) int (block (expr (call ping)) "
     "(return (call add 1 (call twice (+ 2 3)))))))"),
    ("call", "println.shyc",
     '(program (fn main (params) int (block (expr (macro println "hello")) '
     '(expr (macro println "{} {}" 1 (+ 2 3))) (return 0))))'),
    ("call", "macro.shyc",
     '(program (fn main (params) int (block (expr (macro trace "value\\n" 1)) (return 0))))'),
    ("control", "blocks.shyc",
     "(program (fn main (params) int (block (empty) "
     "(block (decl int (var a 1)) (block (expr (= a (+ a 1))))) (return 0))))"),
    ("control", "if.shyc",
     "(program (fn main (params) int (block "
     "(if 1 (if 0 (return 1) (return 2))) (if (! 0) (block (return 3))) (return 0))))"),
    ("control", "loops.shyc",
     "(program (fn main (params) int (block (decl int (var i 3)) "
     "(while i (block (expr (= i (- i 1))) (if i (continue)) (break))) (return i))))"),
    ("function", "functions.shyc",
     "(program (fn empty (params) int (block)) (fn main (params) int (block (return 42))))"),
    ("function", "signatures.shyc",
     "(program (prototype add (params (param int a) (param int b)) int) "
     "(fn empty (params) void (block (return))) "
     "(fn add (params (param int a) (param int b)) int (block (return (+ a b)))) "
     "(fn main (params) int (block (expr (call empty)) (return (call add 20 22)))))"),
    ("function", "empty.shyc",
     "(program (fn empty (params) void (block)) "
     "(fn stop (params) void (block (return))) "
     "(fn main (params) int (block (return 0))))"),
    ("program", "shyc_subset.shyc",
     "(program (fn main (params) int (block (decl int (var a 10)) "
     '(decl int (var b (+ (* a 10) (- 20 (/ 30 3))))) (expr (macro println "{}" b)) (return a))))'),
    ("program", "program.shyc",
     "(program (fn sum (params (param int n)) int (block (let-mut result 0) "
     "(while (> n 0) (block (expr (= result (+ result n))) (expr (post-- n)))) (return result))) "
     "(fn main (params) int (block (decl int (var value (call sum 5))) "
     '(if (== value 15) (expr (macro println "{}" value)) (return 1)) (return 0))))'),
]

# 每项是：输入文件、行、列、错误消息。
ERRORS = [
    ("missing_semicolon.shyc", 3, 1, "syntax error"),
    ("missing_paren.shyc", 2, 18, "syntax error"),
    ("missing_operand.shyc", 2, 16, "syntax error"),
    ("unexpected_eof.shyc", 3, 1, "syntax error"),
    ("missing_argument.shyc", 2, 16, "syntax error"),
    ("stray_else.shyc", 2, 5, "syntax error"),
    ("trailing_token.shyc", 2, 1, "syntax error"),
    ("missing_condition.shyc", 2, 12, "syntax error"),
    ("missing_initializer.shyc", 2, 10, "syntax error"),
    ("illegal_char.shyc", 2, 12, "illegal character '@'"),
    ("unclosed_comment.shyc", 2, 5, "unclosed block comment"),
]


def run(cmd, cwd):
    """沿用 exp1 的命令执行方式，分别保留 stdout 和 stderr。"""
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
        return None, "", f"找不到命令: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return None, "", "超时（60 秒）"
    return p.returncode, p.stdout, p.stderr


def check_output(name, steps, expected):
    """依次运行 steps，最后一步应只向 stdout 输出 expected。"""
    def test(cwd):
        for cmd in steps:
            code, stdout, stderr = run(cmd, cwd)
            if code != 0:
                return cmd, "退出码 0", "没有运行" if code is None else f"退出码 {code}", stdout + stderr
            if cmd is steps[-1] and (stdout, stderr) != (expected, ""):
                return cmd, repr((expected, "")), repr((stdout, stderr)), ""
        return None
    return name, test


def check_error(name, case_name, line, column, message):
    """错误应写入 stderr，stdout 为空，并以退出码 1 结束。"""
    expected = f"{CASES / case_name}:{line}:{column}: error: {message}\n"
    def test(cwd):
        cmd = [str(MYCC), str(CASES / case_name)]
        code, stdout, stderr = run(cmd, cwd)
        if code != 1:
            return cmd, "退出码 1", "没有运行" if code is None else f"退出码 {code}", stdout + stderr
        if (stdout, stderr) != ("", expected):
            return cmd, repr(("", expected)), repr((stdout, stderr)), ""
        return None
    return name, test


def report(index, name, failure):
    cmd, expected, got, output = failure
    print(f"{RED}{BOLD}error[exam{index}]{RESET}{BOLD}: {name}{RESET}")
    print(f"  {BLUE}-->{RESET} {' '.join(cmd)}")
    print(f"   {BLUE}|{RESET}")
    print(f"   {BLUE}= 预期:{RESET} {expected}")
    print(f"   {BLUE}= 得到:{RESET} {got}")
    for line in output.rstrip().splitlines():
        print(f"   {BLUE}|{RESET} {line}")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", nargs="?", choices=STAGES, default="error",
                        help="累积检查到这一层；省略时检查全部")
    args = parser.parse_args()
    selected = STAGES[:STAGES.index(args.stage) + 1]
    cmd = ["make", "build/mycc"]
    code, stdout, stderr = run(cmd, ROOT)
    if code != 0:
        report(0, "build/mycc", (cmd, "退出码 0",
               "没有运行" if code is None else f"退出码 {code}", stdout + stderr))
        return 1

    failures = []
    for i, stage in enumerate(selected, 1):
        tests = [check_output(filename,
                              [[str(MYCC), str(CASES / filename)]], ast + "\n")
                 for group, filename, ast in EXAMPLES if group == stage]
        if stage == "error":
            tests.extend(check_error(filename, filename, line, column, message)
                         for filename, line, column, message in ERRORS)

        failure = None
        for name, test in tests:
            failure = test(ROOT)
            if failure is not None:
                failures.append((i, f"{stage}: {name}", failure))
                break

        if failure is None:
            print(f"{GREEN}[exam{i}] {stage} Passed!{RESET}")
        else:
            print(f"{RED}[exam{i}] {stage} Failed!{RESET}")

    print()
    for i, name, failure in failures:
        report(i, name, failure)

    total = len(selected)
    if failures:
        passed = total - len(failures)
        print(f"{BOLD}{GREEN}{passed} exams passed{RESET}{BOLD}, {RED}{len(failures)} exams failed.{RESET}")
        return 1
    print(f"{BOLD}{GREEN}All {total} exams passed.{RESET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
