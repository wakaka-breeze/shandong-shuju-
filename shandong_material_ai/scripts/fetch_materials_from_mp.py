"""
从 Materials Project 官方 API 拉取候选材料的可追溯物性数据。

使用方式：
1. 在 PowerShell 中设置环境变量：
   $env:MP_API_KEY="你的 Materials Project API Key"
2. 运行：
   python scripts/fetch_materials_from_mp.py

注意：
- 本脚本不会把 API Key 写入任何文件。
- 查不到或字段为空的数据会继续保留为“待接入”。
- 拉取到的数值仅代表 Materials Project 数据库中的对应条目，不等同于涂层真实腐蚀速率。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from mp_api.client import MPRester


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MATERIAL_FILE = DATA_DIR / "material_candidates.csv"

MP_FIELDS = [
    "material_id",
    "formula_pretty",
    "formation_energy_per_atom",
    "energy_above_hull",
    "band_gap",
    "density",
    "is_stable",
]


def _value(doc: Any, field: str) -> Any:
    """兼容 mp-api 返回的 pydantic 对象和 dict。"""
    if isinstance(doc, dict):
        return doc.get(field)
    return getattr(doc, field, None)


def _round_or_pending(value: Any, digits: int = 6) -> Any:
    if value is None or value == "":
        return "待接入"
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return value


def _select_best_doc(docs: list[Any]) -> Any | None:
    """优先选择 energy_above_hull 最低的条目，保证公式匹配时取更稳定候选。"""
    if not docs:
        return None
    return sorted(docs, key=lambda doc: float(_value(doc, "energy_above_hull") or 9999))[0]


def fetch_one_formula(mpr: MPRester, formula: str) -> dict[str, Any] | None:
    docs = mpr.materials.summary.search(formula=formula, fields=MP_FIELDS)
    doc = _select_best_doc(list(docs))
    if doc is None:
        return None

    material_id = str(_value(doc, "material_id") or "")
    return {
        "formula": formula,
        "source_database": "Materials Project",
        "source_id": material_id,
        "source_url": f"https://materialsproject.org/materials/{material_id}" if material_id else "",
        "data_status": "已接入 Materials Project 官方 API 数据",
        "formation_energy": _round_or_pending(_value(doc, "formation_energy_per_atom")),
        "energy_above_hull": _round_or_pending(_value(doc, "energy_above_hull")),
        "band_gap": _round_or_pending(_value(doc, "band_gap")),
        "density": _round_or_pending(_value(doc, "density")),
        "elastic_modulus": "待接入",
        "mp_formula_pretty": _value(doc, "formula_pretty") or "",
        "mp_is_stable": _value(doc, "is_stable"),
    }


def fetch_materials(formulas: list[str], api_key: str) -> pd.DataFrame:
    records = []
    with MPRester(api_key) as mpr:
        for formula in formulas:
            try:
                record = fetch_one_formula(mpr, formula)
            except Exception as exc:  # API 单项失败时不中断整批材料
                print(f"[WARN] {formula}: {exc}")
                record = None
            if record:
                print(f"[OK] {formula}: {record['source_id']}")
                records.append(record)
            else:
                print(f"[MISS] {formula}: no Materials Project match")
    return pd.DataFrame(records)


def update_material_candidates(real_data: pd.DataFrame) -> Path:
    materials = pd.read_csv(MATERIAL_FILE)
    if real_data.empty:
        print("No Materials Project data fetched. material_candidates.csv remains unchanged.")
        return MATERIAL_FILE

    update_cols = [
        "source_database",
        "source_id",
        "source_url",
        "data_status",
        "formation_energy",
        "energy_above_hull",
        "band_gap",
        "density",
        "elastic_modulus",
    ]
    # 这些列会混合“待接入”和真实数值/链接，先转为 object，避免 pandas 未来版本类型报错。
    for col in update_cols:
        if col in materials.columns:
            materials[col] = materials[col].astype("object")

    real_lookup = real_data.set_index("formula")
    for index, row in materials.iterrows():
        formula = row["formula"]
        if formula not in real_lookup.index:
            continue
        for col in update_cols:
            materials.at[index, col] = real_lookup.at[formula, col]

    materials.to_csv(MATERIAL_FILE, index=False, encoding="utf-8-sig")
    audit_path = DATA_DIR / "materials_project_fetch_audit.csv"
    real_data.to_csv(audit_path, index=False, encoding="utf-8-sig")
    print(f"Updated {MATERIAL_FILE}")
    print(f"Saved audit file {audit_path}")
    return MATERIAL_FILE


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("MP_API_KEY") or os.getenv("MATERIALS_PROJECT_API_KEY")
    if not api_key:
        raise RuntimeError("Missing MP_API_KEY. Please set it in the environment or .env file.")

    materials = pd.read_csv(MATERIAL_FILE)
    formulas = materials["formula"].dropna().drop_duplicates().tolist()
    real_data = fetch_materials(formulas, api_key)
    update_material_candidates(real_data)


if __name__ == "__main__":
    main()
