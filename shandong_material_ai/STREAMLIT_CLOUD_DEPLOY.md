# Streamlit Community Cloud 部署说明

本项目可以先用 Streamlit Community Cloud 做外网展示原型。该方案适合评审、演示和临时分享，不适合作为最终生产部署。

## 1. 准备 GitHub 仓库

1. 在 GitHub 新建一个仓库，例如 `shandong-material-ai`。
2. 把本项目根目录 `shandong_material_ai` 推送到该仓库。
3. 确认仓库根目录包含：
   - `app.py`
   - `requirements.txt`
   - `runtime.txt`
   - `.streamlit/config.toml`
   - `pages/`
   - `data/`
   - `assets/`
   - `scripts/`

## 2. 在 Streamlit Community Cloud 创建应用

1. 打开 https://share.streamlit.io/
2. 使用 GitHub 登录。
3. 点击 `Create app` 或 `New app`。
4. 选择刚才的 GitHub 仓库。
5. Branch 选择 `main` 或你实际使用的分支。
6. Main file path 填：

```text
app.py
```

7. 点击 Deploy。

## 3. 部署后的访问形式

部署成功后，访问地址会类似：

```text
https://你的应用名.streamlit.app
```

文献证据库、材料推荐等页面会通过 Streamlit 多页面路由访问。

## 4. 当前数据说明

当前仓库内已包含演示用 CSV 数据，因此第一次部署不需要配置外部数据库。

当前外部数据和文献数据属于原型数据：

- Materials Project / OQMD / AFLOW 条目用于材料库候选线索。
- Crossref / Europe PMC / DOI 期刊论文候选用于文献线索。
- SCI / Web of Science 收录状态仍需账号或人工复核。
- 推荐结果不能视为工程采购结论。

## 5. 可选 Secrets

当前页面展示不依赖 API Key。后续如果要在云端刷新材料库或文献数据，可在 Streamlit Cloud 的 `App settings -> Secrets` 中配置：

```toml
MP_API_KEY = "你的 Materials Project API Key"
OPENALEX_MAILTO = "你的邮箱"
OPENALEX_API_KEY = "可选"
SEMANTIC_SCHOLAR_API_KEY = "可选"
```

不要把 `.env` 或 `.streamlit/secrets.toml` 提交到 GitHub。

## 6. 常见问题

如果部署失败，优先检查：

1. `requirements.txt` 是否安装成功。
2. GitHub 仓库根目录是否就是本项目目录。
3. `app.py` 是否在仓库根目录。
4. `data/` 和 `assets/` 是否被提交。
5. 页面文件名是否完整上传。

如果页面打开但数据为空，通常是 `data/` 没有提交到 GitHub。

