from __future__ import annotations

import argparse
import hashlib
import json
import re
import zlib
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import pypdfium2 as pdfium


OBJECT_STREAM_RE = re.compile(rb"(\d+)\s+(\d+)\s+obj(.*?)stream\r?\n", re.S)
LENGTH_RE = re.compile(rb"/Length\s+(\d+)")
ENCRYPT_REF_RE = re.compile(rb"/Encrypt\s+(\d+)\s+(\d+)\s+R")
ID_RE = re.compile(rb"/ID\s*\[\s*<([0-9A-Fa-f]+)>")
PASSWORD_PADDING = bytes(
    [
        0x28,
        0xBF,
        0x4E,
        0x5E,
        0x4E,
        0x75,
        0x8A,
        0x41,
        0x64,
        0x00,
        0x4E,
        0x56,
        0xFF,
        0xFA,
        0x01,
        0x08,
        0x2E,
        0x2E,
        0x00,
        0xB6,
        0xD0,
        0x68,
        0x3E,
        0x80,
        0x2F,
        0x0C,
        0xA9,
        0xFE,
        0x64,
        0x53,
        0x69,
        0x7A,
    ]
)
TO_UNICODE_REF_RE = re.compile(rb"/ToUnicode\s+(\d+)\s+0\s+R")
HEX_RE = re.compile(r"<([0-9A-Fa-f\s]+)>")
LITERAL_RE = re.compile(r"\((?:\\.|[^\\()])*\)")
ACTUAL_TEXT_HEX_RE = re.compile(r"/ActualText\s*<([0-9A-Fa-f\s]+)>")
ACTUAL_TEXT_LITERAL_RE = re.compile(r"/ActualText\s*(\((?:\\.|[^\\()])*\))")


@dataclass
class PdfStudySource:
    source_file: str
    output_text: str
    output_terms: str
    chars: int
    lines: int
    top_terms: list[tuple[str, int]]


def decompress_streams(pdf_bytes: bytes) -> dict[int, bytes]:
    encryption_key = get_encryption_key(pdf_bytes)
    streams: dict[int, bytes] = {}
    for match in OBJECT_STREAM_RE.finditer(pdf_bytes):
        obj_id = int(match.group(1))
        gen_id = int(match.group(2))
        header = match.group(3)
        length_match = LENGTH_RE.search(header)
        if not length_match:
            continue
        length = int(length_match.group(1))
        start = match.end()
        payload = pdf_bytes[start : start + length]
        if encryption_key:
            payload = rc4(object_key(encryption_key, obj_id, gen_id), payload)
        if b"/FlateDecode" in header:
            try:
                streams[obj_id] = zlib.decompress(payload)
            except zlib.error:
                continue
        else:
            streams[obj_id] = payload
    return streams


def read_object(pdf_bytes: bytes, obj_id: int, gen_id: int = 0) -> bytes:
    pattern = (str(obj_id) + r"\s+" + str(gen_id) + r"\s+obj(.*?)endobj").encode()
    match = re.search(pattern, pdf_bytes, re.S)
    return match.group(1) if match else b""


def parse_pdf_literal_bytes(data: bytes, start: int) -> tuple[bytes, int]:
    if data[start : start + 1] != b"(":
        raise ValueError("literal must start with '('")
    out = bytearray()
    depth = 1
    index = start + 1
    while index < len(data) and depth:
        char = data[index]
        if char == 0x5C:
            index += 1
            if index >= len(data):
                break
            esc = data[index]
            if esc in b"nrtbf":
                out.extend({ord("n"): b"\n", ord("r"): b"\r", ord("t"): b"\t", ord("b"): b"\b", ord("f"): b"\f"}[esc])
            elif esc in b"()\\":
                out.append(esc)
            elif 48 <= esc <= 55:
                octal = bytes([esc])
                for _ in range(2):
                    if index + 1 < len(data) and 48 <= data[index + 1] <= 55:
                        index += 1
                        octal += bytes([data[index]])
                out.append(int(octal, 8))
            else:
                out.append(esc)
        elif char == 0x28:
            depth += 1
            out.append(char)
        elif char == 0x29:
            depth -= 1
            if depth:
                out.append(char)
        else:
            out.append(char)
        index += 1
    return bytes(out), index


def find_literal_after(data: bytes, marker: bytes) -> bytes:
    pos = data.find(marker)
    if pos < 0:
        return b""
    start = data.find(b"(", pos)
    if start < 0:
        return b""
    value, _ = parse_pdf_literal_bytes(data, start)
    return value


