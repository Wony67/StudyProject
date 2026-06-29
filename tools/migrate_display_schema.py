from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DATA_PATH = Path("data/processed/past_questions.json")
REPORT_PATH = Path("data/processed/display_migration_report.json")


CHOICE_MARKERS = {"보기", "[보기]", "<보기>", "보 기"}
CONDITION_MARKERS = {"조건", "[조건]", "테이블 조건", "SQL 조건"}
TARGET_MARKERS = {"구하는 것"}
CODE_MARKERS = {"SQL 문", "SQL 구문", "[SQL]", "[ SQL ]", "SQL"}


def compact_whitespace(value: str) -> str:
    value = re.sub(r"\s+([,.?!:;])", r"\1", value)
    value = re.sub(r"([(\[{<])\s+", r"\1", value)
    value = re.sub(r"\s+([)\]}>])", r"\1", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_block(lines: list[str]) -> str:
    return compact_whitespace(" ".join(line.strip() for line in lines if line.strip()))


def normalize_lines(text: str) -> list[str]:
    raw = [line.strip() for line in str(text).splitlines() if line.strip()]
    raw = [line for line in raw if line not in {"Colored by Color Scripter", "cs"}]

    merged: list[str] = []
    index = 0
    while index < len(raw):
        current = raw[index]
        nxt = raw[index + 1] if index + 1 < len(raw) else ""
        third = raw[index + 2] if index + 2 < len(raw) else ""

        if current == "[" and nxt == "보기" and third == "]":
            merged.append("[보기]")
            index += 3
            continue
        if current == "<" and nxt == "보기" and third == ">":
            merged.append("<보기>")
            index += 3
            continue
        if current == "보" and nxt == "기":
            merged.append("보기")
            index += 2
            continue
        if current == "테이블" and nxt == "조건":
            merged.append("테이블 조건")
            index += 2
            continue
        if current == "SQL" and nxt in {"조건", "문", "구문"}:
            merged.append(f"SQL {nxt}")
            index += 2
            continue
        if current == "구하는" and nxt == "것":
            merged.append("구하는 것")
            index += 2
            continue
        if re.fullmatch(r"\d+", current) and nxt == ".":
            merged.append(f"{current}.")
            index += 2
            continue
        if re.fullmatch(r"[ㄱ-ㅎㅏ-ㅣ가-힣A-Za-z]", current) and nxt == ".":
            merged.append(f"{current}.")
            index += 2
            continue

        merged.append(current)
        index += 1

    return merged


def strip_section_prefix(lines: list[str], markers: set[str]) -> list[str]:
    if lines and lines[0] in markers:
        return lines[1:]
    if len(lines) >= 2 and lines[0] in markers and lines[1] == ":":
        return lines[2:]
    return lines


def is_section_marker(lines: list[str], index: int, markers: set[str]) -> bool:
    line = lines[index]
    if line not in markers:
        return False
    if markers is not CONDITION_MARKERS:
        return True

    if line in {"[조건]", "테이블 조건", "SQL 조건"}:
        return True

    previous = lines[index - 1] if index > 0 else ""
    nxt = lines[index + 1] if index + 1 < len(lines) else ""
    if nxt in {":", "-", "·", "ㆍ", "•"}:
        return True
    if previous.endswith(("참고하여 쓰시오.", "참고하여 작성하시오.", "참고하여 적으시오.")):
        return True
    lookback = " ".join(lines[max(0, index - 6) : index])
    if "조건을 참고하여" in lookback:
        return True
    if "아래 조건" in previous or "[조건]" in previous:
        return True
    return False


def find_marker(lines: list[str], markers: set[str]) -> int | None:
    for index, line in enumerate(lines):
        if is_section_marker(lines, index, markers):
            return index
    return None


def split_at_marker(lines: list[str], markers: set[str]) -> tuple[list[str], list[str]]:
    index = find_marker(lines, markers)
    if index is None:
        return lines, []
    return lines[:index], lines[index:]


def split_marked_sections(lines: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    body, choices = split_at_marker(lines, CHOICE_MARKERS)
    body, targets = split_at_marker(body, TARGET_MARKERS)
    body, conditions = split_at_marker(body, CONDITION_MARKERS)

    if conditions:
        conditions = strip_section_prefix(conditions, CONDITION_MARKERS)
        cond_body, cond_targets = split_at_marker(conditions, TARGET_MARKERS)
        conditions = cond_body
        if cond_targets and not targets:
            targets = cond_targets
    if targets:
        targets = strip_section_prefix(targets, TARGET_MARKERS)
    if choices:
        choices = strip_section_prefix(choices, CHOICE_MARKERS)

    return body, conditions, choices, targets


def is_item_start(line: str) -> bool:
    if re.match(r"^\d+[.)]\s*", line):
        return True
    if re.match(r"^\(\s*\d+\s*\)", line):
        return True
    return False


def split_items(lines: list[str]) -> tuple[list[str], list[str]]:
    starts = [index for index, line in enumerate(lines) if is_item_start(line)]
    if len(starts) < 2:
        return lines, []

    prompt = lines[: starts[0]]
    items: list[str] = []
    for item_index, start in enumerate(starts):
        end = starts[item_index + 1] if item_index + 1 < len(starts) else len(lines)
        item = normalize_block(lines[start:end])
        if item:
            items.append(item)
    return prompt, items


def find_line_number_block(lines: list[str]) -> tuple[int, int] | None:
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


def normalize_bullets(lines: list[str]) -> list[str]:
    output: list[str] = []
    pending_bullet = False
    pending_label = ""

    for line in lines:
        if line in {":", "："}:
            continue
        if line in {"-", "·", "ㆍ", "•"}:
            if len(output) >= 2 and not output[-1].startswith("- ") and not output[-2].startswith("- "):
                if not re.search(r"[.?!:]$", output[-2]) and not re.search(r"[.?!:]$", output[-1]):
                    output[-2] = compact_whitespace(f"{output[-2]} {output[-1]}")
                    output.pop()
            pending_bullet = True
            continue
        if re.fullmatch(r"[a-zA-Zㄱ-ㅎ]\.", line):
            pending_label = line
            continue
        if pending_bullet:
            output.append(f"- {line}")
            pending_bullet = False
            continue
        if pending_label:
            output.append(f"{pending_label} {line}")
            pending_label = ""
            continue
        if output and output[-1].startswith("- ") and not re.search(r"[.?!]$", output[-1]):
            output[-1] = compact_whitespace(f"{output[-1]} {line}")
            continue
        output.append(line)

    return [compact_whitespace(line) for line in output if compact_whitespace(line)]


def split_slash_choices(text: str) -> list[str]:
    if "/" in text and not re.search(r"https?://|Condition/Decision|Modified Condition/Decision", text, re.I):
        return [compact_whitespace(part) for part in text.split("/") if compact_whitespace(part)]
    return [compact_whitespace(text)] if compact_whitespace(text) else []


def parse_choices(lines: list[str]) -> list[str]:
    lines = normalize_bullets(lines)
    joined = normalize_block(lines)
    if not joined:
        return []

    letter_matches = list(re.finditer(r"(?=(?:^|\s)([ㄱ-ㅎ])\.\s*)", joined))
    if len(letter_matches) >= 2:
        choices: list[str] = []
        for index, match in enumerate(letter_matches):
            start = match.start()
            end = letter_matches[index + 1].start() if index + 1 < len(letter_matches) else len(joined)
            choices.append(compact_whitespace(joined[start:end]))
        return choices

    comma_parts = [part for part in re.split(r"\s*,\s*", joined) if part.strip()]
    if len(comma_parts) >= 2:
        return [compact_whitespace(part) for part in comma_parts]

    return split_slash_choices(joined)


def parse_list_section(lines: list[str]) -> list[str]:
    lines = normalize_bullets(lines)
    if not lines:
        return []

    bullet_lines = [line for line in lines if line.startswith("- ")]
    if len(bullet_lines) >= 2:
        prefix = [line for line in lines if not line.startswith("- ")]
        return [compact_whitespace(line) for line in [*prefix, *bullet_lines] if compact_whitespace(line)]

    starts = [index for index, line in enumerate(lines) if is_item_start(line) or re.match(r"^[a-zA-Zㄱ-ㅎ]\.\s+", line)]
    if len(starts) >= 2:
        items: list[str] = []
        for item_index, start in enumerate(starts):
            end = starts[item_index + 1] if item_index + 1 < len(starts) else len(lines)
            item = normalize_block(lines[start:end])
            if item:
                items.append(item)
        return items
    return [normalize_block(lines)]


def split_code_section(lines: list[str]) -> tuple[list[str], str, str]:
    candidates = [index for index, line in enumerate(lines) if is_section_marker(lines, index, CODE_MARKERS)]
    for marker_index in reversed(candidates):
        candidate = lines[marker_index + 1 :]
        code_text = "\n".join(candidate).strip()
        if re.search(r"\b(SELECT|CREATE|INSERT|UPDATE|DELETE|ALTER|FROM|WHERE|JOIN)\b", code_text, re.I):
            return lines[:marker_index], "sql", code_text
    return lines, "", ""


def parse_option_text(option_text: str) -> tuple[list[str], list[str], list[str]]:
    lines = normalize_lines(option_text)
    _, conditions, choices, targets = split_marked_sections(lines)

    if not conditions and not choices and not targets:
        if lines and lines[0] in CHOICE_MARKERS:
            choices = strip_section_prefix(lines, CHOICE_MARKERS)
        elif lines and lines[0] in TARGET_MARKERS:
            targets = strip_section_prefix(lines, TARGET_MARKERS)
        else:
            conditions = lines

    return parse_list_section(conditions), parse_choices(choices), parse_list_section(targets)


def display_from_existing(question: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    raw_lines = normalize_lines(str(question.get("question", "")))
    body, _, _ = split_code_section(raw_lines)
    if body == raw_lines:
        number_block = find_line_number_block(raw_lines)
        if number_block:
            body = raw_lines[: number_block[0]]
    body, condition_lines, choice_lines, target_lines = split_marked_sections(body)
    conditions = parse_list_section(condition_lines)
    choices: list[str] = []
    if choice_lines:
        conditions.extend(parse_list_section(choice_lines))
    targets = parse_list_section(target_lines)

    if previous.get("option"):
        previous_conditions, previous_choices, previous_targets = parse_option_text(str(previous.get("option", "")))
        conditions = conditions or previous_conditions
        choices = choices or previous_choices
        targets = targets or previous_targets

    return {
        "prompt": str(previous.get("prompt") or "").strip() or normalize_block(normalize_lines(question.get("question", ""))),
        "description": list(previous.get("description") or []),
        "items": list(previous.get("items") or []),
        "conditions": conditions,
        "choices": choices,
        "targets": targets,
        "code_language": str(previous.get("code_language") or ""),
        "code": str(previous.get("code") or ""),
        "input": str(previous.get("input") or ""),
    }


def build_display(question: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    previous = question.get("display")
    if isinstance(previous, dict) and previous.get("code"):
        display = display_from_existing(question, previous)
        reasons = []
        if question.get("image_refs"):
            reasons.append("image_refs")
        return display, reasons

    lines = normalize_lines(str(question.get("question", "")))
    body, code_language, code = split_code_section(lines)
    body, conditions_lines, choices_lines, targets_lines = split_marked_sections(body)
    prompt_lines, items = split_items(body)

    prompt = normalize_block(prompt_lines) or normalize_block(body)
    conditions = parse_list_section(conditions_lines)
    choices = parse_choices(choices_lines)
    targets = parse_list_section(targets_lines)

    reasons: list[str] = []
    if question.get("image_refs"):
        reasons.append("image_refs")
    if not prompt:
        reasons.append("empty_prompt")
    if not items and re.search(r"\n1\.\s|\n1\.\n", str(question.get("question", ""))):
        reasons.append("possible_items")
    if re.search(r"\b(보기|조건|구하는 것)\b", prompt):
        reasons.append("marker_text_in_prompt")

    return {
        "prompt": prompt,
        "description": list((previous or {}).get("description") or []) if isinstance(previous, dict) else [],
        "items": items,
        "conditions": conditions,
        "choices": choices,
        "targets": targets,
        "code_language": code_language,
        "code": code,
        "input": str((previous or {}).get("input") if isinstance(previous, dict) else ""),
    }, reasons


def main() -> None:
    questions = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    report: list[dict[str, Any]] = []

    for question in questions:
        display, reasons = build_display(question)
        question["display"] = display
        if reasons:
            report.append(
                {
                    "id": question.get("id"),
                    "year": question.get("year"),
                    "round": question.get("round"),
                    "number": question.get("number"),
                    "reasons": reasons,
                }
            )

    DATA_PATH.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"questions": len(questions), "review_count": len(report)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
