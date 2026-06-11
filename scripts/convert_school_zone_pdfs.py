#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path

import pandas as pd
import pypdf

try:
    import pdfplumber
except ImportError:  # pragma: no cover - fallback keeps the script usable.
    pdfplumber = None


ROOT = Path(__file__).resolve().parents[1]
INCOME_DIR = ROOT / "school"
HEADERS_RAW = ["學年度", "學制", "行政區", "學校名稱", "基本學區原文", "自由學區原文", "備註原文", "頁碼"]
HEADERS_EXPANDED = ["學年度", "學制", "行政區", "學校名稱", "學區類型", "村里", "鄰里備註", "資料來源"]


def load_income_villages():
    latest = sorted(INCOME_DIR.glob("*_165-F.csv"))[-1]
    df = pd.read_csv(latest, encoding="utf-8-sig")
    df.columns = [str(col).replace("\ufeff", "").replace("鄉鎮市區", "縣市別") for col in df.columns]
    df["行政區"] = df["縣市別"].astype(str).str.replace("新北市", "", regex=False).str.strip()
    df["村里"] = df["村里"].astype(str).str.replace("\u3000", "", regex=False).str.strip()
    df = df[~df["村里"].isin(["合計", "其他"])]
    return {
        district: sorted(group["村里"].unique(), key=len, reverse=True)
        for district, group in df.groupby("行政區")
    }


def page_items(page):
    items = []

    def visitor(text, cm, tm, font_dict, font_size):
        value = text.strip()
        if value:
            items.append({"x": float(tm[4]), "y": float(tm[5]), "text": value})

    page.extract_text(visitor_text=visitor)
    return items


def layout_text(page):
    return page.extract_text(extraction_mode="layout") or ""


def find_district(text):
    match = re.search(r"([^\s\d]{1,4}區)\s*115\s*學年度", text)
    if match:
        return match.group(1)
    match = re.search(r"([^\s\d]{1,4}區)115\s*學年度", text)
    if match:
        return match.group(1)
    return ""


def columns_for(level):
    if level == "國小":
        return {
            "school_max": 112,
            "basic_min": 112,
            "basic_max": 232,
            "free_min": 232,
            "free_max": 338,
            "note_min": 338,
        }
    return {
        "school_max": 95,
        "basic_min": 95,
        "basic_max": 265,
        "free_min": 265,
        "free_max": 500,
        "note_min": 500,
    }


def join_text(parts):
    text = "".join(part["text"] for part in sorted(parts, key=lambda item: (-item["y"], item["x"])))
    text = re.sub(r"\s+", "", text)
    text = text.replace("（", "(").replace("）", ")").replace("－", "-").replace("—", "-")
    return text.strip()


def school_candidates(items, level):
    cfg = columns_for(level)
    names = []
    for item in items:
        text = item["text"].strip()
        if item["x"] >= cfg["school_max"]:
            continue
        if "學校名稱" in text or "第" in text:
            continue
        if level == "國小" and "國小" in text:
            names.append(item)
        elif level == "國中" and ("國中" in text or "高中國中部" in text):
            names.append(item)
    names.sort(key=lambda item: -item["y"])
    return names


def extract_raw_rows(pdf_path, level, academic_year):
    rows = []
    reader = pypdf.PdfReader(str(pdf_path))
    for page_no, page in enumerate(reader.pages, start=1):
        text = layout_text(page)
        district = find_district(text)
        if not district:
            continue

        items = page_items(page)
        schools = school_candidates(items, level)
        if not schools:
            continue

        cfg = columns_for(level)
        for index, school in enumerate(schools):
            upper = 720 if level == "國小" else 785
            if index > 0:
                upper = (schools[index - 1]["y"] + school["y"]) / 2
            lower = 45
            if index + 1 < len(schools):
                lower = (school["y"] + schools[index + 1]["y"]) / 2

            in_band = [item for item in items if lower <= item["y"] <= upper]
            basic = [
                item
                for item in in_band
                if cfg["basic_min"] <= item["x"] < cfg["basic_max"] and "基本學區" not in item["text"]
            ]
            free = [
                item
                for item in in_band
                if cfg["free_min"] <= item["x"] < cfg["free_max"] and "自由學區" not in item["text"]
            ]
            note = [
                item
                for item in in_band
                if item["x"] >= cfg["note_min"] and "備註" not in item["text"]
            ]
            rows.append(
                {
                    "學年度": academic_year,
                    "學制": level,
                    "行政區": district,
                    "學校名稱": school["text"].strip(),
                    "基本學區原文": join_text(basic),
                    "自由學區原文": join_text(free),
                    "備註原文": join_text(note),
                    "頁碼": page_no,
                }
            )
    return rows


def clean_zone_text(text):
    text = str(text)
    text = text.replace("\n", "")
    text = text.replace("等里", "里")
    text = text.replace("各里", "")
    text = re.sub(r"[一二三四五六七八九十]+、", "、", text)
    text = re.sub(r"【[^】]*】", "", text)
    return text


def context_note(text, village):
    compact = clean_zone_text(text)
    stem = village[:-1] if village.endswith("里") else village
    pattern = rf"({re.escape(village)}|{re.escape(stem)})(?P<note>\([^)]*鄰[^)]*\))?"
    match = re.search(pattern, compact)
    if not match:
        return ""
    notes = []
    inline_note = match.group("note")
    if inline_note:
        notes.append(inline_note)
    window = compact[match.start() : match.end() + 8]
    if "除" in window or (inline_note and "除" in inline_note):
        notes.append("含除外條件，依原文整里估算")
    if "自由學區" in text:
        notes.append("自由學區")
    if notes:
        return "；".join(dict.fromkeys(notes))
    return ""