def rc4(key: bytes, data: bytes) -> bytes:
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) & 0xFF
        s[i], s[j] = s[j], s[i]
    out = bytearray()
    i = j = 0
    for byte in data:
        i = (i + 1) & 0xFF
        j = (j + s[i]) & 0xFF
        s[i], s[j] = s[j], s[i]
        out.append(byte ^ s[(s[i] + s[j]) & 0xFF])
    return bytes(out)


def get_encryption_key(pdf_bytes: bytes, password: bytes = b"") -> bytes | None:
    ref = ENCRYPT_REF_RE.search(pdf_bytes)
    id_match = ID_RE.search(pdf_bytes)
    if not ref or not id_match:
        return None
    enc = read_object(pdf_bytes, int(ref.group(1)), int(ref.group(2)))
    revision = int(re.search(rb"/R\s+(\d+)", enc).group(1))
    key_bits = int(re.search(rb"/Length\s+(\d+)", enc).group(1))
    permissions = int(re.search(rb"/P\s+(-?\d+)", enc).group(1))
    owner = find_literal_after(enc, b"/O")
    user = find_literal_after(enc, b"/U")
    file_id = bytes.fromhex(id_match.group(1).decode("ascii"))
    padded = (password + PASSWORD_PADDING)[:32]
    digest = hashlib.md5(padded + owner + permissions.to_bytes(4, "little", signed=True) + file_id).digest()
    key_len = key_bits // 8
    if revision >= 3:
        for _ in range(50):
            digest = hashlib.md5(digest[:key_len]).digest()
    key = digest[:key_len]
    if revision >= 3:
        check = hashlib.md5(PASSWORD_PADDING + file_id).digest()
        encrypted = rc4(key, check)
        for i in range(1, 20):
            encrypted = rc4(bytes(byte ^ i for byte in key), encrypted)
        if encrypted[:16] != user[:16]:
            print("warning: empty PDF password did not verify; extraction may fail")
    return key


def object_key(encryption_key: bytes, obj_id: int, gen_id: int) -> bytes:
    material = (
        encryption_key
        + obj_id.to_bytes(3, "little")
        + gen_id.to_bytes(2, "little")
    )
    return hashlib.md5(material).digest()[: min(len(encryption_key) + 5, 16)]


def parse_cmaps(streams: dict[int, bytes]) -> dict[int, str]:
    cmap: dict[int, str] = {}
    for stream in streams.values():
        text = stream.decode("latin-1", errors="ignore")
        if "beginbfchar" not in text and "beginbfrange" not in text:
            continue

        bfchar_blocks = re.findall(r"beginbfchar(.*?)endbfchar", text, re.S)
        for block in bfchar_blocks:
            for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
                if len(dst) % 4 == 0:
                    try:
                        cmap[int(src, 16)] = bytes.fromhex(dst).decode("utf-16-be")
                    except UnicodeDecodeError:
                        pass

        range_re = re.compile(
            r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(?:<([0-9A-Fa-f]+)>|\[(.*?)\])",
            re.S,
        )
        bfrange_blocks = re.findall(r"beginbfrange(.*?)endbfrange", text, re.S)
        for block in bfrange_blocks:
            for start_hex, end_hex, dst_hex, dst_list in range_re.findall(block):
                start = int(start_hex, 16)
                end = int(end_hex, 16)
                if dst_hex:
                    dst_start = int(dst_hex, 16)
                    for offset, code in enumerate(range(start, end + 1)):
                        try:
                            cmap[code] = (dst_start + offset).to_bytes(2, "big").decode("utf-16-be")
                        except UnicodeDecodeError:
                            continue
                elif dst_list:
                    items = re.findall(r"<([0-9A-Fa-f]+)>", dst_list)
                    for code, dst in zip(range(start, end + 1), items):
                        try:
                            cmap[code] = bytes.fromhex(dst).decode("utf-16-be")
                        except UnicodeDecodeError:
                            continue
    return cmap


def decode_pdf_literal(token: str) -> str:
    raw = token[1:-1]
    raw = raw.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
    raw = raw.replace(r"\n", "\n").replace(r"\r", "\n").replace(r"\t", "\t")
    return raw


