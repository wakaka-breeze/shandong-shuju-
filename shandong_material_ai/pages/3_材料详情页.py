from pathlib import Path
import importlib
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
sys.path.append(str(BASE_DIR / "scripts"))
sys.path.append(str(BASE_DIR))

from score_materials import score_materials  # noqa: E402
import ui_components  # noqa: E402
from ui_theme import apply_theme, render_top_nav  # noqa: E402

ui_components = importlib.reload(ui_components)


st.set_page_config(page_title="材料证据档案", layout="wide")
apply_theme("material")
render_top_nav("材料档案")


@st.cache_data
def read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


materials = read_csv("material_candidates.csv")
literature = read_csv("literature_evidence.csv")
multi_literature = read_csv("literature_evidence_multi_source.csv")
if not multi_literature.empty:
    literature = multi_literature
external_material_db = read_csv("material_database_external_candidates.csv")
systems = read_csv("candidate_material_systems.csv")
routes = read_csv("material_route_rules.csv")

st.title("材料证据档案")
st.caption("把候选材料的基础信息、Materials Project 物性、SCMS 评分、文献线索和验证建议放到同一张证据卡中。")

if materials.empty:
    st.warning("缺少 material_candidates.csv，无法展示材料详情。")
    st.stop()

formula = st.selectbox("选择材料", materials["formula"].tolist())
material = materials[materials["formula"] == formula].iloc[0]
score_table = score_materials(top_n=None)
score_row = score_table[score_table["formula"] == formula].iloc[0]
material_lit = literature[literature["formula"] == formula] if not literature.empty else pd.DataFrame()
material_external = external_material_db[external_material_db["formula"] == formula] if not external_material_db.empty else pd.DataFrame()

ui_components.render_compact_stats(
    [
        ("材料", formula),
        ("对象类型", material.get("recommendation_object_type", "表面工程与防护涂层")),
        ("材料体系", material.get("material_system", "陶瓷与硬质涂层")),
        ("材料库", material.get("source_id", "待接入")),
        ("外部库候选", len(material_external)),
        ("文献线索", len(material_lit)),
    ],
    columns=5,
)

st.warning("SCMS 是候选筛选评分，不是腐蚀速率预测；文献线索需人工复核题名、摘要、实验条件和全文。")

tab_profile, tab_properties, tab_evidence, tab_validation = st.tabs(["材料画像", "官方物性", "文献证据", "验证建议"])

with tab_profile:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("基础信息")
        info = {
            "中文名称": material["material_name_cn"],
            "化学式": material["formula"],
            "元素组成": material["elements"],
            "推荐对象类型": material.get("recommendation_object_type", "表面工程与防护涂层"),
            "材料体系": material.get("material_system", "陶瓷与硬质涂层"),
            "化学组成标签": material.get("chemistry_tags", material["category"]),
            "适用工程部位": material.get("engineering_components", "运动摩擦部件|紧固与连接件"),
            "防护机制": material.get("protection_mechanisms", "耐磨|阻隔|耐蚀"),
            "制备路线": material.get("process_route", "待补充"),
            "适用尺度": material.get("applicable_scale", "局部关键部件"),
            "候选池范围": material.get("pilot_scope", "首批验证候选池"),
            "数据完整性": material.get("data_completeness", "基础材料信息完整，工程性能证据待补充"),
            "证据状态": material.get("evidence_status", "文献线索待人工复核"),
            "候选应用": material["candidate_application"],
            "成本等级": material["cost_level"],
            "毒性风险": material["toxicity_risk"],
            "稀有元素风险": material["rare_element_risk"],
            "数据状态": material["data_status"],
        }
        st.dataframe(pd.DataFrame(info.items(), columns=["字段", "内容"]), use_container_width=True, hide_index=True)

    with right:
        st.subheader("五维评分")
        labels = ["稳定性", "防护潜力", "成本友好性", "环境适配度", "产业适配度"]
        values = [
            score_row["S_stability"],
            score_row["S_protection"],
            score_row["S_cost"],
            score_row["S_environment"],
            score_row["S_industry"],
        ]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]], fill="toself", name=formula))
        fig.update_layout(height=420, polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("推荐解释")
    st.write(score_row["recommendation_reason"])
    st.info("氧化物、氮化物、碳化物等在当前架构中作为化学组成标签展示，不再作为网站一级材料分类。")

with tab_properties:
    st.subheader("Materials Project / 真实数据库字段")
    properties = {
        "source_database": material.get("source_database", ""),
        "source_id": material.get("source_id", ""),
        "source_url": material.get("source_url", ""),
        "formation_energy": material.get("formation_energy", "待接入"),
        "energy_above_hull": material.get("energy_above_hull", "待接入"),
        "band_gap": material.get("band_gap", "待接入"),
        "density": material.get("density", "待接入"),
        "elastic_modulus": material.get("elastic_modulus", "待接入"),
    }
    st.dataframe(pd.DataFrame(properties.items(), columns=["字段", "值"]), use_container_width=True, hide_index=True)
    source_url = str(material.get("source_url", "")).strip()
    if source_url and source_url != "nan":
        st.markdown(f"[打开 Materials Project 条目]({source_url})")
    else:
        st.info("该材料的真实 DFT 数据尚未接入，请后续通过 Materials Project、OQMD 或 AFLOW 补充。")

    st.subheader("外部材料库候选条目")
    if material_external.empty:
        st.info("暂无外部材料库候选条目，或当前网络环境尚未成功抓取。")
    else:
        st.dataframe(
            material_external[
                [
                    "source_database",
                    "source_id",
                    "matched_formula",
                    "formation_energy",
                    "energy_above_hull",
                    "band_gap",
                    "spacegroup",
                    "data_status",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

with tab_evidence:
    st.subheader("文献线索")
    if material_lit.empty:
        st.info("该材料暂无文献元数据线索。可运行 `python scripts/fetch_literature_crossref.py` 补充。")
    else:
        st.dataframe(
            material_lit[["evidence_id", "title", "journal", "year", "doi", "url", "data_status"]],
            use_container_width=True,
            hide_index=True,
        )
        for _, row in material_lit.head(6).iterrows():
            with st.expander(str(row["title"])[:100]):
                st.write(f"期刊/来源：{row.get('journal', '')}")
                st.write(f"年份：{row.get('year', '')}")
                st.write(f"DOI：{row.get('doi', '')}")
                if str(row.get("url", "")).strip():
                    st.markdown(f"[来源链接]({row['url']})")
                snippet = str(row.get("abstract_snippet", "")).strip()
                if snippet and snippet != "nan":
                    st.write(snippet)
                st.caption(row["data_status"])

with tab_validation:
    st.subheader("实验验证建议")
    st.write(score_row["limitation"])
    st.markdown(
        """
        建议优先形成以下验证闭环：

        1. 文献与专利精筛：确认材料体系、制备工艺和海洋腐蚀场景是否匹配。
        2. 小试制备：记录基体材料、涂层厚度、孔隙率、沉积参数和后处理条件。
        3. 盐雾与湿热测试：建立可比较的暴露时间、失效形貌和评级口径。
        4. 电化学测试：补充开路电位、极化曲线、电化学阻抗谱等指标。
        5. 附着力与磨损测试：验证涂层在港口机械、海上风电或海洋装备中的机械可靠性。
        """
    )
    if not routes.empty:
        route = routes[routes["route_name"].str.contains("耐环境防护", na=False)]
        if not route.empty:
            st.markdown("**相关材料路线规则**")
            st.dataframe(route[["route_id", "route_name", "engineering_needs", "performance_targets", "verification_keywords"]], use_container_width=True, hide_index=True)
