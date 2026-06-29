from __future__ import annotations

import json
from pathlib import Path


OUTPUT = Path("data/processed/expected_questions.json")


def display(
    prompt: str,
    *,
    description: list[str] | None = None,
    items: list[str] | None = None,
    conditions: list[str] | None = None,
    choices: list[str] | None = None,
    targets: list[str] | None = None,
    code_language: str = "",
    code: str = "",
    input_text: str = "",
    output: str = "",
    tables: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "prompt": prompt,
        "description": description or [],
        "items": items or [],
        "conditions": conditions or [],
        "choices": choices or [],
        "targets": targets or [],
        "code_language": code_language,
        "code": code,
        "input": input_text,
    }
    if output:
        data["output"] = output
    if tables:
        data["tables"] = tables
    return data


def q(
    round_no: int,
    number: int,
    category: str,
    question_type: str,
    basis: list[str],
    display_data: dict[str, object],
    answer: str,
    explanation: str,
    difficulty: str = "medium",
) -> dict[str, object]:
    return {
        "id": f"expected-2026-{round_no}-{number:02d}",
        "type": "expected",
        "exam": "정보처리기사 실기",
        "year": 1,
        "round": round_no,
        "number": number,
        "category": category,
        "difficulty": difficulty,
        "basis": basis,
        "display": display_data,
        "answer": answer,
        "explanation": explanation,
        "source_url": "",
        "image_refs": [],
        "question_type": question_type,
    }