def find_villages(text, district, villages_by_district):
    compact = clean_zone_text(text)
    villages = villages_by_district.get(district, [])
    hits = []
    occupied = []
    for village in villages:
        stem = village[:-1] if village.endswith("里") else village
        patterns = [re.escape(village)]
        if stem:
            patterns.append(rf"(?<![一-龥]){re.escape(stem)}(?=(、|,|，|\(|里|$))")
        found = False
        for pattern in patterns:
            for match in re.finditer(pattern, compact):
                span = match.span()
                if any(not (span[1] <= old[0] or span[0] >= old[1]) for old in occupied):
                    continue
                occupied.append(span)
                found = True
                break
            if found:
                break
        if found:
            hits.append(village)
    return sorted(set(hits), key=lambda value: compact.find(value if value in compact else value[:-1]))


def expand_rows(raw_rows, pdf_path, villages_by_district):
    expanded = []
    source = str(pdf_path)
    for row in raw_rows:
        for zone_type, field in [("基本學區", "基本學區原文"), ("自由學區", "自由學區原文")]:
            text = row[field]
            for village in find_villages(text, row["行政區"], villages_by_district):
                expanded.append(
                    {
                        "學年度": row["學年度"],
                        "學制": row["學制"],
                        "行政區": row["行政區"],
                        "學校名稱": row["學校名稱"],
                        "學區類型": zone_type,
                        "村里": village,
                        "鄰里備註": context_note(text, village),
                        "資料來源": source,
                    }
                )
    return expanded


def write_csv(path, rows, headers):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def normalize_cell(value):
    if value is None:
        return ""
    value = str(value).replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n+", "\n", value)
    return value.strip()


def normalize_school_name(value):
    value = normalize_cell(value)
    value = value.replace("\n", "")
    value = re.sub(r"\s+", "", value)
    value = value.replace("(國中部)", "國中部").replace("（國中部）", "國中部")
    return value.strip()


def normalize_table_text(value):
    value = normalize_cell(value)
    value = value.replace("－", "-").replace("（", "(").replace("）", ")")
    value = re.sub(r"[ \t]+", "", value)
    return value.strip()


def is_header_or_noise_school(name, level):
    if not name:
        return False
    noise = ["學校名稱", "學年度", "學區一覽表", "調整備註", "附件"]
    if any(token in name for token in noise):
        return True
    if level == "國小":
        return "國小" not in name
    return not ("國中" in name or "高中國中部" in name)


def extract_raw_rows_with_pdfplumber(pdf_path, level, academic_year):
    if pdfplumber is None:
        return None

    rows = []
    last_row = None
    current_district = ""
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
            found_district = find_district(page_text)
            if found_district:
                current_district = found_district
            district = current_district
            if not district:
                continue

            tables = page.extract_tables()
            for table in tables:
                for raw in table:
                    if not raw:
                        continue
                    cells = [normalize_table_text(cell) for cell in raw]
                    if not any(cells):
                        continue

                    school = normalize_school_name(cells[0] if len(cells) > 0 else "")
                    if school and is_header_or_noise_school(school, level):
                        continue

                    basic = cells[1] if len(cells) > 1 else ""
                    free = cells[2] if len(cells) > 2 else ""
                    note = "\n".join(cell for cell in cells[3:] if cell)
                    if school:
                        row = {
                            "學年度": academic_year,
                            "學制": level,
                            "行政區": district,
                            "學校名稱": school,
                            "基本學區原文": basic,
                            "自由學區原文": free,
                            "備註原文": note,
                            "頁碼": page_no,
                        }
                        rows.append(row)
                        last_row = row
                    elif last_row and last_row["行政區"] == district:
                        if basic:
                            last_row["基本學區原文"] = "\n".join(
                                part for part in [last_row["基本學區原文"], basic] if part
                            )
                        if free:
                            last_row["自由學區原文"] = "\n".join(
                                part for part in [last_row["自由學區原文"], free] if part
                            )
                        if note:
                            last_row["備註原文"] = "\n".join(
                                part for part in [last_row["備註原文"], note] if part
                            )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--elementary", type=Path, required=True)
    parser.add_argument("--junior-high", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=INCOME_DIR)
    parser.add_argument("--academic-year", default="115")
    args = parser.parse_args()

    villages_by_district = load_income_villages()
    elementary_raw = extract_raw_rows_with_pdfplumber(args.elementary, "國小", args.academic_year)
    if elementary_raw is None:
        elementary_raw = extract_raw_rows(args.elementary, "國小", args.academic_year)
    junior_raw = extract_raw_rows_with_pdfplumber(args.junior_high, "國中", args.academic_year)
    if junior_raw is None:
        junior_raw = extract_raw_rows(args.junior_high, "國中", args.academic_year)
    expanded = expand_rows(elementary_raw, args.elementary, villages_by_district)
    expanded += expand_rows(junior_raw, args.junior_high, villages_by_district)

    write_csv(args.out_dir / "115_elementary_zones_raw.csv", elementary_raw, HEADERS_RAW)
    write_csv(args.out_dir / "115_junior_high_zones_raw.csv", junior_raw, HEADERS_RAW)
    write_csv(args.out_dir / "115_school_zones_extracted.csv", expanded, HEADERS_EXPANDED)

    print(f"Elementary raw rows: {len(elementary_raw)}")
    print(f"Junior high raw rows: {len(junior_raw)}")
    print(f"Expanded village rows: {len(expanded)}")


if __name__ == "__main__":
    main()
