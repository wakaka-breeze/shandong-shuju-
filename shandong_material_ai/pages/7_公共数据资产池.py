from pathlib import Path
import sys

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
sys.path.append(str(BASE_DIR))

from ui_theme import apply_theme, render_top_nav  # noqa: E402


st.set_page_config(page_title="公共数据资产池", layout="wide")
apply_theme("literature")
render_top_nav("公共数据")


@st.cache_data
def read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


catalog = read_csv("public_data_catalog_seed.csv")
evidence = read_csv("public_data_evidence.csv")
file_resources = read_csv("sd_public_data_file_resources.csv")
api_services = read_csv("sd_public_data_api_services.csv")

st.title("山东公共数据资产池")
st.caption("围绕材料产业、材料研发、材料应用和验证服务整理山东公共数据开放网目录，区分证据层、候选观察和禁用目录。")

if catalog.empty:
    st.warning("缺少 public_data_catalog_seed.csv。")
    st.stop()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("目录资产", len(catalog))
col2.metric("证据层", len(evidence))
col3.metric("来源部门", catalog["source_department"].nunique())
col4.metric("总数据量", f"{pd.to_numeric(catalog['record_count'], errors='coerce').fillna(0).sum():,.0f}")
col5.metric("文件资源", len(file_resources))
col6.metric("API 服务", len(api_services))

left, mid, right = st.columns([1, 1, 1])
with left:
    status_options = ["全部"] + sorted(catalog["use_status"].dropna().unique().tolist())
    status = st.selectbox("使用状态", status_options)
with mid:
    tier_options = ["全部"] + sorted(catalog["reliability_tier"].dropna().unique().tolist())
    tier = st.selectbox("可靠性等级", tier_options)
with right:
    city_options = ["全部"] + sorted(catalog["city"].dropna().unique().tolist())
    city = st.selectbox("城市", city_options)

shown = catalog.copy()
if status != "全部":
    shown = shown[shown["use_status"] == status]
if tier != "全部":
    shown = shown[shown["reliability_tier"] == tier]
if city != "全部":
    shown = shown[shown["city"] == city]

st.subheader("目录资产清单")
st.dataframe(
    shown[
        [
            "city",
            "catalog_name",
            "source_department",
            "domain",
            "updated_at",
            "record_count",
            "reliability_tier",
            "use_status",
            "intended_use",
            "quality_notes",
            "source_url",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    height=420,
)

st.subheader("证据层目录")
if evidence.empty:
    st.info("暂无进入证据层的公共数据目录。")
else:
    st.dataframe(
        evidence[
            [
                "evidence_id",
                "city",
                "support_dimension",
                "catalog_name",
                "source_department",
                "updated_at",
                "record_count",
                "relevance_note",
                "data_status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        height=360,
    )

st.subheader("已识别资源入口")
if file_resources.empty and api_services.empty:
    st.info("暂无文件资源或 API 服务清单，请先运行 fetch_sd_public_data_resources.py。")
else:
    resource_left, resource_right = st.columns([1, 1])
    with resource_left:
        st.markdown("**文件格式分布**")
        if file_resources.empty:
            st.write("暂无文件资源。")
        else:
            format_counts = file_resources["format"].fillna("unknown").value_counts().reset_index()
            format_counts.columns = ["format", "count"]
            st.dataframe(format_counts, use_container_width=True, hide_index=True)
    with resource_right:
        st.markdown("**API 服务部门分布**")
        if api_services.empty:
            st.write("暂无 API 服务。")
        else:
            dept_counts = api_services["source_department"].fillna("unknown").value_counts().reset_index()
            dept_counts.columns = ["source_department", "count"]
            st.dataframe(dept_counts, use_container_width=True, hide_index=True)

    with st.expander("查看文件资源明细", expanded=False):
        if not file_resources.empty:
            st.dataframe(
                file_resources[
                    [
                        "catalog_name",
                        "source_department",
                        "format",
                        "resource_name",
                        "file_id",
                        "status",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                height=360,
            )
