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


START_URL = (
    "https://velog.io/@kkr96/"
    "%EC%A0%95%EB%B3%B4%EC%B2%98%EB%A6%AC%EA%B8%B0%EC%82%AC-"
    "%EC%8B%A4%EA%B8%B0-%EC%9A%94%EC%95%BD-"
    "%EC%A0%95%EB%A6%AC-1%EC%9E%A5"
)
BASE_URL = "https://velog.io"
SUMMARY_TITLE_RE = re.compile(r"정보처리기사\s+실기\s+요약\s+정리\s+(\d+)장")
NOISE_TEXTS = {"정보처리기사", "0개의 댓글", "댓글 작성"}


@dataclass
class LinkRef:
    title: str
    url: str


@dataclass
class VelogSection:
    title: str
    level: int
    content: list[str]


@dataclass
class VelogImage:
    url: str
    local_path: str
    index: int
    alt: str
    content_type: str


@dataclass
class VelogChapter:
    id: str
    chapter: int
    title: str
    subject: str
    source_url: str
    previous: LinkRef | None
    next: LinkRef | None
    heading_count: int
    keywords: list[str]
    image_refs: list[VelogImage]
    text: str
    sections: list[VelogSection]


class VelogParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.tokens: list[dict[str, object]] = []
        self.links: list[LinkRef] = []
        self._skip_depth = 0
        self._current_heading: int | None = None
        self._heading_parts: list[str] = []
        self._current_block: str | None = None
        self._block_parts: list[str] = []
        self._href_stack: list[str] = []
        self._link_parts: list[str] = []
        self._table_depth = 0
        self._row_depth = 0
        self._cell_depth = 0
        self._row_cells: list[str] = []
        self._cell_parts: list[str] = []
        self._table_rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "a":
            href = attrs_dict.get("href") or ""
            self._href_stack.append(href)
            self._link_parts = []
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._flush_block()
            self._current_heading = int(tag[1])
            self._heading_parts = []
        elif tag in {"p", "li", "blockquote", "pre"}:
            self._flush_block()
            self._current_block = "pre" if tag == "pre" else "text"
            self._block_parts = []
        elif tag == "br":
            self._append_text("\n")
        elif tag == "table":
            self._flush_block()
            self._table_depth += 1
            self._table_rows = []
        elif tag == "tr" and self._table_depth:
            self._row_depth += 1
            self._row_cells = []
        elif tag in {"td", "th"} and self._row_depth:
            self._cell_depth += 1
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._current_heading:
            text = clean_text("".join(self._heading_parts))
            if text:
                self.tokens.append({"type": "heading", "level": self._current_heading, "text": text})
            self._current_heading = None
            self._heading_parts = []
        elif tag in {"p", "li", "blockquote", "pre"}:
            self._flush_block()
        elif tag in {"td", "th"} and self._cell_depth:
            text = clean_text("".join(self._cell_parts))
            self._row_cells.append(text)
            self._cell_parts = []
            self._cell_depth -= 1
        elif tag == "tr" and self._row_depth:
            if any(self._row_cells):
                self._table_rows.append(self._row_cells)
            self._row_cells = []
            self._row_depth -= 1
        elif tag == "table" and self._table_depth:
            if self._table_rows:
                rows = [" | ".join(cell for cell in row if cell) for row in self._table_rows]
                self.tokens.append({"type": "table", "text": "\n".join(rows)})
            self._table_rows = []
            self._table_depth -= 1
        if tag == "a" and self._href_stack:
            href = self._href_stack.pop()
            label = clean_text("".join(self._link_parts))
            if href and label:
                self.links.append(LinkRef(title=label, url=absolute_url(href)))
            self._link_parts = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self._append_text(html.unescape(data))

    def handle_entityref(self, name: str) -> None:
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.handle_data(f"&#{name};")

    def close(self) -> None:
        self._flush_block()
        super().close()

    def _append_text(self, text: str) -> None:
        if self._current_heading is not None:
            self._heading_parts.append(text)
        elif self._cell_depth:
            self._cell_parts.append(text)
        elif self._current_block:
            self._block_parts.append(text)
        if self._href_stack:
            self._link_parts.append(text)

    def _flush_block(self) -> None:
        if not self._current_block:
            return
        text = clean_text("".join(self._block_parts))
        if text and text not in NOISE_TEXTS:
            self.tokens.append({"type": self._current_block, "level": 0, "text": text})
        self._current_block = None
        self._block_parts = []


