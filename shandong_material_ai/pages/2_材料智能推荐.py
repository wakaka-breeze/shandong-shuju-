from __future__ import annotations

from html import escape
from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
sys.path.append(str(BASE_DIR / "scripts"))
sys.path.append(str(BASE_DIR))

from recommendation_engine import (  # noqa: E402
    ENGINEERING_COMPONENTS,
    MATERIAL_SYSTEMS_BY_OBJECT,
    candidate_pool_status,
    screen_materials,
)
from ui_theme import apply_theme, render_top_nav  # noqa: E402
import ui_components  # noqa: E402


st.set_page_config(page_title="沿海产业材料推荐工作台", layout="wide")
apply_theme("recommend")
render_top_nav("智能推荐")


@st.cache_data
def read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def split_tags(value: object) -> list[str]:
    return [tag.strip() for tag in str(value).split("|") if tag.strip() and tag.strip() != "nan"]


def render_result_cards(result: pd.DataFrame) -> None:
    cards = []
    for _, row in result.head(6).iterrows():
        width = max(0, min(100, float(row["screening_score"])))
        source_id = str(row.get("source_id", "")).strip()
        source_label = f"MP {source_id}" if source_id and source_id != "nan" else "材料库待接入"
        cards.append(
            f"""
            <article class="uiverse-result-card">
                <span class="rank">#{int(row["rank"])}</span>
                <div class="card-title">{escape(str(row["formula"]))} 硬质表面工程候选体系</div>
                <div class="name">{escape(str(row["material_name_cn"]))}</div>
                <div class="meta">
                    <span class="pill">{escape(str(row["pilot_scope"]))}</span>
                    <span class="pill">{escape(str(row["material_system"]))}</span>
                    <span class="pill">{escape(str(row["chemistry_tags"]))}</span>
                    <span class="pill">{escape(source_label)}</span>
                    <span class="pill">外部库 {escape(str(row.get("external_material_database_candidates", 0)))} 条</span>
                    <span class="pill">文献 {escape(str(row.get("literature_count", 0)))} 条</span>
                </div>
                <p class="score">适配 {escape(str(row["screening_score"]))} ｜ 证据 {escape(str(row["evidence_confidence"]))}</p>
                <p>{escape(str(row["match_reason"]))}</p>
                <div class="bar"><span style="width:{width}%"></span></div>
            </article>
            """
        )
    st.html(f'<section class="uiverse-result-grid">{"".join(cards)}</section>')


industry = read_csv("city_industry.csv")
materials = read_csv("material_candidates.csv")
public_evidence = read_csv("public_data_evidence.csv")
integration_audit = read_csv("material_data_integration_audit.csv")

st.html(
    """
    <section class="recommend-hero compact">
        <div class="uiverse-chip-row" style="margin-top:0;margin-bottom:16px;">
            <span class="uiverse-chip" data-tip="按城市场景和工程部位先缩小候选池。">Scene First</span>
            <span class="uiverse-chip" data-tip="当前候选池只用于文献复核和小试验证排序。">Validation First</span>
            <span class="uiverse-chip" data-tip="氧化物、氮化物、碳化物保留为化学标签。">Chemistry Tags</span>
        </div>
        <h1>沿海产业材料推荐工作台</h1>
        <p>输入材料或选择工程场景，系统先按工程部位缩小候选池，再给出可解释的验证优先级。当前首批候选池聚焦硬质表面工程材料，后续逐步接入耐蚀合金、有机防腐、热喷涂和复合防护体系。</p>
    </section>
    """
)

if industry.empty or materials.empty:
    st.warning("缺少产业场景或候选材料数据，无法生成推荐。")
    st.stop()

st.subheader("1. 快速筛选")

search_query = st.text_input(
    "材料搜索",
    placeholder="搜索 CrN、TiN、氧化铝、氮化物、PVD候选、运动部件等",
)

row1 = st.columns([1, 1.2, 1.15, 1.25])
city = row1[0].selectbox("城市", sorted(industry["city"].dropna().unique()))
scenes = industry[industry["city"] == city]["application_scene"].dropna().unique().tolist()
application_scene = row1[1].selectbox("应用场景", scenes)
engineering_component = row1[2].selectbox(
    "工程部位",
    ENGINEERING_COMPONENTS,
    index=ENGINEERING_COMPONENTS.index("运动摩擦部件"),
)
object_type = "表面工程与防护涂层"
system_options = MATERIAL_SYSTEMS_BY_OBJECT.get(object_type, [])
default_system_index = system_options.index("陶瓷与硬质涂层") if "陶瓷与硬质涂层" in system_options else 0
material_system = row1[3].selectbox("材料体系", system_options, index=default_system_index)

