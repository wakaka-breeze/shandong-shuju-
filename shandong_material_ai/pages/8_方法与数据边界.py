from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
sys.path.append(str(BASE_DIR))

from ui_theme import apply_theme, render_top_nav  # noqa: E402

st.set_page_config(page_title="方法与数据边界", layout="wide")
apply_theme("home")
render_top_nav("方法边界")


@st.cache_data
def read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


materials = read_csv("material_candidates.csv")
literature = read_csv("literature_evidence.csv")
catalog = read_csv("public_data_catalog_seed.csv")
evidence = read_csv("public_data_evidence.csv")
file_resources = read_csv("sd_public_data_file_resources.csv")
api_services = read_csv("sd_public_data_api_services.csv")

st.title("方法与数据边界")
st.caption("把当前 demo 能证明什么、不能证明什么说清楚，系统才站得住。")

st.subheader("当前推荐公式")
st.latex(
    r"""
    Score = w_s S_{stability} + w_p S_{protection} + w_c S_{cost}
    + w_e S_{environment} + w_i S_{industry}
    """
)
st.markdown(
    """
    当前推荐是**透明规则筛选**：高/中/低等级映射为分值，叠加城市环境、产业场景和人工显式权重。
    新版推荐先按推荐对象类型、材料体系和工程部位缩小候选池，再回答“同一候选池内哪个候选更值得先复核和小试”，不是“哪个材料真实寿命更长”。
    """
)

st.subheader("多层材料分类边界")
st.markdown(
    """
    当前原型已建立可扩展的多层材料分类架构。
    首批候选池聚焦硬质表面工程材料，用于验证“区域场景—工程部位—性能约束—材料候选—验证路径”的决策链路。
    后续将逐步接入耐蚀合金、有机防腐体系、热喷涂体系、复合防护材料、二维材料增强体系及修复辅助材料。

    氧化物、氮化物、碳化物、硼化物、硫化物等只作为 `chemistry_tags` 一类的化学组成属性，不作为网站一级材料分类。
    对于尚未接入真实候选数据的材料体系，页面保留分类入口并明确显示“该体系当前尚未接入可比较候选数据”，不会伪造推荐结果。
    """
)

st.subheader("当前数据的四个层级")
data_layers = pd.DataFrame(
    [
        ["区域公共数据", len(catalog), len(evidence), "山东公共数据开放网目录、文件资源和 API 服务，主要证明区域产业/场景存在。"],
        ["候选材料库", len(materials), int((materials["source_database"] == "Materials Project").sum()) if not materials.empty else 0, "材料基础物性和来源条目，不能直接等同于涂层服役性能。"],
        ["文献线索", len(literature), literature["formula"].nunique() if not literature.empty else 0, "Crossref 元数据线索，需要人工复核全文、实验条件和基体体系。"],
        ["接口/文件资源", len(file_resources), len(api_services), "已识别山东公共数据网资源入口，后续应继续批量下载、清洗和字段建模。"],
    ],
    columns=["层级", "规模", "可用证据数", "边界"],
)
st.dataframe(data_layers, use_container_width=True, hide_index=True)

st.subheader("答辩时不要再说的句子")
bad = pd.DataFrame(
    [
        ["系统能自动发现新材料", "当前没有训练模型、真实标签和外部验证集。"],
        ["推荐分数代表耐腐蚀性能", "分数只是规则筛选适配度，不是腐蚀速率或寿命。"],
        ["公共数据证明材料需求强度", "很多目录还停留在目录级或供给侧证据，不能直接证明采购或工程需求。"],
        ["Materials Project 可证明涂层防护效果", "它提供基础物性，不等于盐雾、电化学、附着力和磨损性能。"],
    ],
    columns=["不要这样说", "原因"],
)
st.dataframe(bad, use_container_width=True, hide_index=True)

st.subheader("可以严谨地说")
good = [
    "这是一个面向山东沿海装备场景的候选材料决策支持原型。",
    "系统把区域场景证据、候选材料基础数据、文献线索和验证路径放在同一个可追溯流程里。",
    "推荐结果用于确定文献复核和小试验证优先级，不直接输出工程结论。",
    "山东公共数据网已经形成目录资产池，后续工作是批量下载明细数据、字段化清洗，并把产业需求和环境暴露量化。",
]
for item in good:
    st.markdown(f"- {item}")

st.subheader("最短的数据升级路线")
st.markdown(
    """
    1. 从公共数据目录走到**明细字段**：年份、装备数量、行业规模、区域分布、企业/项目清单。  
    2. 从 Crossref 线索走到**可复核实验字段**：基体、涂层厚度、制备工艺、盐雾时长、腐蚀电流密度、阻抗、附着力。  
    3. 从规则权重走到**可校准模型**：有真实实验标签后，再谈回归、排序学习或贝叶斯优化。  
    4. 从 demo 页面走到**数据闭环**：每个结论都能追溯到目录、文件、接口、文献或实验记录。  
    """
)

st.info(
    "下一阶段最值得补的不是更多页面，而是可批量复用的数据管道：山东公共数据下载、材料文献抽取、实验字段模板和证据质量评分。"
)
