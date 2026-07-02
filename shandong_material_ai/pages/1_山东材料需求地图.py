from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st
import sys
from html import escape


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
NO_LABEL_MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json"
sys.path.append(str(BASE_DIR))

from ui_theme import apply_theme, render_top_nav  # noqa: E402

st.set_page_config(page_title="山东材料需求地图", layout="wide")
apply_theme("map")
render_top_nav("需求地图")


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    env_path = DATA_DIR / "city_environment.csv"
    industry_path = DATA_DIR / "city_industry.csv"
    evidence_path = DATA_DIR / "public_data_evidence.csv"
    if not env_path.exists() or not industry_path.exists():
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    evidence = pd.read_csv(evidence_path) if evidence_path.exists() else pd.DataFrame()
    return pd.read_csv(env_path), pd.read_csv(industry_path), evidence


env, industry, evidence = load_data()

st.title("山东材料需求地图")
st.caption("以中文标注和沿海装备场景为核心，展示山东沿海城市环境风险、产业场景和材料需求画像。")

if env.empty or industry.empty:
    st.warning("缺少城市环境或产业数据，请先运行 scripts/initialize_data.py 或检查 data 目录。")
    st.stop()

city_options = env["city"].tolist()
if "selected_map_city" not in st.session_state or st.session_state.selected_map_city not in city_options:
    st.session_state.selected_map_city = city_options[0]

selected_city = st.session_state.selected_map_city
city_env = env[env["city"] == selected_city].iloc[0]
city_industry = industry[industry["city"] == selected_city]
city_evidence = evidence[evidence["city"] == selected_city] if not evidence.empty else pd.DataFrame()

def risk_class(value: object) -> str:
    text = str(value)
    if "高" in text:
        return "high"
    if "中" in text:
        return "mid"
    return "low"


map_data = env.copy()
map_data["is_selected"] = map_data["city"].eq(selected_city)
map_data["scene_count"] = map_data["city"].map(industry.groupby("city").size()).fillna(0).astype(int)
map_data["hit_radius"] = 12000
map_data["point_radius"] = map_data["is_selected"].map({True: 2200, False: 1200})
map_data["ring_radius"] = map_data["is_selected"].map({True: 5200, False: 0})
map_data["fill_color"] = map_data["is_selected"].map({True: [10, 118, 160, 220], False: [8, 128, 150, 175]})
map_data["ring_color"] = map_data["is_selected"].map({True: [24, 164, 184, 32], False: [24, 164, 184, 0]})
map_data["line_color"] = map_data["is_selected"].map({True: [255, 255, 255, 245], False: [255, 255, 255, 220]})
map_data["label"] = map_data["city"] + "｜" + map_data["scene_count"].astype(str) + "个场景"

hit_layer = pdk.Layer(
    "ScatterplotLayer",
    id="city-hit-points",
    data=map_data,
    get_position="[longitude, latitude]",
    get_radius="hit_radius",
    get_fill_color=[10, 118, 160, 1],
    pickable=True,
    stroked=False,
    filled=True,
    opacity=0.01,
)
ring_layer = pdk.Layer(
    "ScatterplotLayer",
    id="selected-city-ring",
    data=map_data,
    get_position="[longitude, latitude]",
    get_radius="ring_radius",
    get_fill_color="ring_color",
    get_line_color=[24, 164, 184, 95],
    line_width_min_pixels=1,
    pickable=False,
    stroked=True,
    filled=True,
)
point_layer = pdk.Layer(
    "ScatterplotLayer",
    id="city-points",
    data=map_data,
    get_position="[longitude, latitude]",
    get_radius="point_radius",
    get_fill_color="fill_color",
    get_line_color="line_color",
    line_width_min_pixels=2,
    pickable=False,
    stroked=True,
    filled=True,
    opacity=0.92,
)
view = pdk.ViewState(latitude=36.65, longitude=120.95, zoom=5.35, pitch=0)
st.caption("点击地图点位切换城市，悬浮查看环境与产业摘要。")
map_event = st.pydeck_chart(
    pdk.Deck(
        layers=[hit_layer, ring_layer, point_layer],
        initial_view_state=view,
        map_style=NO_LABEL_MAP_STYLE,
        tooltip={
            "html": """
                <div style="font-family:Microsoft YaHei, sans-serif; min-width:170px;">
                    <div style="font-size:15px;font-weight:700;margin-bottom:6px;">{city}</div>
                    <div>产业场景：{scene_count} 个</div>
                    <div>盐雾风险：{salt_spray_risk}</div>
                    <div>高湿风险：{humidity_risk}</div>
                    <div>工业污染：{industrial_pollution_risk}</div>
                </div>
            """,
            "style": {
                "backgroundColor": "rgba(10, 38, 58, 0.92)",
                "border": "1px solid rgba(148, 220, 232, 0.35)",
                "borderRadius": "8px",
                "boxShadow": "0 14px 30px rgba(15, 23, 42, 0.22)",
                "color": "#ffffff",
                "fontFamily": "Microsoft YaHei, sans-serif",
                "fontSize": "13px",
            },
        },
    ),
    use_container_width=True,
    height=520,
    on_select="rerun",
    selection_mode="single-object",
    key="demand-city-map",
)

