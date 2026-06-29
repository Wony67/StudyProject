from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


WEB_SOURCE_NAMES = {
    "web-summary-193": "chobopark 족보 1탄",
    "web-summary-197": "chobopark 족보 2탄",
    "web-summary-198": "chobopark 족보 3탄",
}

CONCEPT_GROUPS = [
    {
        "id": "network-osi-7-layer",
        "title": "OSI 7계층",
        "category": "network",
        "aliases": ["OSI 7계층", "OSI", "응용 계층", "표현 계층", "세션 계층", "전송 계층", "네트워크 계층", "데이터링크 계층", "물리 계층"],
    },
    {
        "id": "network-protocol-elements",
        "title": "프로토콜의 3요소",
        "category": "network",
        "aliases": ["프로토콜의 3요소", "구문", "의미", "타이밍"],
    },
    {
        "id": "network-routing-ospf",
        "title": "OSPF와 라우팅",
        "category": "network",
        "aliases": ["OSPF", "라우팅", "다익스트라", "홉 카운트"],
    },
    {
        "id": "network-icmp-ip-tcp",
        "title": "ICMP와 TCP/IP",
        "category": "network",
        "aliases": ["ICMP", "TCP/IP", "TCP", "IP 패킷", "Internet Control Message Protocol"],
    },
    {
        "id": "security-crypto-hash",
        "title": "암호화와 해시",
        "category": "security",
        "aliases": ["암호화", "해시", "MD5", "SHA-1", "SHA-256", "HAS-160", "대칭 키", "비대칭 키"],
    },
    {
        "id": "security-access-control",
        "title": "접근통제",
        "category": "security",
        "aliases": ["접근통제", "서버 접근통제", "DAC", "MAC", "RBAC", "임의적 접근통제", "강제적 접근통제", "역할 기반 접근통제"],
    },
    {
        "id": "security-network-attacks",
        "title": "네트워크 공격 기법",
        "category": "security",
        "aliases": ["네트워크 공격", "스니핑", "스푸핑", "ARP 스푸핑", "IP 스푸핑", "패스워드 크래킹", "트로이 목마"],
    },
    {
        "id": "db-transaction-acid",
        "title": "트랜잭션 특성",
        "category": "database",
        "aliases": ["트랜잭션 특성", "원자성", "일관성", "격리성", "영속성", "ACID"],
    },
    {
        "id": "db-normalization",
        "title": "정규화와 반정규화",
        "category": "database",
        "aliases": ["정규화", "반정규화", "반정규화의 주요 기법", "함수적 종속", "테이블 병합", "테이블 분할"],
    },
    {
        "id": "db-anomaly",
        "title": "데이터베이스 이상 현상",
        "category": "database",
        "aliases": ["이상 현상", "데이터베이스 이상", "삽입 이상", "삭제 이상", "갱신 이상"],
    },
    {
        "id": "db-design-modeling",
        "title": "DB 설계와 데이터 모델링",
        "category": "database",
        "aliases": ["DB 설계", "DB설계", "데이터 모델링", "데이터모델링", "개념적 설계", "논리적 설계", "물리적 설계"],
    },
    {
        "id": "db-model-components",
        "title": "데이터 모델 구성요소",
        "category": "database",
        "aliases": ["데이터 모델 구성요소", "연산", "구조", "제약조건"],
    },
    {
        "id": "db-sql-tcl",
        "title": "SQL과 TCL",
        "category": "database",
        "aliases": ["SQL", "TCL", "커밋", "롤백", "체크 포인트", "COMMIT", "ROLLBACK"],
    },
    {
        "id": "sw-methodology",
        "title": "소프트웨어 개발방법론",
        "category": "software_engineering",
        "aliases": ["소프트웨어 개발방법론", "폭포수", "나선형", "애자일", "구조적 방법론", "정보공학", "객체지향 방법론", "컴포넌트 기반"],
    },
    {
        "id": "sw-agile-xp",
        "title": "애자일과 XP",
        "category": "software_engineering",
        "aliases": ["애자일", "XP", "스크럼", "Scrum", "FDD", "칸반", "Lean"],
    },
    {
        "id": "sw-coupling-cohesion",
        "title": "결합도와 응집도",
        "category": "software_engineering",
        "aliases": ["결합도", "응집도", "자료 결합도", "내용 결합도", "기능적 응집도"],
    },
    {
        "id": "sw-design-pattern",
        "title": "디자인 패턴",
        "category": "software_engineering",
        "aliases": ["디자인 패턴", "생성 패턴", "구조 패턴", "행위 패턴", "Mediator", "Iterator", "Observer", "Strategy"],
    },
    {
        "id": "sw-refactoring",
        "title": "리팩토링",
        "category": "software_engineering",
        "aliases": ["리팩토링", "유지보수성", "소스의 가독성", "품질 향상"],
    },
    {
        "id": "sw-uml-modeling",
        "title": "UML과 모델링 도구",
        "category": "software_engineering",
        "aliases": ["UML", "HIPO", "자료 사전", "DFD", "유스케이스"],
    },
    {
        "id": "test-black-white-oracle",
        "title": "테스트 기법과 테스트 오라클",
        "category": "testing",
        "aliases": ["블랙박스 테스트", "화이트박스 테스트", "테스트 오라클", "동등분할", "경곗값", "참 오라클", "샘플링 오라클"],
    },
    {
        "id": "ui-design-quality",
        "title": "UI 설계 원칙과 품질 요구사항",
        "category": "ui",
        "aliases": ["UI 설계 원칙", "UI 품질", "직관성", "유효성", "학습성", "유연성", "신뢰성", "이식성"],
    },
    {
        "id": "app-performance",
        "title": "애플리케이션 성능 측정 지표",
        "category": "software_engineering",
        "aliases": ["애플리케이션 성능", "처리량", "응답 시간", "경과 시간", "자원 사용률"],
    },
    {
        "id": "integration-eai",
        "title": "EAI 구축 유형",
        "category": "integration",
        "aliases": ["EAI", "포인트 투 포인트", "허브 앤 스포크", "메시지 버스", "하이브리드"],
    },
    {
        "id": "algorithm-flowchart-debugging",
        "title": "순서도와 디버깅",
        "category": "algorithm",
        "aliases": ["순서도", "디버깅", "단자", "준비", "처리", "판단", "Process", "Decision"],
    },
    {
        "id": "algorithm-sort",
        "title": "정렬 알고리즘",
        "category": "algorithm",
        "aliases": ["삽입 정렬", "선택 정렬", "버블 정렬", "Insertion Sort", "Selection Sort", "Bubble Sort"],
    },
    {
        "id": "blockchain-consensus",
        "title": "블록체인 합의 알고리즘",
        "category": "new_tech",
        "aliases": ["블록체인 합의", "PoW", "Proof of Work", "PoS", "Proof of Stake"],
    },
    {
        "id": "android-features",
        "title": "안드로이드 특징",
        "category": "platform",
        "aliases": ["안드로이드", "리눅스 기반", "SDK", "자바와 코틀린"],
    },
]


