from __future__ import annotations

import argparse
import html
import json
import re
import time
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path

from collect_chobopark_practical import absolute_url, fetch, normalize_lines, parse_html


BASE_URL = "https://chobopark.tistory.com/540"
PROGRAMMING_LINKS = {
    "정보처리기사 실기 Python편": ("python", "Python"),
    "정보처리기사 실기 Java편": ("java", "Java"),
    "정보처리기사 실기 C언어편": ("c", "C/C++"),
}
HEADING_TAILS = {
    "python": "Python편",
    "java": "Java편",
    "c": "C언어편",
}
END_MARKERS = [
    "\n클릭하면 해당 페이지로 이동됩니다.",
    "\n공유하기",
    "\n게시글 관리",
    "\n관련글",
    "\n댓글",
    "\n태그",
]


@dataclass
class ProgrammingLink:
    label: str
    slug: str
    language: str
    url: str


@dataclass
class ProgrammingQuestion:
    id: str
    type: str
    language: str
    number: int
    question: str
    answer: str
    explanation: str
    source_url: str


@dataclass
class ProgrammingPage:
    title: str
    language: str
    slug: str
    url: str
    raw_text: str
    questions: list[ProgrammingQuestion]


class ArticleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.text_parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "pre"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "pre"}:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.text_parts.append(html.unescape(data))

    def handle_entityref(self, name: str) -> None:
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.handle_data(f"&#{name};")

    @property
    def text(self) -> str:
        return normalize_lines("".join(self.text_parts))


def parse_article_text(raw_html: str) -> str:
    parser = ArticleTextParser()
    parser.feed(raw_html)
    return parser.text


def clean_label(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def discover_programming_links(base_url: str) -> list[ProgrammingLink]:
    parser = parse_html(fetch(base_url))
    found: dict[str, ProgrammingLink] = {}
    for label, href in parser.links:
        normalized = clean_label(label)
        if normalized not in PROGRAMMING_LINKS:
            continue
        slug, language = PROGRAMMING_LINKS[normalized]
        url = absolute_url(href).split("#", 1)[0].split("?", 1)[0].rstrip("/")
        found[url] = ProgrammingLink(normalized, slug, language, url)
    return sorted(found.values(), key=lambda item: ["python", "java", "c"].index(item.slug))


def trim_article_end(text: str) -> str:
    end_positions = [text.find(marker) for marker in END_MARKERS if text.find(marker) > 0]
    if end_positions:
        return text[: min(end_positions)]
    return text


def clean_article_text(text: str) -> str:
    noise = {
        "반응형",
        "cs",
        "Colored by Color Scripter",
        "본문 바로가기",
        "Life-Journey",
    }
    cleaned: list[str] = []
    for line in text.splitlines():
        line = clean_label(line)
        if not line or line in noise:
            continue
        if line.startswith("by Life-Journey"):
            continue
        if re.fullmatch(r"\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.", line):
            continue
        cleaned.append(line)
    return normalize_lines("\n".join(cleaned))


def extract_article_text(raw_html: str, link: ProgrammingLink) -> tuple[str, str]:
    parsed_text = parse_article_text(raw_html)
    lines = [clean_label(line) for line in parsed_text.splitlines()]
    nonempty = [line for line in lines if line]
    heading_tail = HEADING_TAILS[link.slug]
    start_index = -1
    nav_index = -1
    for index, line in enumerate(nonempty):
        if line == "프로그래밍 언어 문제":
            nav_index = index
            break
    for index in range(max(nav_index + 1, 0), len(nonempty)):
        if nonempty[index] == link.label:
            start_index = index
            break
    for index in range(len(nonempty) - 2):
        if start_index < 0 and nonempty[index : index + 3] == ["정보처리기사", "실기", heading_tail]:
            start_index = index
            break
    if start_index < 0:
        raise ValueError(f"본문 제목을 찾지 못했습니다: {link.label}")

    article_lines: list[str] = [link.label]
    body_start = start_index + 3 if nonempty[start_index : start_index + 3] == ["정보처리기사", "실기", heading_tail] else start_index + 1
    for line in nonempty[body_start:]:
        if line in {"클릭하면 해당 페이지로 이동됩니다.", "공유하기", "게시글 관리"}:
            break
        article_lines.append(line)
    cleaned = clean_article_text("\n".join(article_lines))
    first_line, _, rest = cleaned.partition("\n")
    return first_line.strip(), rest.strip()


def is_question_start(line: str) -> bool:
    if len(line) > 180:
        return False
    if line in {"클릭하면 해당 페이지로 이동됩니다.", "반응형"}:
        return False
    if re.match(r"^(#include|import|public|class|void|int|float|char|print|printf|System\.)", line):
        return False
    patterns = [
        r"^다음.*(작성하시오|쓰시오|결과|코드|빈\s*칸|분석)",
        r"^(C\+\+|C언어|Java|Python|파이선).*(작성하시오|출력값|출력 결과|결과)",
        r"^(실수형|문자형|조건문|반복문|포인터|구조체|배열).*(작성하시오|출력하시오|출력값)",
        r"(빈\s*칸.*알맞|괄호.*코드|실행 결과.*작성하시오|출력 결과.*작성하시오)",
    ]
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)


