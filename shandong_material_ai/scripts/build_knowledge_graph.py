from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def add_node(nodes: dict, node_id: str, label: str, node_type: str, description: str, city: str = "", material: str = "") -> None:
    nodes[node_id] = {
        "node_id": node_id,
        "label": label,
        "node_type": node_type,
        "description": description,
        "city": city,
        "material": material,
    }


def build_graph_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    env = pd.read_csv(DATA_DIR / "city_environment.csv")
    industry = pd.read_csv(DATA_DIR / "city_industry.csv")
    materials = pd.read_csv(DATA_DIR / "material_candidates.csv")

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for _, row in env.iterrows():
        city_id = f"city:{row['city']}"
        add_node(nodes, city_id, row["city"], "城市", row["environment_summary"], city=row["city"])
        for risk in ["盐雾风险", "高湿风险", "工业污染风险"]:
            risk_id = f"env:{row['city']}:{risk}"
            value = row["salt_spray_risk"] if risk == "盐雾风险" else row["humidity_risk"] if risk == "高湿风险" else row["industrial_pollution_risk"]
            label = f"{value}{risk}"
            add_node(nodes, risk_id, label, "环境", f"{row['city']}的{risk}示例等级为{value}。", city=row["city"])
            edges.append({"source": city_id, "target": risk_id, "relation": "具有", "description": f"{row['city']}具有{label}", "city": row["city"], "material": ""})

    for _, row in industry.iterrows():
        city_id = f"city:{row['city']}"
        industry_id = f"industry:{row['city']}:{row['industry_type']}"
        scene_id = f"scene:{row['application_scene']}"
        demand_id = f"demand:{row['application_scene']}:{row['material_demand']}"
        add_node(nodes, industry_id, row["industry_type"], "产业", row["description"], city=row["city"])
        add_node(nodes, scene_id, row["application_scene"], "应用场景", row["description"])
        add_node(nodes, demand_id, row["material_demand"], "性能需求", row["material_demand"])
        edges.append({"source": city_id, "target": industry_id, "relation": "拥有", "description": f"{row['city']}拥有{row['industry_type']}", "city": row["city"], "material": ""})
        edges.append({"source": industry_id, "target": scene_id, "relation": "对应", "description": f"{row['industry_type']}对应{row['application_scene']}", "city": row["city"], "material": ""})
        edges.append({"source": scene_id, "target": demand_id, "relation": "需要", "description": f"{row['application_scene']}需要{row['material_demand']}", "city": row["city"], "material": ""})

    for _, row in materials.iterrows():
        material_id = f"material:{row['formula']}"
        category_id = f"category:{row['category']}"
        protection_id = f"feature:{row['formula']}:防护潜力"
        add_node(nodes, material_id, row["formula"], "候选材料", row["notes"], material=row["formula"])
        add_node(nodes, category_id, row["category"], "材料类别", row["category"])
        add_node(nodes, protection_id, f"{row['protective_layer_potential']}防护潜力", "性能需求", f"{row['formula']}的防护潜力示例等级。", material=row["formula"])
        edges.append({"source": material_id, "target": category_id, "relation": "属于", "description": f"{row['formula']}属于{row['category']}", "city": "", "material": row["formula"]})
        edges.append({"source": material_id, "target": protection_id, "relation": "具有", "description": f"{row['formula']}具有{row['protective_layer_potential']}防护潜力", "city": "", "material": row["formula"]})
        for scene in str(row["candidate_application"]).split("、"):
            scene_id = f"scene:{scene}"
            add_node(nodes, scene_id, scene, "应用场景", scene)
            edges.append({"source": material_id, "target": scene_id, "relation": "适用于", "description": f"{row['formula']}适用于{scene}", "city": "", "material": row["formula"]})

    return pd.DataFrame(nodes.values()), pd.DataFrame(edges)


def save_graph_tables() -> tuple[Path, Path]:
    nodes, edges = build_graph_tables()
    node_path = DATA_DIR / "knowledge_nodes.csv"
    edge_path = DATA_DIR / "knowledge_edges.csv"
    nodes.to_csv(node_path, index=False, encoding="utf-8-sig")
    edges.to_csv(edge_path, index=False, encoding="utf-8-sig")
    return node_path, edge_path


if __name__ == "__main__":
    node_path, edge_path = save_graph_tables()
    print(f"Knowledge graph saved to {node_path} and {edge_path}")
