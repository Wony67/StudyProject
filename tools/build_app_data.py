from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path.cwd()
    past_source = root / "data" / "processed" / "past_questions.json"
    expected_source = root / "data" / "processed" / "expected_questions.json"
    output = root / "app-data.js"
    past_questions = json.loads(past_source.read_text(encoding="utf-8"))
    expected_questions = json.loads(expected_source.read_text(encoding="utf-8")) if expected_source.exists() else []
    payload = (
        "window.PAST_QUESTIONS = "
        + json.dumps(past_questions, ensure_ascii=False, separators=(",", ":"))
        + ";\nwindow.EXPECTED_QUESTIONS = "
        + json.dumps(expected_questions, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )
    output.write_text(payload, encoding="utf-8")
    print(f"wrote {output} ({len(past_questions)} past, {len(expected_questions)} expected questions)")


if __name__ == "__main__":
    main()
