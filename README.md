# Komari Node Manager (探针与节点管理一体化主控系统)

> **固化定制版本 (Pinned Build)**：集成 Komari 探针系统与 Sing-box 代理节点自适应管理系统，包含完整的后端 API、持久化数据库、自适应订阅分流引擎以及现代化前端面板。换机迁移时开箱即用，免除对上游破坏性更新的依赖。

![Version](https://img.shields.io/badge/Komari-v1.6.0_Custom-blue.svg)
![Architecture](https://img.shields.io/badge/Arch-amd64%20%7C%20arm64-success.svg)
![Sing-box](https://img.shields.io/badge/Sing--box-Auto_Sync-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## ⚡ 全新服务器一键安装部署

在全新的 Linux VPS（支持 Debian、Ubuntu、CentOS、AlmaLinux、Rocky、Alpine）上以 **root** 权限执行以下命令：

### 方式一：一键远程静默 / 交互安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/2290145679/komari-node-manager/main/install-hub.sh | sudo bash
```

### 方式二：克隆仓库本地安装

```bash
git clone https://github.com/2290145679/komari-node-manager.git
cd komari-node-manager
sudo bash install-hub.sh
```

> **脚本特性**：
> 1. 自动检测系统架构（支持 x86_64 / amd64 与 aarch64 / arm64）；
> 2. 自动安装 Python3、SQLite3、Nginx、Gzip 等基础系统组件；
> 3. 自动释放固化版 Komari 主控程序、后台节点管理 API 以及 Web 魔改面板；
> 4. 自动注册 Systemd 开机自启守护服务（支持崩溃自动拉起）；
> 5. 交互引导配置主控端口（默认 80）、域名绑定与管理员账号密码；
> 6. 自动初始化分流规则引擎与订阅 Token。

---

## 🌟 核心功能亮点

### 1. 探针与节点自动双向协同
- **一键纳管**：在被控端运行一条指令，即可在安装 Komari 探针监控的同时，自动安装并配置 `sing-box` 代理服务端。
- **配置热重载**：主控端后台修改节点端口、密钥或伪装域名后，被控节点定时守护脚本自动同步并无缝平滑重载核心，无需人工 SSH 登录。

### 2. 协议矩阵与外部节点统一托管
- **主流抗封锁协议**：原生支持 `VLESS-Reality`（XTLS Vision）、`Hysteria 2`（极速 UDP）、`TUIC v5`、`Trojan` 等。
- **外部节点一键导入**：支持直接粘贴外部节点链接（如 `vless://` 等）统一纳入托管，聚合分流。

### 3. 自适应分流与订阅规则引擎
- **全客户端自适应输出**：统一订阅地址自适应识别客户端 User-Agent，自动转换下发：
  - **Clash / Mihomo / Clash Verge / Party** (YAML)
  - **Shadowrocket（小火箭） / v2rayN** (Base64)
  - **Sing-box** (JSON Profile)
  - **Surge / Quantumult X / Stash**
- **可视化分流配置**：支持自定义 BT/PT 流量强制直连（防封端口）、国内域名与 IP 直连（加速访问）、广告拦截黑名单及兜底策略。

### 4. ⚡ 一键唤起客户端 & 全能扫码
- **PC / 移动端 Scheme 一键唤醒**：点击按钮直接唤醒 Clash、Shadowrocket、Sing-box 等客户端自动填入配置。
- **双模二维码**：支持扫码导入整套订阅，或针对单个自建/外部节点直接生成独立直连二维码。

### 5. 精确流量差值统计
- 自动建立节点入库流量基线，精确计算节点自被纳管以来产生的上行/下行真实流量消耗，支持实时统计重置。

---

## 🖥️ 探针节点（被控端）接入指南

主控端部署完成后，在各台需要被监控或作为代理出入口的 VPS 上执行：

```bash
wget -qO- https://<你的主控域名或IP>/install-node.sh | sudo bash -s -- -e https://<你的主控域名或IP> -t <你的AGENT_TOKEN> --disable-web-ssh
```

> **参数说明**：
> - `-e`：主控端公网访问地址（支持带端口）。
> - `-t`：在 Komari 管理后台【实例列表】点击【添加服务器】获取的专属 Token。
> - `--disable-web-ssh`：安全建议参数（禁用远程网页终端，增强安全性）。

---

## 📁 仓库代码与组件架构

```text
komari-node-manager/
├── install-hub.sh               # 全新服务器一键安装部署脚本
├── README.md                    # 本说明文档
├── bin/                         # 固化跨平台核心二进制包
│   ├── komari-linux-amd64.gz    # Komari 主控端核心 (x86_64)
│   ├── komari-linux-arm64.gz    # Komari 主控端核心 (aarch64)
│   ├── agent-linux-amd64.gz     # Komari 探针核心 (x86_64)
│   └── agent-linux-arm64.gz     # Komari 探针核心 (aarch64)
├── node-mgr/                    # 节点管理与自适应订阅后端系统
│   ├── server.py                # Python3 异步 HTTP 核心服务
│   └── schema.sql               # SQLite 数据库建表结构
├── web-patch/                   # 前端魔改补丁 (侧边栏、路由与防缓存层)
│   ├── assets/
│   │   ├── chunk-index-BfURcdSr.js
│   │   ├── chunk-_layout-KM9Ke-Y5.js
│   │   ├── chunk-plugin_page-Xen4h3Tc.js
│   │   └── komari-singbox-helper.js
│   ├── registerSW.js
│   └── sw.js
├── plugin/                      # 节点管理前端插件
│   └── node-manager/
│       ├── komari-plugin.json   # Komari 插件描述文件
│       ├── script.js            # 插件加载脚本
│       └── panel/
│           └── index.html       # 节点管理完整交互面板
├── conf/                        # 进程守护与反向代理模板
│   ├── komari.service           # Komari Systemd 守护单元
│   ├── komari-node-mgr.service  # 节点管理 Systemd 守护单元
│   └── nginx-komari.conf        # Nginx 统一反向代理网关配置
├── index.html                   # 独立运行版入口
└── panel_index.html             # 独立运行版备用面板
```

---

## 🔧 运维管理常用命令

| 操作 | 对应命令 |
| :--- | :--- |
| **查看主控状态** | `systemctl status komari` |
| **查看节点管理状态** | `systemctl status komari-node-mgr` |
| **重启所有组件** | `systemctl restart komari komari-node-mgr nginx` |
| **修改管理员密码** | `/opt/komari/komari chpasswd -p <新密码>` |
| **查看主控日志** | `journalctl -u komari -f -n 50` |
| **查看节点管理日志** | `journalctl -u komari-node-mgr -f -n 50` |

---

## 📄 开源许可证

本项目遵循 [MIT License](LICENSE) 开源协议。