selected_objects = map_event.selection.get("objects", {}) if map_event else {}
clicked_objects = selected_objects.get("city-hit-points", []) or selected_objects.get("city-points", [])
if clicked_objects:
    clicked_city = clicked_objects[0].get("city")
    if clicked_city in city_options and clicked_city != st.session_state.selected_map_city:
        st.session_state.selected_map_city = clicked_city
        st.rerun()

st.markdown(
    """
    <style>
    .map-detail-grid {
        margin-top: 18px;
    }
    .map-summary-copy {
        margin: 0 0 14px;
        color: #344b5e;
        line-height: 1.72;
        font-size: 0.95rem;
    }
    .risk-compact-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin-top: 10px;
    }
    .risk-compact-card {
        min-height: 86px;
        padding: 12px 14px;
        border-radius: 8px;
        border: 1px solid rgba(148, 163, 184, 0.22);
        background: rgba(255, 255, 255, 0.78);
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
        backdrop-filter: blur(10px);
    }
    .risk-compact-card span {
        display: block;
        color: #5d7284;
        font-size: 0.82rem;
        margin-bottom: 9px;
    }
    .risk-compact-card strong {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 40px;
        height: 30px;
        padding: 0 12px;
        border-radius: 999px;
        color: #ffffff;
        font-size: 1.06rem;
        line-height: 1;
        background: #1f77b4;
    }
    .risk-compact-card.high strong { background: #b84a62; }
    .risk-compact-card.mid strong { background: #b7791f; }
    .risk-compact-card.low strong { background: #2f855a; }
    .map-table-note {
        margin: 8px 0 0;
        color: #5d7284;
        font-size: 0.84rem;
    }
    @media (max-width: 900px) {
        .risk-compact-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([0.95, 1.05])
with left:
    st.subheader(f"{selected_city}环境特征")
    st.markdown(
        f"""
        <p class="map-summary-copy">{escape(str(city_env["environment_summary"]))}</p>
        <div class="risk-compact-grid">
            <div class="risk-compact-card {risk_class(city_env["salt_spray_risk"])}">
                <span>盐雾风险</span><strong>{escape(str(city_env["salt_spray_risk"]))}</strong>
            </div>
            <div class="risk-compact-card {risk_class(city_env["humidity_risk"])}">
                <span>高湿风险</span><strong>{escape(str(city_env["humidity_risk"]))}</strong>
            </div>
            <div class="risk-compact-card {risk_class(city_env["industrial_pollution_risk"])}">
                <span>工业污染风险</span><strong>{escape(str(city_env["industrial_pollution_risk"]))}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.subheader("主要产业与应用场景")
    st.dataframe(
        city_industry[["industry_type", "application_scene", "industry_priority", "material_demand"]],
        use_container_width=True,
        hide_index=True,
        height=152,
    )
    st.markdown('<p class="map-table-note">点击地图城市后，产业场景与材料需求同步切换。</p>', unsafe_allow_html=True)

st.subheader("城市材料需求画像")
scenes = "、".join(city_industry["application_scene"].tolist())
demands = "、".join(city_industry["material_demand"].drop_duplicates().tolist())
st.info(
    f"城市：{selected_city}\n\n"
    f"主要场景：{scenes}\n\n"
    f"环境特征：{city_env['salt_spray_risk']}盐雾、{city_env['humidity_risk']}高湿、"
    f"{city_env['industrial_pollution_risk']}工业污染风险\n\n"
    f"材料需求：{demands}"
)
st.caption(str(city_env["data_status"]))

st.subheader("公共数据支撑证据")
if city_evidence.empty:
    st.info("该城市暂无已整理的山东公共数据开放网目录证据。")
else:
    evidence_table = city_evidence[
        [
            "support_dimension",
            "catalog_name",
            "source_department",
            "updated_at",
            "record_count",
            "relevance_note",
            "data_status",
        ]
    ].rename(
        columns={
            "support_dimension": "支撑维度",
            "catalog_name": "公共数据目录",
            "source_department": "来源部门",
            "updated_at": "更新时间",
            "record_count": "数据量",
            "relevance_note": "用于支撑",
            "data_status": "数据状态",
        }
    )
    st.dataframe(evidence_table, use_container_width=True, hide_index=True, height=240)
    with st.expander("查看公共数据目录链接", expanded=False):
        for _, row in city_evidence.iterrows():
            st.markdown(f"- [{row['catalog_name']}]({row['source_url']})｜{row['data_status']}")