def split_answer(lines: list[str]) -> tuple[str, str]:
    meaningful = [line for line in lines if line.strip()]
    if not meaningful:
        return "", ""
    answer_lines: list[str] = []
    explanation_lines: list[str] = []
    explanation_started = False
    for index, line in enumerate(meaningful):
        explanatory = bool(
            re.search(
                r"(합니다|됩니다|입니다|되게|통해|의미|때문|므로|에서|에는|으로|변수|출력하고|초기화|반복|계산|대입|저장|선언|호출|삭제|기준)",
                line,
            )
        )
        if answer_lines and explanatory:
            explanation_started = True
        if explanation_started:
            explanation_lines.append(line)
        else:
            answer_lines.append(line)
    if not explanation_lines and len(answer_lines) > 4:
        explanation_lines = answer_lines[4:]
        answer_lines = answer_lines[:4]
    return normalize_lines("\n".join(answer_lines)), normalize_lines("\n".join(explanation_lines))


def parse_question_block(block: list[str], link: ProgrammingLink, number: int) -> ProgrammingQuestion | None:
    if "더보기" not in block:
        return None
    answer_index = block.index("더보기")
    question = normalize_lines("\n".join(block[:answer_index]))
    answer, explanation = split_answer(block[answer_index + 1 :])
    if not question or not answer:
        return None
    question_id = f"programming-{link.slug}-{number:03d}"
    return ProgrammingQuestion(
        id=question_id,
        type="programming",
        language=link.language,
        number=number,
        question=question,
        answer=answer,
        explanation=explanation or answer,
        source_url=link.url,
    )


def split_questions(raw_text: str, link: ProgrammingLink) -> list[ProgrammingQuestion]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if is_question_start(line):
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            current.append(line)
    if current:
        blocks.append(current)

    questions: list[ProgrammingQuestion] = []
    for block in blocks:
        question = parse_question_block(block, link, len(questions) + 1)
        if question:
            questions.append(question)
    return questions


def collect_one(link: ProgrammingLink) -> ProgrammingPage:
    raw_html = fetch(link.url)
    title, raw_text = extract_article_text(raw_html, link)
    questions = split_questions(raw_text, link)
    return ProgrammingPage(title, link.language, link.slug, link.url, raw_text, questions)


def write_files(pages: list[ProgrammingPage], output_dir: Path) -> None:
    raw_dir = output_dir / "raw" / "programming"
    processed_dir = output_dir / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    all_questions: list[dict[str, object]] = []
    for page in pages:
        (raw_dir / f"{page.slug}.txt").write_text(page.raw_text, encoding="utf-8")
        (raw_dir / f"{page.slug}.json").write_text(
            json.dumps(asdict(page), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        all_questions.extend(asdict(question) for question in page.questions)

    (processed_dir / "programming_question_pages.json").write_text(
        json.dumps([asdict(page) for page in pages], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (processed_dir / "programming_questions.json").write_text(
        json.dumps(all_questions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def collect(base_url: str, output_dir: Path, delay: float) -> list[ProgrammingPage]:
    links = discover_programming_links(base_url)
    if not links:
        raise ValueError("기준 페이지에서 프로그래밍 언어 문제 링크를 찾지 못했습니다.")
    pages: list[ProgrammingPage] = []
    for index, link in enumerate(links, start=1):
        print(f"[{index}/{len(links)}] {link.label} - {link.url}")
        pages.append(collect_one(link))
        if delay:
            time.sleep(delay)
    write_files(pages, output_dir)
    return pages


def main() -> None:
    parser = argparse.ArgumentParser(description="chobopark 프로그래밍 언어 문제 수집기")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--delay", type=float, default=0.3)
    args = parser.parse_args()

    pages = collect(args.base_url, Path(args.output_dir), args.delay)
    question_count = sum(len(page.questions) for page in pages)
    print(json.dumps({"pages": len(pages), "questions": question_count}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
