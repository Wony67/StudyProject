from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class TopicDefinition:
    topic_id: str
    title: str
    keywords: list[str]
    include_any: list[str]
    include_all: list[str]
    code_extensions: list[str]
    code_name_terms: list[str]
    notes: list[str]


@dataclass
class TopicKnowledge:
    topic_id: str
    title: str
    keywords: list[str]
    notes: list[str]
    summary_pages: list[dict[str, object]]
    image_refs: list[dict[str, object]]
    past_questions: list[dict[str, object]]
    code_questions: list[dict[str, object]]


TOPICS = [
    TopicDefinition(
        topic_id="flowchart-debugging",
        title="순서도와 디버깅",
        keywords=["순서도", "디버깅", "단자", "처리", "판단", "반복", "흐름선"],
        include_any=["순서도", "디버깅", "단자", "Terminal", "Preparation", "Process", "Decision", "흐름선", "반복형", "분기형", "직선형"],
        include_all=[],
        code_extensions=[],
        code_name_terms=[],
        notes=[
            "처리(Process)는 계산이나 대입을 나타내는 직사각형이다.",
            "판단(Decision)은 조건에 따라 흐름이 갈라지는 마름모이다.",
            "순서도 문제는 변수, 조건식, 출력문을 표로 추적하며 디버깅한다.",
        ],
    ),
    TopicDefinition(
        topic_id="java-output",
        title="Java 출력 결과",
        keywords=["Java", "System.out.print", "class", "static", "상속", "오버라이딩", "예외"],
        include_any=["Java", "JAVA", "자바", "System.out", "println", "class", "상속", "오버라이딩", "오버로딩", "예외"],
        include_all=[],
        code_extensions=[".java"],
        code_name_terms=["Java", "자바", "클래스", "제어문", "break", "continue"],
        notes=[
            "Java 출력 문제는 객체 생성, static/instance, 상속, 예외 처리, 문자열 연산이 자주 쓰인다.",
            "System.out.print와 println의 줄바꿈 차이를 확인한다.",
        ],
    ),
    TopicDefinition(
        topic_id="c-output-pointer",
        title="C언어 출력과 포인터",
        keywords=["C언어", "printf", "포인터", "배열", "구조체", "문자열"],
        include_any=["C언어", "printf", "scanf", "포인터", "구조체", "stdlib.h", "stdio.h", "배열", "문자열", "malloc"],
        include_all=[],
        code_extensions=[".c"],
        code_name_terms=["C언어", "포인터", "구조체", "사용자 정의 함수", "연산자", "제어문"],
        notes=[
            "C언어 문제는 배열 인덱스, 포인터 연산, 구조체 멤버 접근, 문자열 종료 문자를 주의한다.",
            "printf 형식 지정자와 증감 연산자의 적용 시점을 확인한다.",
        ],
    ),
    TopicDefinition(
        topic_id="python-output",
        title="Python 출력 결과",
        keywords=["Python", "리스트", "딕셔너리", "슬라이스", "range", "for", "while", "print"],
        include_any=["Python", "파이썬", "리스트", "딕셔너리", "Range", "슬라이스", "for문", "while문", "input( )", "print( )"],
        include_all=[],
        code_extensions=[".py"],
        code_name_terms=["Python", "파이썬", "Range", "슬라이스", "람다", "클래스"],
        notes=[
            "Python 문제는 리스트 인덱스, 슬라이싱, range 범위, 딕셔너리 키/값 처리를 자주 확인한다.",
            "문자열과 리스트의 위치는 0부터 시작한다.",
        ],
    ),
    TopicDefinition(
        topic_id="sorting-searching",
        title="정렬과 검색",
        keywords=["삽입 정렬", "선택 정렬", "버블 정렬", "이분 검색", "해싱"],
        include_any=["삽입 정렬", "선택 정렬", "버블 정렬", "이분 검색", "이진 검색", "해싱", "Insertion Sort", "Selection Sort", "Bubble Sort"],
        include_all=[],
        code_extensions=[],
        code_name_terms=["정렬", "검색"],
        notes=[
            "삽입 정렬은 앞쪽 정렬 영역에 현재 값을 끼워 넣는다.",
            "버블 정렬은 인접한 값을 비교해 큰 값을 뒤로 보내는 흐름을 반복한다.",
            "이분 검색은 정렬된 데이터에서 중간값 기준으로 탐색 범위를 절반씩 줄인다.",
        ],
    ),
    TopicDefinition(
        topic_id="database-sql",
        title="데이터베이스와 SQL",
        keywords=["데이터베이스", "SQL", "SELECT", "JOIN", "정규화", "트랜잭션", "인덱스"],
        include_any=["데이터베이스", "SQL", "SELECT", "JOIN", "정규화", "트랜잭션", "인덱스", "COMMIT", "ROLLBACK", "관계 데이터 모델"],
        include_all=[],
        code_extensions=[],
        code_name_terms=[],
        notes=[
            "SQL 문제는 SELECT 실행 결과, JOIN 조건, GROUP BY, 트랜잭션 제어어를 확인한다.",
            "정규화는 이상 현상을 줄이고 데이터 중복을 최소화하기 위한 과정이다.",
        ],
    ),
    TopicDefinition(
        topic_id="erd-modeling",
        title="ERD와 관계 데이터 모델",
        keywords=["ERD", "개체", "속성", "관계", "카디널리티", "키"],
        include_any=["ERD", "Entity", "Relationship", "개체", "속성", "카디널리티", "Crow-foot", "관계 데이터 모델", "키(Key)"],
        include_all=[],
        code_extensions=[],
        code_name_terms=[],
        notes=[
            "ERD는 개체, 속성, 관계를 시각적으로 표현한다.",
            "관계 차수와 카디널리티 표기를 이미지와 함께 보는 것이 중요하다.",
        ],
    ),
    TopicDefinition(
        topic_id="logic-circuit",
        title="논리회로와 카르노맵",
        keywords=["논리 게이트", "카르노맵", "진리표", "AND", "OR", "XOR", "NAND", "NOR"],
        include_any=["논리 게이트", "카르노맵", "진리표", "논리식", "XOR", "XNOR", "NAND", "NOR", "AND", "OR", "NOT"],
        include_all=[],
        code_extensions=[],
        code_name_terms=[],
        notes=[
            "논리 게이트는 기호, 진리표, 논리식을 함께 암기한다.",
            "카르노맵은 인접한 1을 큰 묶음으로 만들어 간소화한다.",
        ],
    ),
    TopicDefinition(
        topic_id="network-security",
        title="네트워크와 보안",
        keywords=["OSI", "TCP/IP", "IP", "라우팅", "서브넷", "암호", "해시", "인증", "공격"],
        include_any=["OSI", "TCP", "IP", "HTTP", "라우팅", "서브넷", "CIDR", "네트워크", "보안", "암호", "해시", "인증", "공격", "DRM"],
        include_all=[],
        code_extensions=[],
        code_name_terms=[],
        notes=[
            "네트워크 문제는 계층별 프로토콜, IP/서브넷 계산, 라우팅 개념이 자주 나온다.",
            "보안 문제는 암호화, 해시, 인증, 공격 유형의 구분이 중요하다.",
        ],
    ),
    TopicDefinition(
        topic_id="software-engineering",
        title="소프트웨어공학",
        keywords=["요구사항", "UML", "디자인 패턴", "테스트", "결합도", "응집도", "애자일"],
        include_any=["요구사항", "UML", "디자인 패턴", "테스트", "결합도", "응집도", "애자일", "스크럼", "XP", "모듈", "DFD"],
        include_all=[],
        code_extensions=[],
        code_name_terms=[],
        notes=[
            "결합도는 낮을수록 좋고 응집도는 높을수록 좋다.",
            "요구사항 개발은 도출, 분석, 명세, 확인 흐름으로 정리한다.",
        ],
    ),
]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def contains_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def contains_all(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return all(term.lower() in lowered for term in terms)


def score_text(text: str, topic: TopicDefinition) -> int:
    lowered = text.lower()
    score = 0
    for keyword in topic.include_any + topic.keywords:
        if len(keyword) < 2:
            continue
        score += lowered.count(keyword.lower())
    if topic.include_all and contains_all(text, topic.include_all):
        score += 10
    return score


def page_entry(page: dict[str, object], score: int) -> dict[str, object]:
    return {
        "page_id": page.get("page_id"),
        "score": score,
        "source_pdf": page.get("source_pdf"),
        "page": page.get("page"),
        "image": page.get("image"),
        "keywords": page.get("keywords", [])[:10],
        "topics": page.get("topics", []),
    }


def question_entry(question: dict[str, object], score: int) -> dict[str, object]:
    return {
        "id": question.get("id"),
        "score": score,
        "year": question.get("year"),
        "round": question.get("round"),
        "number": question.get("number"),
        "source_url": question.get("source_url"),
        "preview": str(question.get("question", "")).replace("\n", " ")[:160],
        "answer_preview": str(question.get("answer", "")).replace("\n", " ")[:80],
    }


def code_entry(path: Path, root: Path, score: int) -> dict[str, object]:
    return {
        "path": str(path),
        "score": score,
        "title": path.name,
        "relative_path": str(path.relative_to(root)),
    }


def build_topic(
    topic: TopicDefinition,
    pages: list[dict[str, object]],
    past_questions: list[dict[str, object]],
    question_dir: Path,
    max_pages: int,
    max_questions: int,
    max_code: int,
) -> TopicKnowledge:
    page_scores = []
    for page in pages:
        text = "\n".join(
            [
                str(page.get("text", "")),
                " ".join(page.get("keywords", [])),
                " ".join(page.get("topics", [])),
            ]
        )
        score = score_text(text, topic)
        if score > 0:
            page_scores.append((score, page))
    page_scores.sort(key=lambda item: item[0], reverse=True)

    question_scores = []
    for question in past_questions:
        text = "\n".join(
            [
                str(question.get("question", "")),
                str(question.get("answer", "")),
                str(question.get("explanation", "")),
            ]
        )
        score = score_text(text, topic)
        if score > 0:
            question_scores.append((score, question))
    question_scores.sort(key=lambda item: item[0], reverse=True)

    code_scores = []
    for path in sorted(question_dir.rglob("*")):
        if path.suffix.lower() not in {".c", ".java", ".py"}:
            continue
        name_text = path.name + "\n" + str(path)
        if topic.code_extensions and path.suffix.lower() in topic.code_extensions:
            score = 20
        else:
            score = 0
        if topic.code_name_terms and contains_any(name_text, topic.code_name_terms):
            score += 10
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        score += score_text(name_text + "\n" + text, topic)
        if score > 0:
            code_scores.append((score, path))
    code_scores.sort(key=lambda item: item[0], reverse=True)

    summary_pages = [page_entry(page, score) for score, page in page_scores[:max_pages]]
    image_refs = [
        {
            "page_id": item["page_id"],
            "source_pdf": item["source_pdf"],
            "page": item["page"],
            "image": item["image"],
            "role": "topic_reference",
            "score": item["score"],
        }
        for item in summary_pages
    ]
    return TopicKnowledge(
        topic_id=topic.topic_id,
        title=topic.title,
        keywords=topic.keywords,
        notes=topic.notes,
        summary_pages=summary_pages,
        image_refs=image_refs,
        past_questions=[question_entry(question, score) for score, question in question_scores[:max_questions]],
        code_questions=[code_entry(path, question_dir, score) for score, path in code_scores[:max_code]],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="주제별 이미지/텍스트/문제 지식베이스를 생성합니다.")
    parser.add_argument("--summary-pages", default="data/processed/mapping/summary_pages.json")
    parser.add_argument("--past-questions", default="data/processed/past_questions.json")
    parser.add_argument("--question-dir", default="data/question")
    parser.add_argument("--output", default="data/processed/mapping/topic_knowledge_base.json")
    parser.add_argument("--max-pages", type=int, default=12)
    parser.add_argument("--max-questions", type=int, default=20)
    parser.add_argument("--max-code", type=int, default=25)
    args = parser.parse_args()

    pages = load_json(Path(args.summary_pages))
    past_questions = load_json(Path(args.past_questions))
    question_dir = Path(args.question_dir)
    topics = [
        build_topic(topic, pages, past_questions, question_dir, args.max_pages, args.max_questions, args.max_code)
        for topic in TOPICS
    ]
    data = {
        "version": 1,
        "description": "주제별로 PDF 텍스트, PDF 페이지 이미지, 기출문제, 코드 문제 파일을 연결한 지식베이스",
        "topics": [asdict(topic) for topic in topics],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"topics": len(topics), "output": str(output)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