def clean_text(value: str) -> str:
    value = html.unescape(value).replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def normalize_multiline(lines: list[str]) -> str:
    compacted: list[str] = []
    for line in lines:
        line = clean_text(line)
        if line:
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
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_bytes(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; StudyProjectCollector/1.0)",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": BASE_URL + "/",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read(), response.headers.get("Content-Type", "")


def absolute_url(href: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return BASE_URL + urllib.parse.quote(href, safe="/@")
    return BASE_URL + "/" + urllib.parse.quote(href, safe="/@")


def image_extension(url: str, content_type: str) -> str:
    path = urllib.parse.urlparse(url).path.lower()
    suffix = Path(path).suffix
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        return suffix
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    if "gif" in content_type:
        return ".gif"
    if "svg" in content_type:
        return ".svg"
    return ".jpg"


def relative_path_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.unquote(parsed.path)


def chapter_from_title(title: str) -> int | None:
    match = SUMMARY_TITLE_RE.search(title)
    return int(match.group(1)) if match else None


def chapter_from_url(url: str) -> int | None:
    tail = relative_path_from_url(url).rstrip("/").rsplit("/", 1)[-1]
    match = re.search(r"-(\d+)(?:장)?$", tail)
    return int(match.group(1)) if match else None


def parse_html(raw_html: str) -> VelogParser:
    parser = VelogParser()
    parser.feed(raw_html)
    parser.close()
    return parser


def post_body_from_apollo(raw_html: str) -> str:
    match = re.search(r"window\.__APOLLO_STATE__=(.*?);</script>", raw_html, re.S)
    if not match:
        return ""
    try:
        state = json.loads(match.group(1))
    except json.JSONDecodeError:
        return ""
    for value in state.values():
        if isinstance(value, dict) and value.get("__typename") == "Post" and isinstance(value.get("body"), str):
            return value["body"]
    return ""


def extract_post_images(markdown: str) -> list[tuple[str, str]]:
    images: list[tuple[str, str]] = []
    for alt, url in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", markdown):
        images.append((html.unescape(alt).strip(), html.unescape(url).strip()))
    for attrs in re.findall(r"<img\b([^>]+)>", markdown, re.I):
        src_match = re.search(r"src=[\"']([^\"']+)", attrs, re.I)
        if not src_match:
            continue
        alt_match = re.search(r"alt=[\"']([^\"']*)", attrs, re.I)
        images.append((html.unescape(alt_match.group(1)).strip() if alt_match else "", html.unescape(src_match.group(1)).strip()))
    return images


def download_images(chapter_id: str, markdown: str, output_dir: Path) -> list[VelogImage]:
    image_dir = output_dir / "images" / chapter_id
    image_dir.mkdir(parents=True, exist_ok=True)
    for old_image in image_dir.glob(f"{chapter_id}-*"):
        if old_image.is_file():
            old_image.unlink()

    refs: list[VelogImage] = []
    seen: set[str] = set()
    for alt, raw_url in extract_post_images(markdown):
        if not raw_url or raw_url.startswith("data:"):
            continue
        url = absolute_url(raw_url)
        if url in seen:
            continue
        seen.add(url)
        try:
            content, content_type = fetch_bytes(url)
        except Exception as exc:
            print(f"image download failed: {url}: {exc}")
            continue
        ext = image_extension(url, content_type)
        local_path = image_dir / f"{chapter_id}-{len(refs) + 1:02d}{ext}"
        local_path.write_bytes(content)
        refs.append(
            VelogImage(
                url=url,
                local_path=str(local_path),
                index=len(refs) + 1,
                alt=alt,
                content_type=content_type,
            )
        )
    return refs


def top_keywords(text: str, limit: int = 30) -> list[str]:
    stopwords = {
        "정보처리기사",
        "실기",
        "요약",
        "정리",
        "대한",
        "있는",
        "한다",
        "이다",
        "위한",
        "또는",
        "경우",
        "사용",
        "기능",
    }
    words = re.findall(r"[가-힣A-Za-z0-9+#/.-]{2,}", text)
    counts: dict[str, int] = {}
    for word in words:
        if word in stopwords or word.isdigit():
            continue
        counts[word] = counts.get(word, 0) + 1
    return [word for word, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]]


def find_article_bounds(tokens: list[dict[str, object]], chapter: int) -> tuple[int, int]:
    start = 0
    for index, token in enumerate(tokens):
        if token["type"] == "heading" and chapter_from_title(str(token["text"])) == chapter:
            start = index + 1
            break
    end = len(tokens)
    for index in range(start, len(tokens)):
        token = tokens[index]
        if token["type"] != "heading":
            continue
        text = str(token["text"])
        other_chapter = chapter_from_title(text)
        if other_chapter and other_chapter != chapter:
            end = index
            break
        if text.endswith("개의 댓글"):
            end = index
            break
    return start, end


