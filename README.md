# Komari Node Manager (多服务器节点管理面板)

简洁、现代、响应式的多服务器代理节点集中管理面板。支持与 Komari 探针状态同步，快捷下发配置并生成自适应订阅。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3-38bdf8.svg)
![HTML5](https://img.shields.io/badge/HTML5-Single_Page-orange.svg)

---

## ✨ 核心特性

- 🚀 **多协议支持**：支持 `VLESS-Reality`（免域名强抗封锁）、`Hysteria 2`（极速 UDP/QUIC）、`TUIC v5` 以及 `Trojan` 协议。
- 📊 **多服务器协同**：集中展示各节点状态、监听端口与伪装域名 (SNI)。
- 🔗 **统一订阅与二维码**：一键生成自适应客户端订阅链接，支持直接弹窗展示节点二维码与快速复制导入。
- 🎨 **现代化 UI**：基于 Tailwind CSS 与 Lucide 图标设计，支持自适应深色/浅色模式，交互丝滑。
- 📦 **开箱即用**：纯前端单页面应用（SPA），无需复杂构建，双击 `index.html` 或通过 GitHub Pages 即可直接托管。

---

## 🛠️ 快速开始

### 方式一：本地直接打开
直接双击打开项目根目录下的 `index.html` 即可使用。

### 方式二：部署到 GitHub Pages (免费公网访问)
1. 进入本仓库页面，点击右上角的 **Settings**。
2. 在左侧菜单点击 **Pages**。
3. 在 **Build and deployment** 下方的 **Branch** 选择 `main` 分支，路径选择 `/ (root)`，点击 **Save**。
4. 等待 1~2 分钟，即可获得 GitHub 自动分配的公网在线管理页面链接。

---

## 📁 文件结构

```text
├── index.html         # 核心面板页面（默认入口）
├── panel_index.html   # 备用面板页面文件
└── README.md          # 项目说明文档
```

---

## 📄 开源许可

本项目遵循 [MIT License](LICENSE) 开源协议。
