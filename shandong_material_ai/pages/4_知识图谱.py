from pathlib import Path
import sys

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
sys.path.append(str(BASE_DIR))

from ui_theme import apply_theme, render_top_nav  # noqa: E402

st.set_page_config(page_title="知识图谱", layout="wide")
apply_theme("graph")
render_top_nav("知识图谱")


@st.cache_data
def load_graph() -> tuple[pd.DataFrame, pd.DataFrame]:
    node_path = DATA_DIR / "knowledge_nodes.csv"
    edge_path = DATA_DIR / "knowledge_edges.csv"
    if not node_path.exists() or not edge_path.exists():
        return pd.DataFrame(), pd.DataFrame()
    return pd.read_csv(node_path), pd.read_csv(edge_path)


nodes, edges = load_graph()
st.title("知识图谱")
st.caption("CSV + networkx 轻量展示城市、环境、产业、场景、材料类别和候选材料关系。")

if nodes.empty or edges.empty:
    st.warning("缺少知识图谱数据，请运行 scripts/initialize_data.py。")
    st.stop()

city_options = ["全部"] + sorted([x for x in nodes["city"].dropna().unique().tolist() if x])
material_options = ["全部"] + sorted([x for x in nodes["material"].dropna().unique().tolist() if x])

left, right = st.columns([1, 1])
with left:
    selected_city = st.selectbox("按城市筛选", city_options)
with right:
    selected_material = st.selectbox("按材料筛选", material_options)

filtered_edges = edges.copy()
if selected_city != "全部":
    filtered_edges = filtered_edges[(filtered_edges["city"] == selected_city) | (filtered_edges["city"].isna()) | (filtered_edges["city"] == "")]
if selected_material != "全部":
    filtered_edges = filtered_edges[(filtered_edges["material"] == selected_material) | (filtered_edges["material"].isna()) | (filtered_edges["material"] == "")]

included_ids = set(filtered_edges["source"]).union(set(filtered_edges["target"]))
filtered_nodes = nodes[nodes["node_id"].isin(included_ids)].copy()

graph = nx.Graph()
for _, row in filtered_nodes.iterrows():
    graph.add_node(row["node_id"], label=row["label"], node_type=row["node_type"])
for _, row in filtered_edges.iterrows():
    if row["source"] in included_ids and row["target"] in included_ids:
        graph.add_edge(row["source"], row["target"], relation=row["relation"], description=row["description"])

if graph.number_of_nodes() == 0:
    st.warning("当前筛选条件下没有关系，请调整筛选条件。")
    st.stop()

pos = nx.spring_layout(graph, seed=42, k=0.7)
edge_x, edge_y = [], []
for source, target in graph.edges():
    x0, y0 = pos[source]
    x1, y1 = pos[target]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]

node_x, node_y, node_text, node_color = [], [], [], []
color_map = {
    "城市": "#1f77b4",
    "环境": "#ff7f0e",
    "产业": "#2ca02c",
    "应用场景": "#9467bd",
    "性能需求": "#d62728",
    "材料类别": "#8c564b",
    "候选材料": "#17becf",
}
for node_id in graph.nodes():
    x, y = pos[node_id]
    meta = graph.nodes[node_id]
    node_x.append(x)
    node_y.append(y)
    node_text.append(f"{meta['label']}<br>{meta['node_type']}")
    node_color.append(color_map.get(meta["node_type"], "#7f7f7f"))

fig = go.Figure()
fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1, color="#b8c2cc"), hoverinfo="none"))
fig.add_trace(
    go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=[text.split("<br>")[0] for text in node_text],
        hovertext=node_text,
        hoverinfo="text",
        textposition="top center",
        marker=dict(size=18, color=node_color, line=dict(width=1, color="#ffffff")),
    )
)
fig.update_layout(height=680, showlegend=False, margin=dict(l=10, r=10, t=20, b=10), xaxis=dict(visible=False), yaxis=dict(visible=False))
st.plotly_chart(fig, use_container_width=True)

st.subheader("关系说明")
relation_df = filtered_edges[["source", "relation", "target", "description"]].head(80)
st.dataframe(relation_df, use_container_width=True, hide_index=True)
