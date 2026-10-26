#!/usr/bin/env bash
# ==============================================================================
# Komari Monitor & Node Manager - 全新服务器一键安装部署脚本
# 适用系统: Debian / Ubuntu / CentOS / AlmaLinux / Rocky / Alpine
# 项目主页: https://github.com/2290145679/komari-node-manager
# ==============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
PLAIN='\033[0m'
BOLD='\033[1m'

info() { echo -e "${CYAN}[INFO]${PLAIN} $1"; }
ok()   { echo -e "${GREEN}[OK]${PLAIN} $1"; }
warn() { echo -e "${YELLOW}[WARN]${PLAIN} $1"; }
err()  { echo -e "${RED}[ERROR]${PLAIN} $1" >&2; exit 1; }

# 1. Root 权限检查
if [ "$EUID" -ne 0 ]; then
    err "请使用 root 权限运行此脚本！(例如: sudo bash $0)"
fi

# 2. 系统与架构检测
OS_TYPE=""
INSTALL_CMD=""
if [ -f /etc/debian_version ]; then
    OS_TYPE="debian"
    INSTALL_CMD="apt-get update -y && apt-get install -y"
elif [ -f /etc/redhat-release ]; then
    OS_TYPE="centos"
    INSTALL_CMD="dnf install -y || yum install -y"
elif [ -f /etc/alpine-release ]; then
    OS_TYPE="alpine"
    INSTALL_CMD="apk update && apk add"
else
    OS_TYPE="unknown"
    INSTALL_CMD="apt-get update -y && apt-get install -y"
fi

ARCH_RAW=$(uname -m)
ARCH=""
case "$ARCH_RAW" in
    x86_64|amd64)
        ARCH="amd64"
        ;;
    aarch64|arm64)
        ARCH="arm64"
        ;;
    *)
        err "暂不支持当前系统架构: $ARCH_RAW (仅支持 x86_64/amd64 与 aarch64/arm64)"
        ;;
esac

# 3. 欢迎横幅
clear
echo -e "${PURPLE}==================================================================${PLAIN}"
echo -e "${BOLD}${CYAN}   Komari Monitor & Node Manager 主控端一键部署程序${PLAIN}"
echo -e "${YELLOW}   · 固化专属定制版 (锁定 v1.6.0 核心 · 无缝节点管理与分流订阅)${PLAIN}"
echo -e "${YELLOW}   · 适用系统: Debian / Ubuntu / CentOS / AlmaLinux / Alpine${PLAIN}"
echo -e "${YELLOW}   · 系统架构: ${ARCH_RAW} (${ARCH})${PLAIN}"
echo -e "${PURPLE}==================================================================${PLAIN}"
echo ""

