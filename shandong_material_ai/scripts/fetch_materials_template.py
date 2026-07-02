"""
真实材料数据接入模板。

本文件默认不执行 API 请求，也不包含任何 API Key、真实数据库 ID 或虚构物性数值。
后续接入 Materials Project、OQMD、AFLOW 时，请从官方数据库或可追溯文献获取数据。
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MATERIAL_FILE = PROJECT_ROOT / "data" / "material_candidates.csv"


def read_api_key() -> str | None:
    """从环境变量读取 API Key；不要把 API Key 写死在代码、README 或 CSV 中。"""
    return os.getenv("MP_API_KEY") or os.getenv("MATERIALS_PROJECT_API_KEY")


def fetch_from_materials_project(formulas: list[str]) -> pd.DataFrame:
    """
    Materials Project 接入占位函数。

    未来可获取字段示例：
    formula, material_id, formation_energy_per_atom, energy_above_hull,
    band_gap, density, elastic properties。

    建议通过 .env 或系统环境变量提供 MP_API_KEY。
    """
    _ = formulas
    _ = read_api_key()
    return pd.DataFrame()


def fetch_from_oqmd(formulas: list[str]) -> pd.DataFrame:
    """OQMD 接入占位函数：请遵循 OQMD 官方许可、字段定义和引用要求。"""
    _ = formulas
    return pd.DataFrame()


def fetch_from_aflow(formulas: list[str]) -> pd.DataFrame:
    """AFLOW 接入占位函数：请遵循 AFLOW 官方 API、字段定义和引用要求。"""
    _ = formulas
    return pd.DataFrame()


def merge_real_properties(real_data: pd.DataFrame) -> None:
    """
    将真实数据库返回结果合并到 material_candidates.csv。

    合并时必须同步更新 source_database、source_id、source_url、data_status，
    并保留可追溯来源。没有真实来源的字段应继续标注为“待接入”。
    """
    materials = pd.read_csv(MATERIAL_FILE)
    if real_data.empty:
        print("No real data fetched. material_candidates.csv remains unchanged.")
        return

    updated = materials.merge(real_data, on="formula", how="left", suffixes=("", "_real"))
    updated.to_csv(MATERIAL_FILE, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    formulas = pd.read_csv(MATERIAL_FILE)["formula"].tolist()
    print("Template only. No API request will be sent.")
    print(f"Prepared formulas: {', '.join(formulas)}")
