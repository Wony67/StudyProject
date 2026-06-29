from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import pypdfium2 as pdfium


STOPWORDS = {
    "정보처리기사",
    "핵심",
    "요약",
    "시험에",
    "나오는",
    "것만",
    "공부한다",
    "Page",
    "다음",
    "문제",
    "아래",
    "대한",
    "설명",
    "작성",
    "확인",
    "알맞는",
    "출력값",
    "public",
    "static",
    "void",
    "class",
    "main",
    "String",
    "System",
    "printf",
    "print",
    "return",
    "include",
    "stdio.h",
    "Colored",
    "Color",
    "Scripter",
    "args",
    "int",
    "char",
    "for",
    "while",
    "if",
    "else",
    "있는",
    "한다",
    "있다",
    "이다",
    "으로",
    "에서",
}

TOPIC_KEYWORDS = {
    "순서도": ["순서도", "단자", "준비", "판단", "흐름선", "반복형", "분기형", "직선형", "Terminal"],
    "알고리즘": ["알고리즘", "합계", "수열", "피보나치", "마방진", "배열", "정렬", "검색"],
    "정렬": ["삽입 정렬", "선택 정렬", "버블 정렬", "정렬", "Insertion", "Selection", "Bubble"],
    "프로그래밍": ["C언어", "Java", "Python", "printf", "print", "class", "포인터", "배열", "반복문", "조건문"],
    "데이터베이스": ["데이터베이스", "SQL", "SELECT", "JOIN", "정규화", "트랜잭션", "인덱스", "ERD"],
    "ERD": ["ERD", "Entity", "Relationship", "개체", "속성", "관계", "카디널리티"],
    "논리회로": ["논리 게이트", "카르노맵", "XOR", "NAND", "NOR", "진리표", "논리식"],
    "네트워크": ["네트워크", "OSI", "TCP", "IP", "라우팅", "서브넷", "CIDR", "LAN", "프로토콜"],
    "보안": ["보안", "암호", "해시", "인증", "공격", "접근통제", "DRM"],
    "소프트웨어공학": ["소프트웨어", "요구사항", "UML", "테스트", "결합도", "응집도", "디자인 패턴"],
}


@dataclass
class SummaryPage:
    page_id: str
    source_pdf: str
    source_text: str
    page: int
    image: str
    text: str
    keywords: list[str]
    topics: list[str]


@dataclass
class QuestionMap:
    question_id: str
    source: str
    title: str
    keywords: list[str]
    related_pages: list[dict[str, object]]


def safe_stem(index: int, pdf_path: Path) -> str:
    ascii_slug = re.sub(r"[^A-Za-z0-9]+", "-", pdf_path.stem).strip("-").lower()
    if not ascii_slug:
        ascii_slug = f"pdf-{index:02d}"
    return f"{index:02d}-{ascii_slug}"


def split_pages_from_text(text: str) -> dict[int, str]:
    marker = re.compile(r"^## Page (\d+)\s*$", re.M)
    matches = list(marker.finditer(text))
    if not matches:
        return {}
    pages: dict[int, str] = {}
    for index, match in enumerate(matches):
        page_no = int(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pages[page_no] = text[start:end].strip()
    return pages


def words(text: str) -> list[str]:
    return re.findall(r"[가-힣A-Za-z0-9+#/.-]{2,}", text)


def top_keywords(text: str, limit: int = 12) -> list[str]:
    counter = Counter(
        word
        for word in words(text)
        if word not in STOPWORDS and not word.isdigit()
    )
    return [word for word, _ in counter.most_common(limit)]


def detect_topics(text: str) -> list[str]:
    lowered = text.lower()
    topics = []
    for topic, terms in TOPIC_KEYWORDS.items():
        hits = sum(1 for term in terms if term.lower() in lowered)
        if hits >= 2 or (terms and terms[0].lower() in lowered):
            topics.append(topic)
    return topics


def render_pdf_pages(pdf_path: Path, page_image_dir: Path, stem: str, scale: float) -> list[Path]:
    page_image_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    images: list[Path] = []
    for page_index in range(len(pdf)):
        image_path = page_image_dir / f"{stem}_p{page_index + 1:03d}.png"
        if not image_path.exists():
            pdf[page_index].render(scale=scale).to_pil().convert("RGB").save(image_path)
        images.append(image_path)
    return images


def build_summary_pages(pdf_dir: Path, text_dir: Path, output_dir: Path, scale: float) -> list[SummaryPage]:
    page_image_dir = output_dir / "page_images"
    records: list[SummaryPage] = []
    for index, pdf_path in enumerate(sorted(pdf_dir.glob("*.pdf")), start=1):
        stem = safe_stem(index, pdf_path)
        text_path = text_dir / f"{pdf_path.stem}.txt"
        if not text_path.exists():
            print(f"skip missing text: {text_path}")
            continue
        page_texts = split_pages_from_text(text_path.read_text(encoding="utf-8"))
        images = render_pdf_pages(pdf_path, page_image_dir, stem, scale)
        for page_no, image_path in enumerate(images, start=1):
            text = page_texts.get(page_no, "")
            records.append(
                SummaryPage(
                    page_id=f"{stem}-p{page_no:03d}",
                    source_pdf=str(pdf_path),
                    source_text=str(text_path),
                    page=page_no,
                    image=str(image_path),
                    text=text,
                    keywords=top_keywords(text),
                    topics=detect_topics(text),
                )
            )
    return records


def score_page(query_terms: set[str], query_topics: set[str], page: SummaryPage) -> int:
    haystack = " ".join([page.text, " ".join(page.keywords), " ".join(page.topics)]).lower()
    score = 0
    for term in query_terms:
        if len(term) < 2:
            continue
        score += haystack.count(term.lower())
    score += 25 * len(query_topics.intersection(page.topics))
    return score


def best_pages_for_text(text: str, pages: list[SummaryPage], limit: int = 5, extra_terms: list[str] | None = None) -> list[dict[str, object]]:
    query_topics = set(detect_topics(text))
    query_terms = set(top_keywords(text, 16) + list(query_topics) + (extra_terms or []))
    scored = [(score_page(query_terms, query_topics, page), page) for page in pages]
    best = [(score, page) for score, page in scored if score > 0]
    best.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "page_id": page.page_id,
            "score": score,
            "source_pdf": page.source_pdf,
            "page": page.page,
            "image": page.image,
            "topics": page.topics,
        }
        for score, page in best[:limit]
    ]


