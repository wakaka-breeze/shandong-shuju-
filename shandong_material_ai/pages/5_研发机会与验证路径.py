from pathlib import Path
import importlib
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
sys.path.append(str(BASE_DIR))

import ui_components  # noqa: E402
from ui_theme import apply_theme, render_top_nav  # noqa: E402

ui_components = importlib.reload(ui_components)

st.set_page_config(page_title="研发机会与验证路径", layout="wide")
apply_theme("validation")
render_top_nav("验证路径")


@st.cache_data
def read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


routes = read_csv("material_route_rules.csv")
systems = read_csv("candidate_material_systems.csv")
rd_steps = read_csv("rd_path_rules.csv")
service_rules = read_csv("service_capability_rules.csv")
opportunities = read_csv("opportunity_cards_sample.csv")
manifest = read_csv("first_version_asset_manifest.csv")

st.title("研发机会与验证路径建议")
st.caption("复用第一版中的规则库和样例机会卡，辅助从产业需求走向材料体系与实验验证。")

st.warning(
    "本页导入的是第一版规则资产和示例机会卡。规则可用于需求识别和路径建议；机会卡样例不是已核验真实产业结论，"
    "不能替代企业调研、公开来源核验、专利文献检索和实验验证。"
)

if routes.empty or systems.empty or rd_steps.empty:
    st.error("缺少第一版导入数据，请先运行 scripts/import_first_version_assets.py。")
    st.stop()

route_names = routes["route_name"].tolist()
default_index = 0
for index, name in enumerate(route_names):
    if "耐环境防护" in name:
        default_index = index
        break

selected_route_name = st.selectbox("选择材料研发路线", route_names, index=default_index)
route = routes[routes["route_name"] == selected_route_name].iloc[0]
route_systems = systems[systems["material_route_id"] == route["route_id"]]
route_opps = opportunities[opportunities["material_route_id"] == route["route_id"]] if not opportunities.empty else pd.DataFrame()

ui_components.render_compact_stats(
    [
        ("路线编号", route["route_id"]),
        ("候选体系数", len(route_systems)),
        ("样例机会卡数", len(route_opps)),
        ("验证能力类别", len(service_rules)),
    ],
    columns=4,
)

st.subheader("路线规则")
left, right = st.columns([1, 1])
with left:
    st.markdown("**触发关键词**")
    st.write(route["trigger_keywords"])
    st.markdown("**工程需求**")
    st.write(route["engineering_needs"])
with right:
    st.markdown("**目标性能**")
    st.write(route["performance_targets"])
    st.markdown("**建议验证关键词**")
    st.write(route["verification_keywords"])

st.subheader("候选材料体系")
if route_systems.empty:
    st.info("该路线暂无候选材料体系规则。")
else:
    st.dataframe(
        route_systems[
            [
                "system_id",
                "system_name",
                "target_properties",
                "advantages",
                "limitations",
                "suggested_validation_tests",
                "evidence_level",
                "data_status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("研发验证路径")
for _, step in rd_steps.iterrows():
    with st.expander(f"{step['step_id']}｜{step['step_name']}", expanded=step["step_id"] in ["RD-01", "RD-02", "RD-05"]):
        st.write(step["objective"])
        st.markdown("**输出物**")
        st.write(step["outputs"])
        st.caption(step["data_status"])

st.subheader("验证服务能力关键词")
if service_rules.empty:
    st.info("暂无服务能力规则。")
else:
    st.dataframe(service_rules[["category", "keywords", "data_status"]], use_container_width=True, hide_index=True)

st.subheader("第一版机会卡样例")
if route_opps.empty:
    st.info("该路线暂无第一版机会卡样例。")
else:
    city_filter = st.selectbox("按城市筛选样例", ["全部"] + sorted(route_opps["city"].dropna().unique().tolist()))
    shown = route_opps if city_filter == "全部" else route_opps[route_opps["city"] == city_filter]
    st.dataframe(
        shown[
            [
                "opportunity_id",
                "city",
                "industry",
                "opportunity_name",
                "engineering_needs",
                "performance_targets",
                "opportunity_score",
                "opportunity_level",
                "manual_review_status",
                "data_status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    chart_data = shown.copy()
    chart_data["opportunity_score"] = pd.to_numeric(chart_data["opportunity_score"], errors="coerce").fillna(0)
    fig = px.bar(
        chart_data.head(12),
        x="opportunity_score",
        y="opportunity_name",
        color="city",
        orientation="h",
        title="样例机会卡评分，仅用于界面演示",
    )
    fig.update_layout(yaxis_title="", xaxis_title="机会评分")
    st.plotly_chart(fig, use_container_width=True)

with st.expander("导入资产清单", expanded=False):
    if manifest.empty:
        st.write("暂无导入清单。")
    else:
        st.dataframe(manifest, use_container_width=True, hide_index=True)
