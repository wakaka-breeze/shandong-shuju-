from __future__ import annotations

import argparse
import os
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

from fetch_literature_crossref import SEARCH_TERMS, fetch_crossref_for_material


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MATERIAL_FILE = DATA_DIR / "material_candidates.csv"
BASE_LITERATURE_FILE = DATA_DIR / "literature_evidence.csv"
MULTI_LITERATURE_FILE = DATA_DIR / "literature_evidence_multi_source.csv"
MATERIAL_DB_FILE = DATA_DIR / "material_database_external_candidates.csv"
AUDIT_FILE = DATA_DIR / "material_data_integration_audit.csv"
SOURCE_STATUS_FILE = DATA_DIR / "external_source_status.csv"

USER_AGENT = "shandong-material-ai-prototype/0.2 (mailto:example@example.com)"
LITERATURE_SOURCES = ("crossref", "crossref-sci", "crossref-topic", "openalex", "semantic-scholar", "europe-pmc")
MATERIAL_DATABASE_SOURCES = ("oqmd", "aflow")
FORMULA_ALIASES = {
    "TiN": ["titanium nitride", "TiN"],
    "CrN": ["chromium nitride", "CrN"],
    "AlN": ["aluminum nitride", "aluminium nitride", "AlN"],
    "TiAlN": ["TiAlN", "Ti-Al-N", "titanium aluminum nitride", "titanium aluminium nitride"],
    "Al2O3": ["alumina", "aluminium oxide", "aluminum oxide", "Al2O3"],
    "Cr2O3": ["chromia", "chromium oxide", "Cr2O3"],
    "TiO2": ["titania", "titanium dioxide", "TiO2"],
    "ZrO2": ["zirconia", "zirconium dioxide", "ZrO2"],
    "SiO2": ["silica", "silicon dioxide", "SiO2"],
    "SiC": ["silicon carbide", "SiC"],
    "TiC": ["titanium carbide", "TiC"],
    "WC": ["tungsten carbide", "WC"],
    "ZrN": ["zirconium nitride", "ZrN"],
    "HfN": ["hafnium nitride", "HfN"],
    "AlCrN": ["AlCrN", "Al-Cr-N", "aluminum chromium nitride", "aluminium chromium nitride"],
    "CrAlN": ["CrAlN", "Cr-Al-N", "chromium aluminum nitride", "chromium aluminium nitride"],
}
TOPIC_DISCOVERY_QUERIES = [
    {
        "topic_label": "拓展主题：有机防腐涂层",
        "material_system_hint": "有机防腐涂层",
        "queries": [
            "organic anticorrosion coating marine steel corrosion",
            "epoxy coating marine corrosion protection steel",
            "zinc rich epoxy coating marine corrosion",
        ],
    },
    {
        "topic_label": "拓展主题：金属与合金镀层",
        "material_system_hint": "金属与合金镀层",
        "queries": [
            "metallic coating marine corrosion protection steel",
            "zinc aluminum alloy coating marine corrosion",
            "electroless nickel coating corrosion wear marine",
        ],
    },
    {
        "topic_label": "拓展主题：热喷涂涂层",
        "material_system_hint": "热喷涂涂层",
        "queries": [
            "thermal spray coating marine corrosion protection",
            "HVOF coating corrosion wear seawater",
            "arc sprayed aluminum coating marine corrosion",
        ],
    },
    {
        "topic_label": "拓展主题：陶瓷与硬质涂层",
        "material_system_hint": "陶瓷与硬质涂层",
        "queries": [
            "ceramic coating marine corrosion wear protection",
            "hard coating corrosion wear seawater",
            "PVD hard coating corrosion tribocorrosion",
        ],
    },
    {
        "topic_label": "拓展主题：溶胶凝胶与杂化涂层",
        "material_system_hint": "溶胶凝胶与有机-无机杂化涂层",
        "queries": [
            "sol gel coating corrosion protection marine steel",
            "organic inorganic hybrid coating anticorrosion",
            "silane sol gel coating marine corrosion",
        ],
    },
    {
        "topic_label": "拓展主题：二维材料增强涂层",
        "material_system_hint": "纳米改性与二维材料增强涂层",
        "queries": [
            "graphene coating corrosion protection marine",
            "MXene coating corrosion protection",
            "two dimensional materials reinforced anticorrosion coating",
        ],
    },
    {
        "topic_label": "拓展主题：耐蚀合金",
        "material_system_hint": "结构材料与耐蚀合金",
        "queries": [
            "corrosion resistant alloy marine environment steel structure",
            "stainless steel seawater corrosion alloy coating",
            "nickel based alloy marine corrosion wear",
        ],
    },
    {
        "topic_label": "拓展主题：阴极保护与复合防护",
        "material_system_hint": "复合防护与辅助保护",
        "queries": [
            "cathodic protection coating marine steel corrosion",
            "coating cathodic protection offshore wind corrosion",
            "combined corrosion protection coating cathodic protection",
        ],
    },
    {
        "topic_label": "拓展主题：自修复防腐涂层",
        "material_system_hint": "修复与辅助防护材料",
        "queries": [
            "self healing anticorrosion coating marine",
            "microcapsule self healing coating corrosion protection",
            "smart coating corrosion protection marine steel",
        ],
    },
    {
        "topic_label": "拓展主题：海洋钢结构防护",
        "material_system_hint": "工程对象主题",
        "queries": [
            "marine steel structure corrosion protection coating",
            "offshore wind steel corrosion protective coating",
            "port steel structure marine corrosion coating",
        ],
    },
]


