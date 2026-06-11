#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path

import pypdf


HEADERS = [
    "縣市別",
    "村里",
    "納稅單位(戶)",
    "綜合所得總額",
    "平均數",
    "中位數",
    "第一分位數",
    "第三分位數",
    "標準差",
    "變異係數",
]


DISTRICTS = [
    "板橋區",
    "三重區",
    "中和區",
    "新莊區",
    "新店區",
    "永和區",
    "汐止區",
    "土城區",
    "蘆洲區",
    "樹林區",
    "淡水區",
    "三峽區",
    "林口區",
    "鶯歌區",
    "五股區",
    "泰山區",
    "瑞芳區",
    "八里區",
    "深坑區",
    "三芝區",
    "金山區",
    "萬里區",
    "貢寮區",
    "石門區",
    "雙溪區",
    "石碇區",
    "坪林區",
    "平溪區",
    "烏來區",
    "其他",
]


DATA_LINE = re.compile(
    r"^(?P<village>\S+)\s+"
    r"(?P<total>\d+)\s+"
    r"(?P<avg>\d+)\s+"
    r"(?P<median>\d+)\s+"
    r"(?P<q1>\d+)\s+"
    r"(?P<q3>\d+)\s+"
    r"(?P<std>\d+\.\d+)\s+"
    r"(?P<cv_tax_dist>\S+)$"
)


def clean_name(value: str) -> str:
    return value.replace("\u3000", "").strip()


def split_tail(tail: str, total: str, avg: str):
    district = ""
    for candidate in DISTRICTS:
        if tail.endswith(candidate):
            district = candidate
            tail = tail[: -len(candidate)]
            break

    expected_tax = 0
    if int(avg) != 0:
        expected_tax = round(int(total) / int(avg))

    candidates = []
    for suffix_len in range(1, min(8, len(tail)) + 1):
        cv = tail[:-suffix_len]
        tax = tail[-suffix_len:]
        if not re.match(r"^\d+\.\d+$", cv) or not tax.isdigit():
            continue
        distance = abs(int(tax) - expected_tax)
        candidates.append((distance, cv, tax))

    if not candidates:
        raise ValueError(f"Cannot parse tail: {tail!r}")

    _, cv, tax = min(candidates, key=lambda item: item[0])
    return cv, tax, district


def extract_rows(pdf_path: Path):
    reader = pypdf.PdfReader(str(pdf_path))
    current_district = ""
    rows = []

    for page in reader.pages:
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("版號", "表165", "縣市別", "納稅單位", "註", "準")):
                continue

            line = line.replace("其\u3000他", "其他").replace("合\u3000計", "合計")
            match = DATA_LINE.match(line)
            if not match:
                continue

            village = clean_name(match.group("village"))
            cv, tax_units, district = split_tail(
                match.group("cv_tax_dist"), match.group("total"), match.group("avg")
            )
            if district:
                current_district = district
            if not current_district:
                raise ValueError(f"Missing district before line: {line!r}")

            rows.append(
                {
                    "縣市別": f"新北市{current_district}",
                    "村里": village,
                    "納稅單位(戶)": tax_units,
                    "綜合所得總額": match.group("total"),
                    "平均數": match.group("avg"),
                    "中位數": match.group("median"),
                    "第一分位數": match.group("q1"),
                    "第三分位數": match.group("q3"),
                    "標準差": match.group("std"),
                    "變異係數": cv,
                }
            )

    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()

    rows = extract_rows(args.pdf)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()
