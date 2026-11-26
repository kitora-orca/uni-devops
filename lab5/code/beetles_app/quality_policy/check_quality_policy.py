"""Проверка запретов на ослабление контроля качества проекта."""

import ast
import io
import re
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_COVERAGE = 40

# Разрешены только эти обоснованные исключения.
ALLOWED_EXCEPTIONS = {
    ("tests/test_main.py", "S105", 'password = "test_password"'): (
        "Фиктивный пароль для тестирования хеширования и авторизации"
    ),
    ("tests/conftest.py", "E402", "from database import DB_CONFIG"): (
        "Импорт после настройки тестовой БД защищает рабочую БД"
    ),
}

PYTHON_FILES = [
    ROOT / "main.py",
    ROOT / "database.py",
    *sorted((ROOT / "tests").glob("test_*.py")),
    ROOT / "tests" / "conftest.py",
]

EXCEPTION_RE = re.compile(r"\b(noqa|nosec)\b(?:\s*:\s*([A-Z]\d+))?", re.I)
SKIP_MARKERS = {"skip", "skipif", "xfail"}


def check_python_file(path: Path) -> list[str]:
    if not path.is_file():
        return [f"Отсутствует файл: {path.relative_to(ROOT)}"]

    errors = []
    source = path.read_text(encoding="utf-8-sig")
    relative_path = path.relative_to(ROOT).as_posix()
    lines = source.splitlines()

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type != tokenize.COMMENT:
                continue
            match = EXCEPTION_RE.search(token.string)
            if not match:
                continue

            line_number = token.start[0]
            rule = (match.group(2) or "").upper()
            source_line = lines[line_number - 1]
            standalone = source_line.lstrip().startswith("#")

            # Это поясняющий комментарий, а не директива на строке кода.
            if (
                relative_path == "tests/conftest.py"
                and standalone
                and rule == "E402"
                and "импорт" in source_line.lower()
            ):
                continue

            allowed = any(
                file_name == relative_path
                and allowed_rule == rule
                and fragment in source_line
                for file_name, allowed_rule, fragment in ALLOWED_EXCEPTIONS
            )
            if not allowed:
                errors.append(
                    f"{relative_path}:{line_number}: "
                    "исключение noqa/nosec не разрешено"
                )
    except tokenize.TokenError as exc:
        errors.append(f"{relative_path}: ошибка разбора комментариев: {exc}")

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return errors + [f"{relative_path}:{exc.lineno}: {exc.msg}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "pytest"
                and func.attr in SKIP_MARKERS
            ):
                errors.append(
                    f"{relative_path}:{node.lineno}: запрещён pytest.{func.attr}()"
                )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for decorator in node.decorator_list:
                target = (
                    decorator.func
                    if isinstance(decorator, ast.Call)
                    else decorator
                )
                if (
                    isinstance(target, ast.Attribute)
                    and target.attr in SKIP_MARKERS
                    and isinstance(target.value, ast.Attribute)
                    and target.value.attr == "mark"
                    and isinstance(target.value.value, ast.Name)
                    and target.value.value.id == "pytest"
                ):
                    errors.append(
                        f"{relative_path}:{node.lineno}: "
                        f"запрещён декоратор pytest.mark.{target.attr}"
                    )

    return errors


def check_verify_command() -> list[str]:
    makefile = ROOT / "Makefile.ps1"
    if not makefile.is_file():
        return ["Не найден Makefile.ps1"]

    content = makefile.read_text(encoding="utf-8-sig")
    errors = []
    required_commands = {
        "-m quality_policy.check_quality_policy": "Проверка политики",
        "-m ruff check": "Ruff",
        "-m bandit": "Bandit",
        "-m pytest": "Pytest",
    }
    for command, name in required_commands.items():
        if command not in content:
            errors.append(f"В Makefile.ps1 отсутствует {name}")

    match = re.search(r"--cov-fail-under=(\d+)", content)
    if not match:
        errors.append("Не указан порог покрытия")
    elif int(match.group(1)) < MIN_COVERAGE:
        errors.append(
            f"Порог покрытия нельзя снижать ниже {MIN_COVERAGE}%"
        )

    return errors


def main() -> int:
    errors = []
    for path in PYTHON_FILES:
        errors.extend(check_python_file(path))
    errors.extend(check_verify_command())

    if errors:
        print("Нарушения политики качества:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Политика качества соблюдена.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
