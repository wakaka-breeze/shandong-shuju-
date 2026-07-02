from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


# SCMS 等级换算规则：当前原型只使用“高/中/低”等示例等级。
# 这些分数用于可解释排序，不代表真实腐蚀速率、真实热力学稳定性或实验寿命。
LEVEL_SCORE = {"高": 90, "中": 70, "低": 50, "待接入": 0, "": 0}
COST_SCORE = {"低": 90, "中": 70, "高": 50, "待接入": 0, "": 0}
RISK_SCORE = {"低": 90, "中": 70, "高": 50, "待接入": 0, "": 0}

DEFAULT_WEIGHTS = {
    "weight_stability": 0.25,
    "weight_protection": 0.30,
    "weight_cost": 0.20,
    "weight_environment": 0.15,
    "weight_industry": 0.10,
}

PREFERENCE_WEIGHTS = {
    "综合平衡": DEFAULT_WEIGHTS,
    "稳定性优先": {
        "weight_stability": 0.36,
        "weight_protection": 0.25,
        "weight_cost": 0.14,
        "weight_environment": 0.15,
        "weight_industry": 0.10,
    },
    "防护潜力优先": {
        "weight_stability": 0.22,
        "weight_protection": 0.42,
        "weight_cost": 0.11,
        "weight_environment": 0.15,
        "weight_industry": 0.10,
    },
    "低成本优先": {
        "weight_stability": 0.20,
        "weight_protection": 0.25,
        "weight_cost": 0.35,
        "weight_environment": 0.12,
        "weight_industry": 0.08,
    },
}

CATEGORY_SCENE_BONUS = {
    "港口机械": {"碳化物涂层": 8, "氮化物涂层": 6, "氧化物涂层": 3},
    "海洋装备": {"氧化物涂层": 6, "氮化物涂层": 6, "碳化物涂层": 4},
    "海上风电设备": {"氧化物涂层": 7, "氮化物涂层": 6, "碳化物涂层": 3},
    "海洋牧场装备": {"氧化物涂层": 8, "氮化物涂层": 4, "碳化物涂层": 3},
    "船舶装备": {"氧化物涂层": 7, "氮化物涂层": 5, "碳化物涂层": 4},
    "船舶配套": {"氧化物涂层": 7, "氮化物涂层": 5, "碳化物涂层": 4},
    "海水环境装备": {"氧化物涂层": 8, "氮化物涂层": 4, "碳化物涂层": 3},
    "海洋工程": {"氧化物涂层": 6, "氮化物涂层": 6, "碳化物涂层": 4},
    "海洋运输装备": {"氧化物涂层": 7, "氮化物涂层": 5, "碳化物涂层": 4},
    "钢铁装备防护": {"碳化物涂层": 8, "氮化物涂层": 6, "氧化物涂层": 4},
}


def load_data() -> Dict[str, pd.DataFrame]:
    return {
        "materials": pd.read_csv(DATA_DIR / "material_candidates.csv"),
        "environment": pd.read_csv(DATA_DIR / "city_environment.csv"),
        "industry": pd.read_csv(DATA_DIR / "city_industry.csv"),
        "rules": pd.read_csv(DATA_DIR / "scenario_rules.csv"),
    }


def get_weight_profile(city: str, application_scene: str, preference: str, rules: pd.DataFrame) -> Dict[str, float]:
    if preference in PREFERENCE_WEIGHTS and preference != "综合平衡":
        return PREFERENCE_WEIGHTS[preference]

    matched = rules[(rules["city"] == city) & (rules["application_scene"] == application_scene)]
    if matched.empty:
        return DEFAULT_WEIGHTS

    row = matched.iloc[0]
    return {key: float(row.get(key, value)) for key, value in DEFAULT_WEIGHTS.items()}


def _level_score(value: object, mapping: Dict[str, int] = LEVEL_SCORE) -> int:
    return mapping.get(str(value).strip(), 60)


def _environment_score(material: pd.Series, city_env: pd.Series, application_scene: str) -> int:
    base = _level_score(material.get("marine_environment_adaptability"))
    salt_penalty = 8 if city_env.get("salt_spray_risk") == "高" and base < 80 else 0
    pollution_bonus = 5 if city_env.get("industrial_pollution_risk") == "高" and material.get("category") in ["碳化物涂层", "氮化物涂层"] else 0
    scene_bonus = CATEGORY_SCENE_BONUS.get(application_scene, {}).get(material.get("category"), 0)
    toxicity_penalty = 6 if material.get("toxicity_risk") == "高" else 0
    return max(0, min(100, base - salt_penalty + pollution_bonus + scene_bonus - toxicity_penalty))


