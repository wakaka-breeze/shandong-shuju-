"""Transparent screening engine for the materials decision-support prototype.

This module separates screening suitability from evidence confidence. It does
not claim to predict corrosion rate, service life, or a deployable formulation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

LEVEL_SCORE = {"高": 90, "中": 70, "低": 50, "待接入": 0, "": 0}
COST_SCORE = {"低": 90, "中": 70, "高": 50, "待接入": 0, "": 0}

RECOMMENDATION_OBJECT_TYPES = [
    "结构材料与耐蚀合金",
    "表面工程与防护涂层",
    "高分子与复合防护材料",
    "功能材料与功能复合体系",
    "修复与辅助防护材料",
]

MATERIAL_SYSTEMS_BY_OBJECT = {
    "结构材料与耐蚀合金": ["耐蚀不锈钢与高合金钢", "铝、镁、钛等轻合金", "镍基与特种耐蚀合金"],
    "表面工程与防护涂层": [
        "有机防腐涂层",
        "金属与合金镀层",
        "热喷涂涂层",
        "陶瓷与硬质涂层",
        "转化膜与化学处理层",
        "溶胶凝胶与有机-无机杂化涂层",
        "多层、梯度与复合涂层",
        "纳米改性与二维材料增强涂层",
    ],
    "高分子与复合防护材料": ["纤维增强复合材料", "高阻隔聚合物复合材料", "密封与防渗聚合物材料"],
    "功能材料与功能复合体系": ["导电与传感功能材料", "导热绝缘复合材料", "低介电与电子封装材料"],
    "修复与辅助防护材料": ["修复补强材料", "阴极保护与牺牲阳极体系", "阻燃、密封与辅助防护材料"],
}

ENGINEERING_COMPONENTS = [
    "大面积钢结构",
    "运动摩擦部件",
    "紧固与连接件",
    "管道、阀门与换热部件",
    "海洋装备外壳",
    "导电、传感与功能部件",
]

SCENE_COMPONENT_HINTS = {
    "港口机械": "运动摩擦部件",
    "海洋装备": "海洋装备外壳",
    "海上风电设备": "紧固与连接件",
    "海洋牧场装备": "海洋装备外壳",
    "船舶装备": "海洋装备外壳",
    "船舶配套": "紧固与连接件",
    "海水环境装备": "管道、阀门与换热部件",
    "海洋工程": "大面积钢结构",
    "海洋运输装备": "海洋装备外壳",
    "钢铁装备防护": "大面积钢结构",
}

SYSTEM_SCENE_BONUS = {
    "港口机械": {"陶瓷与硬质涂层": 8, "热喷涂涂层": 5, "金属与合金镀层": 4},
    "海洋装备": {"有机防腐涂层": 8, "金属与合金镀层": 6, "热喷涂涂层": 6, "陶瓷与硬质涂层": 4},
    "海上风电设备": {"金属与合金镀层": 7, "热喷涂涂层": 6, "陶瓷与硬质涂层": 5},
    "海洋牧场装备": {"有机防腐涂层": 8, "金属与合金镀层": 5, "陶瓷与硬质涂层": 3},
    "船舶装备": {"有机防腐涂层": 8, "金属与合金镀层": 5, "热喷涂涂层": 5},
    "船舶配套": {"金属与合金镀层": 6, "陶瓷与硬质涂层": 5, "热喷涂涂层": 5},
    "海水环境装备": {"有机防腐涂层": 7, "金属与合金镀层": 6, "陶瓷与硬质涂层": 4},
    "海洋工程": {"有机防腐涂层": 8, "热喷涂涂层": 7, "金属与合金镀层": 7},
    "海洋运输装备": {"有机防腐涂层": 8, "金属与合金镀层": 6, "热喷涂涂层": 5},
    "钢铁装备防护": {"热喷涂涂层": 8, "有机防腐涂层": 7, "金属与合金镀层": 7, "陶瓷与硬质涂层": 5},
}

COMPONENT_SYSTEM_PRIORITY = {
    "大面积钢结构": {"有机防腐涂层": 10, "热喷涂涂层": 8, "金属与合金镀层": 8},
    "运动摩擦部件": {"陶瓷与硬质涂层": 12, "热喷涂涂层": 7, "多层、梯度与复合涂层": 6},
    "紧固与连接件": {"陶瓷与硬质涂层": 8, "金属与合金镀层": 8, "多层、梯度与复合涂层": 6},
    "管道、阀门与换热部件": {"金属与合金镀层": 8, "热喷涂涂层": 7, "有机防腐涂层": 6},
    "海洋装备外壳": {"有机防腐涂层": 10, "热喷涂涂层": 8, "金属与合金镀层": 8},
    "导电、传感与功能部件": {"导电与传感功能材料": 10, "纳米改性与二维材料增强涂层": 6},
}

DEFAULT_WEIGHTS = {
    "stability": 0.25,
    "protection": 0.30,
    "cost": 0.20,
    "environment": 0.15,
    "industry": 0.10,
}

PREFERENCE_WEIGHTS = {
    "综合平衡": DEFAULT_WEIGHTS,
    "稳定性优先": {"stability": 0.36, "protection": 0.25, "cost": 0.14, "environment": 0.15, "industry": 0.10},
    "防护潜力优先": {"stability": 0.22, "protection": 0.42, "cost": 0.11, "environment": 0.15, "industry": 0.10},
    "低成本优先": {"stability": 0.20, "protection": 0.25, "cost": 0.35, "environment": 0.12, "industry": 0.08},
}


def load_data() -> dict[str, pd.DataFrame]:
    def read(name: str) -> pd.DataFrame:
        path = DATA_DIR / name
        return pd.read_csv(path) if path.exists() else pd.DataFrame()

    return {
        "materials": read("material_candidates.csv"),
        "environment": read("city_environment.csv"),
        "industry": read("city_industry.csv"),
        "literature": read("literature_evidence_multi_source.csv")
        if (DATA_DIR / "literature_evidence_multi_source.csv").exists()
        else read("literature_evidence.csv"),
        "public_evidence": read("public_data_evidence.csv"),
    }


def _score(value: object, mapping: Mapping[str, int] = LEVEL_SCORE) -> int:
    return mapping.get(str(value).strip(), 0)


def _normalized_weights(weights: Mapping[str, float] | None, preference: str) -> dict[str, float]:
    source = dict(weights or PREFERENCE_WEIGHTS.get(preference, DEFAULT_WEIGHTS))
    result = {key: max(0.0, float(source.get(key, 0))) for key in DEFAULT_WEIGHTS}
    total = sum(result.values())
    return {key: value / total for key, value in result.items()} if total > 0 else dict(DEFAULT_WEIGHTS)


def _contains_pipe_tag(value: object, selected: str) -> bool:
    if selected in {"", "全部"}:
        return True
    tags = [tag.strip() for tag in str(value).split("|")]
    return selected in tags


def _filter_by_pipe_tag(materials: pd.DataFrame, column: str, selected: str) -> pd.DataFrame:
    if selected in {"", "全部"} or column not in materials.columns:
        return materials
    return materials[materials[column].fillna("").apply(lambda value: _contains_pipe_tag(value, selected))]


def _ensure_taxonomy_columns(materials: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        "recommendation_object_type": "表面工程与防护涂层",
        "material_system": "陶瓷与硬质涂层",
        "chemistry_tags": "",
        "engineering_components": "运动摩擦部件|紧固与连接件",
        "protection_mechanisms": "耐磨|阻隔|耐蚀",
        "process_route": "待补充",
        "applicable_scale": "局部关键部件",
        "pilot_scope": "首批验证候选池",
        "data_completeness": "基础材料信息完整，待补充工艺与性能证据",
        "evidence_status": "文献线索待人工复核",
    }
    for column, default in defaults.items():
        if column not in materials.columns:
            materials[column] = default
        else:
            materials[column] = materials[column].fillna("").replace("", default)
    return materials


def _environment_score(material: pd.Series, env: pd.Series, scene: str, engineering_component: str) -> int:
    base = _score(material.get("marine_environment_adaptability"))
    material_system = str(material.get("material_system", ""))
    scene_bonus = SYSTEM_SCENE_BONUS.get(scene, {}).get(material_system, 0)
    component_bonus = COMPONENT_SYSTEM_PRIORITY.get(engineering_component, {}).get(material_system, 0)
    salt_penalty = 8 if env.get("salt_spray_risk") == "高" and base < 80 else 0
    toxicity_penalty = 6 if material.get("toxicity_risk") == "高" else 0
    return int(max(0, min(100, base + scene_bonus + component_bonus - salt_penalty - toxicity_penalty)))


def _industry_score(material: pd.Series, city: str, scene: str, engineering_component: str, industry: pd.DataFrame) -> int:
    matched = industry[(industry["city"] == city) & (industry["application_scene"] == scene)]
    priority = matched.iloc[0]["industry_priority"] if not matched.empty else "中"
    material_system = str(material.get("material_system", ""))
    system_bonus = SYSTEM_SCENE_BONUS.get(scene, {}).get(material_system, 0)
    component_bonus = COMPONENT_SYSTEM_PRIORITY.get(engineering_component, {}).get(material_system, 0)
    cost_penalty = 5 if priority == "高" and material.get("cost_level") == "高" else 0
    return int(max(0, min(100, _score(priority) + system_bonus + component_bonus - cost_penalty)))


def _confidence(material: pd.Series, literature_count: int, env_status: str, public_evidence_count: int) -> tuple[int, list[str]]:
    """Score traceability, not expected performance."""
    score, reasons = 0, []
    source = str(material.get("source_database", "")).strip()
    if source == "Materials Project" and str(material.get("source_id", "")).strip():
        score += 30
        reasons.append("存在可追溯的 Materials Project 条目")
    else:
        reasons.append("缺少可追溯的材料数据库条目")

    if literature_count >= 5:
        score += 25
        reasons.append(f"已关联 {literature_count} 条文献线索")
    elif literature_count > 0:
        score += 15
        reasons.append(f"已关联 {literature_count} 条文献线索，但尚未完成全文复核")
    else:
        reasons.append("尚未关联可复核文献线索")

    observed_fields = ["formation_energy", "energy_above_hull", "band_gap", "density"]
    observed = sum(str(material.get(field, "")).strip() not in {"", "nan", "待接入"} for field in observed_fields)
    score += round(25 * observed / len(observed_fields))
    reasons.append(f"基础物性字段覆盖 {observed}/{len(observed_fields)}")

    if public_evidence_count > 0 and "仍需" not in env_status:
        score += 20
        reasons.append("区域场景具备公共数据目录支撑")
    elif public_evidence_count > 0:
        score += 10
        reasons.append("区域场景已有目录级证据，但需求强度仍待明细数据验证")
    else:
        reasons.append("区域场景缺少公共数据目录证据")

    return min(100, int(score)), reasons


def decision_label(screening_score: float, confidence: int) -> str:
    if confidence < 45:
        return "仅作线索：先补证据"
    if screening_score >= 80 and confidence >= 65:
        return "优先进入文献/小试验证"
    if screening_score >= 70:
        return "候选：需补关键验证"
    return "低优先级候选"


def candidate_pool_status(materials: pd.DataFrame, object_type: str, material_system: str, engineering_component: str) -> str:
    scoped = _ensure_taxonomy_columns(materials.copy()) if not materials.empty else materials
    if scoped.empty:
        return "候选数据表为空"
    scoped = scoped[scoped["recommendation_object_type"] == object_type]
    scoped = scoped[scoped["material_system"] == material_system]
    scoped = _filter_by_pipe_tag(scoped, "engineering_components", engineering_component)
    if scoped.empty:
        return "该体系当前尚未接入可比较候选数据"
    scopes = sorted(scoped["pilot_scope"].dropna().astype(str).unique())
    return "；".join(scopes) if scopes else "首批验证候选池"


def screen_materials(
    city: str,
    application_scene: str,
    recommendation_object_type: str = "表面工程与防护涂层",
    material_system: str = "陶瓷与硬质涂层",
    engineering_component: str = "运动摩擦部件",
    chemistry_tag: str = "全部",
    category: str = "全部",
    preference: str = "综合平衡",
    weights: Mapping[str, float] | None = None,
    exclude_high_toxicity: bool = False,
    exclude_rare_elements: bool = False,
) -> pd.DataFrame:
    data = load_data()
    materials = _ensure_taxonomy_columns(data["materials"].copy())
    if materials.empty:
        return materials

    if recommendation_object_type != "全部":
        materials = materials[materials["recommendation_object_type"] == recommendation_object_type]
    if material_system != "全部":
        materials = materials[materials["material_system"] == material_system]
    if engineering_component != "全部":
        materials = _filter_by_pipe_tag(materials, "engineering_components", engineering_component)
    if chemistry_tag != "全部":
        materials = _filter_by_pipe_tag(materials, "chemistry_tags", chemistry_tag)
    if category != "全部":
        materials = materials[materials["category"] == category]
    if exclude_high_toxicity:
        materials = materials[materials["toxicity_risk"] != "高"]
    if exclude_rare_elements:
        materials = materials[materials["rare_element_risk"] != "高"]

    if materials.empty:
        return materials

    env_rows = data["environment"][data["environment"]["city"] == city]
    env = env_rows.iloc[0] if not env_rows.empty else pd.Series(dtype=object)
    env_status = str(env.get("data_status", ""))
    public_count = int((data["public_evidence"].get("city", pd.Series(dtype=str)) == city).sum())
    literature_count = data["literature"].groupby("formula").size().to_dict() if not data["literature"].empty else {}
    used_weights = _normalized_weights(weights, preference)

    rows = []
    for _, material in materials.iterrows():
        components = {
            "stability": _score(material.get("stability_level")),
            "protection": _score(material.get("protective_layer_potential")),
            "cost": _score(material.get("cost_level"), COST_SCORE),
            "environment": _environment_score(material, env, application_scene, engineering_component),
            "industry": _industry_score(material, city, application_scene, engineering_component, data["industry"]),
        }
        screening_score = round(sum(components[key] * used_weights[key] for key in components), 1)
        lit = int(literature_count.get(material["formula"], 0))
        confidence, confidence_reasons = _confidence(material, lit, env_status, public_count)
        material_path = (
            f"{material.get('recommendation_object_type', '')} → "
            f"{material.get('material_system', '')} → "
            f"{material.get('chemistry_tags', '').split('|')[0]}"
        )
        rows.append({
            "material_id": material["material_id"],
            "formula": material["formula"],
            "material_name_cn": material["material_name_cn"],
            "category": material["category"],
            "elements": material.get("elements", ""),
            "recommendation_object_type": material.get("recommendation_object_type", ""),
            "material_system": material.get("material_system", ""),
            "material_path": material_path,
            "chemistry_tags": material.get("chemistry_tags", ""),
            "engineering_components": material.get("engineering_components", ""),
            "protection_mechanisms": material.get("protection_mechanisms", ""),
            "process_route": material.get("process_route", "待补充"),
            "applicable_scale": material.get("applicable_scale", ""),
            "pilot_scope": material.get("pilot_scope", "首批验证候选池"),
            "data_completeness": material.get("data_completeness", ""),
            "evidence_status": material.get("evidence_status", ""),
            "screening_score": screening_score,
            "evidence_confidence": confidence,
            "decision_label": decision_label(screening_score, confidence),
            "S_stability": components["stability"],
            "S_protection": components["protection"],
            "S_cost": components["cost"],
            "S_environment": components["environment"],
            "S_industry": components["industry"],
            "literature_count": lit,
            "source_database": material.get("source_database", ""),
            "source_id": material.get("source_id", ""),
            "source_url": material.get("source_url", ""),
            "data_status": material.get("data_status", ""),
            "recommended_application": material.get("candidate_application", ""),
            "match_reason": f"{city}{application_scene}场景先按工程部位“{engineering_component}”缩小候选池，再比较同一池内材料；当前材料机制为{material.get('protection_mechanisms', '')}。",
            "current_action": "进入文献复核与小试验证优先队列",
            "confidence_reasons": "；".join(confidence_reasons),
            "screening_basis": (
                f"候选池：{material.get('pilot_scope', '首批验证候选池')}；权重：稳定性 {used_weights['stability']:.0%}，"
                f"防护 {used_weights['protection']:.0%}，成本 {used_weights['cost']:.0%}，"
                f"环境 {used_weights['environment']:.0%}，产业 {used_weights['industry']:.0%}"
            ),
        })

    result = pd.DataFrame(rows).sort_values(["screening_score", "evidence_confidence"], ascending=False).reset_index(drop=True)
    result.insert(0, "rank", range(1, len(result) + 1))
    return result
