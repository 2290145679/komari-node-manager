# Komari Node Manager (探针与节点管理一体化主控系统)

> **固化定制版本 (Pinned Build)**：集成 Komari 探针系统与 Sing-box 代理节点自适应管理系统，包含完整的后端 API、持久化数据库、自适应订阅分流引擎以及现代化前端面板。换机迁移时开箱即用，免除对上游破坏性更新的依赖。

![Version](https://img.shields.io/badge/Komari-v1.6.0_Custom-blue.svg)
![Architecture](https://img.shields.io/badge/Arch-amd64%20%7C%20arm64-success.svg)
![Sing-box](https://img.shields.io/badge/Sing--box-Auto_Sync-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## ⚡ 全新服务器一键安装部署

在全新的 Linux VPS（支持 Debian、Ubuntu、CentOS、AlmaLinux、Rocky、Alpine）上以 **root** 权限执行以下命令：

### 方式一：一键远程交互安装（推荐）

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/2290145679/komari-node-manager/main/install-hub.sh)
```
*或使用管道安装（全自动兼容终端交互与默认值）：*
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
> 6. 自动初始化分流规则引擎与订阅 Token；
> 7. 自动配置专属终端管理指令 `hhub`。

---

## 🛠️ 主控端终端管理菜单 (hhub)

主控端部署完成后，已内置终端快捷管理命令 `hhub`。在服务器任意终端中直接输入：

```bash
hhub
```

即可调出可视化控制中心，随时进行以下设置与管理：
- **服务状态与控制**：实时监控核心运行状态，一键启动、停止、重启 Komari、节点管理与 Nginx 服务；
- **实时日志诊断**：查看 Komari 核心、节点管理服务以及 Nginx 的实时输出日志；
- **域名与网络配置**：
  - **更改绑定域名**：自动更新 Nginx 反代与服务配置，并可一键申请 Let's Encrypt SSL 证书；
  - **不使用域名（纯公网 IP 访问）**：一键关闭域名绑定并移除 SSL 强制跳转，恢复纯 IP HTTP 直连；
  - **更改 Web 访问端口**：自选任意端口，自动同步 Nginx 并放行防火墙端口；
  - **SSL 证书续签**：一键重新签发或续期证书；
- **一键在线更新**：安全拉取 GitHub 最新前端优化补丁（手机端对称卡片、发光指示灯等）与核心组件，**数据库与配置安全无损**；
- **数据管理与备份**：一键备份与还原数据库（`nodes.db` / `komari.db`），重置/查看统一分流订阅 Token；
- **重置管理员密码**：忘记密码时一键重置用户记录，回到初始管理员创建向导；
- **完全卸载**：一键清理所有服务与文件，支持选择是否保留历史数据。

---

## 🌟 核心功能亮点

### 1. 探针与节点自动双向协同 (Komari Pro 独立隔离)
- **环境隔离**：默认部署至 `/opt/komari-pro`，服务单元采用 `komari-pro` 专属命名，与服务器原有官方 Komari 探针完全隔离、零冲突！
- **一键纳管**：在被控端运行一条指令，即可在安装 Komari 探针监控的同时，自动安装并配置 `sing-box` 代理服务端。
- **配置热重载**：主控端后台修改节点端口、密钥或伪装域名后，被控节点定时守护脚本自动同步并无缝平滑重载核心，无需人工 SSH 登录。

### 2. 独立用户自助服务中心 (User Portal)
- **用户前台直达**：访问 `https://<域名>/user`，输入专属 Token 或直接粘贴订阅链接免密查看。
- **用量与到期可视卡片**：实时显示已消耗流量、套餐总限额、剩余配额及动态百分比进度条（绿/黄/红过渡）。
- **一键多协议客户端导入**：支持一键导入 Clash / Meta / Verge、Shadowrocket (小火箭)、Sing-box，并支持手机扫码快速订阅。
- **可用节点清单与单节点复制**：展示当前可用高可用节点、协议类型、地区与延迟。

### 3. 多用户专属凭据与硬核流量配额熔断
- **多用户独立授权**：管理员可在后台随时创建独立用户，并分配独立的 UUID 凭据。
- **精准流量限额控制**：管理员可设定每用户每月限额（GB）与到期时间。
- **两层硬核流量阻断**：
  - **Sing-box 服务端内核级断流**：一旦用户流量超标或到期，Sing-box 认证名单实时剔除该用户 UUID，直连握手当场拒绝；
  - **客户端订阅劫持提示**：超标刷新订阅时下发零端口阻断节点（如 `⛔ 流量已用尽 (XX / YY) - 请联系管理员续费`），既阻断了流量，又在客户端显示醒目标签；
  - **RFC/Clash 用量标头**：注入 `Subscription-Userinfo` 标头，客户端原生显示流量进度条。
- **一键重置流量**：客户月付续费后，管理员在卡片上一键清零已用流量即可恢复。

### 4. 协议矩阵与外部节点统一托管
- **主流抗封锁协议**：原生支持 `VLESS-Reality`（XTLS Vision）、`Hysteria 2`（极速 UDP）、`TUIC v5`、`Trojan` 等。
- **外部节点一键导入**：支持直接粘贴外部节点链接（如 `vless://` 等）统一纳入托管，聚合分流。

### 5. 自适应分流与订阅规则引擎
- **全客户端自适应输出**：统一订阅地址自适应识别客户端 User-Agent，自动转换下发：
  - **Clash / Mihomo / Clash Verge / Party** (YAML)
  - **Shadowrocket（小火箭） / v2rayN** (Base64)
  - **Sing-box** (JSON Profile)
  - **Surge / Quantumult X / Stash**
- **可视化分流配置**：支持自定义 BT/PT 流量强制直连（防封端口）、国内域名与 IP 直连（加速访问）、广告拦截黑名单及兜底策略。

### 6. ⚡ 一键唤起客户端 & 全能扫码
- **PC / 移动端 Scheme 一键唤醒**：点击按钮直接唤醒 Clash、Shadowrocket、Sing-box 等客户端自动填入配置。
- **双模二维码**：支持扫码导入整套订阅，或针对单个自建/外部节点直接生成独立直连二维码。

### 7. 精确流量差值统计
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