from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


BASE_URL = "https://chobopark.tistory.com/540"
TARGET_TITLE_RE = re.compile(
    r"\[(20(?:21|22|23|24|25|26)년\s+\d회)\]\s*정보처리기사\s+실기\s+(?:복원\s+문제|기출문제!?+)"
)
TARGET_LINK_RE = re.compile(r"^(20(?:21|22|23|24|25|26)년)\s+(\d회)$")
QUESTION_START_RE = re.compile(r"^\s*(\d{1,2})\.\s*(.*)")


@dataclass
class ExamLink:
    title: str
    year: int
    round: int
    url: str


@dataclass
class Question:
    number: int
    question: str
    answer: str
    image_urls: list[str]


@dataclass
class ExamPage:
    title: str
    year: int
    round: int
    url: str
    questions: list[Question]
    raw_text: str


class TextAndLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._href_stack: list[str | None] = []
        self._link_text: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "a":
            self._href_stack.append(attrs_dict.get("href"))
            self._link_text = []
        if tag == "img":
            image_url = first_image_url(attrs_dict)
            if image_url:
                self.text_parts.append(f"\n[[IMAGE:{absolute_url(image_url)}]]\n")
        if tag in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "pre"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "a" and self._href_stack:
            href = self._href_stack.pop()
            label = clean_text("".join(self._link_text))
            if href and label:
                self.links.append((label, href))
            self._link_text = []
        if tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "pre"}:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        unescaped = html.unescape(data)
        self.text_parts.append(unescaped)
        if self._href_stack:
            self._link_text.append(unescaped)

    def handle_entityref(self, name: str) -> None:
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.handle_data(f"&#{name};")

    @property
    def text(self) -> str:
        return normalize_lines("\n".join(self.text_parts))


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value).replace("\xa0", " ")).strip()


def normalize_lines(value: str) -> str:
    value = html.unescape(value).replace("\xa0", " ")
    lines = [clean_text(line) for line in value.splitlines()]
    compacted: list[str] = []
    for line in lines:
        if line or (compacted and compacted[-1]):
            compacted.append(line)
    return "\n".join(compacted).strip()


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; StudyProjectCollector/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        raw = response.read()
        return raw.decode("utf-8", errors="replace")


def fetch_bytes(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; StudyProjectCollector/1.0)",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://chobopark.tistory.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        return response.read(), content_type


def parse_html(raw_html: str) -> TextAndLinkParser:
    parser = TextAndLinkParser()
    parser.feed(raw_html)
    return parser


def absolute_url(href: str) -> str:
    if href.startswith("data:"):
        return href
    if href.startswith("//"):
        return f"https:{href}"
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return f"https://chobopark.tistory.com{href}"
    return f"https://chobopark.tistory.com/{href}"


def first_image_url(attrs: dict[str, str | None]) -> str:
    for key in ("data-origin-width",):
        attrs.pop(key, None)
    for key in ("src", "data-src", "data-original", "data-image-src", "data-filename"):
        value = attrs.get(key)
        if value and not value.startswith("data:"):
            return value.strip()
    srcset = attrs.get("srcset") or attrs.get("data-srcset")
    if srcset:
        first = srcset.split(",", 1)[0].strip().split(" ", 1)[0]
        if first and not first.startswith("data:"):
            return first
    return ""


def canonical_url(url: str) -> str:
    return url.split("#", 1)[0].split("?", 1)[0].rstrip("/")


def discover_exam_links(raw_html: str) -> list[ExamLink]:
    parser = parse_html(raw_html)
    found: dict[str, ExamLink] = {}
    for label, href in parser.links:
        title_match = TARGET_TITLE_RE.search(label)
        simple_match = TARGET_LINK_RE.search(label)
        if title_match:
            year_round = title_match.group(1)
        elif simple_match:
            year_round = f"{simple_match.group(1)} {simple_match.group(2)}"
        else:
            continue
        year_match = re.search(r"(20\d{2})년\s+(\d)회", year_round)
        if not year_match:
            continue
        year = int(year_match.group(1))
        round_no = int(year_match.group(2))
        url = absolute_url(href)
        found[canonical_url(url)] = ExamLink(
            title=f"[{year}년 {round_no}회] 정보처리기사 실기 복원 문제",
            year=year,
            round=round_no,
            url=canonical_url(url),
        )
    return sorted(found.values(), key=lambda item: (item.year, item.round))


def extract_exam_text(page_text: str) -> tuple[str, str]:
    title_matches = list(TARGET_TITLE_RE.finditer(page_text))
    if not title_matches:
        raise ValueError("본문에서 정보처리기사 실기 복원 문제 제목을 찾지 못했습니다.")
    question_match = re.search(r"(?m)^\s*1\.\s+", page_text)
    if question_match:
        prior_titles = [match for match in title_matches if match.start() < question_match.start()]
        title_match = prior_titles[-1] if prior_titles else title_matches[0]
    else:
        title_match = title_matches[-1]
    start = title_match.start()
    tail = page_text[start:]
    end_markers = [
        "\n클릭하면 해당 페이지로 이동됩니다.",
        "\n공유하기",
        "\n게시글 관리",
        "\n관련글",
        "\n댓글",
    ]
    end_positions = [tail.find(marker) for marker in end_markers if tail.find(marker) > 0]
    body = tail[: min(end_positions)] if end_positions else tail
    first_line, _, rest = body.partition("\n")
    return clean_text(first_line), normalize_lines(rest)