def build_past_question_map(past_questions_path: Path, pages: list[SummaryPage]) -> list[QuestionMap]:
    if not past_questions_path.exists():
        return []
    questions = json.loads(past_questions_path.read_text(encoding="utf-8"))
    maps = []
    for question in questions:
        text = "\n".join(
            [
                str(question.get("question", "")),
                str(question.get("answer", "")),
                str(question.get("explanation", "")),
            ]
        )
        extra_terms = language_terms(question.get("question", ""))
        maps.append(
            QuestionMap(
                question_id=str(question.get("id")),
                source="past_questions.json",
                title=f"{question.get('year')}년 {question.get('round')}회 {question.get('number')}번",
                keywords=top_keywords(text),
                related_pages=best_pages_for_text(text, pages, extra_terms=extra_terms),
            )
        )
    return maps


def language_terms(text: object, path: Path | None = None) -> list[str]:
    joined = str(text).lower()
    if path:
        joined += " " + path.suffix.lower() + " " + path.name.lower()
    terms: list[str] = []
    if ".py" in joined or "python" in joined or "파이썬" in joined:
        terms += ["Python", "리스트", "딕셔너리", "Range", "슬라이스", "for문", "print"]
    if ".java" in joined or "java" in joined or "자바" in joined:
        terms += ["JAVA", "Java", "출력 함수", "class", "if문"]
    if ".c" in joined or "c언어" in joined or "#include" in joined or "printf" in joined:
        terms += ["C언어", "자료형", "구조체", "포인터", "배열", "printf"]
    return terms


def build_code_question_map(question_dir: Path, pages: list[SummaryPage]) -> list[QuestionMap]:
    maps = []
    for path in sorted(question_dir.rglob("*")):
        if path.suffix.lower() not in {".c", ".java", ".py"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        extra_terms = language_terms(path.name + "\n" + text, path)
        maps.append(
            QuestionMap(
                question_id="code-" + re.sub(r"[^A-Za-z0-9가-힣]+", "-", str(path.with_suffix(""))).strip("-"),
                source=str(path),
                title=path.name,
                keywords=top_keywords(path.name + "\n" + text),
                related_pages=best_pages_for_text(path.name + "\n" + text, pages, extra_terms=extra_terms),
            )
        )
    return maps


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF 페이지 이미지와 학습 자료를 문제/요약 데이터에 매핑합니다.")
    parser.add_argument("--pdf-dir", default="data/pdf")
    parser.add_argument("--text-dir", default="data/processed/pdf")
    parser.add_argument("--output-dir", default="data/processed/mapping")
    parser.add_argument("--past-questions", default="data/processed/past_questions.json")
    parser.add_argument("--question-dir", default="data/question")
    parser.add_argument("--scale", type=float, default=1.35)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    pages = build_summary_pages(Path(args.pdf_dir), Path(args.text_dir), output_dir, args.scale)
    past_maps = build_past_question_map(Path(args.past_questions), pages)
    code_maps = build_code_question_map(Path(args.question_dir), pages)

    write_json(output_dir / "summary_pages.json", [asdict(page) for page in pages])
    write_json(output_dir / "past_question_page_map.json", [asdict(item) for item in past_maps])
    write_json(output_dir / "code_question_page_map.json", [asdict(item) for item in code_maps])

    print(
        json.dumps(
            {
                "summary_pages": len(pages),
                "past_question_maps": len(past_maps),
                "code_question_maps": len(code_maps),
                "output_dir": str(output_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
