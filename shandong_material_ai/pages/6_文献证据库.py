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

st.set_page_config(page_title="文献证据库", layout="wide")
apply_theme("literature")
render_top_nav("文献证据")


@st.cache_data
def read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


literature = read_csv("literature_evidence_multi_source.csv")
if literature.empty:
    literature = read_csv("literature_evidence.csv")
materials = read_csv("material_candidates.csv")
for column in ["discovery_scope", "topic", "material_system_hint"]:
    if column not in literature.columns:
        literature[column] = ""

st.title("文献证据库")
st.caption("按候选材料关联 Crossref、Europe PMC 与 DOI 期刊论文候选线索，作为后续 SCI/WoS 人工复核、全文精读和实验指标抽取入口。")
st.warning("本页展示的是公开文献元数据与 SCI 风格候选线索；是否被 Web of Science / SCI 收录仍需账号或人工复核，不代表系统已经完成全文审读、实验数据抽取或结论认证。")

if literature.empty:
    st.info("暂无文献元数据。请运行 `python scripts/fetch_external_evidence_sources.py` 后刷新页面。")
    st.stop()

formulas = ["全部"] + sorted(literature["formula"].dropna().unique().tolist())
selected_formula = st.selectbox("按材料 / 拓展主题筛选", formulas)
shown = literature if selected_formula == "全部" else literature[literature["formula"] == selected_formula]
topic_count = int(shown["discovery_scope"].fillna("").astype(str).str.contains("拓展主题").sum())

ui_components.render_compact_stats(
    [
        ("文献线索数", len(shown)),
        ("覆盖材料/主题数", shown["formula"].nunique()),
        ("含 DOI 记录", int(shown["doi"].fillna("").astype(str).str.len().gt(0).sum())),
        ("拓展主题线索", topic_count),
    ],
    columns=4,
)

count_by_formula = shown.groupby("formula", as_index=False).size().rename(columns={"size": "count"})
if not count_by_formula.empty:
    fig = px.bar(count_by_formula, x="formula", y="count", title="材料与拓展主题文献线索数量")
    fig.update_layout(xaxis_title="材料 / 拓展主题", yaxis_title="文献线索数")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("文献线索列表")
columns = [
    "evidence_id",
    "formula",
    "material_system_hint",
    "title",
    "journal",
    "year",
    "doi",
    "url",
    "evidence_type",
    "data_status",
]
table = shown[[column for column in columns if column in shown.columns]].copy()
st.dataframe(table, use_container_width=True, hide_index=True)

st.subheader("证据卡片")
for _, row in shown.head(20).iterrows():
    with st.expander(f"{row['formula']}｜{row['title'][:80]}"):
        st.write(f"期刊/来源：{row.get('journal', '')}")
        st.write(f"年份：{row.get('year', '')}")
        st.write(f"DOI：{row.get('doi', '')}")
        if str(row.get("url", "")).strip():
            st.markdown(f"[打开来源链接]({row['url']})")
        snippet = str(row.get("abstract_snippet", "")).strip()
        if snippet and snippet != "nan":
            st.write(snippet)
        st.caption(row["data_status"])

with st.expander("材料数据库交叉查看", expanded=False):
    if materials.empty:
        st.write("暂无材料数据库。")
    else:
        merged = literature.groupby("formula", as_index=False).size().rename(columns={"size": "literature_count"})
        view = materials.merge(merged, on="formula", how="left")
        view["literature_count"] = view["literature_count"].fillna(0).astype(int)
        st.dataframe(
            view[["formula", "category", "source_database", "source_id", "data_status", "literature_count"]],
            use_container_width=True,
            hide_index=True,
        )