def split_questions(exam_text: str) -> list[Question]:
    lines = [line for line in exam_text.splitlines() if line.strip()]
    questions: list[Question] = []
    current_number: int | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_number, current_lines
        if current_number is None:
            return
        question_text, answer_text, image_urls = split_answer(current_lines)
        questions.append(Question(current_number, question_text, answer_text, image_urls))
        current_number = None
        current_lines = []

    for line in lines:
        match = QUESTION_START_RE.match(line)
        if match and (
            current_number is None
            or ("더보기" in current_lines and int(match.group(1)) == current_number + 1)
        ):
            flush()
            current_number = int(match.group(1))
            first_line = match.group(2).strip()
            current_lines = [first_line] if first_line else []
        elif current_number is not None:
            current_lines.append(line)
    flush()
    return questions


def split_answer(lines: list[str]) -> tuple[str, str, list[str]]:
    image_urls: list[str] = []
    cleaned_lines: list[str] = []
    image_re = re.compile(r"\[\[IMAGE:(.+?)\]\]")
    for line in lines:
        found = image_re.findall(line)
        image_urls.extend(found)
        line = image_re.sub("", line).strip()
        if line:
            cleaned_lines.append(line)
    lines = cleaned_lines
    try:
        idx = lines.index("더보기")
    except ValueError:
        return normalize_lines("\n".join(lines)), "", image_urls
    question = normalize_lines("\n".join(lines[:idx]))
    answer = normalize_lines("\n".join(lines[idx + 1 :]))
    return question, answer, image_urls


def parse_exam_page(link: ExamLink, raw_html: str) -> ExamPage:
    parser = parse_html(raw_html)
    title, exam_text = extract_exam_text(parser.text)
    questions = split_questions(exam_text)
    return ExamPage(
        title=title or link.title,
        year=link.year,
        round=link.round,
        url=link.url,
        questions=questions,
        raw_text=exam_text,
    )


def image_extension(url: str, content_type: str) -> str:
    content_type = content_type.lower()
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    if "gif" in content_type:
        return ".gif"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return suffix if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"} else ".png"


def download_question_images(question_id: str, image_urls: list[str], image_dir: Path) -> list[dict[str, str | int]]:
    refs: list[dict[str, str | int]] = []
    image_dir.mkdir(parents=True, exist_ok=True)
    for index, url in enumerate(image_urls, start=1):
        if url.startswith("data:"):
            continue
        try:
            content, content_type = fetch_bytes(url)
        except Exception as exc:
            refs.append({"url": url, "index": index, "error": str(exc)})
            continue
        ext = image_extension(url, content_type)
        local_path = image_dir / f"{question_id}-{index:02d}{ext}"
        local_path.write_bytes(content)
        refs.append(
            {
                "url": url,
                "index": index,
                "local_path": str(local_path),
                "role": "question_image",
                "content_type": content_type,
            }
        )
    return refs


def write_exam_files(exam_pages: Iterable[ExamPage], output_dir: Path) -> None:
    raw_dir = output_dir / "raw" / "web"
    processed_dir = output_dir / "processed"
    image_dir = processed_dir / "past_images"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    pages = list(exam_pages)
    for page in pages:
        stem = f"{page.year}_{page.round}회_정보처리기사_실기_복원문제"
        (raw_dir / f"{stem}.txt").write_text(page.raw_text, encoding="utf-8")
        (raw_dir / f"{stem}.json").write_text(
            json.dumps(asdict(page), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    all_questions = []
    for page in pages:
        for question in page.questions:
            question_id = f"past-{page.year}-{page.round}-{question.number:02d}"
            image_refs = download_question_images(question_id, question.image_urls, image_dir)
            all_questions.append(
                {
                    "id": question_id,
                    "type": "past",
                    "exam": "정보처리기사 실기",
                    "year": page.year,
                    "round": page.round,
                    "number": question.number,
                    "question": question.question,
                    "answer": question.answer,
                    "explanation": question.answer,
                    "image_refs": image_refs,
                    "source_url": page.url,
                }
            )
    (processed_dir / "past_questions.json").write_text(
        json.dumps(all_questions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (processed_dir / "past_exam_pages.json").write_text(
        json.dumps([asdict(page) for page in pages], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def collect(base_url: str, output_dir: Path, delay: float) -> list[ExamPage]:
    base_html = fetch(base_url)
    links = discover_exam_links(base_html)
    if not links:
        raise ValueError("기준 페이지에서 2021~2026 기출 링크를 찾지 못했습니다.")

    pages: list[ExamPage] = []
    for index, link in enumerate(links, start=1):
        print(f"[{index}/{len(links)}] {link.title} - {link.url}")
        raw_html = fetch(link.url)
        pages.append(parse_exam_page(link, raw_html))
        if delay:
            time.sleep(delay)
    write_exam_files(pages, output_dir)
    return pages


def main() -> None:
    parser = argparse.ArgumentParser(description="chobopark 정보처리기사 실기 복원 문제 수집기")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--delay", type=float, default=0.3)
    args = parser.parse_args()

    pages = collect(args.base_url, Path(args.output_dir), args.delay)
    question_count = sum(len(page.questions) for page in pages)
    print(f"saved {len(pages)} exam pages, {question_count} questions")


if __name__ == "__main__":
    main()