def build_new_questions() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    rows.extend(
        [
            q(6, 1, "소프트웨어공학", "concept", ["velog-summary-01", "summary-sw-methodology"], display("다음 설명에 해당하는 소프트웨어 생명주기 모형을 쓰시오.", description=["개발 초기부터 위험을 식별하고 분석하며, 계획 수립, 위험 분석, 개발 및 검증, 고객 평가 과정을 반복적으로 수행한다."]), "나선형 모형", "나선형 모형은 반복 개발 구조에 위험 분석 활동을 포함한 생명주기 모형이다."),
            q(6, 2, "데이터베이스", "concept", ["velog-summary-02", "summary-db-model-components"], display("다음 데이터 모델 구성 요소에 해당하는 용어를 쓰시오.", items=["1. 데이터베이스에 저장되는 대상이나 사물을 의미한다.", "2. 개체 사이에 존재하는 연관성을 의미한다."], targets=["1", "2"]), "1. 개체\n2. 관계", "데이터 모델은 개체, 속성, 관계로 구성된다. 개체는 관리 대상이고 관계는 개체 간 연관성이다."),
            q(6, 3, "SQL", "sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 SQL 실행 결과로 조회되는 행의 수를 쓰시오.", tables=[{"title": "EMP", "headers": ["ID", "DEPT", "SAL"], "rows": [["1", "개발", "300"], ["2", "보안", "420"], ["3", "개발", "500"], ["4", "품질", "280"]]}], code_language="sql", code="SELECT COUNT(*)\nFROM EMP\nWHERE DEPT = '개발' AND SAL >= 300;"), "2", "DEPT가 개발인 행은 1번과 3번이고 두 행 모두 SAL이 300 이상이므로 결과는 2건이다."),
            q(6, 4, "보안", "choice", ["velog-summary-09", "summary-security-crypto-hash"], display("다음 설명에 해당하는 암호화 방식을 보기에서 고르시오.", description=["암호화와 복호화에 서로 다른 키를 사용하며, 공개키와 개인키 쌍을 이용한다."], choices=["대칭키 암호화", "비대칭키 암호화", "해시", "스테가노그래피"]), "비대칭키 암호화", "비대칭키 암호화는 공개키와 개인키처럼 서로 다른 키를 사용한다."),
            q(6, 5, "프로그래밍", "code_output", ["programming-python-001", "velog-summary-04"], display("다음 Python 코드의 출력 결과를 작성하시오.", code_language="python", code="nums = [3, 1, 4, 1, 5]\nnums[1:4] = [sum(nums[:2])]\nprint(''.join(map(str, nums)))"), "345", "nums[:2]의 합은 4이고, 인덱스 1부터 3까지가 [4]로 치환되어 [3, 4, 5]가 된다."),
            q(6, 6, "네트워크", "concept", ["summary-network-protocol-elements", "web-summary-193"], display("프로토콜의 3요소 중 데이터 형식, 부호화, 신호 레벨 등을 규정하는 요소를 쓰시오."), "구문", "프로토콜의 구문은 데이터 형식과 코딩, 신호 레벨 등을 정의한다."),
            q(6, 7, "프로그래밍", "code_output", ["programming-java-001", "question-bank-java-array"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="public class Main {\n  public static void main(String[] args) {\n    int[] a = {1, 2, 3};\n    for (int i = 0; i < a.length; i++) {\n      a[i] += (i == 0) ? a[2] : a[i - 1];\n    }\n    System.out.print(\"\" + a[0] + a[1] + a[2]);\n  }\n}"), "469", "a[0]은 1+3=4, a[1]은 2+4=6, a[2]는 3+6=9가 되어 469가 출력된다."),
            q(6, 8, "데이터베이스", "concept", ["velog-summary-02", "summary-db-normalization"], display("다음 설명에 해당하는 정규형을 쓰시오.", description=["제2정규형을 만족하고, 기본키가 아닌 속성 사이의 이행 함수 종속을 제거한 정규형이다."]), "제3정규형", "제3정규형은 제2정규형에서 이행 함수 종속을 제거한 정규형이다."),
            q(6, 9, "SQL", "table_sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 STUDENT 테이블에서 SQL 실행 결과를 쓰시오.", tables=[{"title": "STUDENT", "headers": ["NAME", "SCORE"], "rows": [["Kim", "80"], ["Lee", "90"], ["Park", "90"], ["Choi", "70"]]}], code_language="sql", code="SELECT MAX(SCORE)\nFROM STUDENT;"), "90", "SCORE 값 중 가장 큰 값은 90이다."),
            q(6, 10, "프로그래밍", "code_output", ["programming-c-001", "question-bank-c-operator"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nint main() {\n  int a = 5, b = 2;\n  printf(\"%d\", a++ + ++b * 2);\n  return 0;\n}"), "11", "a++는 식에서 5로 사용되고, ++b는 3이 된다. 5 + 3*2 = 11이다."),
            q(6, 11, "소프트웨어공학", "concept", ["velog-summary-01", "summary-sw-agile-xp"], display("XP의 5가지 가치 중 빈칸에 들어갈 용어를 쓰시오.", items=["의사소통", "단순성", "용기", "존중", "(  )"], targets=["(  )"]), "피드백", "XP의 주요 가치는 의사소통, 단순성, 용기, 존중, 피드백이다."),
            q(6, 12, "프로그래밍", "code_output", ["programming-python-002", "question-bank-python-slice"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="s = 'security'\nprint(s[1:7:2] + s[-1])"), "euiy", "s[1:7:2]는 e, u, i이고 마지막 문자는 y이므로 euiy가 출력된다."),
            q(6, 13, "테스트", "concept", ["velog-summary-07", "summary-test-black-white-oracle"], display("동등 분할과 경계값 분석이 대표적으로 속하는 테스트 기법을 쓰시오."), "블랙박스 테스트", "동등 분할과 경계값 분석은 내부 구조가 아니라 입력과 출력에 기반한 블랙박스 테스트 기법이다."),
            q(6, 14, "프로그래밍", "code_output", ["programming-java-002", "question-bank-java-string"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="public class Main {\n  public static void main(String[] args) {\n    String s = \"ABCD\";\n    System.out.print(s.substring(1, 3) + s.charAt(0));\n  }\n}"), "BCA", "substring(1,3)은 인덱스 1부터 2까지인 BC이고 charAt(0)은 A이다."),
            q(6, 15, "UI", "choice", ["velog-summary-06", "summary-ui-design-quality"], display("다음 설명에 해당하는 UI 설계 원칙을 보기에서 고르시오.", description=["사용자가 별도의 학습 없이 쉽게 이해하고 사용할 수 있어야 한다는 원칙이다."], choices=["직관성", "유효성", "학습성", "유연성"]), "직관성", "직관성은 사용자가 쉽게 이해하고 사용할 수 있어야 한다는 UI 설계 원칙이다."),
            q(6, 16, "프로그래밍", "code_output", ["programming-c-002", "question-bank-c-loop"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nint main() {\n  int sum = 0;\n  for (int i = 1; i <= 5; i++) {\n    if (i % 2 == 0) continue;\n    sum += i;\n  }\n  printf(\"%d\", sum);\n  return 0;\n}"), "9", "1, 3, 5만 더하므로 합은 9이다."),
            q(6, 17, "통합/연계", "concept", ["velog-summary-05", "summary-integration-eai"], display("EAI 구축 유형 중 중앙의 허브 시스템을 통해 데이터를 전송하고 관리하는 방식을 쓰시오."), "허브 앤 스포크", "허브 앤 스포크 방식은 중앙 허브를 통해 각 시스템을 연결한다."),
            q(6, 18, "프로그래밍", "code_output", ["programming-python-003", "question-bank-python-dict"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="d = {'a': 2, 'b': 3}\nd['a'] += d.get('c', 4)\nprint(d['a'] * d['b'])"), "18", "d.get('c',4)는 4이므로 a는 6이 되고 6*3=18이다."),
            q(6, 19, "보안", "short_answer", ["velog-summary-09", "summary-security-access-control"], display("접근통제 방식 중 사용자 역할에 따라 권한을 부여하는 방식을 쓰시오."), "RBAC", "RBAC는 Role Based Access Control로 역할 기반 접근통제이다."),
            q(6, 20, "SQL", "sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 SQL문의 빈칸에 들어갈 명령어를 쓰시오.", description=["트랜잭션 작업 결과를 데이터베이스에 영구 반영한다."], code_language="sql", code="(   );"), "COMMIT", "COMMIT은 트랜잭션 결과를 데이터베이스에 반영하는 TCL 명령어이다."),
        ]
    )

    rows.extend(
        [
            q(7, 1, "데이터베이스", "concept", ["velog-summary-02", "summary-db-anomaly"], display("다음 설명에 해당하는 이상 현상을 쓰시오.", description=["튜플을 삭제할 때 의도하지 않은 다른 정보까지 함께 사라지는 현상이다."]), "삭제 이상", "삭제 이상은 데이터 삭제 과정에서 보존해야 할 정보가 함께 사라지는 이상 현상이다."),
            q(7, 2, "프로그래밍", "code_output", ["programming-python-004", "question-bank-python-list"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="a = [1, 2, 3]\nb = a\nb.append(4)\na[0] = b[-1]\nprint(sum(a))"), "13", "a와 b는 같은 리스트를 참조한다. append 후 [1,2,3,4], a[0]=4가 되어 합은 13이다."),
            q(7, 3, "소프트웨어공학", "concept", ["velog-summary-01", "summary-sw-uml-modeling"], display("UML 관계 중 한 클래스가 다른 클래스의 특성을 상속받는 관계를 쓰시오."), "일반화 관계", "일반화 관계는 상위 개념과 하위 개념 사이의 상속 관계를 표현한다."),
            q(7, 4, "SQL", "sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 조건을 만족하는 SQL문의 빈칸에 들어갈 절을 쓰시오.", description=["DEPT별 평균 급여가 300 이상인 부서만 조회한다."], code_language="sql", code="SELECT DEPT, AVG(SAL)\nFROM EMP\nGROUP BY DEPT\n(          );"), "HAVING AVG(SAL) >= 300", "그룹 함수 조건은 WHERE가 아니라 HAVING 절에 작성한다."),
            q(7, 5, "보안", "choice", ["velog-summary-09", "summary-security-network-attacks"], display("다음 설명에 해당하는 공격 기법을 보기에서 고르시오.", description=["정상 사이트와 유사한 가짜 사이트로 사용자를 유도하여 개인정보를 탈취한다."], choices=["스니핑", "스푸핑", "피싱", "세션 하이재킹"]), "피싱", "피싱은 가짜 사이트나 메시지를 이용해 개인정보를 탈취하는 공격이다."),
            q(7, 6, "프로그래밍", "code_output", ["programming-java-004", "question-bank-java-loop"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="public class Main {\n  public static void main(String[] args) {\n    int n = 0;\n    for (int i = 1; i <= 4; i++) {\n      n += i % 2 == 0 ? i * 2 : i;\n    }\n    System.out.print(n);\n  }\n}"), "16", "1 + 4 + 3 + 8 = 16이다."),
            q(7, 7, "네트워크", "concept", ["velog-summary-03", "summary-network-osi-7-layer"], display("OSI 7계층 중 종단 간 신뢰성 있는 데이터 전송과 흐름 제어를 담당하는 계층을 쓰시오."), "전송 계층", "전송 계층은 종단 간 통신, 흐름 제어, 오류 제어를 담당한다."),
            q(7, 8, "프로그래밍", "code_output", ["programming-c-003", "question-bank-c-pointer"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nint main() {\n  int a[3] = {2, 4, 6};\n  int *p = a;\n  printf(\"%d\", *(p + 1) + *p);\n  return 0;\n}"), "6", "*(p+1)은 4, *p는 2이므로 합은 6이다."),
            q(7, 9, "데이터베이스", "concept", ["velog-summary-02", "summary-db-transaction-acid"], display("트랜잭션 ACID 특성 중 트랜잭션 실행 중 다른 트랜잭션이 중간 결과에 접근할 수 없도록 하는 특성을 쓰시오."), "격리성", "격리성은 트랜잭션의 중간 결과가 다른 트랜잭션에 영향을 주지 않도록 보장한다."),
            q(7, 10, "SQL", "table_sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 테이블에서 SQL 실행 결과를 쓰시오.", tables=[{"title": "ORDERS", "headers": ["ID", "AMT"], "rows": [["1", "100"], ["2", "200"], ["3", "100"]]}], code_language="sql", code="SELECT SUM(AMT)\nFROM ORDERS\nWHERE AMT <> 100;"), "200", "AMT가 100이 아닌 행은 ID 2 한 건이며 합은 200이다."),
            q(7, 11, "프로그래밍", "code_output", ["programming-python-005", "question-bank-python-set"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="a = {1, 2, 3}\nb = {3, 4}\nprint(len(a | b), len(a & b))"), "4 1", "합집합은 {1,2,3,4}로 4개, 교집합은 {3}으로 1개이다."),
            q(7, 12, "테스트", "concept", ["velog-summary-07", "summary-test-black-white-oracle"], display("테스트 오라클 중 모든 입력값에 대해 기대 결과를 생성할 수 있는 오라클을 쓰시오."), "참 오라클", "참 오라클은 모든 테스트 케이스에 대해 기대 결과를 제공한다."),
            q(7, 13, "프로그래밍", "code_output", ["programming-java-005", "question-bank-java-class"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="class Box {\n  int v;\n  Box(int v) { this.v = v; }\n}\npublic class Main {\n  public static void main(String[] args) {\n    Box b = new Box(3);\n    Box c = b;\n    c.v += 4;\n    System.out.print(b.v);\n  }\n}"), "7", "b와 c는 같은 객체를 참조하므로 c.v를 변경하면 b.v도 7로 보인다."),
            q(7, 14, "소프트웨어공학", "concept", ["velog-summary-04", "summary-sw-coupling-cohesion"], display("모듈 내부의 모든 기능이 단일 목적을 위해 수행되는 가장 강한 응집도를 쓰시오."), "기능적 응집도", "기능적 응집도는 모듈 내 요소들이 하나의 기능 수행을 위해 구성된 가장 강한 응집도이다."),
            q(7, 15, "신기술", "choice", ["summary-blockchain-consensus", "web-summary-198"], display("다음 설명에 해당하는 블록체인 합의 방식을 보기에서 고르시오.", description=["연산 경쟁을 통해 블록 생성 권한을 얻는 방식으로 많은 컴퓨팅 자원이 필요하다."], choices=["PoW", "PoS", "PBFT", "DPoS"]), "PoW", "PoW는 작업 증명 방식으로 계산 작업을 통해 합의를 수행한다."),
            q(7, 16, "프로그래밍", "code_output", ["programming-c-004", "question-bank-c-array"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nint main() {\n  int a[] = {1, 3, 5, 7};\n  printf(\"%d\", a[3] - a[1] + a[0]);\n  return 0;\n}"), "5", "7 - 3 + 1 = 5이다."),
            q(7, 17, "UI", "short_answer", ["velog-summary-06", "summary-ui-design-quality"], display("UI 품질 요구사항 중 사용자의 요구를 정확하고 완전하게 달성하는 정도를 의미하는 특성을 쓰시오."), "유효성", "유효성은 사용자의 목적이 정확하고 완전하게 달성되는 정도를 의미한다."),
            q(7, 18, "프로그래밍", "code_output", ["programming-python-006", "question-bank-python-range"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="total = 0\nfor i in range(2, 9, 2):\n    total += i // 2\nprint(total)"), "10", "i는 2,4,6,8이고 각각 1,2,3,4를 더하므로 합은 10이다."),
            q(7, 19, "통합/연계", "concept", ["velog-summary-05", "summary-integration-eai"], display("서로 다른 시스템 간 인터페이스를 위해 송수신 데이터 구조와 형식을 정의한 문서를 무엇이라 하는지 쓰시오."), "인터페이스 명세서", "인터페이스 명세서는 시스템 간 송수신 데이터, 방식, 제약 등을 정의한다."),
            q(7, 20, "데이터베이스", "concept", ["velog-summary-02", "summary-db-design-modeling"], display("데이터베이스 설계 단계 중 목표 DBMS에 맞는 스키마, 트랜잭션 인터페이스 등을 설계하는 단계를 쓰시오."), "논리적 설계", "논리적 설계는 목표 DBMS의 논리 데이터 모델에 맞게 스키마를 설계하는 단계이다."),
        ]
    )

    rows.extend(
        [
            q(8, 1, "SQL", "sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 SQL에서 빈칸에 들어갈 키워드를 쓰시오.", description=["중복을 제거한 합집합 결과를 반환한다."], code_language="sql", code="SELECT NAME FROM A\n(     )\nSELECT NAME FROM B;"), "UNION", "UNION은 두 SELECT 결과를 합치며 중복을 제거한다. UNION ALL은 중복을 포함한다."),
            q(8, 2, "프로그래밍", "code_output", ["programming-python-007", "question-bank-python-string"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="s = 'AB12CD'\nprint(s[::2] + s[1::3])"), "A1CBC", "s[::2]는 A1C이고 s[1::3]은 인덱스 1과 4의 B, C이므로 A1CBC가 출력된다."),
        ]
    )

    rows.extend(
        [
            q(8, 3, "소프트웨어공학", "concept", ["velog-summary-04", "summary-sw-design-pattern"], display("디자인 패턴 중 객체 상태 변화에 따라 관련 객체들에게 자동으로 통지하는 행위 패턴을 쓰시오."), "Observer", "Observer 패턴은 한 객체의 상태 변화가 의존 객체들에게 자동으로 전달되도록 한다."),
            q(8, 4, "데이터베이스", "concept", ["velog-summary-02", "summary-db-normalization"], display("정규화의 목적으로 가장 적절한 내용을 쓰시오.", description=["이상 현상을 줄이고 데이터 중복을 최소화하기 위해 테이블을 체계적으로 분해한다."]), "데이터 중복 최소화 및 이상 현상 제거", "정규화는 중복을 줄이고 삽입, 삭제, 갱신 이상을 방지하기 위한 과정이다."),
            q(8, 5, "프로그래밍", "code_output", ["programming-java-006", "question-bank-java-inheritance"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="class A { int f() { return 2; } }\nclass B extends A { int f() { return 5; } }\npublic class Main {\n  public static void main(String[] args) {\n    A x = new B();\n    System.out.print(x.f() + 1);\n  }\n}"), "6", "오버라이딩된 B의 f()가 동적 바인딩으로 호출되어 5+1=6이 출력된다."),
            q(8, 6, "보안", "concept", ["velog-summary-09", "summary-security-crypto-hash"], display("입력값의 길이와 관계없이 고정 길이의 결과값을 생성하고, 원문 복원이 어려운 함수를 쓰시오."), "해시 함수", "해시 함수는 임의 길이 입력을 고정 길이 값으로 변환하며 일방향성이 있다."),
            q(8, 7, "프로그래밍", "code_output", ["programming-c-005", "question-bank-c-format"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nint main() {\n  printf(\"%04d %.1f\", 7, 3.26);\n  return 0;\n}"), "0007 3.3", "%04d는 네 자리 0 채움이고 %.1f는 소수 둘째 자리에서 반올림한다."),
            q(8, 8, "네트워크", "concept", ["summary-network-icmp-ip-tcp", "web-summary-197"], display("IP 계층에서 오류 보고와 진단 메시지 전송에 사용되는 프로토콜을 쓰시오."), "ICMP", "ICMP는 IP 패킷 처리 중 발생한 오류 보고와 진단에 사용된다."),
            q(8, 9, "SQL", "table_sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 테이블에서 SQL 실행 결과를 쓰시오.", tables=[{"title": "SALES", "headers": ["AREA", "AMT"], "rows": [["A", "10"], ["A", "20"], ["B", "15"]]}], code_language="sql", code="SELECT AREA, SUM(AMT)\nFROM SALES\nGROUP BY AREA\nHAVING SUM(AMT) >= 20;"), "A 30", "A의 합은 30, B의 합은 15이므로 HAVING 조건을 만족하는 그룹은 A뿐이다."),
            q(8, 10, "프로그래밍", "code_output", ["programming-python-008", "question-bank-python-dict"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="data = ['aa', 'b', 'ccc']\nprint(''.join(str(len(x)) for x in data))"), "213", "각 문자열 길이는 2, 1, 3이므로 213이 출력된다."),
            q(8, 11, "테스트", "choice", ["velog-summary-07", "summary-test-black-white-oracle"], display("다음 설명에 해당하는 테스트를 보기에서 고르시오.", description=["소프트웨어 내부 구조와 경로를 고려하여 테스트 케이스를 설계한다."], choices=["블랙박스 테스트", "화이트박스 테스트", "인수 테스트", "알파 테스트"]), "화이트박스 테스트", "화이트박스 테스트는 내부 로직, 제어 흐름, 경로를 기준으로 테스트한다."),
            q(8, 12, "프로그래밍", "code_output", ["programming-java-007", "question-bank-java-collection"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="import java.util.*;\npublic class Main {\n  public static void main(String[] args) {\n    ArrayList<Integer> a = new ArrayList<>();\n    a.add(2); a.add(4); a.add(1);\n    a.remove(1);\n    System.out.print(a.get(1));\n  }\n}"), "1", "remove(1)은 인덱스 1의 값 4를 제거하므로 남은 리스트는 [2,1]이다."),
            q(8, 13, "소프트웨어공학", "concept", ["velog-summary-01", "summary-sw-uml-modeling"], display("자료 흐름도 DFD에서 데이터의 저장 장소를 의미하는 구성 요소를 쓰시오."), "자료 저장소", "DFD의 자료 저장소는 데이터가 저장되는 위치를 나타낸다."),
            q(8, 14, "프로그래밍", "code_output", ["programming-c-006", "question-bank-c-function"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nint f(int x) { return x * 2 + 1; }\nint main() {\n  printf(\"%d\", f(f(1)));\n  return 0;\n}"), "7", "f(1)=3이고 f(3)=7이다."),
            q(8, 15, "통합/연계", "concept", ["velog-summary-03", "summary-integration-eai"], display("연계 방식 중 송신 시스템이 중간 저장소에 파일을 생성하고 수신 시스템이 이를 읽어 처리하는 방식을 쓰시오."), "파일 연계", "파일 연계는 중간 파일을 통해 시스템 간 데이터를 주고받는 방식이다."),
            q(8, 16, "프로그래밍", "code_output", ["programming-python-009", "question-bank-python-class"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="class A:\n    v = 1\nx = A()\ny = A()\nx.v = 3\nprint(x.v + y.v)"), "4", "x.v는 인스턴스 속성 3이고 y.v는 클래스 속성 1을 참조하므로 합은 4이다."),
            q(8, 17, "데이터베이스", "concept", ["velog-summary-02", "summary-db-design-modeling"], display("E-R 다이어그램에서 개체는 일반적으로 어떤 도형으로 표현하는지 쓰시오."), "사각형", "E-R 다이어그램에서 개체는 사각형, 관계는 마름모, 속성은 타원으로 표현한다."),
            q(8, 18, "프로그래밍", "code_output", ["programming-c-007", "question-bank-c-struct"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nstruct S { int a; int b; };\nint main() {\n  struct S s = {2, 5};\n  s.a += s.b;\n  printf(\"%d\", s.a - s.b);\n  return 0;\n}"), "2", "s.a는 7이 되고 7-5=2가 출력된다."),
            q(8, 19, "보안", "short_answer", ["velog-summary-09", "summary-security-access-control"], display("강제적 접근통제를 의미하는 영문 약어를 쓰시오."), "MAC", "MAC는 Mandatory Access Control의 약어이다."),
            q(8, 20, "SQL", "sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 SQL문의 빈칸에 들어갈 명령어를 쓰시오.", description=["사용자 KIM에게 EMP 테이블 조회 권한을 부여한다."], code_language="sql", code="(     ) SELECT ON EMP TO KIM;"), "GRANT", "GRANT는 사용자에게 권한을 부여하는 DCL 명령어이다."),
        ]
    )

    rows.extend(
        [
            q(9, 1, "소프트웨어공학", "concept", ["velog-summary-01", "summary-sw-agile-xp"], display("애자일 방법론 중 매일 짧은 회의를 통해 진행 상황과 장애 요소를 공유하는 기법을 쓰시오."), "일일 스크럼 회의", "스크럼에서는 매일 짧은 회의로 작업 현황과 문제를 공유한다."),
            q(9, 2, "프로그래밍", "code_output", ["programming-python-010", "question-bank-python-loop"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="r = ''\nfor ch in 'DATA':\n    r = ch + r\nprint(r[1:])"), "TAD", "문자열을 역순으로 누적하면 ATAD이고 인덱스 1부터 출력하면 TAD이다."),
            q(9, 3, "SQL", "table_sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 테이블에서 SQL 실행 결과를 쓰시오.", tables=[{"title": "T", "headers": ["A", "B"], "rows": [["1", "10"], ["2", "10"], ["3", "20"]]}], code_language="sql", code="SELECT COUNT(DISTINCT B)\nFROM T;"), "2", "B의 서로 다른 값은 10과 20이므로 2개이다."),
            q(9, 4, "보안", "concept", ["velog-summary-09", "summary-security-network-attacks"], display("네트워크 상에서 전송되는 패킷을 몰래 엿보는 공격 기법을 쓰시오."), "스니핑", "스니핑은 네트워크 트래픽을 도청하여 정보를 탈취하는 공격이다."),
            q(9, 5, "프로그래밍", "code_output", ["programming-java-008", "question-bank-java-operator"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="public class Main {\n  public static void main(String[] args) {\n    int a = 3;\n    int b = a++ + ++a;\n    System.out.print(a + \":\" + b);\n  }\n}"), "5:8", "a++는 3을 사용 후 4가 되고, ++a는 5가 되어 b는 8, a는 5이다."),
            q(9, 6, "데이터베이스", "concept", ["velog-summary-02", "summary-db-model-components"], display("관계형 데이터베이스에서 하나의 행을 의미하는 용어를 쓰시오."), "튜플", "관계형 데이터베이스에서 행은 튜플 또는 레코드라고 한다."),
            q(9, 7, "프로그래밍", "code_output", ["programming-c-008", "question-bank-c-recursion"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nint f(int n) {\n  if (n <= 1) return 1;\n  return n + f(n - 2);\n}\nint main() {\n  printf(\"%d\", f(5));\n  return 0;\n}"), "9", "f(5)=5+f(3), f(3)=3+f(1), f(1)=1이므로 합은 9이다."),
            q(9, 8, "UI", "concept", ["velog-summary-06", "summary-ui-design-quality"], display("UI 설계 원칙 중 사용자의 요구사항을 최대한 수용하고 오류를 최소화해야 한다는 원칙을 쓰시오."), "유효성", "유효성은 사용자의 목적을 정확하게 달성하고 오류를 최소화하는 원칙이다."),
            q(9, 9, "SQL", "sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 SQL문의 빈칸에 들어갈 키워드를 쓰시오.", description=["조건에 맞는 튜플을 삭제한다."], code_language="sql", code="(      ) FROM EMP\nWHERE DEPT = '임시';"), "DELETE", "DELETE FROM은 조건에 맞는 튜플을 삭제하는 DML 명령이다."),
            q(9, 10, "프로그래밍", "code_output", ["programming-python-011", "question-bank-python-list"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="a = [2, 4, 6]\nprint(a.pop() + a.pop(0))"), "8", "pop()은 6, pop(0)은 2를 반환하므로 합은 8이다."),
            q(9, 11, "테스트", "choice", ["velog-summary-07", "summary-test-black-white-oracle"], display("다음 설명에 해당하는 테스트 단계를 보기에서 고르시오.", description=["개발된 시스템이 사용자의 요구사항을 만족하는지 사용자가 중심이 되어 확인한다."], choices=["단위 테스트", "통합 테스트", "시스템 테스트", "인수 테스트"]), "인수 테스트", "인수 테스트는 사용자의 요구사항 충족 여부를 확인하는 테스트 단계이다."),
            q(9, 12, "프로그래밍", "code_output", ["programming-java-009", "question-bank-java-string"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="public class Main {\n  public static void main(String[] args) {\n    String s = \"test\";\n    System.out.print(s.replace(\"t\", \"T\"));\n  }\n}"), "TesT", "replace는 모든 t를 T로 바꾸므로 TesT가 출력된다."),
            q(9, 13, "통합/연계", "concept", ["velog-summary-05", "summary-integration-eai"], display("SOAP, WSDL, UDDI 등을 활용하며 표준 웹 기술로 시스템을 연계하는 방식을 쓰시오."), "웹 서비스", "웹 서비스 방식은 SOAP, WSDL, UDDI 등 웹 표준 기술을 이용한다."),
            q(9, 14, "프로그래밍", "code_output", ["programming-c-009", "question-bank-c-loop"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nint main() {\n  int i = 0, s = 0;\n  while (i++ < 4) s += i;\n  printf(\"%d\", s);\n  return 0;\n}"), "10", "i가 1,2,3,4일 때 더해져 합은 10이다."),
            q(9, 15, "데이터베이스", "concept", ["velog-summary-02", "summary-db-design-modeling"], display("하나의 속성이 가질 수 있는 원자값들의 집합을 의미하는 용어를 쓰시오."), "도메인", "도메인은 속성이 가질 수 있는 값의 범위 또는 집합이다."),
            q(9, 16, "프로그래밍", "code_output", ["programming-python-012", "question-bank-python-comprehension"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="nums = [1, 2, 3, 4]\nprint(sum(x for x in nums if x % 2 == 0))"), "6", "짝수 2와 4의 합은 6이다."),
            q(9, 17, "신기술", "concept", ["summary-blockchain-consensus", "velog-summary-09"], display("블록체인에서 보유 지분이 많을수록 블록 생성 권한을 얻을 가능성이 커지는 합의 방식을 쓰시오."), "PoS", "PoS는 Proof of Stake로 지분 기반 합의 방식이다."),
            q(9, 18, "프로그래밍", "code_output", ["programming-java-010", "question-bank-java-array"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="public class Main {\n  public static void main(String[] args) {\n    int[][] a = {{1, 2}, {3, 4}};\n    System.out.print(a[1][0] + a[0][1]);\n  }\n}"), "5", "a[1][0]은 3, a[0][1]은 2이므로 합은 5이다."),
            q(9, 19, "보안", "short_answer", ["velog-summary-09", "summary-security-crypto-hash"], display("해시 알고리즘 중 160비트 해시값을 생성하는 SHA 계열 알고리즘을 쓰시오."), "SHA-1", "SHA-1은 160비트 해시값을 생성하는 해시 알고리즘이다."),
            q(9, 20, "SQL", "sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 SQL문의 빈칸에 들어갈 키워드를 쓰시오.", description=["이미 생성된 테이블에 컬럼을 추가한다."], code_language="sql", code="ALTER TABLE EMP\n(   ) EMAIL VARCHAR2(50);"), "ADD", "ALTER TABLE에서 컬럼을 추가할 때 ADD를 사용한다."),
        ]
    )

    rows.extend(
        [
            q(10, 1, "데이터베이스", "concept", ["velog-summary-02", "summary-db-design-modeling"], display("데이터베이스 설계 단계 중 저장 구조, 접근 경로, 인덱스 등을 결정하는 단계를 쓰시오."), "물리적 설계", "물리적 설계는 실제 저장 구조와 접근 방법을 결정하는 단계이다."),
            q(10, 2, "프로그래밍", "code_output", ["programming-python-013", "question-bank-python-slice"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="s = 'network'\nprint(s[-3:] + s[:2])"), "orkne", "s[-3:]은 ork, s[:2]는 ne이므로 orkne가 출력된다."),
            q(10, 3, "소프트웨어공학", "concept", ["velog-summary-01", "summary-sw-methodology"], display("프로토타입 모형의 핵심 특징을 쓰시오.", description=["사용자 요구를 명확히 파악하기 위해 실제 개발될 시스템의 견본을 먼저 만든다."]), "시제품을 통해 요구사항을 확인한다", "프로토타입 모형은 견본품을 만들어 사용자 요구사항을 확인하고 보완한다."),
            q(10, 4, "SQL", "table_sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 테이블에서 SQL 실행 결과를 쓰시오.", tables=[{"title": "ITEM", "headers": ["CODE", "QTY"], "rows": [["A", "3"], ["B", "5"], ["C", "2"]]}], code_language="sql", code="SELECT CODE\nFROM ITEM\nWHERE QTY = (SELECT MIN(QTY) FROM ITEM);"), "C", "최소 QTY는 2이고 해당 CODE는 C이다."),
            q(10, 5, "보안", "choice", ["velog-summary-09", "summary-security-crypto-hash"], display("다음 중 일방향성 특성을 가지며 비밀번호 저장 등에 활용되는 것을 고르시오.", choices=["AES", "RSA", "SHA-256", "DES"]), "SHA-256", "SHA-256은 해시 알고리즘으로 일방향성이 있어 비밀번호 검증 등에 활용된다."),
            q(10, 6, "프로그래밍", "code_output", ["programming-c-010", "question-bank-c-pointer"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nint main() {\n  int x = 4;\n  int *p = &x;\n  *p += 3;\n  printf(\"%d\", x);\n  return 0;\n}"), "7", "포인터 p가 x를 가리키므로 *p += 3은 x를 7로 변경한다."),
            q(10, 7, "테스트", "concept", ["velog-summary-07", "summary-test-black-white-oracle"], display("테스트 케이스 실행 결과가 참인지 거짓인지 판단하기 위해 사전에 정의한 참값이나 기준을 무엇이라 하는지 쓰시오."), "테스트 오라클", "테스트 오라클은 테스트 결과의 정오를 판단하기 위한 기준이다."),
            q(10, 8, "프로그래밍", "code_output", ["programming-java-011", "question-bank-java-loop"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="public class Main {\n  public static void main(String[] args) {\n    int s = 1;\n    for (int i = 1; i <= 3; i++) s *= i + 1;\n    System.out.print(s);\n  }\n}"), "24", "2*3*4가 차례로 곱해져 24가 출력된다."),
            q(10, 9, "네트워크", "concept", ["summary-network-protocol-elements", "velog-summary-03"], display("프로토콜 3요소 중 데이터 전송 속도와 순서 제어를 규정하는 요소를 쓰시오."), "타이밍", "타이밍은 통신 속도 조절과 데이터 전송 순서를 규정한다."),
            q(10, 10, "SQL", "sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 SQL문의 빈칸에 들어갈 키워드를 쓰시오.", description=["테이블 구조를 변경할 때 사용하는 DDL 명령이다."], code_language="sql", code="(     ) TABLE EMP ADD PHONE VARCHAR2(20);"), "ALTER", "ALTER TABLE은 테이블 정의를 변경할 때 사용하는 DDL 명령이다."),
            q(10, 11, "프로그래밍", "code_output", ["programming-python-014", "question-bank-python-dict"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="m = {'x': 1}\nm['y'] = m['x'] + 2\nprint(sorted(m.values()))"), "[1, 3]", "values는 1과 3이고 sorted 결과는 [1, 3]이다."),
            q(10, 12, "소프트웨어공학", "concept", ["velog-summary-04", "summary-sw-coupling-cohesion"], display("결합도 중 한 모듈이 다른 모듈의 내부 자료나 제어 정보를 직접 참조하는 가장 강한 결합도를 쓰시오."), "내용 결합도", "내용 결합도는 다른 모듈 내부를 직접 참조하는 가장 강한 결합도이다."),
            q(10, 13, "프로그래밍", "code_output", ["programming-c-011", "question-bank-c-array"], display("다음 C 코드의 출력값을 작성하시오.", code_language="c", code="#include <stdio.h>\nint main() {\n  char s[] = \"SQL\";\n  printf(\"%c%c\", s[2], s[0]);\n  return 0;\n}"), "LS", "s[2]는 L, s[0]은 S이다."),
            q(10, 14, "통합/연계", "concept", ["velog-summary-05", "summary-integration-eai"], display("EAI 구축 유형 중 각 시스템이 1:1로 직접 연결되어 시스템 수가 늘수록 연결 수가 급증하는 방식을 쓰시오."), "포인트 투 포인트", "포인트 투 포인트 방식은 시스템을 개별적으로 직접 연결한다."),
            q(10, 15, "UI", "choice", ["velog-summary-06", "summary-ui-design-quality"], display("다음 설명에 해당하는 UI 품질 특성을 보기에서 고르시오.", description=["사용자의 실수를 방지하고, 발생한 오류를 쉽게 회복할 수 있도록 하는 특성이다."], choices=["오류성", "유연성", "오류 예방성", "이식성"]), "오류 예방성", "오류 예방성은 사용자 실수를 줄이고 오류 상황에서 회복하기 쉽게 하는 품질 특성이다."),
            q(10, 16, "프로그래밍", "code_output", ["programming-java-012", "question-bank-java-string"], display("다음 Java 코드의 출력값을 작성하시오.", code_language="java", code="public class Main {\n  public static void main(String[] args) {\n    String s = \"2026\";\n    System.out.print(s.charAt(0) + s.substring(2));\n  }\n}"), "226", "charAt(0)은 2이고 substring(2)는 26이므로 226이 출력된다."),
            q(10, 17, "데이터베이스", "concept", ["velog-summary-02", "summary-db-transaction-acid"], display("트랜잭션 수행 결과가 장애 발생 후에도 데이터베이스에 계속 보존되어야 하는 특성을 쓰시오."), "영속성", "영속성은 완료된 트랜잭션 결과가 영구적으로 보존되는 특성이다."),
            q(10, 18, "프로그래밍", "code_output", ["programming-python-015", "question-bank-python-lambda"], display("다음 Python 코드의 출력값을 작성하시오.", code_language="python", code="f = lambda x: x * x - 1\nprint(f(4) - f(2))"), "12", "f(4)=15, f(2)=3이므로 차는 12이다."),
            q(10, 19, "보안", "short_answer", ["velog-summary-09", "summary-security-network-attacks"], display("IP 주소를 속여 다른 시스템으로 가장하는 공격 기법을 쓰시오."), "IP 스푸핑", "IP 스푸핑은 출발지 IP 주소를 위조하여 신뢰된 시스템처럼 가장하는 공격이다."),
            q(10, 20, "SQL", "sql", ["velog-summary-08", "summary-db-sql-tcl"], display("다음 SQL문의 빈칸에 들어갈 명령어를 쓰시오.", description=["사용자 KIM에게 부여한 EMP 테이블 조회 권한을 회수한다."], code_language="sql", code="(      ) SELECT ON EMP FROM KIM;"), "REVOKE", "REVOKE는 부여된 권한을 회수하는 DCL 명령어이다."),
        ]
    )

    return rows


def main() -> None:
    current = json.loads(OUTPUT.read_text(encoding="utf-8"))
    new_questions = build_new_questions()
    if len(new_questions) != 100:
        raise ValueError(f"expected 100 generated questions, got {len(new_questions)}")

    kept = [item for item in current if int(item.get("round", 0)) < 6 or int(item.get("round", 0)) > 10]
    combined = kept + new_questions
    combined.sort(key=lambda item: (int(item["round"]), int(item["number"])))

    ids = [item["id"] for item in combined]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate question ids")

    OUTPUT.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total": len(combined), "added_rounds": [6, 7, 8, 9, 10]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
