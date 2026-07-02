from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_ZIP = Path(r"E:\数据要素\第一版\shandong_material_opportunity_platform.zip")
ZIP_PREFIX = "shandong_material_opportunity_platform/"


def _read_text_from_zip(zip_file: zipfile.ZipFile, inner_path: str) -> str:
    return zip_file.read(ZIP_PREFIX + inner_path).decode("utf-8", errors="replace")


def _as_text_list(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    return str(value)


def import_route_rules(zip_file: zipfile.ZipFile) -> pd.DataFrame:
    data = yaml.safe_load(_read_text_from_zip(zip_file, "rules/material_route_rules.yaml"))
    rows = []
    for route in data.get("routes", []):
        rows.append(
            {
                "route_id": route.get("route_id", ""),
                "route_name": route.get("route_name", ""),
                "trigger_keywords": _as_text_list(route.get("trigger_keywords")),
                "engineering_needs": _as_text_list(route.get("engineering_needs")),
                "performance_targets": _as_text_list(route.get("performance_targets")),
                "verification_keywords": _as_text_list(route.get("verification_keywords")),
                "source_asset": "第一版 rules/material_route_rules.yaml",
                "data_status": "规则库数据，需结合真实产业记录人工审核",
            }
        )
    return pd.DataFrame(rows)


def import_candidate_systems(zip_file: zipfile.ZipFile) -> pd.DataFrame:
    data = yaml.safe_load(_read_text_from_zip(zip_file, "rules/candidate_material_systems.yaml"))
    rows = []
    for item in data.get("systems", []):
        rows.append(
            {
                "system_id": item.get("system_id", ""),
                "system_name": item.get("system_name", ""),
                "material_route_id": item.get("material_route_id", ""),
                "applicable_engineering_needs": _as_text_list(item.get("applicable_engineering_needs")),
                "target_properties": _as_text_list(item.get("target_properties")),
                "advantages": _as_text_list(item.get("advantages")),
                "limitations": _as_text_list(item.get("limitations")),
                "suggested_validation_tests": _as_text_list(item.get("suggested_validation_tests")),
                "evidence_level": item.get("evidence_level", "路线级知识"),
                "needs_expert_review": item.get("needs_expert_review", True),
                "source_asset": "第一版 rules/candidate_material_systems.yaml",
                "data_status": "候选体系规则，非真实配方或性能预测",
            }
        )
    return pd.DataFrame(rows)


def import_rd_steps(zip_file: zipfile.ZipFile) -> pd.DataFrame:
    data = yaml.safe_load(_read_text_from_zip(zip_file, "rules/rd_path_rules.yaml"))
    rows = []
    for step in data.get("steps", []):
        rows.append(
            {
                "step_id": step.get("step_id", ""),
                "step_name": step.get("step_name", ""),
                "objective": step.get("objective", ""),
                "outputs": _as_text_list(step.get("outputs")),
                "source_asset": "第一版 rules/rd_path_rules.yaml",
                "data_status": "研发流程规则，需按具体项目人工审核",
            }
        )
    return pd.DataFrame(rows)


def import_service_rules(zip_file: zipfile.ZipFile) -> pd.DataFrame:
    data = yaml.safe_load(_read_text_from_zip(zip_file, "rules/service_capability_rules.yaml"))
    rows = []
    for rule in data.get("capability_rules", []):
        rows.append(
            {
                "category": rule.get("category", ""),
                "keywords": _as_text_list(rule.get("keywords")),
                "source_asset": "第一版 rules/service_capability_rules.yaml",
                "data_status": "服务能力关键词规则，非机构资质认证",
            }
        )
    return pd.DataFrame(rows)


def import_opportunity_cards(zip_file: zipfile.ZipFile) -> pd.DataFrame:
    text = _read_text_from_zip(zip_file, "data/exports/opportunity_cards.json")
    records = json.loads(text)
    rows = []
    for record in records:
        rows.append(
            {
                "opportunity_id": record.get("opportunity_id", ""),
                "city": record.get("city", ""),
                "industry": record.get("industry", ""),
                "opportunity_name": record.get("opportunity_name", ""),
                "material_route_id": record.get("material_route_id", ""),
                "material_route_name": record.get("material_route_name", ""),
                "engineering_needs": _as_text_list(record.get("engineering_needs")),
                "performance_targets": _as_text_list(record.get("performance_targets")),
                "matched_keywords": _as_text_list(record.get("matched_keywords")),
                "opportunity_score": record.get("opportunity_score", ""),
                "opportunity_level": record.get("opportunity_level", ""),
                "manual_review_status": record.get("manual_review_status", ""),
                "limitations": _as_text_list(record.get("limitations")),
                "source_asset": "第一版 data/exports/opportunity_cards.json",
                "data_status": "第一版示例机会卡，仅作页面样例与规则验证，不作为真实产业结论",
            }
        )
    return pd.DataFrame(rows)


def save_csv(df: pd.DataFrame, filename: str) -> Path:
    path = DATA_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def import_assets(zip_path: Path = DEFAULT_ZIP) -> list[Path]:
    if not zip_path.exists():
        raise FileNotFoundError(f"Cannot find first-version zip: {zip_path}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zip_file:
        outputs = [
            save_csv(import_route_rules(zip_file), "material_route_rules.csv"),
            save_csv(import_candidate_systems(zip_file), "candidate_material_systems.csv"),
            save_csv(import_rd_steps(zip_file), "rd_path_rules.csv"),
            save_csv(import_service_rules(zip_file), "service_capability_rules.csv"),
            save_csv(import_opportunity_cards(zip_file), "opportunity_cards_sample.csv"),
        ]

    manifest = pd.DataFrame(
        [
            {
                "asset_name": path.name,
                "source_zip": str(zip_path),
                "source_version": "第一版 shandong_material_opportunity_platform",
                "data_status": "从第一版导入的规则或样例数据，需保留边界说明",
            }
            for path in outputs
        ]
    )
    outputs.append(save_csv(manifest, "first_version_asset_manifest.csv"))
    return outputs


if __name__ == "__main__":
    for output in import_assets():
        print(output)
