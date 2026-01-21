# 健身小助手（Streamlit）打包 Android APK

这个项目是 `Streamlit`（Python）应用，**不能直接**打包成原生 Android APK。最省事、最稳定的做法是：

1. 把 Streamlit 部署到可访问的地址（推荐 HTTPS 域名）
2. 用一个 Android `WebView` 壳应用加载该地址

本仓库已提供一个 WebView 壳工程：`android_webview/`。

## 1) 先准备一个可访问的 URL

- **本机调试（模拟器）**：`http://10.0.2.2:8501/`（模拟器访问电脑 localhost 的固定地址）
- **真机同一 Wi‑Fi**：`http://<电脑局域网IP>:8501/`（手机访问你电脑上的 Streamlit）
- **线上部署（推荐）**：`https://<你的域名>/`

注意：Android 里 `localhost` 指的是 **手机自己**，不是电脑。

## 2) 配置壳应用加载的 URL

修改：`android_webview/app/src/main/res/values/strings.xml` 里的 `app_url`。

## 3) 构建 APK（推荐用 Android Studio）

1. 安装 Android Studio（包含 JDK）
2. 用 Android Studio 打开 `android_webview/`
3. 等待 Gradle Sync 完成
4. `Build` → `Build Bundle(s) / APK(s)` → `Build APK(s)`

构建产物一般在：`android_webview/app/build/outputs/apk/`

