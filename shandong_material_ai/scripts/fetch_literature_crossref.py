from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MATERIAL_FILE = DATA_DIR / "material_candidates.csv"
OUTPUT_FILE = DATA_DIR / "literature_evidence.csv"


SEARCH_TERMS = {
    "TiN": "TiN coating corrosion NaCl",
    "CrN": "CrN coating corrosion NaCl",
    "AlN": "AlN coating corrosion coating",
    "TiAlN": "TiAlN coating corrosion",
    "Al2O3": "Al2O3 coating corrosion protection",
    "Cr2O3": "Cr2O3 coating corrosion protection",
    "TiO2": "TiO2 coating corrosion protection",
    "ZrO2": "ZrO2 coating corrosion protection",
    "SiO2": "SiO2 coating corrosion protection",
    "SiC": "SiC coating corrosion wear",
    "TiC": "TiC coating corrosion wear",
    "WC": "WC coating corrosion wear",
    "ZrN": "ZrN coating corrosion",
    "HfN": "HfN coating corrosion",
    "AlCrN": "AlCrN coating corrosion",
    "CrAlN": "CrAlN coating corrosion",
}


def _plain_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item)
    if value is None:
        return ""
    return str(value)


def _year(item: dict[str, Any]) -> str:
    for key in ["published-print", "published-online", "published"]:
        parts = item.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            return str(parts[0][0])
    return ""


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def fetch_crossref_for_material(formula: str, query: str, rows: int = 5) -> list[dict[str, Any]]:
    response = None
    for attempt in range(3):
        response = requests.get(
            "https://api.crossref.org/works",
            params={"query.bibliographic": query, "rows": rows, "select": "DOI,title,container-title,published-print,published-online,published,URL,abstract,type"},
            headers={"User-Agent": "shandong-material-ai-prototype/0.1 (mailto:example@example.com)"},
            timeout=30,
        )
        if response.status_code != 429:
            break
        time.sleep(4 + attempt * 4)
    response.raise_for_status()
    items = response.json().get("message", {}).get("items", [])

    records = []
    for item in items:
        title = _clean(_plain_text(item.get("title")))
        if not is_relevant_title(formula, title):
            continue
        journal = _clean(_plain_text(item.get("container-title")))
        abstract = _clean(item.get("abstract", ""))
        doi = str(item.get("DOI", "")).strip()
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        records.append(
            {
                "formula": formula,
                "query": query,
                "title": title,
                "journal": journal,
                "year": _year(item),
                "doi": doi,
                "url": url,
                "abstract_snippet": abstract[:420],
                "evidence_type": "Crossref 文献元数据",
                "relevance_note": "题名命中材料化学式或材料缩写，仍需人工复核实验条件",
                "data_status": "文献线索，需人工复核题名、摘要、全文和实验条件",
            }
        )
    return records


def is_relevant_title(formula: str, title: str) -> bool:
    normalized_title = re.sub(r"[^a-z0-9]+", "", title.lower())
    normalized_formula = re.sub(r"[^a-z0-9]+", "", formula.lower())
    lowered = title.lower().strip()
    if not title or len(title) < 30:
        return False
    if lowered.startswith("review for") or "v2/review" in lowered:
        return False
    # TiN / AlN 这类短缩写容易与英文单词 tin 等混淆，必须大小写形式明确命中。
    if formula in {"TiN", "CrN", "AlN", "ZrN", "HfN"}:
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(formula)}(?![A-Za-z0-9])", title) is not None
    if normalized_formula and normalized_formula in normalized_title:
        return True
    aliases = {
        "Al2O3": ["alumina"],
        "Cr2O3": ["chromia", "chromiumoxide", "chromiumoxidecoating"],
        "TiO2": ["titania", "titaniumdioxide"],
        "ZrO2": ["zirconia", "zirconiumdioxide"],
        "SiO2": ["silica", "silicondioxide"],
        "SiC": ["siliconcarbide"],
        "WC": ["tungstencarbide", "wc"],
    }
    return any(alias in normalized_title for alias in aliases.get(formula, []))


def fetch_all() -> pd.DataFrame:
    materials = pd.read_csv(MATERIAL_FILE)
    formulas = materials["formula"].dropna().drop_duplicates().tolist()
    records: list[dict[str, Any]] = []

    for formula in formulas:
        query = SEARCH_TERMS.get(formula, f"{formula} coating corrosion")
        try:
            rows = fetch_crossref_for_material(formula, query, rows=4)
        except Exception as exc:
            print(f"[WARN] {formula}: {exc}")
            rows = []
        print(f"[OK] {formula}: {len(rows)} literature candidates")
        records.extend(rows)

    df = pd.DataFrame(records)
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["formula", "doi", "title"]).reset_index(drop=True)
    df.insert(0, "evidence_id", [f"LIT-{i + 1:04d}" for i in range(len(df))])
    return df


def main() -> None:
    df = fetch_all()
    if df.empty:
        if OUTPUT_FILE.exists():
            existing = pd.read_csv(OUTPUT_FILE)
            print(f"No new literature metadata fetched. Kept existing {OUTPUT_FILE} with {len(existing)} records.")
        else:
            print("No literature metadata fetched.")
        return
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Saved {OUTPUT_FILE} with {len(df)} records")


if __name__ == "__main__":
    main()