def _clean(text: object) -> str:
    text = "" if text is None else str(text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _plain_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item)
    if value is None:
        return ""
    return str(value)


def _year_from_crossref(item: dict[str, Any]) -> str:
    for key in ["published-print", "published-online", "published"]:
        parts = item.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            return str(parts[0][0])
    return ""


def _doi_url(doi: object) -> str:
    doi_text = str(doi or "").strip()
    return f"https://doi.org/{doi_text}" if doi_text else ""


def _formula_elements(formula: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"[A-Z][a-z]?", str(formula))))


def _abstract_from_openalex(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        for position in positions:
            words.append((int(position), word))
    return " ".join(word for _, word in sorted(words))[:420]


def _request_json(url: str, *, params: dict[str, Any], headers: dict[str, str] | None = None, attempts: int = 2) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = requests.get(url, params=params, headers=headers or {"User-Agent": USER_AGENT}, timeout=30)
            if response.status_code == 429:
                time.sleep(4 + attempt * 4)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(str(last_error))


def _literature_queries(formula: str, base_query: str) -> list[str]:
    aliases = FORMULA_ALIASES.get(formula, [formula])
    focused = [
        base_query,
        f"{formula} coating corrosion",
        f"{formula} coating wear corrosion",
        f"{formula} PVD coating corrosion",
    ]
    for alias in aliases[:2]:
        focused.append(f"{alias} coating corrosion")
    return list(dict.fromkeys(query for query in focused if query.strip()))


def _matches_formula_or_alias(formula: str, title: str, abstract: str = "") -> bool:
    text = f"{title} {abstract}".lower()
    compact = re.sub(r"[^a-z0-9]+", "", text)
    for alias in FORMULA_ALIASES.get(formula, [formula]):
        alias_lower = alias.lower()
        alias_compact = re.sub(r"[^a-z0-9]+", "", alias_lower)
        if len(alias_compact) <= 3:
            if re.search(rf"(?<![a-z0-9]){re.escape(alias_lower)}(?![a-z0-9])", text):
                return True
        elif alias_compact and alias_compact in compact:
            return True
    return False


def fetch_crossref_sci_like_for_material(formula: str, query: str, rows: int = 8) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for expanded_query in _literature_queries(formula, query):
        try:
            response = requests.get(
                "https://api.crossref.org/works",
                params={
                    "query.bibliographic": expanded_query,
                    "rows": rows,
                    "filter": "type:journal-article",
                    "select": "DOI,title,container-title,published-print,published-online,published,URL,abstract,type,ISSN,publisher",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=12,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            print(f"[Crossref SCI-like WARN] {formula} / {expanded_query}: {exc}")
            continue
        items = data.get("message", {}).get("items", [])
        for item in items:
            title = _clean(_plain_text(item.get("title")))
            journal = _clean(_plain_text(item.get("container-title")))
            abstract = _clean(item.get("abstract", ""))
            doi = str(item.get("DOI", "")).strip()
            if not title or not journal or not doi:
                continue
            if not _matches_formula_or_alias(formula, title, abstract):
                continue
            records.append(
                {
                    "formula": formula,
                    "query": expanded_query,
                    "title": title,
                    "journal": journal,
                    "year": _year_from_crossref(item),
                    "doi": doi,
                    "url": item.get("URL") or _doi_url(doi),
                    "abstract_snippet": abstract[:420],
                    "publisher": item.get("publisher", ""),
                    "issn": "|".join(item.get("ISSN", []) or []),
                    "evidence_type": "Crossref DOI期刊论文候选",
                    "relevance_note": "按 DOI、期刊名和材料题名相关性筛选，接近 SCI 检索入口；是否 SCI 收录需 Web of Science 人工复核",
                    "data_status": "SCI 候选文献线索，尚未完成 Web of Science 收录核验、全文精读和实验指标抽取",
                }
            )
        time.sleep(0.2)
    return records


def fetch_crossref_topic_discovery(rows: int = 8, topic_filter: set[str] | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for topic in TOPIC_DISCOVERY_QUERIES:
        topic_label = topic["topic_label"]
        material_system_hint = topic["material_system_hint"]
        if topic_filter and not any(token in topic_label or token in material_system_hint for token in topic_filter):
            continue
        for query in topic["queries"]:
            try:
                response = requests.get(
                    "https://api.crossref.org/works",
                    params={
                        "query.bibliographic": query,
                        "rows": rows,
                        "filter": "type:journal-article",
                        "select": "DOI,title,container-title,published-print,published-online,published,URL,abstract,type,ISSN,publisher",
                    },
                    headers={"User-Agent": USER_AGENT},
                    timeout=12,
                )
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                print(f"[Crossref Topic WARN] {topic_label} / {query}: {exc}")
                continue
            for item in data.get("message", {}).get("items", []):
                title = _clean(_plain_text(item.get("title")))
                journal = _clean(_plain_text(item.get("container-title")))
                doi = str(item.get("DOI", "")).strip()
                if not title or not journal or not doi:
                    continue
                records.append(
                    {
                        "formula": topic_label,
                        "query": query,
                        "title": title,
                        "journal": journal,
                        "year": _year_from_crossref(item),
                        "doi": doi,
                        "url": item.get("URL") or _doi_url(doi),
                        "abstract_snippet": _clean(item.get("abstract", ""))[:420],
                        "publisher": item.get("publisher", ""),
                        "issn": "|".join(item.get("ISSN", []) or []),
                        "evidence_type": "Crossref 主题拓展期刊论文",
                        "discovery_scope": "材料体系拓展主题",
                        "topic": topic_label,
                        "material_system_hint": material_system_hint,
                        "relevance_note": "按材料体系、海洋腐蚀、防护涂层和工程场景扩展检索；不局限于当前首批候选材料",
                        "data_status": "拓展主题文献线索，需人工复核材料体系、工程对象、实验条件、SCI/WoS 收录状态和全文指标",
                    }
                )
            time.sleep(0.2)
    return records


def fetch_oqmd_for_formula(formula: str) -> list[dict[str, Any]]:
    data = _request_json(
        "http://oqmd.org/oqmdapi/formationenergy",
        params={
            "composition": formula,
            "fields": "name,entry_id,delta_e,stability,band_gap,spacegroup,ntypes,natoms,volume",
            "limit": 5,
            "format": "json",
        },
    )
    rows = data.get("data", [])
    records = []
    for row in rows:
        records.append(
            {
                "formula": formula,
                "source_database": "OQMD",
                "source_id": str(row.get("entry_id", "")),
                "source_url": f"http://oqmd.org/materials/entry/{row.get('entry_id')}" if row.get("entry_id") else "",
                "matched_formula": row.get("name", ""),
                "formation_energy": row.get("delta_e", ""),
                "energy_above_hull": row.get("stability", ""),
                "band_gap": row.get("band_gap", ""),
                "spacegroup": row.get("spacegroup", ""),
                "data_status": "OQMD REST API 候选条目，需人工复核结构与公式匹配",
            }
        )
    return records


def fetch_aflow_for_formula(formula: str, rows: int = 5) -> list[dict[str, Any]]:
    elements = _formula_elements(formula)
    if not elements:
        return []
    query_parts = [f"species({element})" for element in elements]
    query_parts.extend(
        [
            f"nspecies({len(elements)})",
            f"$paging(1,{rows})",
            "compound",
            "auid",
            "aurl",
            "enthalpy_formation_atom",
            "Egap",
            "spacegroup_relax",
            "Pearson_symbol_relax",
        ]
    )
    response = requests.get(
        "https://aflow.org/API/aflux/?" + ",".join(query_parts),
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        return []
    records = []
    for row in data:
        aurl = str(row.get("aurl", "") or "")
        records.append(
            {
                "formula": formula,
                "source_database": "AFLOW",
                "source_id": str(row.get("auid", "") or ""),
                "source_url": f"https://{aurl}" if aurl and not aurl.startswith("http") else aurl,
                "matched_formula": row.get("compound", ""),
                "formation_energy": row.get("enthalpy_formation_atom", ""),
                "energy_above_hull": "",
                "band_gap": row.get("Egap", ""),
                "spacegroup": row.get("spacegroup_relax", ""),
                "pearson_symbol": row.get("Pearson_symbol_relax", ""),
                "data_status": "AFLOW 元素组成候选条目，需人工复核结构、相组成与涂层适用性",
            }
        )
    return records


def fetch_openalex_for_material(formula: str, query: str, rows: int = 5) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "search": query,
        "per-page": rows,
        "select": "id,doi,title,publication_year,primary_location,cited_by_count,abstract_inverted_index",
    }
    mailto = os.getenv("OPENALEX_MAILTO")
    api_key = os.getenv("OPENALEX_API_KEY")
    if mailto:
        params["mailto"] = mailto
    if api_key:
        params["api_key"] = api_key
    data = _request_json("https://api.openalex.org/works", params=params)
    records = []
    for item in data.get("results", []):
        title = _clean(item.get("title", ""))
        if not title:
            continue
        location = item.get("primary_location") or {}
        source = (location.get("source") or {}).get("display_name", "")
        doi = str(item.get("doi") or "").replace("https://doi.org/", "")
        records.append(
            {
                "formula": formula,
                "query": query,
                "title": title,
                "journal": source,
                "year": item.get("publication_year", ""),
                "doi": doi,
                "url": item.get("doi") or item.get("id", ""),
                "abstract_snippet": _abstract_from_openalex(item.get("abstract_inverted_index")),
                "evidence_type": "OpenAlex 文献元数据",
                "relevance_note": "OpenAlex 搜索命中，需人工复核材料体系、实验条件和全文",
                "data_status": "文献线索，需人工复核题名、摘要、全文和实验条件",
            }
        )
    return records


def fetch_semantic_scholar_for_material(formula: str, query: str, rows: int = 5) -> list[dict[str, Any]]:
    headers = {"User-Agent": USER_AGENT}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    data = _request_json(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={
            "query": query,
            "limit": rows,
            "fields": "title,year,venue,url,externalIds,abstract,citationCount,openAccessPdf",
        },
        headers=headers,
    )
    records = []
    for item in data.get("data", []):
        title = _clean(item.get("title", ""))
        if not title:
            continue
        external = item.get("externalIds") or {}
        doi = external.get("DOI", "")
        records.append(
            {
                "formula": formula,
                "query": query,
                "title": title,
                "journal": item.get("venue", ""),
                "year": item.get("year", ""),
                "doi": doi,
                "url": item.get("url") or _doi_url(doi),
                "abstract_snippet": _clean(item.get("abstract", ""))[:420],
                "evidence_type": "Semantic Scholar 文献元数据",
                "relevance_note": "Semantic Scholar 搜索命中，需人工复核材料体系、实验条件和全文",
                "data_status": "文献线索，需人工复核题名、摘要、全文和实验条件",
            }
        )
    return records


def fetch_europe_pmc_for_material(formula: str, query: str, rows: int = 5) -> list[dict[str, Any]]:
    data = _request_json(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={
            "query": query,
            "format": "json",
            "pageSize": rows,
            "resultType": "core",
        },
    )
    records = []
    for item in data.get("resultList", {}).get("result", []):
        title = _clean(item.get("title", ""))
        if not title:
            continue
        doi = str(item.get("doi") or "").strip()
        records.append(
            {
                "formula": formula,
                "query": query,
                "title": title,
                "journal": item.get("journalTitle", ""),
                "year": item.get("pubYear", ""),
                "doi": doi,
                "url": _doi_url(doi) or item.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url", ""),
                "abstract_snippet": _clean(item.get("abstractText", ""))[:420],
                "evidence_type": "Europe PMC 文献元数据",
                "relevance_note": "Europe PMC 检索命中，需人工复核材料体系、实验条件和全文",
                "data_status": "文献线索，需人工复核题名、摘要、全文和实验条件",
            }
        )
    return records


def _selected_materials(materials: pd.DataFrame, formula_arg: str | None) -> pd.DataFrame:
    if not formula_arg:
        return materials
    wanted = {item.strip() for item in formula_arg.split(",") if item.strip()}
    return materials[materials["formula"].astype(str).isin(wanted)].copy()


def _merge_existing(new_df: pd.DataFrame, existing_file: Path, keys: list[str]) -> pd.DataFrame:
    frames = []
    if existing_file.exists():
        frames.append(pd.read_csv(existing_file))
    if not new_df.empty:
        frames.append(new_df)
    if not frames:
        return pd.DataFrame()
    merged = pd.concat(frames, ignore_index=True, sort=False)
    usable_keys = [key for key in keys if key in merged.columns]
    if usable_keys:
        merged = merged.drop_duplicates(subset=usable_keys).reset_index(drop=True)
    return merged


def _write_csv(df: pd.DataFrame, path: Path) -> bool:
    try:
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return True
    except PermissionError as exc:
        print(f"[WRITE WARN] {path}: {exc}")
        return False


def fetch_material_database_candidates(materials: pd.DataFrame, sources: set[str]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for formula in materials["formula"].dropna().drop_duplicates():
        if "oqmd" in sources:
            try:
                rows = fetch_oqmd_for_formula(str(formula))
                print(f"[OQMD] {formula}: {len(rows)} candidates")
            except Exception as exc:
                print(f"[OQMD WARN] {formula}: {exc}")
                rows = []
            records.extend(rows)
        if "aflow" in sources:
            try:
                rows = fetch_aflow_for_formula(str(formula))
                print(f"[AFLOW] {formula}: {len(rows)} candidates")
            except Exception as exc:
                print(f"[AFLOW WARN] {formula}: {exc}")
                rows = []
            records.extend(rows)
    return pd.DataFrame(records)


def fetch_literature_multi_source(
    materials: pd.DataFrame,
    *,
    sources: set[str],
    rows_per_source: int = 4,
    include_base: bool = True,
    topic_filter: set[str] | None = None,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    if include_base and BASE_LITERATURE_FILE.exists():
        records.extend(pd.read_csv(BASE_LITERATURE_FILE).to_dict("records"))

    if "crossref-topic" in sources:
        topic_rows = fetch_crossref_topic_discovery(rows=rows_per_source, topic_filter=topic_filter)
        print(f"[Crossref Topic] {len(topic_rows)} records")
        records.extend(topic_rows)

    fetchers = {
        "crossref": ("Crossref", fetch_crossref_for_material),
        "crossref-sci": ("Crossref SCI-like", fetch_crossref_sci_like_for_material),
        "openalex": ("OpenAlex", fetch_openalex_for_material),
        "semantic-scholar": ("Semantic Scholar", fetch_semantic_scholar_for_material),
        "europe-pmc": ("Europe PMC", fetch_europe_pmc_for_material),
    }
    for formula in materials["formula"].dropna().drop_duplicates():
        query = SEARCH_TERMS.get(str(formula), f"{formula} coating corrosion")
        for source_key in sources:
            if source_key not in fetchers:
                continue
            source_name, fetcher = fetchers[source_key]
            try:
                rows = fetcher(str(formula), query, rows=rows_per_source)
                print(f"[{source_name}] {formula}: {len(rows)} records")
            except Exception as exc:
                print(f"[{source_name} WARN] {formula}: {exc}")
                rows = []
            records.extend(rows)

    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    for column in ["doi", "title", "evidence_type"]:
        if column not in df.columns:
            df[column] = ""
    df = df.drop_duplicates(subset=["formula", "doi", "title", "evidence_type"]).reset_index(drop=True)
    if "evidence_id" in df.columns:
        df = df.drop(columns=["evidence_id"])
    df.insert(0, "evidence_id", [f"LIT-MULTI-{i + 1:04d}" for i in range(len(df))])
    return df


def write_integration_audit(materials: pd.DataFrame, literature: pd.DataFrame, material_db: pd.DataFrame) -> pd.DataFrame:
    lit_counts = literature.groupby("formula").size().to_dict() if not literature.empty else {}
    external_counts = material_db.groupby("formula").size().to_dict() if not material_db.empty else {}
    rows = []
    for _, row in materials.iterrows():
        source = str(row.get("source_database", ""))
        source_id = str(row.get("source_id", ""))
        has_mp = source == "Materials Project" and source_id and source_id != "nan"
        rows.append(
            {
                "formula": row["formula"],
                "material_name_cn": row["material_name_cn"],
                "recommendation_object_type": row.get("recommendation_object_type", ""),
                "material_system": row.get("material_system", ""),
                "chemistry_tags": row.get("chemistry_tags", ""),
                "materials_database_status": "已接入 Materials Project" if has_mp else "待接入真实材料数据库",
                "source_database": source,
                "source_id": "" if source_id == "nan" else source_id,
                "external_material_database_candidates": int(external_counts.get(row["formula"], 0)),
                "literature_records": int(lit_counts.get(row["formula"], 0)),
                "literature_status": "已接入多源文献线索" if lit_counts.get(row["formula"], 0) else "暂无文献线索",
                "evidence_gap": "待补充基体、工艺、厚度、盐雾/电化学/磨损等可比实验字段",
            }
        )
    audit = pd.DataFrame(rows)
    return audit


def write_source_status(material_db: pd.DataFrame, literature: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "source_name": "Materials Project",
            "source_type": "materials_database",
            "records": "",
            "integration_status": "已在候选材料主表接入；新增条目需配置 MP_API_KEY 后刷新",
        },
        {
            "source_name": "OQMD",
            "source_type": "materials_database",
            "records": int(len(material_db)) if not material_db.empty else 0,
            "integration_status": "已接入公开 REST 候选条目，需人工复核结构与公式匹配",
        },
    ]
    if not material_db.empty and "source_database" in material_db.columns:
        rows[1]["records"] = int((material_db["source_database"] == "OQMD").sum())
        rows.append(
            {
                "source_name": "AFLOW",
                "source_type": "materials_database",
                "records": int((material_db["source_database"] == "AFLOW").sum()),
                "integration_status": "已接入元素组成候选结构，需人工复核相组成与涂层适用性",
            }
        )
    if not literature.empty and "evidence_type" in literature.columns:
        for source, count in literature["evidence_type"].fillna("未知来源").value_counts().items():
            rows.append(
                {
                    "source_name": source,
                    "source_type": "literature_metadata",
                    "records": int(count),
                    "integration_status": "已接入文献元数据线索，尚未完成全文精读和实验指标抽取",
                }
            )
    status = pd.DataFrame(rows)
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch external material database and literature evidence metadata.")
    parser.add_argument("--formulas", help="Comma-separated formula list, e.g. TiN,CrN,SiC. Defaults to all candidates.")
    parser.add_argument("--rows", type=int, default=4, help="Rows requested per literature source and material.")
    parser.add_argument(
        "--sources",
        default="oqmd,aflow,crossref-sci,europe-pmc",
        help="Comma-separated sources: oqmd,aflow,crossref,crossref-sci,crossref-topic,openalex,semantic-scholar,europe-pmc,all.",
    )
    parser.add_argument("--replace", action="store_true", help="Replace output files instead of merging with existing records.")
    parser.add_argument("--topics", help="Optional topic keyword filter for crossref-topic, e.g. 有机防腐,热喷涂.")
    return parser.parse_args()


def _source_set(source_arg: str) -> set[str]:
    sources = {item.strip().lower() for item in source_arg.split(",") if item.strip()}
    if "all" in sources:
        return set(MATERIAL_DATABASE_SOURCES) | set(LITERATURE_SOURCES)
    return sources


def main() -> None:
    args = parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    materials = _selected_materials(pd.read_csv(MATERIAL_FILE), args.formulas)
    sources = _source_set(args.sources)
    literature_sources = sources & set(LITERATURE_SOURCES)
    material_sources = sources & set(MATERIAL_DATABASE_SOURCES)
    topic_filter = {item.strip() for item in str(args.topics or "").split(",") if item.strip()} or None

    material_db = fetch_material_database_candidates(materials, material_sources)
    if not args.replace and material_sources:
        material_db = _merge_existing(material_db, MATERIAL_DB_FILE, ["formula", "source_database", "source_id", "matched_formula"])
    if material_sources and not material_db.empty:
        if _write_csv(material_db, MATERIAL_DB_FILE):
            print(f"Saved {MATERIAL_DB_FILE} with {len(material_db)} rows")
    elif MATERIAL_DB_FILE.exists():
        material_db = pd.read_csv(MATERIAL_DB_FILE)
        print(f"No new material database rows. Kept existing {MATERIAL_DB_FILE} with {len(material_db)} rows")

    fetched_literature = fetch_literature_multi_source(
        materials,
        sources=literature_sources,
        rows_per_source=args.rows,
        include_base=False,
        topic_filter=topic_filter,
    )
    literature = fetched_literature
    if not args.replace:
        literature = _merge_existing(literature, MULTI_LITERATURE_FILE, ["formula", "doi", "title", "evidence_type"])
        if not literature.empty:
            if "evidence_id" in literature.columns:
                literature = literature.drop(columns=["evidence_id"])
            literature.insert(0, "evidence_id", [f"LIT-MULTI-{i + 1:04d}" for i in range(len(literature))])
    if not fetched_literature.empty or args.replace:
        if _write_csv(literature, MULTI_LITERATURE_FILE):
            print(f"Saved {MULTI_LITERATURE_FILE} with {len(literature)} rows")
    elif MULTI_LITERATURE_FILE.exists():
        literature = pd.read_csv(MULTI_LITERATURE_FILE)
        print(f"No new literature rows. Kept existing {MULTI_LITERATURE_FILE} with {len(literature)} rows")
    elif BASE_LITERATURE_FILE.exists():
        literature = pd.read_csv(BASE_LITERATURE_FILE)

    all_materials = pd.read_csv(MATERIAL_FILE)
    audit = write_integration_audit(all_materials, literature, material_db)
    status = write_source_status(material_db, literature)
    if _write_csv(audit, AUDIT_FILE):
        print(f"Saved {AUDIT_FILE} with {len(audit)} rows")
    if _write_csv(status, SOURCE_STATUS_FILE):
        print(f"Saved {SOURCE_STATUS_FILE} with {len(status)} rows")


if __name__ == "__main__":
    main()
