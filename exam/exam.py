#!/usr/bin/env python3
"""exp2 检查：按语法层次检查现有 mycc 的 AST 输出和错误诊断。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MYCC = ROOT / "build" / "mycc"
CASES = ROOT / "exam" / "case"

# 每项依次为：层名、输入文件、预期 AST。
EXAMPLES = [
    ("minimal", "minimal.shyc", "(program (fn main (block (return 42))))"),
    (
        "expr", "expr.shyc",
        "(program (fn main (block (return (+ (* (+ 1 2) 3) 4)))))",
    ),
    (
        "expr", "precedence.shyc",
        "(program (fn main (block (return (+ 1 (* 2 3))))))",
    ),
    (
        "expr", "associativity.shyc",
        "(program (fn main (block (return (- (- 10 3) 2)) "
        "(return (/ (/ 24 4) 2)) (return (/ 24 (/ 4 2))))))",
    ),
    (
        "variable", "variable.shyc",
        "(program (fn main (block (let a 10) (let b (+ a 2)) (return b))))",
    ),
    (
        "println", "println.shyc",
        '(program (fn main (block (println "hello") '
        '(println "{} {}" 1 (+ 2 3)) (return 0))))',
    ),
    (
        "program", "shyc_subset.shyc",
        '(program (fn main (block (let a 10) '
        '(let b (+ (* a 10) (- 20 (/ 30 3)))) (println "{}" b) (return a))))',
    ),
    (
        "program", "functions.shyc",
        "(program (fn empty (block)) (fn main (block (return 42))))",
    ),
]

# 每项依次为：输入文件、行、列、错误消息。
ERRORS = [
    ("missing_semicolon.shyc", 3, 1, "syntax error"),
    ("missing_paren.shyc", 2, 18, "syntax error"),
    ("missing_operand.shyc", 2, 16, "syntax error"),
    ("unexpected_eof.shyc", 3, 1, "syntax error"),
    ("illegal_char.shyc", 2, 12, "illegal character '@'"),
    ("unclosed_comment.shyc", 2, 5, "unclosed block comment"),
]


def main():
    groups = {"minimal", "expr", "variable", "println", "program", "error"}
    selected = set(sys.argv[1:]) or groups
    if not selected <= groups:
        print("usage: python3 exam/exam.py [minimal|expr|variable|println|program|error ...]",
              file=sys.stderr)
        return 1
    if not MYCC.is_file():
        print("找不到 build/mycc，请先运行 make build", file=sys.stderr)
        return 1

    checks = [
        (filename, 0, ast + "\n", "")
        for group, filename, ast in EXAMPLES if group in selected
    ]
    if "error" in selected:
        checks.extend(
            (filename, 1, "", f"{CASES / filename}:{line}:{column}: error: {message}\n")
            for filename, line, column, message in ERRORS
        )

    failed = 0
    for filename, code, stdout, stderr in checks:
        try:
            result = subprocess.run(
                [str(MYCC), str(CASES / filename)],
                capture_output=True, text=True, timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"FAIL {filename}: {error}")
            failed += 1
            continue

        actual = (result.returncode, result.stdout, result.stderr)
        expected = (code, stdout, stderr)
        if actual == expected:
            print(f"PASS {filename}")
        else:
            failed += 1
            print(f"FAIL {filename}")
            print(f"  预期 (退出码, stdout, stderr): {expected!r}")
            print(f"  实际 (退出码, stdout, stderr): {actual!r}")

    print(f"{len(checks) - failed}/{len(checks)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
