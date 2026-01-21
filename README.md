# 健身小助手（Streamlit）

本项目是一个基于 Streamlit 的健身记录/周报/AI 建议小工具。

## 本地运行

```powershell
python -m streamlit run app.py
```

可选：在同目录放置 `.env`（不要提交到 Git）：

```env
OPENAI_API_KEY="你的key"
OPENAI_BASE_URL="https://api.deepseek.com"
OPENAI_MODEL="deepseek-chat"
```

## 部署到 Streamlit Community Cloud（公网访问）

1. 将本仓库推到 GitHub（公开仓库即可）
2. 打开 Streamlit Cloud 并选择该仓库部署，入口文件选 `app.py`
3. 在 Streamlit Cloud 的 **Secrets** 中配置（推荐）：

```toml
OPENAI_API_KEY="你的key"
OPENAI_BASE_URL="https://api.deepseek.com"
OPENAI_MODEL="deepseek-chat"
```

部署完成后会得到一个 `*.streamlit.app` 的公网地址。

## Android APK（WebView 壳）

见 `ANDROID_APK.md`（`android_webview/` 只是加载网页的壳，真正的应用仍是公网/局域网中的 Streamlit 服务）。