# 4. 获取公网 IP
PUBLIC_IP=$(curl -s4 --max-time 3 https://api.ipify.org || curl -s4 --max-time 3 https://ifconfig.me || echo "127.0.0.1")

# 5. 用户交互配置 (非交互模式自动使用默认值)
read -p "$(echo -e "${CYAN}请输入主控端绑定域名或公网IP [默认: ${PUBLIC_IP}]: ${PLAIN}")" USER_DOMAIN
SERVER_NAME="${USER_DOMAIN:-$PUBLIC_IP}"

read -p "$(echo -e "${CYAN}请输入 Web 访问端口 [默认: 80]: ${PLAIN}")" USER_PORT
WEB_PORT="${USER_PORT:-80}"

# 生成默认密码
DEFAULT_PASS=$(tr -dc A-Za-z0-9 2>/dev/null < /dev/urandom | head -c 12 || echo "Komari_2026")
read -p "$(echo -e "${CYAN}请设置管理员密码 (留空随机生成) [默认: ${DEFAULT_PASS}]: ${PLAIN}")" USER_PASS
ADMIN_PASS="${USER_PASS:-$DEFAULT_PASS}"

echo ""
info "正在准备安装环境并下载依赖..."

# 6. 安装基础依赖
if [ "$OS_TYPE" = "debian" ]; then
    DEBIAN_FRONTEND=noninteractive apt-get update -y >/dev/null 2>&1
    DEBIAN_FRONTEND=noninteractive apt-get install -y curl wget tar gzip python3 sqlite3 nginx >/dev/null 2>&1
elif [ "$OS_TYPE" = "centos" ]; then
    dnf install -y curl wget tar gzip python3 sqlite nginx >/dev/null 2>&1 || yum install -y curl wget tar gzip python3 sqlite nginx >/dev/null 2>&1
elif [ "$OS_TYPE" = "alpine" ]; then
    apk update >/dev/null 2>&1
    apk add bash curl wget tar gzip python3 sqlite nginx >/dev/null 2>&1
fi
ok "系统依赖安装完成 (Python3 / SQLite3 / Nginx / Gzip)"

# 7. 检测当前运行环境 (本地仓库执行 or 远程 curl 管道安装)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_BASE="https://raw.githubusercontent.com/2290145679/komari-node-manager/main"
WORK_DIR="/tmp/komari-hub-setup"

mkdir -p "$WORK_DIR"
mkdir -p /opt/komari/bin
mkdir -p /opt/komari/node-mgr
mkdir -p /opt/komari/web-patch/assets
mkdir -p /opt/komari/data/plugin/node-manager/panel

info "正在停止可能存在的旧版本服务..."
systemctl stop komari komari-node-mgr 2>/dev/null || true

# 获取二进制与资源文件
info "正在部署核心服务端程序与前端资源..."
if [ -f "$SCRIPT_DIR/bin/komari-linux-${ARCH}.gz" ]; then
    ok "检测到本地文件仓库，正在直接释放..."
    gzip -d -c "$SCRIPT_DIR/bin/komari-linux-${ARCH}.gz" > /opt/komari/komari
    gzip -d -c "$SCRIPT_DIR/bin/agent-linux-${ARCH}.gz" > /opt/komari/agent
    cp -r "$SCRIPT_DIR"/web-patch/* /opt/komari/web-patch/
    cp -r "$SCRIPT_DIR"/plugin/node-manager/* /opt/komari/data/plugin/node-manager/
    cp -r "$SCRIPT_DIR"/node-mgr/* /opt/komari/node-mgr/
    cp -r "$SCRIPT_DIR"/conf /opt/komari/
else
    ok "正在从 GitHub 官方仓库下载固化核心组件..."
    curl -fsSL "${REPO_BASE}/bin/komari-linux-${ARCH}.gz" | gzip -d > /opt/komari/komari
    curl -fsSL "${REPO_BASE}/bin/agent-linux-${ARCH}.gz" | gzip -d > /opt/komari/agent

    # 下载 Web 补丁
    curl -fsSL "${REPO_BASE}/web-patch/registerSW.js" -o /opt/komari/web-patch/registerSW.js
    curl -fsSL "${REPO_BASE}/web-patch/sw.js" -o /opt/komari/web-patch/sw.js
    curl -fsSL "${REPO_BASE}/web-patch/assets/chunk-index-BfURcdSr.js" -o /opt/komari/web-patch/assets/chunk-index-BfURcdSr.js
    curl -fsSL "${REPO_BASE}/web-patch/assets/chunk-_layout-KM9Ke-Y5.js" -o /opt/komari/web-patch/assets/chunk-_layout-KM9Ke-Y5.js
    curl -fsSL "${REPO_BASE}/web-patch/assets/chunk-plugin_page-Xen4h3Tc.js" -o /opt/komari/web-patch/assets/chunk-plugin_page-Xen4h3Tc.js
    curl -fsSL "${REPO_BASE}/web-patch/assets/komari-singbox-helper.js" -o /opt/komari/web-patch/assets/komari-singbox-helper.js

    # 下载插件前端
    curl -fsSL "${REPO_BASE}/plugin/node-manager/komari-plugin.json" -o /opt/komari/data/plugin/node-manager/komari-plugin.json
    curl -fsSL "${REPO_BASE}/plugin/node-manager/script.js" -o /opt/komari/data/plugin/node-manager/script.js
    curl -fsSL "${REPO_BASE}/plugin/node-manager/panel/index.html" -o /opt/komari/data/plugin/node-manager/panel/index.html

    # 下载后端服务与数据库模板
    curl -fsSL "${REPO_BASE}/node-mgr/server.py" -o /opt/komari/node-mgr/server.py
    curl -fsSL "${REPO_BASE}/node-mgr/schema.sql" -o /opt/komari/node-mgr/schema.sql

    # 下载配置模板
    mkdir -p /opt/komari/conf
    curl -fsSL "${REPO_BASE}/conf/komari.service" -o /opt/komari/conf/komari.service
    curl -fsSL "${REPO_BASE}/conf/komari-node-mgr.service" -o /opt/komari/conf/komari-node-mgr.service
    curl -fsSL "${REPO_BASE}/conf/nginx-komari.conf" -o /opt/komari/conf/nginx-komari.conf
fi

chmod +x /opt/komari/komari /opt/komari/agent
chmod +x /opt/komari/node-mgr/server.py
ok "服务端主控核心与前端资源释放完毕"

# 8. 初始化数据库
info "正在初始化数据库结构..."
mkdir -p /opt/komari/data
if [ ! -f /opt/komari/data/nodes.db ]; then
    sqlite3 /opt/komari/data/nodes.db < /opt/komari/node-mgr/schema.sql
    # 生成随机订阅 token
    SUB_TOKEN=$(tr -dc a-f0-9 2>/dev/null < /dev/urandom | head -c 32 || echo "11c471015f8d55a9b8979fc745778a2e")
    sqlite3 /opt/komari/data/nodes.db "INSERT OR IGNORE INTO subscriptions (token, name) VALUES ('${SUB_TOKEN}', 'default');"
    ok "已创建全新节点管理数据库与默认订阅 Token: ${SUB_TOKEN}"
else
    # 存在旧库则确保补全分流规则表
    sqlite3 /opt/komari/data/nodes.db < /opt/komari/node-mgr/schema.sql 2>/dev/null || true
    SUB_TOKEN=$(sqlite3 /opt/komari/data/nodes.db "SELECT token FROM subscriptions LIMIT 1;" 2>/dev/null || echo "default")
    ok "保留现有节点数据库，当前订阅 Token: ${SUB_TOKEN}"
fi

# 9. 安装 Systemd 服务
info "正在配置系统自启守护进程 (Systemd)..."
cp /opt/komari/conf/komari.service /etc/systemd/system/komari.service
cp /opt/komari/conf/komari-node-mgr.service /etc/systemd/system/komari-node-mgr.service
systemctl daemon-reload
systemctl enable komari komari-node-mgr >/dev/null 2>&1
ok "守护服务注册完毕"

# 10. 配置 Nginx 反向代理
info "正在配置 Nginx 反向代理网关..."
NGINX_CONF_DEST="/etc/nginx/sites-available/komari.conf"
if [ -d /etc/nginx/sites-available ]; then
    sed -e "s|__PORT__|${WEB_PORT}|g" -e "s|__SERVER_NAME__|${SERVER_NAME}|g" /opt/komari/conf/nginx-komari.conf > "$NGINX_CONF_DEST"
    mkdir -p /etc/nginx/sites-enabled
    ln -sf "$NGINX_CONF_DEST" /etc/nginx/sites-enabled/komari.conf
    # 如果有冲突的 default 站点监听同一端口，则暂时停用
    if [ "$WEB_PORT" = "80" ] && [ -L /etc/nginx/sites-enabled/default ]; then
        rm -f /etc/nginx/sites-enabled/default
    fi
elif [ -d /etc/nginx/conf.d ]; then
    sed -e "s|__PORT__|${WEB_PORT}|g" -e "s|__SERVER_NAME__|${SERVER_NAME}|g" /opt/komari/conf/nginx-komari.conf > /etc/nginx/conf.d/komari.conf
fi

nginx -t >/dev/null 2>&1 || warn "Nginx 语法测试有告警，请在安装后检查配置"
systemctl restart nginx 2>/dev/null || systemctl reload nginx 2>/dev/null || true
ok "Nginx 网关配置完成"

# 11. 启动服务并初始化密码
info "正在启动主控端服务..."
systemctl restart komari
sleep 3
# 初始化管理员密码
/opt/komari/komari chpasswd -p "$ADMIN_PASS" 2>/dev/null || true
systemctl restart komari-node-mgr
sleep 2

# 检查运行状态
if systemctl is-active --quiet komari && systemctl is-active --quiet komari-node-mgr; then
    ok "Komari 主控端与节点管理核心已全部成功启动！"
else
    warn "服务可能正在启动中，请使用 systemctl status komari 检查"
fi

# 12. 清理临时目录
rm -rf "$WORK_DIR"

# 13. 输出完成信息
SCHEME="http"
[ "$WEB_PORT" = "443" ] && SCHEME="https"
PORT_SUFFIX=""
if [ "$WEB_PORT" != "80" ] && [ "$WEB_PORT" != "443" ]; then
    PORT_SUFFIX=":${WEB_PORT}"
fi

BASE_URL="${SCHEME}://${SERVER_NAME}${PORT_SUFFIX}"

echo ""
echo -e "${GREEN}==================================================================${PLAIN}"
echo -e "${BOLD}${GREEN}               🎉 Komari 主控端部署成功！${PLAIN}"
echo -e "${GREEN}==================================================================${PLAIN}"
echo -e "${BOLD}1. 管理后台面板:${PLAIN}    ${CYAN}${BASE_URL}/admin/dashboard${PLAIN}"
echo -e "${BOLD}2. 节点管理独立面板:${PLAIN}${CYAN}${BASE_URL}/api/admin/plugin/node-manager/panel/index.html${PLAIN}"
echo -e "${BOLD}3. 管理员初始账号:${PLAIN}  ${YELLOW}admin${PLAIN}"
echo -e "${BOLD}4. 管理员初始密码:${PLAIN}  ${YELLOW}${ADMIN_PASS}${PLAIN}"
echo -e "${BOLD}5. 统一订阅地址:${PLAIN}    ${CYAN}${BASE_URL}/sub/${SUB_TOKEN}${PLAIN}"
echo -e "${GREEN}------------------------------------------------------------------${PLAIN}"
echo -e "${BOLD}💡 探针被控端一键接入指令 (去其他 VPS 执行即可秒级上线):${PLAIN}"
echo -e "${PURPLE}wget -qO- ${BASE_URL}/install-node.sh | sudo bash -s -- -e ${BASE_URL} -t <AGENT_TOKEN>${PLAIN}"
echo -e "${D}  注: 在 Komari 管理后台【实例列表】点击添加服务器即可获得专属 AGENT_TOKEN${PLAIN}"
echo -e "${GREEN}==================================================================${PLAIN}"
echo ""