def _industry_score(material: pd.Series, city: str, application_scene: str, industry: pd.DataFrame) -> int:
    matched = industry[(industry["city"] == city) & (industry["application_scene"] == application_scene)]
    priority = matched.iloc[0]["industry_priority"] if not matched.empty else "中"
    priority_score = _level_score(priority)
    category_bonus = CATEGORY_SCENE_BONUS.get(application_scene, {}).get(material.get("category"), 0)
    cost_penalty = 5 if priority == "高" and material.get("cost_level") == "高" else 0
    return max(0, min(100, priority_score + category_bonus - cost_penalty))


def build_reason(row: pd.Series, city: str, application_scene: str) -> str:
    return (
        f"该材料属于{row.get('recommendation_object_type', '表面工程与防护涂层')}下的"
        f"{row.get('material_system', '陶瓷与硬质涂层')}候选体系，化学组成标签为"
        f"{row.get('chemistry_tags', row['category'])}；具有{row['stability_level']}稳定性等级和"
        f"{row['protective_layer_potential']}防护潜力等级；在{city}{application_scene}相关盐雾、"
        "高湿或磨损场景中具备较好的初步环境适配评分；成本、毒性和稀有元素风险已纳入可解释评分。"
    )


def build_limitation(row: pd.Series) -> str:
    return (
        "该结果为数据驱动的候选材料初步筛选，不代表实际服役寿命或真实腐蚀速率；实际性能还受涂层制备工艺、"
        "孔隙率、厚度、附着力、基体材料、盐雾浓度、电化学环境和温度等因素影响；建议后续通过盐雾测试、"
        "极化曲线、电化学阻抗谱和附着力测试验证。"
    )


def score_materials(
    city: str = "青岛",
    application_scene: str = "海洋装备",
    category: str = "全部",
    preference: str = "综合平衡",
    exclude_high_toxicity: bool = False,
    exclude_rare_elements: bool = False,
    top_n: int | None = None,
) -> pd.DataFrame:
    data = load_data()
    materials = data["materials"].copy()

    if category != "全部":
        materials = materials[materials["category"] == category]
    if exclude_high_toxicity:
        materials = materials[materials["toxicity_risk"] != "高"]
    if exclude_rare_elements:
        materials = materials[materials["rare_element_risk"] != "高"]

    city_env_rows = data["environment"][data["environment"]["city"] == city]
    city_env = city_env_rows.iloc[0] if not city_env_rows.empty else data["environment"].iloc[0]
    weights = get_weight_profile(city, application_scene, preference, data["rules"])

    scored_rows = []
    for _, material in materials.iterrows():
        stability = _level_score(material.get("stability_level"))
        protection = _level_score(material.get("protective_layer_potential"))
        cost = _level_score(material.get("cost_level"), COST_SCORE)
        environment = _environment_score(material, city_env, application_scene)
        industry = _industry_score(material, city, application_scene, data["industry"])
        total = (
            weights["weight_stability"] * stability
            + weights["weight_protection"] * protection
            + weights["weight_cost"] * cost
            + weights["weight_environment"] * environment
            + weights["weight_industry"] * industry
        )
        scored_rows.append(
            {
                "material_id": material["material_id"],
                "formula": material["formula"],
                "material_name_cn": material["material_name_cn"],
                "category": material["category"],
                "recommendation_object_type": material.get("recommendation_object_type", "表面工程与防护涂层"),
                "material_system": material.get("material_system", "陶瓷与硬质涂层"),
                "chemistry_tags": material.get("chemistry_tags", material["category"]),
                "total_score": round(total, 2),
                "S_stability": stability,
                "S_protection": protection,
                "S_cost": cost,
                "S_environment": environment,
                "S_industry": industry,
                "recommended_application": material["candidate_application"],
                "recommendation_reason": build_reason(material, city, application_scene),
                "limitation": build_limitation(material),
                "data_status": material["data_status"],
                "city": city,
                "application_scene": application_scene,
                "preference": preference,
            }
        )

    result = pd.DataFrame(scored_rows)
    if result.empty:
        return result
    result = result.sort_values("total_score", ascending=False).reset_index(drop=True)
    result.insert(0, "rank", range(1, len(result) + 1))
    return result.head(top_n) if top_n else result


def generate_default_scores() -> pd.DataFrame:
    all_scores = []
    for city in ["青岛", "烟台", "威海", "日照"]:
        scenes = load_data()["industry"].query("city == @city")["application_scene"].unique()
        for scene in scenes:
            all_scores.append(score_materials(city=city, application_scene=scene, preference="综合平衡", top_n=10))
    return pd.concat(all_scores, ignore_index=True)


def save_default_scores() -> Path:
    output_path = DATA_DIR / "material_scores.csv"
    generate_default_scores().to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


if __name__ == "__main__":
    path = save_default_scores()
    print(f"SCMS scores saved to {path}")
