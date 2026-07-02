# 山东沿海产业材料智能推荐平台

本项目是一个可本地运行的 Python Streamlit 网站原型，聚焦山东沿海装备场景下的耐环境防护材料候选筛选。系统不是泛材料百科，也不是腐蚀速率预测系统，而是将山东公共数据、区域环境、产业场景、候选材料库、文献线索和可解释评分连接起来，为后续文献复核与实验验证提供初筛线索。

## 项目目标

- 覆盖青岛、烟台、威海、日照四个山东沿海城市。
- 覆盖海洋装备、海上风电设备、港口机械、海洋牧场装备等应用场景。
- 建立推荐对象类型、材料体系/技术路线、工程部位、化学组成标签组成的多层分类架构。
- 首批候选池聚焦硬质表面工程材料，用于验证“区域场景—工程部位—性能约束—材料候选—验证路径”的决策链路。
- 使用透明规则模型输出 Top 10 候选材料、筛选适配分、证据可信度、推荐理由和限制说明。
- 为后续接入 Materials Project、OQMD、AFLOW 和实验数据预留字段与脚本模板。

## 技术路线

- Python 3
- Streamlit
- pandas
- plotly
- pydeck
- networkx
- CSV 本地数据存储
- scikit-learn 仅作为后续扩展依赖，不在当前版本中训练复杂模型

## UI 来源说明

本项目直接采用并改写了 Uiverse 的开源 UI 元素思想与 CSS 组件类型，包括 glassmorphism cards、gradient buttons 和 CSS tooltip chips。Uiverse 首页说明其 UI elements 以 MIT License 发布，并可用于个人和商业用途。项目中相关实现位于 `ui_theme.py`，已按 Streamlit DOM 结构适配。

参考来源：

- https://uiverse.io/
- https://uiverse.io/ui/glassmorphism-cards
- https://uiverse.io/ui/gradient-buttons
- https://uiverse.io/ui/css-tooltips

## 项目目录

```text
shandong_material_ai/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── city_environment.csv
│   ├── city_industry.csv
│   ├── material_candidates.csv
│   ├── scenario_rules.csv
│   ├── material_scores.csv
│   ├── knowledge_nodes.csv
│   ├── knowledge_edges.csv
│   ├── public_data_catalog_seed.csv
│   ├── public_data_evidence.csv
│   ├── sd_public_data_file_resources.csv
│   └── sd_public_data_api_services.csv
├── scripts/
│   ├── initialize_data.py
│   ├── score_materials.py
│   ├── recommendation_engine.py
│   ├── fetch_sd_public_data_resources.py
│   ├── build_knowledge_graph.py
│   └── fetch_materials_template.py
├── pages/
│   ├── 1_山东材料需求地图.py
│   ├── 2_材料智能推荐.py
│   ├── 3_材料详情页.py
│   ├── 4_知识图谱.py
│   ├── 7_公共数据资产池.py
│   └── 8_方法与数据边界.py
└── assets/
    └── placeholder.txt
```

## 第一版资产补充

本项目已从第一版 `shandong_material_opportunity_platform.zip` 导入可复用资产，转换为第二版可读取的 CSV：

- `data/material_route_rules.csv`：材料研发路线规则
- `data/candidate_material_systems.csv`：候选材料体系规则
- `data/rd_path_rules.csv`：研发验证路径步骤
- `data/service_capability_rules.csv`：验证服务能力关键词
- `data/opportunity_cards_sample.csv`：第一版机会卡样例
- `data/first_version_asset_manifest.csv`：导入清单

这些数据中，规则库可以用于页面逻辑和研发路径建议；机会卡样例必须标注为“示例/待审核”，不能作为真实产业结论。

重新导入命令：

```bash
python scripts/import_first_version_assets.py
```

## 本地安装与运行

Windows PowerShell 下进入项目目录：

```bash
cd shandong_material_ai
pip install -r requirements.txt
python scripts/initialize_data.py
streamlit run app.py
```

启动后浏览器通常会打开：

```text
http://localhost:8501
```

## 数据说明

当前版本中的城市环境、产业画像、材料等级和推荐结果均为原型示例数据或待接入真实数据库字段。真实材料性质数据必须来自官方数据库或可追溯文献；不得为了展示效果而伪造 Materials Project、OQMD、AFLOW 数据。

## 山东公共数据接入原则

项目新增两层公共数据表，避免为了贴合 demo 而把弱相关目录当成证据：

- `data/public_data_catalog_seed.csv`：山东公共数据开放网目录资产池，记录目录名称、来源部门、更新时间、数据量、开放格式、链接、可靠性分层和使用状态。
- `data/public_data_evidence.csv`：可进入页面和模型解释的证据层，只保留与当前城市、产业、环境画像直接相关或明确可作为供给侧证据的目录。

使用规则：

- A/B 级目录可以进入证据层，但仍需下载明细数据后复核字段、时间口径、单位、缺失值和重复项。
- C 级目录只能作为候选观察或宏观背景，不得直接支撑材料需求结论。
- D 级目录禁止进入证据层。
- 页面中的风险等级和材料需求判断必须保留边界说明，不能把目录元数据等同于真实腐蚀速率、企业采购需求或材料性能结论。