all_chemistry_tags = sorted({tag for value in materials.get("chemistry_tags", pd.Series(dtype=str)).dropna() for tag in split_tags(value)})
with st.expander("高级筛选", expanded=False):
    adv1, adv2, adv3, adv4 = st.columns([1, 1, 1, 1])
    chemistry_tag = adv1.selectbox("化学组成标签", ["全部"] + all_chemistry_tags)
    preference = adv2.selectbox("排序偏好", ["综合平衡", "稳定性优先", "防护潜力优先", "低成本优先"])
    exclude_toxic = adv3.checkbox("排除高毒性风险", value=False)
    exclude_rare = adv4.checkbox("排除稀有元素高风险", value=False)

pool_status = candidate_pool_status(materials, object_type, material_system, engineering_component)
if pool_status == "该体系当前尚未接入可比较候选数据":
    st.info(
        f"{object_type} → {material_system} → {engineering_component}：该体系当前尚未接入可比较候选数据。"
        "页面保留分类入口，但不生成推荐结果。"
    )

result = screen_materials(
    city=city,
    application_scene=application_scene,
    recommendation_object_type=object_type,
    material_system=material_system,
    engineering_component=engineering_component,
    chemistry_tag=chemistry_tag,
    preference=preference,
    exclude_high_toxicity=exclude_toxic,
    exclude_rare_elements=exclude_rare,
)

search_query = search_query.strip()
if not result.empty and search_query:
    search_columns = [
        "formula",
        "material_name_cn",
        "material_system",
        "chemistry_tags",
        "engineering_components",
        "recommended_application",
        "data_completeness",
        "evidence_status",
        "decision_label",
        "confidence_reasons",
    ]
    available_columns = [column for column in search_columns if column in result.columns]
    haystack = result[available_columns].fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    result = result[haystack.str.contains(search_query.lower(), regex=False)].copy()

if result.empty:
    st.warning("当前筛选条件没有可比较候选材料。请切换工程部位、材料体系或化学标签；系统不会把空分类放进总排行榜硬排。")
    st.stop()

if not integration_audit.empty:
    audit_cols = ["formula", "external_material_database_candidates"]
    available_audit_cols = [column for column in audit_cols if column in integration_audit.columns]
    result = result.merge(integration_audit[available_audit_cols], on="formula", how="left")
    result["external_material_database_candidates"] = result["external_material_database_candidates"].fillna(0).astype(int)
else:
    result["external_material_database_candidates"] = 0

result = result.head(10).reset_index(drop=True)
result["rank"] = range(1, len(result) + 1)
top = result.iloc[0]
city_evidence_count = int((public_evidence["city"] == city).sum()) if not public_evidence.empty else 0

st.subheader("2. 先看候选池，再看排序")
ui_components.render_compact_stats(
    [
        ("当前候选池", pool_status),
        ("首选材料", top["formula"]),
        ("筛选适配分", top["screening_score"]),
        ("城市公共证据", city_evidence_count),
    ],
    columns=4,
)

st.warning(
    "当前排序仅在同一工程部位与同一接入候选池内比较，用于确定文献复核和小试验证优先级。Materials Project 字段、文献线索和公共数据目录不能直接证明涂层在盐雾、浸泡或电化学条件下的真实防护性能。"
)

render_result_cards(result)

display = result.rename(
    columns={
        "rank": "排名",
        "formula": "材料",
        "material_name_cn": "中文名称",
        "recommendation_object_type": "推荐对象类型",
        "material_path": "材料体系路径",
        "chemistry_tags": "化学组成标签",
        "engineering_components": "适用工程部位",
        "pilot_scope": "当前候选池范围",
        "source_database": "材料库",
        "source_id": "材料库条目",
        "external_material_database_candidates": "外部库候选",
        "data_completeness": "数据完整性",
        "evidence_status": "证据状态",
        "current_action": "当前建议动作",
        "screening_score": "筛选适配分",
        "evidence_confidence": "证据可信度",
        "decision_label": "决策标签",
        "S_stability": "稳定性",
        "S_protection": "防护潜力",
        "S_cost": "成本友好性",
        "S_environment": "环境适配",
        "S_industry": "产业适配",
        "literature_count": "文献线索",
        "match_reason": "区域场景匹配原因",
    }
)

