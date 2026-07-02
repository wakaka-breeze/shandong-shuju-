from pathlib import Path

import pandas as pd
import streamlit as st

from ui_theme import apply_theme, render_top_nav


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


st.set_page_config(
    page_title="山东沿海产业材料智能推荐平台",
    page_icon="SCMS",
    layout="wide",
)

apply_theme("home")
render_top_nav("首页")


@st.cache_data
def read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def metric_card(label: str, value: int | str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    .hero {
        padding: 38px 34px;
        border-left: 6px solid #1f77b4;
        background:
            linear-gradient(90deg, rgba(255, 255, 255, 0.96) 0%, rgba(238, 244, 250, 0.70) 48%, rgba(238, 244, 250, 0.16) 100%),
            var(--coastal-bg-image);
        background-size: cover;
        background-position: center right;
        border-radius: 8px;
        margin-bottom: 18px;
        box-shadow: 0 12px 36px rgba(15, 23, 42, 0.08);
    }
    .hero h1 { color: #102a43; font-size: 2.1rem; margin-bottom: 8px; }
    .hero p { color: #486581; font-size: 1.02rem; max-width: 760px; }
    .metric-card {
        background: rgba(255,255,255,0.88);
        border: 1px solid #d9e2ec;
        border-radius: 8px;
        padding: 18px;
        min-height: 104px;
    }
    .metric-label { color: #52616b; font-size: 0.94rem; }
    .metric-value { color: #0b3954; font-size: 2rem; font-weight: 700; margin-top: 8px; }
    .flow {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        margin: 12px 0 20px;
    }
    .flow-step {
        background: rgba(255,255,255,0.88);
        border: 1px solid #d9e2ec;
        border-radius: 8px;
        padding: 14px;
        min-height: 78px;
        color: #102a43;
        font-weight: 600;
        text-align: center;
    }
    .notice {
        background: rgba(255,248,230,0.94);
        border: 1px solid #f2d27a;
        border-radius: 8px;
        padding: 16px 18px;
        color: #604600;
    }
    @media (max-width: 900px) {
        .flow { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


env = read_csv("city_environment.csv")
industry = read_csv("city_industry.csv")
materials = read_csv("material_candidates.csv")
scores = read_csv("material_scores.csv")
routes = read_csv("material_route_rules.csv")
systems = read_csv("candidate_material_systems.csv")
rd_steps = read_csv("rd_path_rules.csv")
literature = read_csv("literature_evidence_multi_source.csv")
if literature.empty:
    literature = read_csv("literature_evidence.csv")
public_evidence = read_csv("public_data_evidence.csv")
file_resources = read_csv("sd_public_data_file_resources.csv")

st.markdown(
    """
    <div class="hero">
        <h1>山东沿海产业材料智能推荐平台</h1>
        <p>区域公共数据 x 产业场景 x 材料数据库 x 文献线索 x 可解释评分，为耐环境防护材料候选筛选和验证优先级提供依据。</p>
        <div class="uiverse-chip-row">
            <span class="uiverse-chip" data-tip="Materials Project 官方 API 已接入部分候选材料基础物性。">Materials Project</span>
            <span class="uiverse-chip" data-tip="Crossref 文献元数据仅作为线索，需要人工复核全文和实验条件。">Crossref Evidence</span>
            <span class="uiverse-chip" data-tip="SCMS 是可解释候选筛选评分，不是真实腐蚀速率预测。">SCMS Score</span>
            <span class="uiverse-chip" data-tip="已接入山东公共数据开放网目录、文件资源和 API 服务清单。">Shandong Public Data</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

cols = st.columns(6)
with cols[0]:
    metric_card("覆盖城市数", len(env["city"].unique()) if not env.empty else 0)
with cols[1]:
    metric_card("产业场景数", len(industry["application_scene"].unique()) if not industry.empty else 0)
with cols[2]:
    metric_card("候选材料数", len(materials) if not materials.empty else 0)
with cols[3]:
    metric_card("公共证据目录", len(public_evidence) if not public_evidence.empty else 0)
with cols[4]:
    metric_card("文件资源清单", len(file_resources) if not file_resources.empty else 0)
with cols[5]:
    metric_card("文献线索数", len(literature) if not literature.empty else 0)

st.subheader("项目流程")
st.markdown(
    """
    <div class="flow">
        <div class="flow-step">区域环境数据</div>
        <div class="flow-step">产业需求画像</div>
        <div class="flow-step">候选材料数据库</div>
        <div class="flow-step">透明规则筛选</div>
        <div class="flow-step">证据链与验证路径</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
        <div class="notice">
    本系统为材料候选筛选与区域场景适配工具，不等同于真实腐蚀速率预测系统。
    当前原型已建立可扩展的多层材料分类架构，首批候选池聚焦硬质表面工程材料，用于验证“区域场景—工程部位—性能约束—材料候选—验证路径”的决策链路；
    后续将逐步接入耐蚀合金、有机防腐体系、热喷涂体系、复合防护材料、二维材料增强体系及修复辅助材料。
    Materials Project 字段仅代表官方数据库基础物性，不代表涂层真实耐腐蚀性能。
    第一版导入资产用于材料路线、研发机会和验证路径建议，示例机会卡不作为已核验产业结论。
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1, 1])
with left:
    real_mp_count = int((materials["source_database"] == "Materials Project").sum()) if not materials.empty and "source_database" in materials.columns else 0
    st.markdown(
        f"""
        <div class="uiverse-glass-panel">
            <h3>数据状态</h3>
            <p>已接入 Materials Project 官方 API 条目：<strong>{real_mp_count}</strong></p>
            <p>已抓取 Crossref 文献线索：<strong>{len(literature) if not literature.empty else 0}</strong></p>
            <p>已纳入山东公共数据证据：<strong>{len(public_evidence) if not public_evidence.empty else 0}</strong></p>
            <p>已识别公共数据文件资源：<strong>{len(file_resources) if not file_resources.empty else 0}</strong></p>
            <p>研发路径步骤规则：<strong>{len(rd_steps) if not rd_steps.empty else 0}</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
        <div class="uiverse-glass-panel">
            <h3>科学边界</h3>
            <p>真实材料性质必须来自官方数据库或可追溯文献。</p>
            <p>示例机会卡、规则命中和路线建议需要人工审核与实验验证。</p>
            <p>后续重点应补充盐雾、电化学、附着力、硬度、磨损率和制备工艺数据。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.expander("候选材料来源概览", expanded=False):
    if materials.empty:
        st.write("暂无材料数据。")
    else:
        st.dataframe(materials[["formula", "category", "source_database", "source_id", "data_status"]], use_container_width=True)
