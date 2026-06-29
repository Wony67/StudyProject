from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path.cwd()
DIST_ROOT = ROOT / "dist"
PACKAGE_DIR = DIST_ROOT / "studyproject-lite"
ZIP_PATH = DIST_ROOT / "studyproject-lite.zip"

APP_FILES = [
    "index.html",
    "styles.css",
    "app.js",
    "app-data.js",
]


def clean_dist() -> None:
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)


def copy_app_files() -> None:
    for name in APP_FILES:
        shutil.copy2(ROOT / name, PACKAGE_DIR / name)
    (PACKAGE_DIR / ".nojekyll").write_text("", encoding="utf-8")


def load_questions(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_image_paths() -> list[Path]:
    paths: set[Path] = set()
    for source in [
        ROOT / "data" / "processed" / "past_questions.json",
        ROOT / "data" / "processed" / "expected_questions.json",
    ]:
        if not source.exists():
            continue
        for question in load_questions(source):
            for ref in question.get("image_refs") or []:
                if isinstance(ref, dict):
                    raw_path = ref.get("local_path") or ref.get("path") or ""
                else:
                    raw_path = str(ref)
                if not raw_path:
                    continue
                image_path = ROOT / str(raw_path).replace("\\", "/")
                if image_path.exists() and image_path.is_file():
                    paths.add(image_path)
    return sorted(paths)


def copy_images(image_paths: list[Path]) -> None:
    for image_path in image_paths:
        relative = image_path.relative_to(ROOT)
        target = PACKAGE_DIR / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, target)


def write_readme(image_count: int) -> None:
    readme = f"""# StudyProject Lite

정보처리기사 실기 기출문제와 기출 예상문제를 오프라인에서 풀 수 있는 최소 배포판입니다.

## 실행 방법

`index.html`을 브라우저로 열면 됩니다.

모바일에서는 이 폴더 전체를 기기에 복사한 뒤 `index.html`을 열어 사용합니다.

## 포함 파일

- `index.html`
- `styles.css`
- `app.js`
- `app-data.js`
- 문제 풀이에 필요한 이미지 {image_count}개

## 제외한 파일

원본 PDF, 요약본 원문, 수집 원본 HTML, 수집/분석 도구, 중간 JSON 데이터는 배포판에서 제외했습니다.
"""
    (PACKAGE_DIR / "README.md").write_text(readme, encoding="utf-8")


def write_manifest(image_paths: list[Path]) -> None:
    manifest = {
        "name": "studyproject-lite",
        "app_files": APP_FILES,
        "image_count": len(image_paths),
        "images": [str(path.relative_to(ROOT)).replace("\\", "/") for path in image_paths],
        "excluded": [
            "data/pdf",
            "data/raw",
            "data/processed/pdf",
            "data/processed/velog_summary",
            "data/processed/web_summary",
            "data/question",
            "tools",
        ],
    }
    (PACKAGE_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def make_zip() -> None:
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(DIST_ROOT))


def directory_size(path: Path) -> int:
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())


def main() -> None:
    clean_dist()
    copy_app_files()
    image_paths = collect_image_paths()
    copy_images(image_paths)
    write_readme(len(image_paths))
    write_manifest(image_paths)
    make_zip()

    result = {
        "package_dir": str(PACKAGE_DIR),
        "zip": str(ZIP_PATH),
        "images": len(image_paths),
        "package_bytes": directory_size(PACKAGE_DIR),
        "zip_bytes": ZIP_PATH.stat().st_size,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
