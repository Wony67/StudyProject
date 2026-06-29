from __future__ import annotations

import json
import re
from pathlib import Path


DATA_PATH = Path("data/processed/past_questions.json")


def normalize_prose(lines: list[str]) -> str:
    text = " ".join(line.strip() for line in lines if line.strip())
    text = re.sub(r"\s+([,.?!])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    return text.strip()


def normalize_option(lines: list[str]) -> str:
    cleaned = [line.strip() for line in lines if line.strip()]
    if not cleaned:
        return ""

    merged: list[str] = []
    index = 0
    while index < len(cleaned):
        if index + 1 < len(cleaned) and (cleaned[index], cleaned[index + 1]) in {
            ("테이블", "조건"),
            ("구하는", "것"),
            ("보", "기"),
        }:
            merged.append(f"{cleaned[index]} {cleaned[index + 1]}")
            index += 2
            continue
        merged.append(cleaned[index])
        index += 1
    cleaned = merged

    result: list[str] = []
    pending_bullet = False
    pending_label = ""
    paragraph = ""

    def flush() -> None:
        nonlocal paragraph
        if paragraph:
            result.append(paragraph.strip())
            paragraph = ""

    for line in cleaned:
        if line in {"조건", "테이블 조건", "구하는 것", "보기", "[보기]", "<보기>"}:
            flush()
            result.append(line)
            continue
        if line in {"·", "-", "ㆍ"}:
            flush()
            pending_bullet = True
            continue
        if re.match(r"^[a-zA-Zㄱ-ㅎㅁ-ㅎ]\.$", line):
            flush()
            pending_label = line
            continue
        if pending_bullet:
            result.append(f"- {line}")
            pending_bullet = False
            continue
        if pending_label:
            paragraph = f"{pending_label} {line}"
            pending_label = ""
            continue
        if result and result[-1].startswith("- ") and not re.search(r"[.?!]$", result[-1]):
            result[-1] = f"{result[-1]} {line}"
            continue
        paragraph = paragraph + f" {line}" if paragraph else line
        if re.search(r"[.?!:]$", line):
            flush()

    flush()
    return "\n".join(result).strip()


def find_phrase(lines: list[str], phrase: tuple[str, ...], start: int = 0) -> int | None:
    if not phrase:
        return None
    end = len(lines) - len(phrase) + 1
    for index in range(start, max(start, end)):
        if tuple(lines[index : index + len(phrase)]) == phrase:
            return index
    return None


def find_any_phrase(lines: list[str], phrases: list[tuple[str, ...]], start: int = 0) -> tuple[int, tuple[str, ...]] | None:
    matches: list[tuple[int, tuple[str, ...]]] = []
    for phrase in phrases:
        index = find_phrase(lines, phrase, start)
        if index is not None:
            matches.append((index, phrase))
    if not matches:
        return None
    return min(matches, key=lambda item: item[0])


def split_option_block(
    lines: list[str],
    end_index: int | None = None,
    markers: list[tuple[str, ...]] | None = None,
) -> tuple[list[str], str]:
    stop = len(lines) if end_index is None else end_index
    markers = markers or [("테이블", "조건"), ("조건",), ("구하는", "것")]
    marker = find_any_phrase(lines[:stop], markers)
    if not marker:
        return lines[:stop], ""

    start, phrase = marker
    label = " ".join(phrase)
    option_lines = [label, *lines[start + len(phrase) : stop]]
    return lines[:start], normalize_option(option_lines)


def find_number_block(lines: list[str]) -> tuple[int, int] | None:
    for start, line in enumerate(lines):
        if line != "1":
            continue
        expected = 1
        end = start
        while end < len(lines) and lines[end] == str(expected):
            expected += 1
            end += 1
        if expected > 4:
            return start, end
    return None


def detect_language(tokens: list[str]) -> str | None:
    text = " ".join(tokens)
    if any(term in text for term in ["#include", "stdio.h", "printf", "scanf", "void main", "int main"]):
        return "c"
    if any(term in text for term in ["public", "class", "System.out", "String", "HashSet"]):
        return "java"
    if any(term in text for term in ["input()", "print", "split", "range", "append", "join"]):
        return "python"
    return None


def compact_tokens(tokens: list[str]) -> str:
    return " ".join(token for token in tokens if token not in {"Colored by Color Scripter", "cs"})


def normalize_common_expr(value: str) -> str:
    return (
        value.replace(" . ", ".")
        .replace("( ", "(")
        .replace(" )", ")")
        .replace("[ ", "[")
        .replace(" ]", "]")
        .replace(" : ", ":")
        .replace(" :: ", "::")
        .replace(" - ", "-")
        .replace("'' .", "''.")
        .replace('"" .', '"".')
    )


def format_python(tokens: list[str]) -> str:
    text = normalize_common_expr(compact_tokens(tokens))
    replacements = [
        (r"\bi = input\(\)", "i = input()\n"),
        (r"\bx = \[\]", "x = []\n"),
        (r"\bfor word in i\.split\(\):", "\nfor word in i.split():\n"),
        (r"\bx\.append\(word\)", "    x.append(word)\n"),
        (r"\by = ''\.join\(x\)", "\ny = ''.join(x)\n"),
        (r"\bz = ''\.join\(c for c in y\[::-1\] if c not in 'ong'\)", "z = ''.join(c for c in y[::-1] if c not in 'ong')\n"),
        (r"\bprint\(z\)", "print(z)\n"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    text = text.replace("print (z)", "print(z)")
    text = re.sub(r"\n{3,}", "\n\n", text)
    cleaned: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if cleaned and cleaned[-1]:
                cleaned.append("")
            continue
        if stripped.startswith("x.append"):
            cleaned.append(f"    {stripped}")
        else:
            cleaned.append(stripped)
    return "\n".join(cleaned).strip()


def format_c_or_java(tokens: list[str], language: str) -> str:
    text = compact_tokens(tokens)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"#include\s*<\s*([^> ]+)\s*>", r"#include <\1>\n", text)
    text = re.sub(r"\s*([{};])\s*", r"\1\n", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s*\(\s*", "(", text)
    text = re.sub(r"\s*\)\s*", ")", text)
    text = re.sub(r"\s*\[\s*", "[", text)
    text = re.sub(r"\s*\]\s*", "]", text)
    text = re.sub(r"\s*\.\s*", ".", text)
    text = re.sub(r"\+\s+\+", "++", text)
    text = re.sub(r"\s+\+\+", "++", text)
    text = re.sub(r"\+\s+=", "+=", text)
    text = re.sub(r"-\s+-", "--", text)
    text = re.sub(r"-\s+=", "-=", text)
    text = re.sub(r"\*\s+p", "*p", text)
    text = re.sub(r"\n\s+", "\n", text)
    raw_lines = [line.strip() for line in text.splitlines() if line.strip()]

    merged: list[str] = []
    index = 0
    while index < len(raw_lines):
        if (
            raw_lines[index].startswith("for(")
            and index + 2 < len(raw_lines)
            and raw_lines[index].endswith(";")
            and raw_lines[index + 1].endswith(";")
            and raw_lines[index + 2].endswith("{")
        ):
            merged.append(f"{raw_lines[index]} {raw_lines[index + 1]} {raw_lines[index + 2]}".replace("for(", "for ("))
            index += 3
            continue
        merged.append(raw_lines[index])
        index += 1

    depth = 0
    formatted: list[str] = []
    for line in merged:
        line = line.replace(" ++", "++").replace(" +=", "+=").replace("= {", " = {")
        if line.startswith("}"):
            depth = max(0, depth - 1)
        formatted.append(f"{'  ' * depth}{line}")
        if line.endswith("{"):
            depth += 1
    return "\n".join(formatted).strip()


def split_input(lines: list[str]) -> tuple[list[str], str]:
    for index, line in enumerate(lines):
        if re.match(r"^입력\s*:", line):
            return lines[:index], normalize_prose(lines[index:]).replace("입력 :", "").replace("입력:", "").strip()
    return lines, ""


def find_sql_marker(lines: list[str]) -> tuple[int, int] | None:
    for index, line in enumerate(lines):
        normalized = line.strip()
        if normalized in {"[ SQL ]", "[SQL]", "SQL문", "SQL 문", "SQL구문", "SQL 구문"}:
            return index, index + 1
        if normalized.upper() == "SQL" and index + 1 < len(lines) and lines[index + 1] in {"문", "구문"}:
            return index, index + 2
    return None


def format_sql(tokens: list[str]) -> str:
    text = normalize_prose(tokens)
    text = re.sub(r"\s*;\s*", ";\n", text)
    text = re.sub(r"\s*,\s*", ",\n  ", text)
    text = re.sub(r"\s+\(", " (", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"\b(PRIMARY KEY|CONSTRAINT|FOREIGN KEY|REFERENCES|WHERE|FROM|GROUP BY|ORDER BY)\b", r"\n\1", text)
    text = re.sub(r"(CREATE TABLE [A-Z_]+ \()", r"\1\n", text)
    text = re.sub(r"\s+(\(\s*(?:1|2|4)\s*\))", r"\n\1", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    formatted: list[str] = []
    for line in lines:
        line = line.replace("(5));", "(5)\n);")
        if formatted and line.startswith(("PLAYER_", "TEAM_", "PRIMARY", "CONSTRAINT", "FOREIGN", "REFERENCES", "(1", "( 1", "(2", "( 2", "(3", "( 3", "(4", "( 4", "(5", "( 5")):
            formatted.extend(f"  {part}" if part != ");" else part for part in line.splitlines())
        else:
            formatted.extend(line.splitlines())
    return "\n".join(formatted).strip()


def build_sql_display(lines: list[str]) -> dict[str, object] | None:
    marker = find_sql_marker(lines)
    if not marker:
        return None

    marker_start, marker_end = marker
    prompt_lines, option_text = split_option_block(lines, marker_start)
    code = format_sql(lines[marker_end:])
    if not code or not re.search(r"\b(SELECT|CREATE|INSERT|UPDATE|DELETE|ALTER)\b", code, re.IGNORECASE):
        return None

    display: dict[str, object] = {
        "prompt": normalize_prose(prompt_lines),
        "code_language": "sql",
        "code": code,
        "input": "",
    }
    if option_text:
        display["option"] = option_text
    return display


def build_option_display(lines: list[str]) -> dict[str, object] | None:
    prompt_lines, option_text = split_option_block(lines)
    if not option_text or not prompt_lines:
        return None
    return {
        "prompt": normalize_prose(prompt_lines),
        "option": option_text,
        "code_language": "",
        "code": "",
        "input": "",
    }


def build_display(question: dict[str, object]) -> dict[str, object] | None:
    raw_question = str(question.get("question", ""))
    lines = [line.strip() for line in raw_question.splitlines() if line.strip()]
    sql_display = build_sql_display(lines)
    if sql_display:
        return sql_display

    block = find_number_block(lines)
    if not block:
        option_display = build_option_display(lines)
        if option_display:
            return option_display
        return None

    start, end = block
    prompt_lines, option_text = split_option_block(lines, start, [("보기",), ("보", "기"), ("조건",), ("테이블", "조건")])
    prompt = normalize_prose(prompt_lines)
    code_lines, input_text = split_input(lines[end:])
    language = detect_language(code_lines)
    if not language:
        return None

    if language == "python":
        code = format_python(code_lines)
    else:
        code = format_c_or_java(code_lines, language)

    if "\n" not in code or len(code) < 20:
        return None

    display = {
        "prompt": prompt,
        "code_language": language,
        "code": code,
        "input": input_text,
    }
    if option_text:
        display["option"] = option_text
    return display


def main() -> None:
    questions = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    modified: list[dict[str, object]] = []

    for question in questions:
        display = build_display(question)
        if not display:
            continue
        previous = question.get("display")
        question["display"] = display
        if previous != display:
            modified.append(
                {
                    "id": question.get("id"),
                    "year": question.get("year"),
                    "round": question.get("round"),
                    "number": question.get("number"),
                    "language": display["code_language"],
                }
            )

    DATA_PATH.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"modified_count": len(modified), "modified": modified}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
