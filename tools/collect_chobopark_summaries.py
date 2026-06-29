from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from collect_chobopark_practical import (
    absolute_url,
    fetch,
    fetch_bytes,
    image_extension,
    normalize_lines,
    parse_html,
)


SUMMARY_URLS = [
    "https://chobopark.tistory.com/193",
    "https://chobopark.tistory.com/197",
    "https://chobopark.tistory.com/198",
]

TOPIC_KEYWORDS = {
    "programming": ["Java", "C언어", "Python", "printf", "class", "포인터", "배열"],
    "database": ["데이터베이스", "SQL", "정규화", "트랜잭션", "JOIN", "인덱스"],
    "network_security": ["네트워크", "보안", "암호", "해시", "OSI", "TCP", "IP", "공격"],
    "software_engineering": ["요구사항", "UML", "테스트", "결합도", "응집도", "디자인 패턴"],
    "os_system": ["운영체제", "프로세스", "스케줄링", "메모리", "UNIX", "Linux"],
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
class WebSummaryImage:
    url: str
    local_path: str
    index: int
    content_type: str


@dataclass
class WebSummary:
    id: str
    title: str
    source_url: str
    text: str
    keywords: list[str]
    topics: list[str]
    image_refs: list[WebSummaryImage]


class ImageCollectingParser:
    def __init__(self, raw_html: str) -> None:
        parser = parse_html(raw_html)
        self.marked_text = parser.text
        self.image_urls = []
        for line in self.marked_text.splitlines():
            for url in re.findall(r"\[\[IMAGE:(.+?)\]\]", line):
                self.image_urls.append(url)
        self.text = normalize_lines(re.sub(r"\[\[IMAGE:.+?\]\]", "", self.marked_text))


def trim_summary_end(text: str) -> str:
    end_positions = [text.find(marker) for marker in END_MARKERS if text.find(marker) > 0]
    if end_positions:
        return text[: min(end_positions)]
    return text


def clean_summary_text(text: str, title: str) -> str:
    text = trim_summary_end(text)
    noise_patterns = [
        r"^\s*by Life-Journey\s*$",
        r"^\s*\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.\s*$",
        r"^\s*반응형\s*$",
        r"^\s*\(adsbygoogle.*$",
    ]
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(re.search(pattern, line) for pattern in noise_patterns):
            continue
        lines.append(line)
    return normalize_lines("\n".join(lines))


def slice_summary_section(text: str, fallback_title: str, part_no: str) -> str:
    if part_no == "2":
        heading_candidates = [
            "정보처리기사 족보 2탄",
            "정보처리기사 실기 족보 2탄",
            fallback_title.strip("[] "),
        ]
    else:
        heading_candidates = [
            f"정보처리기사 실기 족보 {part_no}탄",
            f"정보처리기사 족보 {part_no}탄",
            fallback_title.strip("[] "),
        ]
    nav_end = text.find("정보처리기사 실기 C언어편")
    search_from = nav_end if nav_end >= 0 else 0
    for heading in heading_candidates:
        if not heading:
            continue
        start = text.find(heading, search_from)
        if start >= 0:
            return text[start:]
    for heading in heading_candidates:
        if not heading:
            continue
        matches = list(re.finditer(re.escape(heading), text))
        if matches:
            start = matches[-1].start() if len(matches) > 1 else matches[0].start()
            return text[start:]
    title_pos = text.rfind(fallback_title)
    if title_pos >= 0:
        return text[title_pos:]
    return text


def extract_title(text: str, fallback_url: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if "정보처리기사 실기 족보" in line:
            return line.strip("[] ")
    return fallback_url.rstrip("/").rsplit("/", 1)[-1]


def top_keywords(text: str, limit: int = 30) -> list[str]:
    stopwords = {
        "정보처리기사",
        "실기",
        "족보",
        "정리",
        "요약",
        "다음",
        "대한",
        "설명",
        "있다",
        "한다",
        "이다",
        "에서",
        "으로",
    }
    words = re.findall(r"[가-힣A-Za-z0-9+#/.-]{2,}", text)
    counts: dict[str, int] = {}
    for word in words:
        if word in stopwords or word.isdigit():
            continue
        counts[word] = counts.get(word, 0) + 1
    return [word for word, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]]


def detect_topics(text: str) -> list[str]:
    lowered = text.lower()
    topics = []
    for topic, terms in TOPIC_KEYWORDS.items():
        if any(term.lower() in lowered for term in terms):
            topics.append(topic)
    return topics


def download_images(summary_id: str, urls: list[str], output_dir: Path) -> list[WebSummaryImage]:
    image_dir = output_dir / "images" / summary_id
    image_dir.mkdir(parents=True, exist_ok=True)
    for old_image in image_dir.glob(f"{summary_id}-*"):
        if old_image.is_file():
            old_image.unlink()
    refs: list[WebSummaryImage] = []
    seen: set[str] = set()
    for index, raw_url in enumerate(urls, start=1):
        url = absolute_url(raw_url)
        if url in seen or url.startswith("data:"):
            continue
        seen.add(url)
        try:
            content, content_type = fetch_bytes(url)
        except Exception as exc:
            print(f"image download failed: {url}: {exc}")
            continue
        ext = image_extension(url, content_type)
        local_path = image_dir / f"{summary_id}-{len(refs) + 1:02d}{ext}"
        local_path.write_bytes(content)
        refs.append(WebSummaryImage(url, str(local_path), len(refs) + 1, content_type))
    return refs


def collect_one(url: str, output_dir: Path) -> WebSummary:
    raw_html = fetch(url)
    parsed = ImageCollectingParser(raw_html)
    title = extract_title(parsed.text, url)
    summary_id = "web-summary-" + url.rstrip("/").rsplit("/", 1)[-1]
    part_no = {"193": "1", "197": "2", "198": "3"}.get(url.rstrip("/").rsplit("/", 1)[-1], "")
    section = trim_summary_end(slice_summary_section(parsed.marked_text, title, part_no))
    image_urls = re.findall(r"\[\[IMAGE:(.+?)\]\]", section)
    text = clean_summary_text(re.sub(r"\[\[IMAGE:.+?\]\]", "", section), title)
    image_refs = download_images(summary_id, image_urls, output_dir)
    return WebSummary(
        id=summary_id,
        title=title,
        source_url=url,
        text=text,
        keywords=top_keywords(text),
        topics=detect_topics(text),
        image_refs=image_refs,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="chobopark 정리&요약 족보 페이지 수집기")
    parser.add_argument("--output-dir", default="data/processed/web_summary")
    parser.add_argument("--delay", type=float, default=0.3)
    parser.add_argument("urls", nargs="*", default=SUMMARY_URLS)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    raw_dir = Path("data/raw/web_summary")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for index, url in enumerate(args.urls, start=1):
        print(f"[{index}/{len(args.urls)}] {url}")
        raw_html = fetch(url)
        (raw_dir / f"{url.rstrip('/').rsplit('/', 1)[-1]}.html").write_text(raw_html, encoding="utf-8")
        summary = collect_one(url, output_dir)
        summaries.append(summary)
        (raw_dir / f"{summary.id}.txt").write_text(summary.text, encoding="utf-8")
        if args.delay:
            time.sleep(args.delay)

    (output_dir / "web_summaries.json").write_text(
        json.dumps([asdict(summary) for summary in summaries], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for summary in summaries:
        (output_dir / f"{summary.id}.txt").write_text(summary.text, encoding="utf-8")

    print(json.dumps({"summaries": len(summaries), "output": str(output_dir)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