@dataclass
class SourceHit:
    source_type: str
    source_id: str
    source_name: str
    path: str
    matched_aliases: list[str]
    excerpt: str


@dataclass
class ConsolidatedConcept:
    id: str
    title: str
    category: str
    aliases: list[str]
    importance_score: int
    duplicate_level: str
    source_count: int
    sources: list[SourceHit]
    merge_policy: str


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def matched_aliases(text: str, aliases: list[str]) -> list[str]:
    compacted = compact(text)
    hits = []
    for alias in aliases:
        alias_compact = compact(alias)
        if len(alias_compact) < 2:
            continue
        if alias_compact in compacted:
            hits.append(alias)
    return hits


def excerpt_around(text: str, aliases: list[str], limit: int = 420) -> str:
    normalized = normalize_text(text)
    compacted = compact(normalized)
    best_index = -1
    for alias in aliases:
        index = compacted.find(compact(alias))
        if index >= 0:
            ratio = max(len(normalized), 1) / max(len(compacted), 1)
            best_index = int(index * ratio)
            break
    if best_index < 0:
        return normalized[:limit]
    start = max(0, best_index - limit // 3)
    end = min(len(normalized), start + limit)
    return normalized[start:end].strip()


def extract_web_entries(web_summaries: list[dict[str, object]]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for summary in web_summaries:
        source_id = str(summary["id"])
        lines = [line.strip() for line in str(summary["text"]).splitlines() if line.strip()]
        for index, line in enumerate(lines):
            if index == 0 and "족보" in line:
                continue
            title = ""
            body = ""
            heading = re.match(r"^(.{2,80}?)(?:\s*[:：]\s*|\s+-\s*)$", line)
            inline = re.match(r"^(.{2,80}?)\s+-\s+(.+)$", line)
            if heading:
                title = heading.group(1).strip()
                body_lines = []
                for next_line in lines[index + 1 : index + 14]:
                    if re.match(r"^(.{2,80}?)(?:\s*[:：]\s*|\s+-\s*)$", next_line):
                        break
                    body_lines.append(next_line)
                body = " ".join(body_lines)
            elif inline:
                title = inline.group(1).strip()
                body = inline.group(2).strip()
            if title and body:
                entries.append(
                    {
                        "source_id": source_id,
                        "source_name": WEB_SOURCE_NAMES.get(source_id, source_id),
                        "path": f"data/processed/web_summary/{source_id}.txt",
                        "title": title,
                        "text": f"{title}\n{body}",
                    }
                )
    return entries


def extract_velog_entries(velog_summaries: list[dict[str, object]]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for chapter in velog_summaries:
        source_id = str(chapter["id"])
        chapter_title = str(chapter["title"])
        for section in chapter.get("sections", []):
            if not isinstance(section, dict):
                continue
            title = str(section.get("title", "")).strip()
            content = section.get("content", [])
            if not title or not isinstance(content, list):
                continue
            body = " ".join(str(line).strip() for line in content if str(line).strip())
            if not body:
                continue
            entries.append(
                {
                    "source_id": source_id,
                    "source_name": f"velog {chapter_title}",
                    "path": f"data/processed/velog_summary/{source_id}.txt",
                    "title": title,
                    "text": f"{title}\n{body}",
                }
            )
    return entries


def build_sources(
    root: Path,
    concept: dict[str, object],
    web_entries: list[dict[str, str]],
    velog_entries: list[dict[str, str]],
    pdf_texts: dict[str, str],
) -> list[SourceHit]:
    aliases = list(concept["aliases"])
    sources: list[SourceHit] = []
    seen: set[tuple[str, str]] = set()

    for entry in web_entries:
        hits = matched_aliases(entry["text"], aliases)
        if not hits:
            continue
        key = ("web", entry["source_id"])
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            SourceHit(
                source_type="web_summary",
                source_id=entry["source_id"],
                source_name=entry["source_name"],
                path=entry["path"],
                matched_aliases=hits[:8],
                excerpt=excerpt_around(entry["text"], hits),
            )
        )

    for entry in velog_entries:
        hits = matched_aliases(entry["text"], aliases)
        if not hits:
            continue
        key = ("velog", entry["source_id"], entry["title"])
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            SourceHit(
                source_type="velog_summary",
                source_id=entry["source_id"],
                source_name=entry["source_name"],
                path=entry["path"],
                matched_aliases=hits[:8],
                excerpt=excerpt_around(entry["text"], hits),
            )
        )

    for name, text in pdf_texts.items():
        hits = matched_aliases(text, aliases)
        if not hits:
            continue
        sources.append(
            SourceHit(
                source_type="pdf_text",
                source_id=name,
                source_name=name.removesuffix(".txt"),
                path=f"data/processed/pdf/{name}",
                matched_aliases=hits[:8],
                excerpt=excerpt_around(text, hits),
            )
        )
    return sources


def duplicate_level(source_count: int) -> str:
    if source_count >= 5:
        return "high"
    if source_count >= 3:
        return "medium"
    if source_count >= 2:
        return "low"
    return "single"


def merge_policy(level: str) -> str:
    if level == "high":
        return "대표 개념으로 병합하고, 상세 설명 1개와 요약 키워드만 유지"
    if level == "medium":
        return "같은 개념으로 묶고 출처별 차이만 보존"
    if level == "low":
        return "중복 후보로 표시하되 원문 삭제는 보류"
    return "단일 출처 개념으로 유지"


def build(root: Path) -> dict[str, object]:
    web_path = root / "data" / "processed" / "web_summary" / "web_summaries.json"
    velog_path = root / "data" / "processed" / "velog_summary" / "velog_summaries.json"
    web_summaries = load_json(web_path)
    if not isinstance(web_summaries, list):
        raise ValueError("web_summaries.json 구조가 예상과 다릅니다.")
    velog_summaries = load_json(velog_path) if velog_path.exists() else []
    if not isinstance(velog_summaries, list):
        raise ValueError("velog_summaries.json 구조가 예상과 다릅니다.")

    pdf_dir = root / "data" / "processed" / "pdf"
    pdf_texts = {
        path.name: path.read_text(encoding="utf-8", errors="ignore")
        for path in sorted(pdf_dir.glob("*.txt"))
    }
    web_entries = extract_web_entries(web_summaries)
    velog_entries = extract_velog_entries(velog_summaries)

    concepts: list[ConsolidatedConcept] = []
    for concept in CONCEPT_GROUPS:
        sources = build_sources(root, concept, web_entries, velog_entries, pdf_texts)
        level = duplicate_level(len(sources))
        concepts.append(
            ConsolidatedConcept(
                id=str(concept["id"]),
                title=str(concept["title"]),
                category=str(concept["category"]),
                aliases=list(concept["aliases"]),
                importance_score=len(sources) * 10 + sum(len(source.matched_aliases) for source in sources),
                duplicate_level=level,
                source_count=len(sources),
                sources=sources,
                merge_policy=merge_policy(level),
            )
        )

    concepts.sort(key=lambda item: (item.duplicate_level != "high", -item.importance_score, item.category, item.title))
    return {
        "version": 1,
        "description": "웹 정리/요약과 PDF 요약본을 중복 개념 기준으로 병합한 통합 지식베이스",
        "source_files": {
            "web_summary": str(web_path.relative_to(root)),
            "velog_summary": str(velog_path.relative_to(root)) if velog_path.exists() else "",
            "pdf_texts": [str((pdf_dir / name).relative_to(root)) for name in sorted(pdf_texts)],
        },
        "build_policy": {
            "deduplication": "같은 개념의 상세 설명과 요약 키워드를 하나의 canonical concept로 묶음",
            "content_policy": "원문 전체가 아니라 출처 추적용 짧은 excerpt와 matched_aliases만 저장",
            "recommended_usage": "importance_score가 높은 개념은 예상문제 생성 시 우선순위를 높임",
        },
        "stats": {
            "concepts": len(concepts),
            "high_duplicate_concepts": sum(1 for item in concepts if item.duplicate_level == "high"),
            "medium_duplicate_concepts": sum(1 for item in concepts if item.duplicate_level == "medium"),
            "web_entries_scanned": len(web_entries),
            "velog_entries_scanned": len(velog_entries),
            "pdf_texts_scanned": len(pdf_texts),
        },
        "concepts": [asdict(item) for item in concepts],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="중복 개념을 병합한 통합 지식베이스 생성")
    parser.add_argument("--output", default="data/processed/consolidated_knowledge_base.json")
    args = parser.parse_args()

    root = Path.cwd()
    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = build(root)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output_path), "stats": data["stats"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