def decode_hex(hex_text: str, cmap: dict[int, str]) -> str:
    clean = re.sub(r"\s+", "", hex_text)
    if len(clean) % 2:
        clean += "0"
    data = bytes.fromhex(clean)
    pieces: list[str] = []
    if cmap and len(data) >= 2:
        for index in range(0, len(data), 2):
            code = int.from_bytes(data[index : index + 2], "big")
            pieces.append(cmap.get(code, ""))
        decoded = "".join(pieces)
        if decoded:
            return decoded
    for encoding in ("utf-16-be", "utf-8", "cp949", "latin-1"):
        try:
            decoded = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        if decoded.strip():
            return decoded
    return ""


def extract_text_from_stream(stream: bytes, cmap: dict[int, str]) -> str:
    text = stream.decode("latin-1", errors="ignore")
    if "beginbfchar" in text or "beginbfrange" in text:
        return ""
    actual_chunks: list[str] = []
    for match in ACTUAL_TEXT_HEX_RE.finditer(text):
        decoded = decode_hex(match.group(1), {})
        if decoded.startswith("\ufeff"):
            decoded = decoded[1:]
        if decoded.strip():
            actual_chunks.append(decoded)
    for match in ACTUAL_TEXT_LITERAL_RE.finditer(text):
        decoded = decode_pdf_literal(match.group(1))
        if decoded.strip():
            actual_chunks.append(decoded)
    if actual_chunks:
        return "\n".join(actual_chunks)

    chunks: list[tuple[int, str]] = []
    for match in HEX_RE.finditer(text):
        decoded = decode_hex(match.group(1), cmap)
        if decoded.strip():
            chunks.append((match.start(), decoded))
    for match in LITERAL_RE.finditer(text):
        decoded = decode_pdf_literal(match.group(0))
        if decoded.strip():
            chunks.append((match.start(), decoded))
    chunks.sort(key=lambda item: item[0])
    return "\n".join(chunk for _, chunk in chunks)


def normalize_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = text.replace("\x07", "")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("CIDInit"):
            continue
        if line in {"초", "치기"}:
            continue
        line = re.sub(r"^(\d{3})\s+치기$", r"\1", line)
        line = re.sub(r"^(.+?)\s+\d+\s+치기$", r"\1", line)
        line = re.sub(r"^초\s+", "", line)
        lines.append(line)
    return "\n".join(lines)


def term_stats(text: str) -> list[tuple[str, int]]:
    words = re.findall(r"[가-힣A-Za-z0-9+#./-]{2,}", text)
    stop = {"정보처리기사", "필기", "핵심", "요약", "문제", "다음", "대한", "있다", "한다", "치기"}
    counter = Counter(word for word in words if word not in stop)
    return counter.most_common(100)


def extract(pdf_path: Path, output_dir: Path) -> PdfStudySource:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_text = extract_with_pdfium(pdf_path)
    if not raw_text.strip():
        pdf_bytes = pdf_path.read_bytes()
        streams = decompress_streams(pdf_bytes)
        cmap = parse_cmaps(streams)
        raw_text = "\n".join(extract_text_from_stream(stream, cmap) for stream in streams.values())
    text = normalize_text(raw_text)
    terms = term_stats(text)

    stem = pdf_path.stem
    text_path = output_dir / f"{stem}.txt"
    terms_path = output_dir / f"{stem}_terms.json"
    text_path.write_text(text, encoding="utf-8")
    terms_path.write_text(json.dumps(terms, ensure_ascii=False, indent=2), encoding="utf-8")

    return PdfStudySource(
        source_file=str(pdf_path),
        output_text=str(text_path),
        output_terms=str(terms_path),
        chars=len(text),
        lines=text.count("\n") + 1 if text else 0,
        top_terms=terms[:20],
    )


def extract_with_pdfium(pdf_path: Path) -> str:
    pdf = pdfium.PdfDocument(str(pdf_path))
    pages: list[str] = []
    for index in range(len(pdf)):
        page = pdf[index]
        textpage = page.get_textpage()
        text = textpage.get_text_range()
        if text.strip():
            pages.append(f"\n\n## Page {index + 1}\n{text}")
    return "\n".join(pages)


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF 텍스트를 추출해 학습 자료로 저장합니다.")
    parser.add_argument("pdf")
    parser.add_argument("--output-dir", default="data/processed/pdf")
    args = parser.parse_args()

    source = extract(Path(args.pdf), Path(args.output_dir))
    print(json.dumps(asdict(source), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