def build_sections(tokens: list[dict[str, object]]) -> list[VelogSection]:
    sections: list[VelogSection] = []
    current: VelogSection | None = None
    for token in tokens:
        text = str(token["text"]).strip()
        if not text or text in NOISE_TEXTS:
            continue
        if token["type"] == "heading":
            current = VelogSection(title=text, level=int(token["level"]), content=[])
            sections.append(current)
            continue
        if current is None:
            current = VelogSection(title="개요", level=0, content=[])
            sections.append(current)
        current.content.append(text)
    return [section for section in sections if section.title or section.content]


def text_from_sections(sections: list[VelogSection]) -> str:
    lines: list[str] = []
    for section in sections:
        if section.title:
            lines.append("#" * max(1, section.level) + " " + section.title)
        lines.extend(section.content)
        lines.append("")
    return normalize_multiline(lines)


def link_refs(links: list[LinkRef], current_chapter: int) -> tuple[LinkRef | None, LinkRef | None]:
    previous: LinkRef | None = None
    next_link: LinkRef | None = None
    for link in links:
        chapter = chapter_from_url(link.url)
        if chapter is None:
            continue
        title_match = SUMMARY_TITLE_RE.search(link.title)
        title = title_match.group(0) if title_match else link.title
        normalized = LinkRef(title=title, url=link.url)
        if chapter < current_chapter and (previous is None or chapter > chapter_from_url(previous.url)):
            previous = normalized
        if chapter > current_chapter and (next_link is None or chapter < chapter_from_url(next_link.url)):
            next_link = normalized
    return previous, next_link


def collect_one(url: str) -> tuple[VelogChapter, str]:
    raw_html = fetch(url)
    parsed = parse_html(raw_html)
    markdown = post_body_from_apollo(raw_html)
    title_token = next(
        (str(token["text"]) for token in parsed.tokens if token["type"] == "heading" and chapter_from_title(str(token["text"]))),
        "",
    )
    chapter = chapter_from_title(title_token) or chapter_from_url(url)
    if chapter is None:
        raise ValueError(f"chapter number not found: {url}")
    start, end = find_article_bounds(parsed.tokens, chapter)
    article_tokens = parsed.tokens[start:end]
    sections = build_sections(article_tokens)
    subject = next((section.title for section in sections if section.level == 1), "")
    text = text_from_sections(sections)
    previous, next_link = link_refs(parsed.links, chapter)
    chapter_id = f"velog-summary-{chapter:02d}"
    image_refs = download_images(chapter_id, markdown, Path("data/processed/velog_summary"))
    return (
        VelogChapter(
            id=chapter_id,
            chapter=chapter,
            title=title_token or f"정보처리기사 실기 요약 정리 {chapter}장",
            subject=subject,
            source_url=url,
            previous=previous,
            next=next_link,
            heading_count=sum(1 for token in article_tokens if token["type"] == "heading"),
            keywords=top_keywords(text),
            image_refs=image_refs,
            text=text,
            sections=sections,
        ),
        raw_html,
    )


def collect_series(start_url: str, delay: float) -> list[tuple[VelogChapter, str]]:
    collected: list[tuple[VelogChapter, str]] = []
    seen: set[str] = set()
    url = start_url
    while url and url not in seen:
        seen.add(url)
        chapter, raw_html = collect_one(url)
        collected.append((chapter, raw_html))
        url = chapter.next.url if chapter.next else ""
        if url and delay:
            time.sleep(delay)
    return collected


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect kkr96 Velog information processing engineer summaries.")
    parser.add_argument("--start-url", default=START_URL)
    parser.add_argument("--output-dir", default="data/processed/velog_summary")
    parser.add_argument("--raw-dir", default="data/raw/velog_summary")
    parser.add_argument("--delay", type=float, default=0.2)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    raw_dir = Path(args.raw_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    collected = collect_series(args.start_url, args.delay)
    chapters = [chapter for chapter, _ in collected]
    for chapter, raw_html in collected:
        stem = f"velog-summary-{chapter.chapter:02d}"
        (raw_dir / f"{stem}.html").write_text(raw_html, encoding="utf-8")
        (output_dir / f"{stem}.txt").write_text(chapter.text, encoding="utf-8")
        (output_dir / f"{stem}.json").write_text(
            json.dumps(asdict(chapter), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    (output_dir / "velog_summaries.json").write_text(
        json.dumps([asdict(chapter) for chapter in chapters], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "chapters": len(chapters),
                "sections": sum(len(chapter.sections) for chapter in chapters),
                "output": str(output_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
