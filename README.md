# StudyProject

정보처리기사 실기 기출문제와 예상문제를 오프라인에서 풀 수 있도록 정리한 학습 프로젝트입니다.

## 데이터 구성

- `data/processed/past_questions.json`: 수집 및 정리된 기출문제 데이터
- `data/processed/expected_questions.json`: 기출문제, 코드 문제 샘플, 요약본을 참고해 생성한 예상문제 데이터
- `data/processed/velog_summary/velog_summaries.json`: Velog 요약 정리 1~9장 수집 데이터
- `data/processed/consolidated_knowledge_base.json`: 웹 요약, Velog 요약, PDF 요약을 개념 단위로 묶은 통합 지식베이스
- `app-data.js`: 브라우저에서 바로 사용할 수 있도록 빌드된 문제 데이터

## 예상문제 출제 근거 표기

예상문제의 `basis` 필드는 문제 생성에 참고한 내부 근거를 나타냅니다. 이 값은 사용자에게 노출하기 위한 문구가 아니라, 문제 품질 검토와 재분석을 위한 내부 식별자입니다.

표기 규칙:

- `past-YYYY-R-NN`: 특정 기출문제 기반
  - 예: `past-2026-1-08`은 2026년 1회 8번 기출문제를 의미합니다.
- `programming-{language}-NNN`: 수집한 프로그래밍 언어 문제 샘플 기반
  - 예: `programming-python-001`은 Python 문제 샘플 1번을 의미합니다.
- `summary-{category}-{topic}`: 요약본 또는 통합 지식베이스의 개념 단위 기반
  - 예: `summary-network-osi-7-layer`는 요약본의 네트워크/OSI 7계층 개념을 의미합니다.
- `velog-summary-XX`: Velog 요약 정리 특정 장 기반
  - 예: `velog-summary-08`은 Velog 요약 정리 8장, SQL 응용 내용을 의미합니다.
- `question-bank-{language}-{topic}`: 로컬 코드 문제 은행 또는 추가 코드 샘플 기반
  - 예: `question-bank-c-linked-list`는 C 언어 연결 리스트 코드 샘플을 의미합니다.

`summary-...` 값은 실제 파일명이 아니라, 요약본에서 추출한 개념 단위를 사람이 추적하기 쉽게 붙인 내부 참조명입니다. Velog 요약은 장 단위로 `velog-summary-XX`를 사용하고, 세부 개념은 통합 지식베이스에서 함께 검색합니다.

## 예상문제 문제은행

예상문제는 고정 회차로도 사용하고, 여러 회차 문제를 섞어 랜덤 1회차를 구성할 수 있도록 문제은행 형태로 관리합니다.

예상문제 주요 메타데이터:

- `category`: 데이터베이스, SQL, 보안, 프로그래밍 등 문제 영역
- `question_type`: 랜덤 회차 구성 시 문제 유형 비율을 맞추기 위한 분류
  - `code_output`: 프로그래밍 코드 출력/분석형
  - `concept`: 개념 설명/빈칸형
  - `short_answer`: 단답형
  - `choice`: 보기 선택형
  - `sql`: SQL 작성/결과형
  - `table_sql`: 표 기반 SQL/결과형

랜덤 회차는 앱에서 문제은행을 섞어 20문항으로 구성합니다. 기본 목표 비율은 코드 7문항, 개념/단답 8문항, SQL/표 3문항, 보기형 2문항입니다.

## GitHub Pages 배포

모바일에서는 ZIP을 직접 여는 것보다 GitHub Pages로 접속하는 방식을 권장합니다.

저장소를 GitHub에 올린 뒤 `Settings > Pages`에서 Source를 `GitHub Actions`로 설정하면, `Deploy GitHub Pages` 워크플로가 `dist/studyproject-lite` 배포판을 빌드해 Pages에 배포합니다.

문제를 추가하거나 수정한 뒤 push하면 다음 파일들이 기준이 되어 자동 배포됩니다.

- `data/processed/past_questions.json`
- `data/processed/expected_questions.json`
- `data/processed/past_images/**`
- `index.html`
- `styles.css`
- `app.js`
- `tools/build_app_data.py`
- `tools/build_distribution.py`

로컬에서 배포판을 직접 갱신하려면 다음 명령을 실행합니다.

```powershell
python .\tools\build_app_data.py
python .\tools\build_distribution.py
```