校验命令：

```bash
python scripts/validate_public_data_sources.py
```

原始数据采集命令：

```bash
# 先试跑 3 个证据层目录，只抓资源清单和 API 服务清单
python scripts/fetch_sd_public_data_resources.py --evidence-only --limit 3

# 下载证据层目录的最新 csv/json/xlsx 文件到 data/raw/sd_public_data/
python scripts/fetch_sd_public_data_resources.py --evidence-only --download --formats csv,json,xlsx
```

采集脚本会生成：

- `data/sd_public_data_file_resources.csv`：文件资源清单
- `data/sd_public_data_api_services.csv`：API 服务清单与入参/出参描述
- `data/sd_public_data_ingest_audit.csv`：下载与资源采集审计表
- `data/raw/sd_public_data/`：原始文件保存目录

注意：山东公共数据开放网部分目录虽然展示 `csv/json/xlsx` 等文件资源，但直接下载可能返回“当前限制类型文件无权限下载”。脚本会把这类情况标记为 `blocked_or_requires_permission`，并保留 `.blocked.json` 响应；这类目录后续需要走平台登录、申请授权或 API 服务调用路径。

项目新增 `data/literature_evidence.csv`，由 `scripts/fetch_literature_crossref.py` 通过 Crossref 元数据接口按候选材料检索生成。该表只作为文献线索库，字段包括题名、期刊/来源、年份、DOI、URL 和摘要片段。文献线索需要人工复核题名、摘要、全文、实验条件和材料体系后，才能作为正式证据引用。

抓取文献元数据：

```bash
python scripts/fetch_literature_crossref.py
```

材料表保留以下来源字段：

- `source_database`
- `source_id`
- `source_url`
- `data_status`

如果真实数据库尚未接入，字段必须标注为：

- `待接入真实数据库`
- `示例数据，仅用于界面测试`

新版材料表新增以下字段，多个标签使用 `|` 分隔：

- `recommendation_object_type`
- `material_system`
- `chemistry_tags`
- `engineering_components`
- `protection_mechanisms`
- `process_route`
- `applicable_scale`
- `pilot_scope`
- `data_completeness`
- `evidence_status`

当前已有候选材料统一归入 `表面工程与防护涂层 / 陶瓷与硬质涂层`，氧化物、氮化物、碳化物、多元氮化物等作为 `chemistry_tags` 展示，不再作为一级材料分类。尚未接入真实候选数据的材料体系会保留入口并显示“该体系当前尚未接入可比较候选数据”，不会生成伪推荐结果。

## 透明筛选与证据可信度

模型名称：

```text
Shandong Coastal Material Suitability Score
山东沿海装备材料适配度评分
简称：SCMS
```

默认总分公式：

```text
Score =
0.25 * S_stability
+ 0.30 * S_protection
+ 0.20 * S_cost
+ 0.15 * S_environment
+ 0.10 * S_industry
```

当前推荐页使用 `scripts/recommendation_engine.py`，将两类分数分开展示：

- `screening_score`：候选材料与城市、场景、成本和材料属性的筛选适配分。
- `evidence_confidence`：材料来源、文献线索、基础物性字段和公共数据目录支撑形成的证据可信度。

等级换算规则如下：

```text
高 = 90
中 = 70
低 = 50
```

成本等级反向计分：

```text
低成本 = 90
中成本 = 70
高成本 = 50
```

这些分数仅用于候选排序和界面演示，不代表真实腐蚀速率、真实 DFT 计算结果或真实服役寿命。

## 科学边界与局限性

当前推荐结果为区域环境、材料类别特征和候选材料数据库驱动的初步筛选结果，不等同于真实腐蚀速率预测。后续仍需通过涂层制备、电化学腐蚀测试、盐雾测试和附着力测试进一步验证。

实际性能还受涂层制备工艺、孔隙率、厚度、附着力、基体材料、盐雾浓度、电化学环境和温度等因素影响。

## 真实数据接入预留

`scripts/fetch_materials_template.py` 提供真实材料数据库接入模板。`scripts/fetch_materials_from_mp.py` 可从 Materials Project 官方 API 拉取候选材料数据。

API Key 应放在 `.env` 或系统环境变量中，不要写死在代码中：

```powershell
$env:MP_API_KEY="你的 Materials Project API Key"
python scripts\fetch_materials_from_mp.py
python scripts\initialize_data.py
```

后续可接入字段包括：

- `formula`
- `material_id`
- `formation_energy_per_atom`
- `energy_above_hull`
- `band_gap`
- `density`
- `elastic properties`

抓取到的真实数据应更新到 `data/material_candidates.csv`，并同步填写来源字段。

## 后续升级方向

1. 接入山东公共数据开放平台真实环境与产业数据。
2. 接入 Materials Project / OQMD / AFLOW 真实材料性质。
3. 引入文献或实验腐蚀数据。
4. 使用机器学习预测耐腐蚀相关代理指标。
5. 将推荐结果用于实验验证，例如盐雾测试、电化学测试、附着力测试。