tab_rank, tab_chart, tab_explain = st.tabs(["候选排序", "评分结构", "证据与下一步"])

with tab_rank:
    st.dataframe(
        display[
            [
                "排名",
                "材料",
                "中文名称",
                "推荐对象类型",
                "材料体系路径",
                "化学组成标签",
                "适用工程部位",
                "材料库",
                "材料库条目",
                "外部库候选",
                "文献线索",
                "筛选适配分",
                "证据可信度",
                "当前候选池范围",
                "数据完整性",
                "证据状态",
                "当前建议动作",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with tab_chart:
    left, right = st.columns([1, 1])
    with left:
        chart = go.Figure()
        chart.add_bar(x=result["formula"], y=result["screening_score"], name="筛选适配分")
        chart.add_bar(x=result["formula"], y=result["evidence_confidence"], name="证据可信度")
        chart.update_layout(barmode="group", yaxis_title="分值", xaxis_title="候选材料", title="候选材料适配分与证据可信度")
        st.plotly_chart(chart, use_container_width=True)
    with right:
        labels = ["稳定性", "防护潜力", "成本友好性", "环境适配", "产业适配"]
        values = [top["S_stability"], top["S_protection"], top["S_cost"], top["S_environment"], top["S_industry"]]
        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]], fill="toself", name=top["formula"]))
        radar.update_layout(title=f"首选候选五维画像：{top['formula']}", polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(radar, use_container_width=True)

with tab_explain:
    st.subheader(f"3. {top['formula']} 硬质表面工程候选体系")
    st.markdown(f"**路径：** {top['material_path']}")
    st.markdown(f"**适用部位：** {top['engineering_components']}")
    st.markdown(f"**当前状态：** {top['pilot_scope']}")
    st.markdown(f"**当前区域场景匹配原因：** {top['match_reason']}")
    st.markdown(f"**材料库接入：** {top.get('source_database', '')} {top.get('source_id', '')}")
    st.markdown(f"**外部材料库候选：** {int(top.get('external_material_database_candidates', 0))} 条 Materials Project/OQMD/AFLOW 相关条目，需人工复核结构、公式和数据库字段。")
    st.markdown(f"**文献线索：** {int(top.get('literature_count', 0))} 条多源文献元数据，需人工复核全文和实验条件。")
    st.markdown(f"**数据边界：** {top['data_completeness']}；具体基体、工艺、厚度与盐雾性能证据待补充。")
    st.markdown(f"**证据状态：** {top['evidence_status']}；{top['confidence_reasons']}")
    st.markdown(f"**建议动作：** {top['current_action']}")
    st.markdown(f"**筛选依据：** {top['screening_basis']}")
    if str(top.get("source_url", "")).startswith("http"):
        st.markdown(f"[打开基础材料数据库条目]({top['source_url']})")

    st.divider()
    for _, row in result.iterrows():
        title = f"#{int(row['rank'])} {row['formula']} | {row['material_system']} | {row['pilot_scope']}"
        with st.expander(title):
            st.markdown(f"**推荐对象类型：** {row['recommendation_object_type']}")
            st.markdown(f"**材料体系路径：** {row['material_path']}")
            st.markdown(f"**化学组成标签：** {row['chemistry_tags']}")
            st.markdown(f"**适用工程部位：** {row['engineering_components']}")
            st.markdown(f"**材料库接入：** {row.get('source_database', '')} {row.get('source_id', '')}")
            st.markdown(f"**外部材料库候选：** {int(row.get('external_material_database_candidates', 0))} 条")
            st.markdown(f"**文献线索：** {int(row.get('literature_count', 0))} 条")
            st.markdown(f"**当前区域场景匹配原因：** {row['match_reason']}")
            st.markdown(f"**当前候选池范围：** {row['pilot_scope']}")
            st.markdown(f"**数据完整性：** {row['data_completeness']}")
            st.markdown(f"**证据状态：** {row['evidence_status']}")
            st.markdown(f"**当前建议动作：** {row['current_action']}")
