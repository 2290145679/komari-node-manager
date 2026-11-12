#!/usr/bin/env python3
import os
import sys
import json
import uuid
import sqlite3
import secrets
import base64
import time
import subprocess
import urllib.parse
import urllib.request
import concurrent.futures
import threading
import socket
import ssl
import re
import io
import zipfile
import shutil
import html
from datetime import datetime, timezone
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Inject default timeout to prevent SQLite database locked errors under concurrency
_orig_sqlite_connect = sqlite3.connect
def _sqlite_connect_with_timeout(*args, **kwargs):
    if "timeout" not in kwargs:
        kwargs["timeout"] = 30.0
    return _orig_sqlite_connect(*args, **kwargs)
sqlite3.connect = _sqlite_connect_with_timeout

BASE_DIR = "/opt/komari-pro" if os.path.exists("/opt/komari-pro") else "/opt/komari"
DATA_DIR = os.path.join(BASE_DIR, "data")
NODES_DB = os.path.join(DATA_DIR, "nodes.db")
KOMARI_DB = os.path.join(DATA_DIR, "komari.db") if os.path.exists(os.path.join(DATA_DIR, "komari.db")) else "/opt/komari/data/komari.db"
METRICS_DB = os.path.join(DATA_DIR, "metrics.db") if os.path.exists(os.path.join(DATA_DIR, "metrics.db")) else "/opt/komari/data/metrics.db"
CERT_DIR = os.path.join(DATA_DIR, "certs")
PORT = 25775
DOMAIN = "jgw2.yohoo.xyz"

os.makedirs(CERT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

THEME_DIR = os.path.join(DATA_DIR, "theme")
if not os.path.exists(THEME_DIR) and os.path.exists("./data/theme"):
    THEME_DIR = "./data/theme"
os.makedirs(THEME_DIR, exist_ok=True)

_market_cache = {"ts": 0, "data": []}

DEFAULT_THEME_PREVIEW_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" width="800" height="450">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3B82F6"/>
      <stop offset="50%" stop-color="#6366F1"/>
      <stop offset="100%" stop-color="#8B5CF6"/>
    </linearGradient>
    <linearGradient id="cardBg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="rgba(255,255,255,0.22)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0.08)"/>
    </linearGradient>
  </defs>
  <rect width="800" height="450" fill="url(#bg)"/>
  <circle cx="100" cy="80" r="160" fill="rgba(255,255,255,0.06)" />
  <circle cx="720" cy="360" r="200" fill="rgba(0,0,0,0.12)" />
  <g transform="translate(60, 40)">
    <rect x="0" y="0" width="680" height="46" rx="14" fill="rgba(255,255,255,0.2)" stroke="rgba(255,255,255,0.25)" stroke-width="1" />
    <circle cx="26" cy="23" r="8" fill="#10B981" />
    <text x="46" y="29" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="16" font-weight="900" fill="#FFFFFF">Komari 官方原生大屏</text>
    <rect x="560" y="12" width="96" height="22" rx="11" fill="rgba(255,255,255,0.25)" />
    <text x="608" y="27" text-anchor="middle" font-family="sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">全网在线 9/9</text>
    <rect x="0" y="62" width="213" height="135" rx="16" fill="url(#cardBg)" stroke="rgba(255,255,255,0.25)" stroke-width="1" />
    <circle cx="24" cy="88" r="5" fill="#10B981" />
    <text x="38" y="92" font-family="sans-serif" font-size="13" font-weight="bold" fill="#FFFFFF">HKcloudx AMD 1号鸡</text>
    <text x="24" y="112" font-family="sans-serif" font-size="11" fill="rgba(255,255,255,0.7)">CPU 28%  RAM 35%</text>
    <rect x="24" y="124" width="165" height="6" rx="3" fill="rgba(255,255,255,0.2)" />
    <rect x="24" y="124" width="55" height="6" rx="3" fill="#34D399" />
    <text x="24" y="152" font-family="monospace" font-size="11" fill="rgba(255,255,255,0.85)">↓ 18.5 MB/s ↑ 4.2 MB/s</text>
    <text x="24" y="172" font-family="sans-serif" font-size="10" fill="rgba(255,255,255,0.6)">连通率 100.0% · 32ms</text>
    <rect x="233" y="62" width="213" height="135" rx="16" fill="url(#cardBg)" stroke="rgba(255,255,255,0.25)" stroke-width="1" />
    <circle cx="257" cy="88" r="5" fill="#10B981" />
    <text x="271" y="92" font-family="sans-serif" font-size="13" font-weight="bold" fill="#FFFFFF">甲骨文 ARM 韩国首尔</text>
    <text x="257" y="112" font-family="sans-serif" font-size="11" fill="rgba(255,255,255,0.7)">CPU 14%  RAM 22%</text>
    <rect x="257" y="124" width="165" height="6" rx="3" fill="rgba(255,255,255,0.2)" />
    <rect x="257" y="124" width="40" height="6" rx="3" fill="#60A5FA" />
    <text x="257" y="152" font-family="monospace" font-size="11" fill="rgba(255,255,255,0.85)">↓ 32.1 MB/s ↑ 12.8 MB/s</text>
    <text x="257" y="172" font-family="sans-serif" font-size="10" fill="rgba(255,255,255,0.6)">连通率 100.0% · 48ms</text>
    <rect x="467" y="62" width="213" height="135" rx="16" fill="url(#cardBg)" stroke="rgba(255,255,255,0.25)" stroke-width="1" />
    <circle cx="491" cy="88" r="5" fill="#10B981" />
    <text x="505" y="92" font-family="sans-serif" font-size="13" font-weight="bold" fill="#FFFFFF">懒猫 JPL 日本东京</text>
    <text x="491" y="112" font-family="sans-serif" font-size="11" fill="rgba(255,255,255,0.7)">CPU 45%  RAM 50%</text>
    <rect x="491" y="124" width="165" height="6" rx="3" fill="rgba(255,255,255,0.2)" />
    <rect x="491" y="124" width="90" height="6" rx="3" fill="#FBBF24" />
    <text x="491" y="152" font-family="monospace" font-size="11" fill="rgba(255,255,255,0.85)">↓ 8.4 MB/s ↑ 2.1 MB/s</text>
    <text x="491" y="172" font-family="sans-serif" font-size="10" fill="rgba(255,255,255,0.6)">连通率 99.8% · 65ms</text>
    <rect x="0" y="215" width="680" height="145" rx="18" fill="url(#cardBg)" stroke="rgba(255,255,255,0.25)" stroke-width="1" />
    <text x="32" y="260" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="22" font-weight="900" fill="#FFFFFF">Komari 官方原生默认主题 (Classic Default)</text>
    <text x="32" y="292" font-family="sans-serif" font-size="13" fill="rgba(255,255,255,0.9)">极简架构 · 响应敏捷 · 原生高帧率探针实时监控</text>
    <rect x="32" y="312" width="100" height="26" rx="13" fill="#10B981" />
    <text x="82" y="329" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="bold" fill="#FFFFFF">✓ 官方内置</text>
  </g>
</svg>"""

def get_installed_themes_list(active_theme=""):
    installed = [
        {
            "short": "default",
            "name": "Komari 默认主题 (Default)",
            "description": "Komari 官方原生极简监控大屏，经典轻量",
            "version": "1.0.0",
            "author": "Komari 官方",
            "url": "https://github.com/komari-monitor/komari",
            "homepage": "https://github.com/komari-monitor/komari",
            "preview": "/api/node-mgr/theme/preview?theme=default",
            "preview_url": "/api/node-mgr/theme/preview?theme=default",
            "builtin": True,
            "is_builtin": True,
            "is_active": (active_theme in ["default", "", None])
        }
    ]
    if os.path.exists(THEME_DIR):
        for d in sorted(os.listdir(THEME_DIR)):
            dp = os.path.join(THEME_DIR, d)
            if os.path.isdir(dp):
                cfg_path = os.path.join(dp, "komari-theme.json")
                has_preview = os.path.exists(os.path.join(dp, "preview.png")) or os.path.exists(os.path.join(dp, "preview.webp")) or os.path.exists(os.path.join(dp, "preview.jpg"))
                preview_url = f"/api/node-mgr/theme/preview?theme={d}" if has_preview else ""
                tinfo = {
                    "short": d,
                    "name": d,
                    "version": "1.0.0",
                    "author": "未知",
                    "description": "",
                    "url": "",
                    "homepage": "",
                    "preview": preview_url,
                    "preview_url": preview_url,
                    "builtin": False,
                    "is_builtin": False,
                    "is_active": (d == active_theme)
                }
                if os.path.exists(cfg_path):
                    try:
                        with open(cfg_path, "r", encoding="utf-8") as f:
                            parsed = json.load(f)
                            tinfo.update(parsed)
                            tinfo["short"] = parsed.get("short") or d
                            if preview_url:
                                tinfo["preview"] = preview_url
                                tinfo["preview_url"] = preview_url
                            tinfo["builtin"] = False
                            tinfo["is_builtin"] = False
                            tinfo["homepage"] = tinfo.get("url") or tinfo.get("homepage") or ""
                            tinfo["is_active"] = (tinfo["short"] == active_theme or d == active_theme)
                    except Exception:
                        pass
                installed.append(tinfo)
    return installed

def install_theme_from_zip_bytes(zip_bytes, custom_short=None):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        manifest_path = None
        for name in z.namelist():
            if name.endswith("komari-theme.json") and not name.startswith("__MACOSX"):
                manifest_path = name
                break
        
        if not manifest_path:
            raise ValueError("ZIP 压缩包中未检测到 komari-theme.json 配置文件，非标准 Komari 主题包")
        
        manifest_data = json.loads(z.read(manifest_path).decode("utf-8"))
        short = custom_short or manifest_data.get("short") or manifest_data.get("name")
        if not short:
            raise ValueError("主题配置中缺少 short 或 name 标识")
        
        short = re.sub(r"[^a-zA-Z0-9_-]", "", short)
        if not short:
            short = "theme_" + str(int(time.time()))
        
        target_dir = os.path.join(THEME_DIR, short)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.makedirs(target_dir, exist_ok=True)
        
        prefix = os.path.dirname(manifest_path)
        if prefix:
            prefix += "/"
        
        for item in z.infolist():
            if item.filename.startswith("__MACOSX"):
                continue
            if prefix and not item.filename.startswith(prefix):
                continue
            rel_path = item.filename[len(prefix):] if prefix else item.filename
            if not rel_path or rel_path.endswith("/"):
                continue
            dest_file = os.path.join(target_dir, rel_path)
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            with z.open(item) as src, open(dest_file, "wb") as dst:
                shutil.copyfileobj(src, dst)
        
        return {
            "short": short,
            "name": manifest_data.get("name", short),
            "version": manifest_data.get("version", "1.0.0"),
            "author": manifest_data.get("author", ""),
            "description": manifest_data.get("description", ""),
            "url": manifest_data.get("url", "")
        }

def resolve_theme_download_url(url):
    url = url.strip()
    if url.endswith(".zip"):
        return url
    
    gh_match = re.match(r"^https?://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)/?$", url)
    if gh_match:
        owner, repo = gh_match.groups()
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "Komari-Theme-Manager"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                rel = json.loads(resp.read().decode())
                assets = rel.get("assets", [])
                for a in assets:
                    if a.get("browser_download_url", "").endswith(".zip"):
                        return a["browser_download_url"]
        except Exception:
            pass
        return f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
    return url

def get_theme_market_catalog():
    global _market_cache
    now = time.time()
    if _market_cache["data"] and (now - _market_cache["ts"]) < 300:
        return _market_cache["data"]
    
    catalog_urls = [
        "https://raw.githubusercontent.com/komari-monitor/theme-market/main/v1.json",
        "https://cdn.jsdelivr.net/gh/komari-monitor/theme-market@main/v1.json"
    ]
    for curl in catalog_urls:
        try:
            req = urllib.request.Request(curl, headers={"User-Agent": "Komari-Theme-Manager"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                themes = data.get("themes", [])
                if themes:
                    _market_cache["ts"] = now
                    _market_cache["data"] = themes
                    return themes
        except Exception:
            continue
    return _market_cache.get("data", [])

_cached_active_uuids = None
_cached_active_uuids_time = 0
_cached_active_users = None
_cached_active_users_time = 0

def get_active_users(force_refresh=False):
    global _cached_active_users, _cached_active_users_time
    now = time.time()
    if not force_refresh and _cached_active_users is not None and (now - _cached_active_users_time < 5):
        return _cached_active_users
    users = []
    try:
        conn = sqlite3.connect(NODES_DB)
        c = conn.cursor()
        c.execute("SELECT id, user_uuid, traffic_limit_bytes, traffic_used_bytes, expire_time FROM subscriptions WHERE enabled = 1")
        today_str = datetime.now().strftime("%Y-%m-%d")
        for row in c.fetchall():
            sub_id = row[0]
            u_uuid = str(row[1] or "").strip()
            limit_b = int(row[2] or 0) if len(row) > 2 and row[2] is not None else 0
            used_b = int(row[3] or 0) if len(row) > 3 and row[3] is not None else 0
            exp = str(row[4] or "").strip() if len(row) > 4 and row[4] is not None else ""

            # Hard traffic quota cutoff
            if limit_b > 0 and used_b >= limit_b:
                continue

            # Hard expiration cutoff
            if exp:
                exp_date = exp.split("T")[0]
                if today_str > exp_date:
                    continue

            if u_uuid:
                users.append({
                    "id": sub_id,
                    "uuid": u_uuid,
                    "limit_bytes": limit_b,
                    "used_bytes": used_b
                })
        conn.close()
        _cached_active_users = users
        _cached_active_users_time = now
    except Exception:
        if _cached_active_users is not None:
            return _cached_active_users
    return users

def get_active_user_uuids(force_refresh=False):
    global _cached_active_uuids, _cached_active_uuids_time
    users = get_active_users(force_refresh=force_refresh)
    uuids = [u["uuid"] for u in users]
    _cached_active_uuids = uuids
    _cached_active_uuids_time = _cached_active_users_time
    return uuids

def init_db():
    conn = sqlite3.connect(NODES_DB)
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    c.execute("PRAGMA busy_timeout=30000;")
    c.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_uuid TEXT NOT NULL,
            server_name TEXT,
            server_ip TEXT,
            name TEXT NOT NULL,
            protocol TEXT NOT NULL,
            port INTEGER NOT NULL,
            uuid_or_passwd TEXT NOT NULL,
            sni TEXT,
            public_key TEXT,
            private_key TEXT,
            short_id TEXT,
            flow TEXT,
            ws_path TEXT,
            raw_link TEXT DEFAULT '',
            is_external INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute("PRAGMA table_info(nodes)")
    cols = [r[1] for r in c.fetchall()]
    if 'raw_link' not in cols:
        c.execute("ALTER TABLE nodes ADD COLUMN raw_link TEXT DEFAULT ''")
    if 'is_external' not in cols:
        c.execute("ALTER TABLE nodes ADD COLUMN is_external INTEGER DEFAULT 0")
    if 'is_relay' not in cols:
        c.execute("ALTER TABLE nodes ADD COLUMN is_relay INTEGER DEFAULT 0")
    if 'relay_server_uuid' not in cols:
        c.execute("ALTER TABLE nodes ADD COLUMN relay_server_uuid TEXT DEFAULT ''")
    if 'relay_server_name' not in cols:
        c.execute("ALTER TABLE nodes ADD COLUMN relay_server_name TEXT DEFAULT ''")
    if 'relay_server_ip' not in cols:
        c.execute("ALTER TABLE nodes ADD COLUMN relay_server_ip TEXT DEFAULT ''")
    if 'relay_port' not in cols:
        c.execute("ALTER TABLE nodes ADD COLUMN relay_port INTEGER DEFAULT 0")

    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT 'default',
            enabled INTEGER DEFAULT 1,
            remark TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute("PRAGMA table_info(subscriptions)")
    sub_cols = [r[1] for r in c.fetchall()]
    if 'enabled' not in sub_cols:
        try:
            c.execute("ALTER TABLE subscriptions ADD COLUMN enabled INTEGER DEFAULT 1")
        except Exception:
            pass
    if 'user_uuid' not in sub_cols:
        try:
            c.execute("ALTER TABLE subscriptions ADD COLUMN user_uuid TEXT DEFAULT ''")
        except Exception:
            pass
    try:
        c.execute("SELECT id, user_uuid FROM subscriptions")
        for sub_row in c.fetchall():
            if not sub_row[1]:
                c.execute("UPDATE subscriptions SET user_uuid = ? WHERE id = ?", (str(uuid.uuid4()), sub_row[0]))
    except Exception:
        pass
    if 'remark' not in sub_cols:
        try:
            c.execute("ALTER TABLE subscriptions ADD COLUMN remark TEXT DEFAULT ''")
        except Exception:
            pass
    if 'traffic_limit_bytes' not in sub_cols:
        try:
            c.execute("ALTER TABLE subscriptions ADD COLUMN traffic_limit_bytes INTEGER DEFAULT 0")
        except Exception:
            pass
    if 'traffic_used_bytes' not in sub_cols:
        try:
            c.execute("ALTER TABLE subscriptions ADD COLUMN traffic_used_bytes INTEGER DEFAULT 0")
        except Exception:
            pass
    if 'expire_time' not in sub_cols:
        try:
            c.execute("ALTER TABLE subscriptions ADD COLUMN expire_time TEXT DEFAULT ''")
        except Exception:
            pass
    if 'username' not in sub_cols:
        try:
            c.execute("ALTER TABLE subscriptions ADD COLUMN username TEXT DEFAULT ''")
        except Exception:
            pass
    if 'password' not in sub_cols:
        try:
            c.execute("ALTER TABLE subscriptions ADD COLUMN password TEXT DEFAULT ''")
        except Exception:
            pass
    try:
        c.execute("UPDATE subscriptions SET username = name WHERE (username IS NULL OR username = '') AND name IS NOT NULL AND name != ''")
        c.execute("UPDATE subscriptions SET password = 'password123' WHERE (password IS NULL OR password = '')")
    except Exception:
        pass
    c.execute('''
        CREATE TABLE IF NOT EXISTS agent_heartbeats (
            token TEXT PRIMARY KEY,
            last_seen INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS realm_heartbeats (
            token TEXT PRIMARY KEY,
            last_seen INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS server_realm_configs (
            uuid TEXT PRIMARY KEY,
            has_realm INTEGER DEFAULT 0,
            custom_ip TEXT DEFAULT '',
            is_landing INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        c.execute("ALTER TABLE server_realm_configs ADD COLUMN custom_ip TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE server_realm_configs ADD COLUMN is_landing INTEGER DEFAULT 0")
    except Exception:
        pass
    c.execute('''
        CREATE TABLE IF NOT EXISTS server_traffic_baselines (
            uuid TEXT PRIMARY KEY,
            baseline_up INTEGER DEFAULT 0,
            baseline_down INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscription_rules (
            id INTEGER PRIMARY KEY,
            direct_bt INTEGER DEFAULT 1,
            direct_cn INTEGER DEFAULT 1,
            direct_lan INTEGER DEFAULT 1,
            block_ads INTEGER DEFAULT 0,
            enable_auto_group INTEGER DEFAULT 1,
            final_match TEXT DEFAULT 'PROXY',
            custom_rules TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    extra_cols = [
        ("proxy_ai", "INTEGER DEFAULT 0"),
        ("proxy_tg", "INTEGER DEFAULT 0"),
        ("proxy_media", "INTEGER DEFAULT 0"),
        ("proxy_dev", "INTEGER DEFAULT 0"),
        ("direct_games", "INTEGER DEFAULT 0"),
        ("target_ai", "TEXT DEFAULT 'PROXY'"),
        ("target_tg", "TEXT DEFAULT 'PROXY'"),
        ("target_media", "TEXT DEFAULT 'PROXY'"),
        ("target_dev", "TEXT DEFAULT 'PROXY'"),
        ("target_games", "TEXT DEFAULT 'DIRECT'"),
        ("sub_title", "TEXT DEFAULT 'Komari Pro 优质节点'")
    ]
    for col, ctype in extra_cols:
        try:
            c.execute(f"ALTER TABLE subscription_rules ADD COLUMN {col} {ctype}")
        except Exception:
            pass

    c.execute("SELECT id FROM subscription_rules WHERE id = 1")
    if not c.fetchone():
        c.execute("""
            INSERT INTO subscription_rules (id, direct_bt, direct_cn, direct_lan, block_ads, enable_auto_group, final_match, custom_rules, proxy_ai, proxy_tg, proxy_media, proxy_dev, direct_games)
            VALUES (1, 1, 1, 1, 0, 1, 'PROXY', '', 0, 0, 0, 0, 0)
        """)
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS notification_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            config TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS notification_rules (
            rule_key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            config TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_key TEXT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            channel TEXT NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS notification_states (
            state_key TEXT PRIMARY KEY,
            state_val TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration: ensure updated_at column exists in notification_channels
    try:
        c.execute("ALTER TABLE notification_channels ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except Exception:
        pass

    default_rules = [
        ("traffic_threshold", "流量消耗预警", "core", "单节点或全网流量达到设定阶梯百分比预警；每月1号重置提醒", 1, json.dumps({"thresholds": [80, 90, 100], "cycle_reset_notify": True})),
        ("singbox_status", "Sing-box 离线 / 恢复通知", "core", "Sing-box 核心进程异常挂掉或重启恢复上线时即时告警", 1, json.dumps({"offline_timeout": 60, "notify_recovery": True})),
        ("server_status", "服务器系统离线 / 恢复通知", "core", "探针心跳超时失联时触发宕机报警，恢复时发送上线通知及离线时长", 1, json.dumps({"offline_timeout": 120, "notify_recovery": True})),
        ("server_expiration", "服务器到期续费提醒", "core", "按到期时间提前阶梯预警，防止机器被服务商回收", 1, json.dumps({"remind_days": [30, 15, 7, 3, 1]})),
        ("traffic_surge", "突发大流量激增 / 盗刷告警", "monitor", "单机流速瞬间突发或短时间内产生巨额流量消耗，防范盗刷与跑量预警", 1, json.dumps({"burst_mbps": 100, "burst_gb": 5, "window_min": 10, "cooldown_sec": 3600})),
        ("resource_exhaustion", "物理硬件资源枯竭告警", "monitor", "CPU / 内存 / 磁盘使用率持续超过设定阈值时预警，防止 OOM 崩溃或日志爆盘", 1, json.dumps({"cpu_pct": 90, "mem_pct": 90, "disk_pct": 90, "cooldown_sec": 1800})),
        ("network_block", "TCP 阻断 / GFW 被墙离线监测", "monitor", "通过真实 TCP/TLS 握手定期实测各节点端口连通性，当端口连续失败疑似被墙时即时告警", 1, json.dumps({"fail_threshold": 2, "notify_on_recovery": True})),
        ("cert_reality_check", "Reality 伪装域名 / 证书失效预警", "monitor", "Reality 伪装 SNI 域名握手异常或 SSL 证书到期前预警", 1, json.dumps({"remind_days": 7, "cooldown_sec": 86400})),
        ("admin_login", "管理面板安全登录提醒", "security", "管理员账号从新设备 / 异地 IP 登录时即时推送安全日志", 1, json.dumps({"notify_all_login": True})),
        ("daily_report", "每日定时运维简报", "report", "每天固定时间推送全网运行状态、在线率、当日总消耗与即将到期概览", 1, json.dumps({"report_time": "09:00"}))
    ]
    for r_key, r_name, r_cat, r_desc, r_en, r_cfg in default_rules:
        c.execute("""
            INSERT OR IGNORE INTO notification_rules (rule_key, name, category, description, enabled, config)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (r_key, r_name, r_cat, r_desc, r_en, r_cfg))

    # Migration: Update traffic_surge config defaults if missing burst_gb or window_min
    try:
        c.execute("UPDATE notification_rules SET description = '单机流速瞬间突发或短时间内产生巨额流量消耗，防范盗刷与跑量预警' WHERE rule_key = 'traffic_surge'")
        c.execute("SELECT config FROM notification_rules WHERE rule_key = 'traffic_surge'")
        r_surge = c.fetchone()
        if r_surge:
            c_dict = json.loads(r_surge[0])
            mod = False
            if "burst_gb" not in c_dict:
                c_dict["burst_gb"] = 5
                mod = True
            if "window_min" not in c_dict:
                c_dict["window_min"] = 10
                mod = True
            if "cooldown_sec" not in c_dict:
                c_dict["cooldown_sec"] = 3600
                mod = True
            if mod:
                c.execute("UPDATE notification_rules SET config = ? WHERE rule_key = 'traffic_surge'", (json.dumps(c_dict),))
    except Exception:
        pass

    # Update title and description for network_block to reflect TCP block detection
    c.execute("""
        UPDATE notification_rules 
        SET name = 'TCP 阻断 / GFW 被墙离线监测',
            description = '通过真实 TCP/TLS 握手定期实测各节点端口连通性，当端口无法连通 (疑似被墙) 时即时告警，恢复时推送解除通知'
        WHERE rule_key = 'network_block'
    """)

    # Ensure default subscription
    c.execute("SELECT token FROM subscriptions LIMIT 1")
    row = c.fetchone()
    if not row:
        token = secrets.token_hex(16)
        c.execute("INSERT INTO subscriptions (token, name) VALUES (?, 'default')", (token,))
    conn.commit()
    conn.close()

init_db()

def get_subscription_rules():
    conn = sqlite3.connect(NODES_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM subscription_rules WHERE id = 1")
    row = c.fetchone()
    conn.close()
    if not row:
        return {
            "direct_bt": True,
            "direct_cn": True,
            "direct_lan": True,
            "block_ads": False,
            "enable_auto_group": True,
            "final_match": "PROXY",
            "custom_rules": "",
            "proxy_ai": False,
            "proxy_tg": False,
            "proxy_media": False,
            "proxy_dev": False,
            "direct_games": False,
            "sub_title": "Komari Pro 优质节点"
        }
    d = dict(row)
    return {
        "direct_bt": bool(d.get("direct_bt", 1)),
        "direct_cn": bool(d.get("direct_cn", 1)),
        "direct_lan": bool(d.get("direct_lan", 1)),
        "block_ads": bool(d.get("block_ads", 0)),
        "enable_auto_group": bool(d.get("enable_auto_group", 1)),
        "final_match": d.get("final_match") or "PROXY",
        "custom_rules": d.get("custom_rules") or "",
        "proxy_ai": bool(d.get("proxy_ai", 0)),
        "proxy_tg": bool(d.get("proxy_tg", 0)),
        "proxy_media": bool(d.get("proxy_media", 0)),
        "proxy_dev": bool(d.get("proxy_dev", 0)),
        "direct_games": bool(d.get("direct_games", 0)),
        "target_ai": d.get("target_ai") or "PROXY",
        "target_tg": d.get("target_tg") or "PROXY",
        "target_media": d.get("target_media") or "PROXY",
        "target_dev": d.get("target_dev") or "PROXY",
        "target_games": d.get("target_games") or "DIRECT",
        "sub_title": d.get("sub_title") or "Komari Pro 优质节点"
    }

def get_rules_referencing_node(node_name):
    if not node_name:
        return []
    conn = sqlite3.connect(NODES_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM subscription_rules WHERE id = 1")
    r_row = c.fetchone()
    conn.close()

    refs = []
    if r_row:
        meta_map = {
            "target_ai": "🤖 AI 大模型服务 (ChatGPT / Claude)",
            "target_tg": "✈️ Telegram 社交专线",
            "target_media": "🎬 海外流媒体 (YouTube / Netflix)",
            "target_dev": "💻 开发者服务 (GitHub / Docker)",
            "target_games": "🎮 主流游戏平台 (Steam / Epic)"
        }
        for f, label in meta_map.items():
            if r_row[f] == node_name:
                refs.append({"type": "preset", "field": f, "name": label})

        custom_rules = r_row["custom_rules"] or ""
        for line in custom_rules.splitlines():
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            parts = [p.strip() for p in t.lstrip("- ").split(",")]
            if len(parts) >= 3 and parts[2] == node_name:
                refs.append({"type": "custom", "rule": t, "name": f"自定义: {parts[0]},{parts[1]}"})
    return refs

def redirect_rules_for_node(node_name, redirect_target="PROXY"):
    if not node_name:
        return 0
    redirect_target = redirect_target or "PROXY"
    conn = sqlite3.connect(NODES_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM subscription_rules WHERE id = 1")
    row = c.fetchone()
    if not row:
        conn.close()
        return 0

    updated_count = 0
    fields_to_check = ["target_ai", "target_tg", "target_media", "target_dev", "target_games"]
    updates = {}
    for f in fields_to_check:
        if row[f] == node_name:
            updates[f] = redirect_target
            updated_count += 1

    custom_rules = row["custom_rules"] or ""
    new_lines = []
    custom_changed = False
    for line in custom_rules.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            new_lines.append(line)
            continue
        parts = [p.strip() for p in trimmed.lstrip("- ").split(",")]
        if len(parts) >= 3 and parts[2] == node_name:
            parts[2] = redirect_target
            prefix = "- " if trimmed.startswith("-") else ""
            new_line = prefix + ",".join(parts)
            new_lines.append(new_line)
            custom_changed = True
            updated_count += 1
        else:
            new_lines.append(line)

    if custom_changed:
        updates["custom_rules"] = "\n".join(new_lines)

    if updates:
        set_clauses = [f"{k} = ?" for k in updates.keys()]
        values = list(updates.values())
        c.execute(f"UPDATE subscription_rules SET {', '.join(set_clauses)}, updated_at=CURRENT_TIMESTAMP WHERE id = 1", values)
        conn.commit()

    conn.close()
    return updated_count

def fix_all_dangling_rules(default_fallback="PROXY"):
    conn = sqlite3.connect(NODES_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT name FROM nodes")
    active_names = set(r["name"] for r in c.fetchall())
    base_actions = {"PROXY", "DIRECT", "REJECT", "自动优选"}
    valid_targets = active_names | base_actions

    c.execute("SELECT * FROM subscription_rules WHERE id = 1")
    row = c.fetchone()
    if not row:
        conn.close()
        return {"fixed": 0}

    fixed_count = 0
    updates = {}
    for f in ["target_ai", "target_tg", "target_media", "target_dev", "target_games"]:
        cur = row[f]
        if cur and cur not in valid_targets:
            updates[f] = default_fallback
            fixed_count += 1

    custom_rules = row["custom_rules"] or ""
    new_lines = []
    custom_changed = False
    for line in custom_rules.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            new_lines.append(line)
            continue
        parts = [p.strip() for p in trimmed.lstrip("- ").split(",")]
        if len(parts) >= 3:
            tgt = parts[2]
            if tgt not in valid_targets:
                parts[2] = default_fallback
                prefix = "- " if trimmed.startswith("-") else ""
                new_lines.append(prefix + ",".join(parts))
                custom_changed = True
                fixed_count += 1
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if custom_changed:
        updates["custom_rules"] = "\n".join(new_lines)

    if updates:
        set_clauses = [f"{k} = ?" for k in updates.keys()]
        values = list(updates.values())
        c.execute(f"UPDATE subscription_rules SET {', '.join(set_clauses)}, updated_at=CURRENT_TIMESTAMP WHERE id = 1", values)
        conn.commit()

    conn.close()
    return {"fixed": fixed_count}

def sync_ping_tasks_all_clients():
    """Ensure all servers in Komari clients table are included in ping tasks marked with all_clients = 1"""
    if not os.path.exists(KOMARI_DB):
        return 0
    try:
        conn_k = sqlite3.connect(KOMARI_DB)
        c_k = conn_k.cursor()
        c_k.execute("SELECT uuid FROM clients")
        all_uuids = [r[0] for r in c_k.fetchall() if r[0]]
        if not all_uuids:
            conn_k.close()
            return 0

        c_k.execute("SELECT id, clients, all_clients FROM ping_tasks WHERE all_clients = 1")
        tasks = c_k.fetchall()
        updated_count = 0
        for tid, clients_json, all_clients in tasks:
            try:
                clist = json.loads(clients_json) if clients_json else []
            except Exception:
                clist = []
            cset = set(clist)
            changed = False
            for u in all_uuids:
                if u not in cset:
                    clist.append(u)
                    cset.add(u)
                    changed = True
            if changed:
                c_k.execute("UPDATE ping_tasks SET clients = ? WHERE id = ?", (json.dumps(clist), tid))
                updated_count += 1
        if updated_count > 0:
            conn_k.commit()
            # Trigger background restart of komari so Go in-memory scheduler loads newly added servers
            def _async_reload_komari():
                time.sleep(1)
                try:
                    subprocess.run("sudo systemctl restart komari", shell=True)
                except Exception as ex:
                    print(f"Error restarting komari service: {ex}")
            threading.Thread(target=_async_reload_komari, daemon=True).start()
        conn_k.close()
        return updated_count
    except Exception as e:
        print(f"[PingSync] Error syncing all_clients ping tasks: {e}")
        return 0

def set_authoritative_server_ip(token, custom_ip):
    """Lock authoritative IP for a server and sync across komari.db, nodes.db and all nodes (永恒防错机制)"""
    if not token or not custom_ip:
        return False, "missing token or ip", None
    token = str(token).strip()
    custom_ip = str(custom_ip).strip()
    suuid = None
    if os.path.exists(KOMARI_DB):
        try:
            conn_k = sqlite3.connect(KOMARI_DB)
            c_k = conn_k.cursor()
            c_k.execute("SELECT uuid FROM clients WHERE token = ? OR uuid = ?", (token, token))
            row_k = c_k.fetchone()
            if row_k:
                suuid = row_k[0]
                c_k.execute("UPDATE clients SET ipv4 = ?, updated_at = ? WHERE uuid = ?", (custom_ip, datetime.now().isoformat(), suuid))
                conn_k.commit()
            conn_k.close()
        except Exception as e:
            print(f"[SetServerIP] komari.db error: {e}")

    if not suuid and os.path.exists(NODES_DB):
        try:
            conn_n = sqlite3.connect(NODES_DB)
            c_n = conn_n.cursor()
            c_n.execute("SELECT server_uuid FROM nodes WHERE server_uuid = ? LIMIT 1", (token,))
            row_n = c_n.fetchone()
            if row_n:
                suuid = row_n[0]
            conn_n.close()
        except Exception:
            pass

    if suuid and os.path.exists(NODES_DB):
        try:
            conn_r = sqlite3.connect(NODES_DB)
            c_r = conn_r.cursor()
            c_r.execute("CREATE TABLE IF NOT EXISTS server_realm_configs (uuid TEXT PRIMARY KEY, has_realm INTEGER DEFAULT 0, custom_ip TEXT DEFAULT '', is_landing INTEGER DEFAULT 0, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            c_r.execute("SELECT has_realm, is_landing FROM server_realm_configs WHERE uuid = ?", (suuid,))
            row_r = c_r.fetchone()
            hr = row_r[0] if row_r else 0
            land = row_r[1] if row_r else 0
            c_r.execute("INSERT OR REPLACE INTO server_realm_configs (uuid, has_realm, custom_ip, is_landing, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", (suuid, hr, custom_ip, land))
            # Also update all nodes attached to this server
            c_r.execute("UPDATE nodes SET server_ip = ? WHERE server_uuid = ?", (custom_ip, suuid))
            conn_r.commit()
            conn_r.close()
            # Invalidate stats cache so UI updates immediately
            _stats_cache["ts"] = 0
            return True, None, suuid
        except Exception as e:
            return False, str(e), None

    return False, "server not found", None

def auto_repair_node_ips():
    """Automatically resolve missing server_ip and server_name for native nodes from komari clients table,
    and enforce authoritative custom_ip from server_realm_configs to prevent WARP / NAT overwrite."""
    if not os.path.exists(KOMARI_DB) or not os.path.exists(NODES_DB):
        return 0
    try:
        # 1. Load custom_ip overrides (authoritative locks)
        conn_n = sqlite3.connect(NODES_DB)
        c_n = conn_n.cursor()
        c_n.execute("CREATE TABLE IF NOT EXISTS server_realm_configs (uuid TEXT PRIMARY KEY, has_realm INTEGER DEFAULT 0, custom_ip TEXT DEFAULT '', is_landing INTEGER DEFAULT 0, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c_n.execute("SELECT uuid, custom_ip FROM server_realm_configs WHERE custom_ip != '' AND custom_ip IS NOT NULL")
        custom_ips = {r[0]: str(r[1]).strip() for r in c_n.fetchall() if r[1] and str(r[1]).strip()}

        # 2. Sync with komari.db clients table
        conn_k = sqlite3.connect(KOMARI_DB)
        c_k = conn_k.cursor()
        c_k.execute("SELECT uuid, name, ipv4, ipv6 FROM clients")
        clients_map = {r[0]: {"name": r[1] or "", "ip": r[2] or r[3] or ""} for r in c_k.fetchall() if r[0]}

        # If a server has an authoritative custom_ip, ensure komari.db clients.ipv4 is locked to it
        for suuid, cip in custom_ips.items():
            if suuid in clients_map:
                clients_map[suuid]["ip"] = cip
                c_k.execute("UPDATE clients SET ipv4 = ? WHERE uuid = ? AND (ipv4 != ? OR ipv4 IS NULL)", (cip, suuid, cip))
        conn_k.commit()
        conn_k.close()

        # 3. Enforce authoritative IP on all nodes bound to self-hosted servers
        c_n.execute("SELECT id, server_uuid, server_name, server_ip FROM nodes WHERE is_external = 0")
        rows = c_n.fetchall()
        repaired = 0
        for nid, suuid, sname, sip in rows:
            if suuid in clients_map:
                cinfo = clients_map[suuid]
                new_name = sname if sname else cinfo["name"]
                new_ip = custom_ips.get(suuid) or sip or cinfo["ip"]
                if (not sname and new_name) or (sip != new_ip):
                    c_n.execute("UPDATE nodes SET server_name = ?, server_ip = ? WHERE id = ?", (new_name, new_ip, nid))
                    repaired += 1
        if repaired > 0:
            conn_n.commit()
        conn_n.close()
        return repaired
    except Exception as e:
        print(f"[NodeRepair] Error auto-repairing node IPs: {e}")
        return 0

def ping_node_handshake(server_ip, port, protocol="", sni="", timeout=3.5):
    """
    真实发起网络握手检测节点连通性与延时
    1. 自适应解析 IPv4 与 IPv6 (socket.getaddrinfo)
    2. 发起真实 TCP 三次握手 (SYN -> SYN-ACK -> ACK)
    3. 若为 TLS/Reality/Trojan，尝试发起真实 TLS 握手 (ClientHello -> ServerHello)
    """
    if not server_ip or not port:
        return {"success": False, "latency_ms": None, "error": "缺少服务器IP或端口"}

    host = str(server_ip).strip("[] \t\r\n")
    try:
        port = int(port)
    except Exception:
        return {"success": False, "latency_ms": None, "error": "无效的端口号"}

    t0 = time.perf_counter()
    sock = None
    try:
        infos = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if not infos:
            return {"success": False, "latency_ms": None, "error": "无法解析目标主机地址"}

        family, socktype, proto_num, canonname, sockaddr = infos[0]
        sock = socket.socket(family, socktype, proto_num)
        sock.settimeout(timeout)

        # 真实 TCP 三次握手
        sock.connect(sockaddr)
        t_tcp = round((time.perf_counter() - t0) * 1000)

        latency = t_tcp
        handshake_type = "TCP"

        # 判断是否可继续进行 TLS 握手 (VLESS-Reality / Trojan / TLS)
        has_tls = any(k in str(protocol).lower() for k in ["tls", "reality", "trojan"]) or bool(sni)
        if has_tls and sni:
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                rem_timeout = max(1.5, timeout - (t_tcp / 1000.0))
                sock.settimeout(rem_timeout)
                ssock = ctx.wrap_socket(sock, server_hostname=sni)
                t_tls = round((time.perf_counter() - t0) * 1000)
                latency = t_tls
                handshake_type = "TLS"
                ssock.close()
                sock = None
            except Exception:
                handshake_type = "TCP"

        if sock:
            try: sock.close()
            except Exception: pass

        return {
            "success": True,
            "latency_ms": max(1, latency),
            "handshake_type": handshake_type
        }
    except socket.timeout:
        if sock:
            try: sock.close()
            except Exception: pass
        return {"success": False, "latency_ms": None, "error": "连接超时 (节点离线或端口被阻断)"}
    except ConnectionRefusedError:
        if sock:
            try: sock.close()
            except Exception: pass
        return {"success": False, "latency_ms": None, "error": "连接被拒绝 (节点核心未运行或端口未监听)"}
    except Exception as e:
        if sock:
            try: sock.close()
            except Exception: pass
        err_msg = str(e)
        if "Network is unreachable" in err_msg or "101" in err_msg:
            err_msg = "网络不可达 (IPv6路由缺失或网络阻断)"
        return {"success": False, "latency_ms": None, "error": err_msg}

def get_reality_keypair():
    try:
        res = subprocess.run(["sing-box", "generate", "reality-keypair"], capture_output=True, text=True, check=True)
        priv, pub = "", ""
        for line in res.stdout.splitlines():
            if line.startswith("PrivateKey:"):
                priv = line.split(":", 1)[1].strip()
            elif line.startswith("PublicKey:"):
                pub = line.split(":", 1)[1].strip()
        return priv, pub
    except Exception as e:
        return "", ""

def get_short_id():
    return secrets.token_hex(4) # 8 chars hex

def parse_proxy_link(link):
    link = link.strip()
    if not link:
        return None
    node = {
        "server_uuid": "external",
        "server_name": "外部导入",
        "server_ip": "",
        "name": "外部节点",
        "protocol": "custom",
        "port": 443,
        "uuid_or_passwd": "",
        "sni": "",
        "public_key": "",
        "private_key": "",
        "short_id": "",
        "flow": "",
        "ws_path": "",
        "raw_link": link,
        "is_external": 1,
        "enabled": 1
    }
    try:
        if link.startswith("vmess://"):
            b64_str = link[8:]
            b64_str += '=' * (-len(b64_str) % 4)
            data = json.loads(base64.b64decode(b64_str).decode('utf-8', errors='ignore'))
            node["name"] = data.get("ps") or "VMess 节点"
            node["server_ip"] = data.get("add") or ""
            node["port"] = int(data.get("port") or 443)
            node["uuid_or_passwd"] = data.get("id") or ""
            node["protocol"] = "vmess_ws" if data.get("net") == "ws" else "vmess"
            node["ws_path"] = data.get("path") or ""
            node["sni"] = data.get("sni") or data.get("host") or ""
            return node

        parsed = urlparse(link)
        scheme = parsed.scheme.lower()
        node["name"] = urllib.parse.unquote(parsed.fragment) if parsed.fragment else f"{scheme.upper()} 节点"
        node["server_ip"] = parsed.hostname or ""
        node["port"] = parsed.port or 443
        node["uuid_or_passwd"] = urllib.parse.unquote(parsed.username or "")
        
        qs = parse_qs(parsed.query)
        node["sni"] = qs.get("sni", [""])[0] or qs.get("peer", [""])[0] or ""
        node["flow"] = qs.get("flow", [""])[0]
        node["public_key"] = qs.get("pbk", [""])[0]
        node["short_id"] = qs.get("sid", [""])[0]
        node["ws_path"] = qs.get("path", [""])[0]

        if scheme in ["vless"]:
            security = qs.get("security", [""])[0]
            if security == "reality" or node["public_key"]:
                node["protocol"] = "vless_reality"
            else:
                node["protocol"] = "vless"
        elif scheme in ["hysteria2", "hy2"]:
            node["protocol"] = "hysteria2"
            if not node["uuid_or_passwd"] and parsed.password:
                node["uuid_or_passwd"] = parsed.password
        elif scheme in ["tuic"]:
            node["protocol"] = "tuic"
        elif scheme in ["trojan"]:
            node["protocol"] = "trojan"
        elif scheme in ["ss"]:
            node["protocol"] = "shadowsocks"
        else:
            node["protocol"] = scheme

        return node
    except Exception as e:
        node["name"] = "外部节点"
        node["protocol"] = "custom"
        return node


_stats_cache = {"ts": 0, "data": None}
_basic_servers_cache = {"ts": 0, "data": []}
_node_latency_cache = {}

def get_servers_basic():
    """
    Ultra-lightweight query for server auth and token mapping from KOMARI_DB (clients table).
    Cached in memory for 5 seconds to eliminate SQLite overhead on high-frequency agent requests.
    Zero ThreadPool, zero metrics.db queries, near 0ms execution time.
    """
    global _basic_servers_cache
    now = time.time()
    if _basic_servers_cache["data"] and (now - _basic_servers_cache["ts"] < 5.0):
        return _basic_servers_cache["data"]

    if not os.path.exists(KOMARI_DB):
        return []
    try:
        conn = sqlite3.connect(KOMARI_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT uuid, token, name, ipv4, ipv6 FROM clients")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        _basic_servers_cache["ts"] = now
        _basic_servers_cache["data"] = rows
        return rows
    except Exception:
        return _basic_servers_cache.get("data") or []

def get_cached_servers_with_stats():
    global _stats_cache
    now = time.time()
    if _stats_cache["data"] and (now - _stats_cache["ts"]) < 3.0:
        return _stats_cache["data"]
    data = get_servers_with_stats()
    _stats_cache["ts"] = now
    _stats_cache["data"] = data
    return data

def get_servers_with_stats():
    servers = []
    if not os.path.exists(KOMARI_DB):
        return {"ok": True, "servers": [], "singbox_online_count": 0, "total_servers": 0, "total_traffic": 0, "total_raw_traffic": 0}

    conn_k = sqlite3.connect(KOMARI_DB)
    conn_k.row_factory = sqlite3.Row
    c_k = conn_k.cursor()
    c_k.execute('SELECT * FROM clients ORDER BY weight DESC, name ASC')
    clients = [dict(r) for r in c_k.fetchall()]
    conn_k.close()

    # Auto-sync ping tasks with all_clients=1 & auto-heal missing server IPs
    try:
        sync_ping_tasks_all_clients()
        auto_repair_node_ips()
    except Exception as e:
        pass

    # Auto-cleanup orphan nodes whose server was deleted from Komari (including relay/landing machines)
    try:
        valid_uuids = set(r["uuid"] for r in clients)
        conn_clean = sqlite3.connect(NODES_DB)
        c_clean = conn_clean.cursor()
        c_clean.execute("SELECT id, server_uuid, name, is_relay, relay_server_uuid FROM nodes WHERE is_external = 0 AND server_uuid != 'external'")
        all_self_nodes = c_clean.fetchall()
        orphan_nodes = []
        for r in all_self_nodes:
            nid, suuid, nname, is_r, r_suuid = r[0], r[1], r[2], r[3], r[4]
            # 1. Main host (landing/server) no longer exists in Komari
            if suuid not in valid_uuids:
                orphan_nodes.append((nid, suuid, nname))
            # 2. Relay node whose relay machine no longer exists in Komari
            elif is_r and r_suuid and r_suuid not in valid_uuids:
                orphan_nodes.append((nid, r_suuid, nname))

        if orphan_nodes:
            orphan_ids = [r[0] for r in orphan_nodes]
            c_clean.execute(f"DELETE FROM nodes WHERE id IN ({','.join('?' * len(orphan_ids))})", orphan_ids)
            conn_clean.commit()
            for oid, osuuid, oname in orphan_nodes:
                redirect_rules_for_node(oname, "PROXY")
        conn_clean.close()
    except Exception as e:
        pass

    conn_n = sqlite3.connect(NODES_DB)
    c_n = conn_n.cursor()
    c_n.execute("SELECT token, last_seen FROM agent_heartbeats")
    heartbeats = dict(c_n.fetchall())
    c_n.execute("CREATE TABLE IF NOT EXISTS realm_heartbeats (token TEXT PRIMARY KEY, last_seen INTEGER)")
    c_n.execute("SELECT token, last_seen FROM realm_heartbeats")
    realm_heartbeats = dict(c_n.fetchall())
    c_n.execute("CREATE TABLE IF NOT EXISTS server_realm_configs (uuid TEXT PRIMARY KEY, has_realm INTEGER DEFAULT 0, custom_ip TEXT DEFAULT '', is_landing INTEGER DEFAULT 0, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    try:
        c_n.execute("ALTER TABLE server_realm_configs ADD COLUMN custom_ip TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c_n.execute("ALTER TABLE server_realm_configs ADD COLUMN is_landing INTEGER DEFAULT 0")
    except Exception:
        pass
    c_n.execute("SELECT uuid, has_realm, custom_ip, is_landing FROM server_realm_configs")
    realm_configs = {r[0]: (r[1], r[2] if len(r) > 2 else '', r[3] if len(r) > 3 else 0) for r in c_n.fetchall()}
    c_n.execute("SELECT DISTINCT relay_server_uuid FROM nodes WHERE is_relay = 1")
    active_relay_uuids = set(r[0] for r in c_n.fetchall() if r[0])
    c_n.execute("SELECT uuid, baseline_up, baseline_down FROM server_traffic_baselines")
    baselines = {r[0]: (r[1], r[2]) for r in c_n.fetchall()}
    conn_n.close()

    # Query real-time instantaneous metrics from Komari internal recent API (live second-by-second)
    recent_metrics = {}
    try:
        def fetch_recent(uuid_val):
            try:
                req = urllib.request.Request(f"http://127.0.0.1:25774/api/recent/{uuid_val}")
                with urllib.request.urlopen(req, timeout=0.8) as resp:
                    data = json.loads(resp.read().decode())
                    items = data.get("data", [])
                    return uuid_val, items[-1] if items else None
            except Exception:
                return uuid_val, None

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            recent_metrics = dict(executor.map(fetch_recent, [r["uuid"] for r in clients]))
    except Exception:
        pass

    # Historical metrics fallback (from SQLite metric_rollups)
    first_seen_by_uuid = {}
    if os.path.exists(METRICS_DB):
        try:
            conn_m = sqlite3.connect(METRICS_DB)
            c_m = conn_m.cursor()
            # First recorded value by Komari (to establish initial baseline if needed)
            c_m.execute("""
                SELECT s.entity_id, s.metric_name, min(r.first_val)
                FROM metric_series s
                JOIN metric_rollups r ON s.id = r.series_id
                WHERE s.metric_name IN ('net.total.up', 'net.total.down')
                GROUP BY s.entity_id, s.metric_name
            """)
            for eid, mname, val in c_m.fetchall():
                if eid not in first_seen_by_uuid:
                    first_seen_by_uuid[eid] = {}
                first_seen_by_uuid[eid][mname] = val
            conn_m.close()
        except Exception:
            pass

    # Auto-initialize missing baselines
    new_baselines = []
    for row in clients:
        uuid_val = row["uuid"]
        rec = recent_metrics.get(uuid_val)
        if rec and "network" in rec:
            cur_up = int(rec["network"].get("totalUp", 0))
            cur_down = int(rec["network"].get("totalDown", 0))
        else:
            cur_up = 0
            cur_down = 0

        if uuid_val not in baselines:
            first_m = first_seen_by_uuid.get(uuid_val, {})
            base_up = int(first_m.get('net.total.up', cur_up))
            base_down = int(first_m.get('net.total.down', cur_down))
            new_baselines.append((uuid_val, base_up, base_down))
            baselines[uuid_val] = (base_up, base_down)

    if new_baselines:
        try:
            conn_b = sqlite3.connect(NODES_DB)
            conn_b.executemany("INSERT OR REPLACE INTO server_traffic_baselines (uuid, baseline_up, baseline_down) VALUES (?, ?, ?)", new_baselines)
            conn_b.commit()
            conn_b.close()
        except Exception:
            pass

    now = int(time.time())
    online_count = 0
    total_traffic = 0
    total_raw_traffic = 0

    for row in clients:
        uuid_val = row["uuid"]
        name = row.get("name")
        ip4 = row.get("ipv4")
        ip6 = row.get("ipv6")
        os_name = row.get("os")
        arch = row.get("arch")
        token = row.get("token")
        updated_at = row.get("updated_at")
        price = row.get("price")
        billing_cycle = row.get("billing_cycle")
        currency = row.get("currency") or "$"
        auto_renewal = bool(row.get("auto_renewal"))
        expired_at = row.get("expired_at")
        traffic_limit = row.get("traffic_limit") or 0
        traffic_limit_type = row.get("traffic_limit_type") or "max"
        group_name = row.get("group") or ""
        tags = row.get("tags") or ""
        hidden = bool(row.get("hidden"))
        weight = row.get("weight") or 0
        remark = row.get("remark") or ""
        public_remark = row.get("public_remark") or ""
        region = row.get("region") or ""

        last_seen = heartbeats.get(token, 0)
        is_online = (now - last_seen) <= 75 if last_seen > 0 else False

        r_last_seen = realm_heartbeats.get(token, 0)
        is_realm_online = (now - r_last_seen) <= 90 if r_last_seen > 0 else False
        r_conf = realm_configs.get(uuid_val, (0, '', 0))
        is_realm_configured = bool(r_conf[0]) if isinstance(r_conf, (list, tuple)) else bool(r_conf)
        custom_ip = str(r_conf[1] if isinstance(r_conf, (list, tuple)) and len(r_conf) > 1 else '').strip()
        is_landing = bool(r_conf[2]) if isinstance(r_conf, (list, tuple)) and len(r_conf) > 2 else False
        if custom_ip:
            ip4 = custom_ip
        is_relay_assigned = uuid_val in active_relay_uuids
        has_realm = is_realm_online or (r_last_seen > 0) or is_realm_configured or is_relay_assigned

        rec = recent_metrics.get(uuid_val)
        is_probe_online = bool(rec and len(rec) > 0)
        is_server_online = is_probe_online or is_online
        if is_server_online:
            online_count += 1
        if rec and "network" in rec:
            net = rec["network"]
            cur_up = int(net.get("totalUp", 0))
            cur_down = int(net.get("totalDown", 0))
            # Komari: net.down is download rate, net.up is upload rate
            in_rate = int(net.get("down", 0))
            out_rate = int(net.get("up", 0))
            rec_updated = rec.get("updated_at") or updated_at
        else:
            cur_up = 0
            cur_down = 0
            in_rate = 0
            out_rate = 0
            rec_updated = updated_at

        raw_tot = cur_up + cur_down
        total_raw_traffic += raw_tot

        base_up, base_down = baselines.get(uuid_val, (0, 0))
        # Handle reboot (if interface reset below baseline)
        if cur_up < base_up:
            base_up = 0
        if cur_down < base_down:
            base_down = 0

        delta_up = max(0, cur_up - base_up)
        delta_down = max(0, cur_down - base_down)
        delta_tot = delta_up + delta_down
        total_traffic += delta_tot

        ip_flag = f" --ip {custom_ip}" if custom_ip else ""
        servers.append({
            "uuid": uuid_val,
            "name": name or ip4 or "Server-" + uuid_val[:6],
            "region": region,
            "ipv4": ip4 or "",
            "custom_ip": custom_ip or "",
            "ipv6": ip6 or "",
            "os": os_name or "",
            "arch": arch or "",
            "token": token or "",
            "install_cmd_wget": f"wget -qO- https://{DOMAIN}/install-node.sh | sudo bash -s -- -e https://{DOMAIN} -t {token}{ip_flag}",
            "install_cmd_curl": f"curl -fsSL https://{DOMAIN}/install-node.sh | sudo bash -s -- -e https://{DOMAIN} -t {token}{ip_flag}",
            "updated_at": str(rec_updated) if rec_updated else "",
            "price": float(price) if price is not None else 0.0,
            "billing_cycle": int(billing_cycle) if billing_cycle is not None else 0,
            "currency": currency or "$",
            "auto_renewal": bool(auto_renewal),
            "expired_at": str(expired_at) if expired_at else "",
            "traffic_limit": int(traffic_limit) if traffic_limit is not None else 0,
            "traffic_limit_type": traffic_limit_type or "max",
            "group": group_name or "",
            "tags": tags or "",
            "hidden": bool(hidden),
            "weight": int(weight) if weight is not None else 0,
            "remark": remark or "",
            "public_remark": public_remark or "",
            "probe_online": is_probe_online,
            "singbox_online": is_online,
            "server_online": is_server_online,
            "singbox_installed": last_seen > 0,
            "realm_online": is_realm_online,
            "realm_installed": (r_last_seen > 0) or is_realm_configured or is_relay_assigned,
            "has_realm": has_realm,
            "custom_ip": custom_ip,
            "is_landing": is_landing,
            "realm_last_seen": r_last_seen,
            "last_seen": last_seen,
            "last_seen_ago": (now - last_seen) if last_seen > 0 else None,
            "traffic_up": delta_up,
            "traffic_down": delta_down,
            "traffic_total": delta_tot,
            "raw_up": cur_up,
            "raw_down": cur_down,
            "raw_total": raw_tot,
            "baseline_up": base_up,
            "baseline_down": base_down,
            "in_rate": in_rate,
            "out_rate": out_rate,
            "cpu_usage": rec.get("cpu", {}).get("usage", 0) if rec else 0,
            "ram_pct": (rec.get("ram", {}).get("used", 0) / rec.get("ram", {}).get("total", 1) * 100) if (rec and rec.get("ram", {}).get("total", 0) > 0) else 0,
            "disk_pct": (rec.get("disk", {}).get("used", 0) / rec.get("disk", {}).get("total", 1) * 100) if (rec and rec.get("disk", {}).get("total", 0) > 0) else 0
        })

    return {
        "ok": True,
        "servers": servers,
        "singbox_online_count": online_count,
        "total_servers": len(servers),
        "total_traffic": total_traffic,
        "total_raw_traffic": total_raw_traffic
    }
def get_servers():
    """
    Fast, lightweight server metadata retrieval for agent endpoints and background tasks.
    """
    return get_servers_basic()

def build_node_share_link(node):
    if node.get("raw_link"):
        return node["raw_link"]

    proto = node.get("protocol")
    is_relay = node.get("is_relay")
    if is_relay and node.get("relay_server_ip"):
        ip = node["relay_server_ip"]
        port = node.get("relay_port") or node.get("port")
    else:
        ip = node.get("server_ip") or DOMAIN
        port = node.get("port")
    name = node.get("name") or "Node"
    quoted_name = urllib.parse.quote(name)
    u = node.get("uuid_or_passwd")
    sni = node.get("sni") or "bing.com"
    url_ip = f"[{ip}]" if (":" in ip and not ip.startswith("[")) else ip
    
    if proto == "vless_reality":
        pbk = node.get("public_key")
        sid = node.get("short_id") or ""
        flow = node.get("flow") or "xtls-rprx-vision"
        return f"vless://{u}@{url_ip}:{port}?encryption=none&flow={flow}&security=reality&sni={sni}&fp=chrome&pbk={pbk}&sid={sid}&type=tcp#{quoted_name}"
    elif proto == "hysteria2":
        return f"hysteria2://{u}@{url_ip}:{port}/?insecure=1&sni={sni}#{quoted_name}"
    elif proto == "tuic":
        return f"tuic://{u}:{u}@{url_ip}:{port}?congestion_control=bbr&alpn=h3&sni={sni}&allow_insecure=1#{quoted_name}"
    elif proto == "trojan":
        return f"trojan://{u}@{url_ip}:{port}?security=tls&sni={sni}&allowInsecure=1#{quoted_name}"
    elif proto == "vmess_ws":
        ws_path = node.get("ws_path") or "/vmess"
        vj = {
            "v": "2",
            "ps": name,
            "add": ip,
            "port": port,
            "id": u,
            "aid": "0",
            "scy": "auto",
            "net": "ws",
            "type": "none",
            "host": "",
            "path": ws_path,
            "tls": ""
        }
        b64 = base64.b64encode(json.dumps(vj).encode()).decode()
        return f"vmess://{b64}"
    return ""

def build_clash_meta_yaml(nodes, rules_cfg=None, sub_title=None):
    if rules_cfg is None:
        rules_cfg = get_subscription_rules()
    if not sub_title:
        sub_title = rules_cfg.get("sub_title") or "Komari Pro 优质节点"

    proxies = []
    names = []
    for n in nodes:
        proto = n.get("protocol")
        name = n.get("name")
        is_relay = n.get("is_relay")
        if is_relay and n.get("relay_server_ip"):
            ip = n["relay_server_ip"]
            port = n.get("relay_port") or n.get("port")
        else:
            ip = n.get("server_ip")
            port = n.get("port")
        u = n.get("uuid_or_passwd")
        sni = n.get("sni") or "addons.mozilla.org"

        if not ip or not port:
            continue

        names.append(name)
        if proto == "vless_reality" or (proto == "vless" and n.get("public_key")):
            proxies.append(f"""  - name: "{name}"
    type: vless
    server: "{ip}"
    port: {port}
    uuid: "{u}"
    network: tcp
    tls: true
    udp: true
    flow: "{n.get('flow') or 'xtls-rprx-vision'}"
    servername: "{sni}"
    reality-opts:
      public-key: "{n.get('public_key')}"
      short-id: "{n.get('short_id') or ''}"
    client-fingerprint: chrome""")
        elif proto == "hysteria2":
            proxies.append(f"""  - name: "{name}"
    type: hysteria2
    server: "{ip}"
    port: {port}
    password: "{u}"
    sni: {sni}
    skip-cert-verify: true
    alpn:
      - h3""")
        elif proto == "tuic":
            proxies.append(f"""  - name: "{name}"
    type: tuic
    server: "{ip}"
    port: {port}
    uuid: {u}
    password: {u}
    sni: {sni}
    skip-cert-verify: true
    congestion-controller: bbr
    alpn: [h3]""")
        elif proto == "trojan":
            proxies.append(f"""  - name: "{name}"
    type: trojan
    server: "{ip}"
    port: {port}
    password: "{u}"
    sni: {sni}
    skip-cert-verify: true
    udp: true""")
        elif proto in ["vmess", "vmess_ws"]:
            proxies.append(f"""  - name: "{name}"
    type: vmess
    server: "{ip}"
    port: {port}
    uuid: {u}
    alterId: 0
    cipher: auto
    network: ws
    ws-opts:
      path: {n.get('ws_path') or '/vmess'}""")

    proxies_text = "\n".join(proxies) if proxies else "  - name: DIRECT\n    type: direct"
    proxy_names = "\n".join([f'      - "{x}"' for x in names]) if names else '      - DIRECT'

    proxy_groups = []
    # 1. Main Proxy selection group
    auto_tag = "      - 自动优选\n" if rules_cfg.get("enable_auto_group") and names else ""
    proxy_groups.append(f"""  - name: PROXY
    type: select
    proxies:
{auto_tag}{proxy_names}
      - DIRECT""")

    # 2. Auto group
    if rules_cfg.get("enable_auto_group") and names:
        proxy_groups.append(f"""  - name: 自动优选
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50
    proxies:
{proxy_names}""")

    groups_text = "\n".join(proxy_groups)

    # Valid targets whitelist for safe fallback
    valid_targets = set(names) | {"PROXY", "DIRECT", "REJECT"}
    if rules_cfg.get("enable_auto_group") and names:
        valid_targets.add("自动优选")

    def safe_target(t, default="PROXY"):
        if not t or t not in valid_targets:
            return default
        return t

    # Build rules list
    rules_list = []

    # 1. User custom rules
    custom = rules_cfg.get("custom_rules", "").strip()
    if custom:
        rules_list.append("  # === 自定义分流规则 ===")
        for line in custom.splitlines():
            line = line.strip()
            if line:
                if not line.startswith("-") and not line.startswith("#"):
                    line = f"- {line}"
                parts = [p.strip() for p in line.lstrip("- ").split(",")]
                if len(parts) >= 3:
                    tgt = parts[2]
                    if tgt not in valid_targets:
                        parts[2] = "PROXY"
                        line = f"- {','.join(parts)}"
                rules_list.append(f"  {line}")

    # 2. AI services
    if rules_cfg.get("proxy_ai"):
        t_ai = safe_target(rules_cfg.get("target_ai"), "PROXY")
        rules_list.append(f"  # === 🤖 AI 大模型服务 (ChatGPT / Claude / Gemini) -> {t_ai} ===")
        rules_list.append(f"  - GEOSITE,openai,{t_ai}")
        rules_list.append(f"  - GEOSITE,anthropic,{t_ai}")
        rules_list.append(f"  - GEOSITE,google-gemini,{t_ai}")
        rules_list.append(f"  - DOMAIN-SUFFIX,chatgpt.com,{t_ai}")
        rules_list.append(f"  - DOMAIN-SUFFIX,openai.com,{t_ai}")
        rules_list.append(f"  - DOMAIN-SUFFIX,oaistatic.com,{t_ai}")
        rules_list.append(f"  - DOMAIN-SUFFIX,oaiusercontent.com,{t_ai}")
        rules_list.append(f"  - DOMAIN-SUFFIX,anthropic.com,{t_ai}")
        rules_list.append(f"  - DOMAIN-SUFFIX,claude.ai,{t_ai}")
        rules_list.append(f"  - DOMAIN-SUFFIX,gemini.google.com,{t_ai}")
        rules_list.append(f"  - DOMAIN-SUFFIX,copilot.microsoft.com,{t_ai}")

    # 3. Telegram
    if rules_cfg.get("proxy_tg"):
        t_tg = safe_target(rules_cfg.get("target_tg"), "PROXY")
        rules_list.append(f"  # === ✈️ Telegram 社交专线 -> {t_tg} ===")
        rules_list.append(f"  - GEOSITE,telegram,{t_tg}")
        rules_list.append(f"  - IP-CIDR,91.108.4.0/22,{t_tg},no-resolve")
        rules_list.append(f"  - IP-CIDR,91.108.8.0/22,{t_tg},no-resolve")
        rules_list.append(f"  - IP-CIDR,91.108.12.0/22,{t_tg},no-resolve")
        rules_list.append(f"  - IP-CIDR,91.108.16.0/22,{t_tg},no-resolve")
        rules_list.append(f"  - IP-CIDR,91.108.56.0/22,{t_tg},no-resolve")
        rules_list.append(f"  - IP-CIDR,149.154.160.0/20,{t_tg},no-resolve")
        rules_list.append(f"  - IP-CIDR,149.154.164.0/22,{t_tg},no-resolve")
        rules_list.append(f"  - IP-CIDR,149.154.168.0/22,{t_tg},no-resolve")
        rules_list.append(f"  - IP-CIDR,149.154.172.0/22,{t_tg},no-resolve")

    # 4. Overseas Streaming Media
    if rules_cfg.get("proxy_media"):
        t_media = safe_target(rules_cfg.get("target_media"), "PROXY")
        rules_list.append(f"  # === 🎬 海外主流流媒体 (YouTube / Netflix / Spotify) -> {t_media} ===")
        rules_list.append(f"  - GEOSITE,youtube,{t_media}")
        rules_list.append(f"  - GEOSITE,netflix,{t_media}")
        rules_list.append(f"  - GEOSITE,disney,{t_media}")
        rules_list.append(f"  - GEOSITE,spotify,{t_media}")
        rules_list.append(f"  - DOMAIN-SUFFIX,youtube.com,{t_media}")
        rules_list.append(f"  - DOMAIN-SUFFIX,googlevideo.com,{t_media}")
        rules_list.append(f"  - DOMAIN-SUFFIX,netflix.com,{t_media}")
        rules_list.append(f"  - DOMAIN-SUFFIX,nflxvideo.net,{t_media}")
        rules_list.append(f"  - DOMAIN-SUFFIX,spotify.com,{t_media}")

    # 5. Developer Services
    if rules_cfg.get("proxy_dev"):
        t_dev = safe_target(rules_cfg.get("target_dev"), "PROXY")
        rules_list.append(f"  # === 💻 开发者服务加速 (GitHub / Docker / Hugging Face) -> {t_dev} ===")
        rules_list.append(f"  - GEOSITE,github,{t_dev}")
        rules_list.append(f"  - DOMAIN-SUFFIX,github.com,{t_dev}")
        rules_list.append(f"  - DOMAIN-SUFFIX,githubusercontent.com,{t_dev}")
        rules_list.append(f"  - DOMAIN-SUFFIX,docker.com,{t_dev}")
        rules_list.append(f"  - DOMAIN-SUFFIX,docker.io,{t_dev}")
        rules_list.append(f"  - DOMAIN-SUFFIX,huggingface.co,{t_dev}")

    # 6. Game Platforms Direct
    if rules_cfg.get("direct_games"):
        t_games = safe_target(rules_cfg.get("target_games"), "DIRECT")
        rules_list.append(f"  # === 🎮 主流游戏平台直连 (Steam / Epic / 暴雪) -> {t_games} ===")
        rules_list.append(f"  - GEOSITE,steam@cn,{t_games}")
        rules_list.append(f"  - GEOSITE,epicgames,{t_games}")
        rules_list.append(f"  - GEOSITE,blizzard,{t_games}")
        rules_list.append(f"  - DOMAIN-SUFFIX,steamserver.net,{t_games}")
        rules_list.append(f"  - DOMAIN-SUFFIX,steamcontent.com,{t_games}")
        rules_list.append(f"  - DOMAIN-SUFFIX,epicgames.com,{t_games}")

    # 7. BT / PT Direct rule
    if rules_cfg.get("direct_bt", True):
        rules_list.append("  # === BT / PT 下载直连防封与防跑流量 ===")
        rules_list.append("  - PROCESS-NAME,qbittorrent,DIRECT")
        rules_list.append("  - PROCESS-NAME,qbittorrent-nox,DIRECT")
        rules_list.append("  - PROCESS-NAME,Transmission,DIRECT")
        rules_list.append("  - PROCESS-NAME,transmission-daemon,DIRECT")
        rules_list.append("  - PROCESS-NAME,aria2c,DIRECT")
        rules_list.append("  - PROCESS-NAME,fdm,DIRECT")
        rules_list.append("  - GEOSITE,category-pt,DIRECT")
        rules_list.append("  - DOMAIN-KEYWORD,tracker,DIRECT")
        rules_list.append("  - DOMAIN-KEYWORD,torrent,DIRECT")
        rules_list.append("  - DOMAIN-KEYWORD,peer,DIRECT")

    # 3. LAN Direct rule
    if rules_cfg.get("direct_lan", True):
        rules_list.append("  # === 本地局域网与私有 IP 直连 ===")
        rules_list.append("  - GEOIP,LAN,DIRECT,no-resolve")
        rules_list.append("  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve")
        rules_list.append("  - IP-CIDR,172.16.0.0/12,DIRECT,no-resolve")
        rules_list.append("  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve")
        rules_list.append("  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve")
        rules_list.append("  - IP-CIDR6,::1/128,DIRECT,no-resolve")
        rules_list.append("  - IP-CIDR6,fc00::/7,DIRECT,no-resolve")
        rules_list.append("  - IP-CIDR6,fe80::/10,DIRECT,no-resolve")

    # 4. Ad blocking
    if rules_cfg.get("block_ads", False):
        rules_list.append("  # === 广告拦截 ===")
        rules_list.append("  - GEOSITE,category-ads-all,REJECT")

    # 5. China Direct rule
    if rules_cfg.get("direct_cn", True):
        rules_list.append("  # === 中国大陆域名与 IP 直连 ===")
        rules_list.append("  - DOMAIN-SUFFIX,cn,DIRECT")
        rules_list.append("  - GEOIP,CN,DIRECT,no-resolve")

    # 6. Final match
    final = rules_cfg.get("final_match") or "PROXY"
    rules_list.append(f"  - MATCH,{final}")

    rules_yaml = "\n".join(rules_list)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return f"""# ========================================================
# 🚀 订阅名称: {sub_title}
# ⏰ 更新时间: {now_str}
# ========================================================

port: 7890
socks-port: 7891
allow-lan: true
mode: rule
log-level: info
ipv6: false
geodata-mode: false
geox-url:
  geoip: "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/geoip.dat"
  geosite: "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/geosite.dat"
  mmdb: "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/country.mmdb"

proxies:
{proxies_text}

proxy-groups:
{groups_text}

rules:
{rules_yaml}
"""

def build_sing_box_client_profile(nodes, rules_cfg=None, sub_title=None):
    if rules_cfg is None:
        rules_cfg = get_subscription_rules()

    outbounds = []
    node_tags = []

    for n in nodes:
        proto = n.get("protocol")
        name = n.get("name") or f"Node-{n.get('id')}"
        is_relay = n.get("is_relay")
        if is_relay and n.get("relay_server_ip"):
            ip = n["relay_server_ip"]
            port = n.get("relay_port") or n.get("port")
        else:
            ip = n.get("server_ip")
            port = n.get("port")
        u = n.get("uuid_or_passwd")
        sni = n.get("sni") or "addons.mozilla.org"

        if not ip or not port:
            continue
        try:
            port = int(port)
        except Exception:
            continue

        tag = name
        base_tag = tag
        c_idx = 1
        while tag in node_tags or tag in ["PROXY", "自动优选", "direct", "block", "dns-out"]:
            tag = f"{base_tag} ({c_idx})"
            c_idx += 1
        node_tags.append(tag)

        if proto == "vless_reality" or (proto == "vless" and n.get("public_key")):
            outbounds.append({
                "type": "vless",
                "tag": tag,
                "server": ip,
                "server_port": port,
                "uuid": u,
                "flow": n.get("flow") or "xtls-rprx-vision",
                "tls": {
                    "enabled": True,
                    "server_name": sni,
                    "reality": {
                        "enabled": True,
                        "public_key": n.get("public_key") or "",
                        "short_id": n.get("short_id") or ""
                    },
                    "utls": {
                        "enabled": True,
                        "fingerprint": "chrome"
                    }
                },
                "packet_encoding": "xudp"
            })
        elif proto == "hysteria2":
            outbounds.append({
                "type": "hysteria2",
                "tag": tag,
                "server": ip,
                "server_port": port,
                "password": u,
                "tls": {
                    "enabled": True,
                    "server_name": sni,
                    "insecure": True,
                    "alpn": ["h3"]
                }
            })
        elif proto == "tuic":
            outbounds.append({
                "type": "tuic",
                "tag": tag,
                "server": ip,
                "server_port": port,
                "uuid": u,
                "password": u,
                "congestion_control": "bbr",
                "tls": {
                    "enabled": True,
                    "server_name": sni,
                    "insecure": True,
                    "alpn": ["h3"]
                }
            })
        elif proto == "trojan":
            outbounds.append({
                "type": "trojan",
                "tag": tag,
                "server": ip,
                "server_port": port,
                "password": u,
                "tls": {
                    "enabled": True,
                    "server_name": sni,
                    "insecure": True
                }
            })
        elif proto in ["vmess", "vmess_ws"]:
            outbounds.append({
                "type": "vmess",
                "tag": tag,
                "server": ip,
                "server_port": port,
                "uuid": u,
                "security": "auto",
                "transport": {
                    "type": "ws",
                    "path": n.get("ws_path") or "/vmess"
                }
            })

    # Group outbounds
    selector_tags = []
    if rules_cfg.get("enable_auto_group", True) and node_tags:
        selector_tags.append("自动优选")
    selector_tags.extend(node_tags)
    selector_tags.append("direct")

    group_outbounds = []
    group_outbounds.append({
        "type": "selector",
        "tag": "PROXY",
        "outbounds": selector_tags if selector_tags else ["direct"],
        "default": selector_tags[0] if selector_tags else "direct"
    })

    if rules_cfg.get("enable_auto_group", True) and node_tags:
        group_outbounds.append({
            "type": "urltest",
            "tag": "自动优选",
            "outbounds": list(node_tags),
            "url": "http://www.gstatic.com/generate_204",
            "interval": "5m",
            "tolerance": 50
        })

    group_outbounds.extend([
        {"type": "direct", "tag": "direct"},
        {"type": "block", "tag": "block"}
    ])

    final_outbounds = group_outbounds + outbounds

    valid_sb_tags = set([o["tag"] for o in final_outbounds])

    def safe_sb_target(t, default="PROXY"):
        if not t:
            return default
        if t in ["DIRECT", "direct"]:
            return "direct"
        if t in ["REJECT", "block"]:
            return "block"
        if t in valid_sb_tags:
            return t
        return default

    # Route rules
    route_rules = [
        {"action": "sniff"},
        {"protocol": "dns", "action": "hijack-dns"},
        {"clash_mode": "Direct", "outbound": "direct"},
        {"clash_mode": "Global", "outbound": "PROXY"}
    ]

    # 1. Custom rules
    custom = rules_cfg.get("custom_rules", "").strip()
    if custom:
        for line in custom.splitlines():
            line = line.strip().lstrip("- ")
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                rtype, rval, rtarget = parts[0].upper(), parts[1], parts[2]
                target_out = "direct" if rtarget.upper() == "DIRECT" else ("block" if rtarget.upper() == "REJECT" else rtarget)
                target_out = safe_sb_target(target_out, "PROXY")
                if rtype in ["DOMAIN-SUFFIX", "DOMAIN"]:
                    route_rules.append({"domain_suffix": [rval], "outbound": target_out})
                elif rtype in ["DOMAIN-KEYWORD"]:
                    route_rules.append({"domain_keyword": [rval], "outbound": target_out})
                elif rtype in ["IP-CIDR", "IP-CIDR6"]:
                    route_rules.append({"ip_cidr": [rval], "outbound": target_out})

    # 2. BT / PT Direct rule
    if rules_cfg.get("direct_bt", True):
        route_rules.append({
            "process_name": [
                "qbittorrent", "qbittorrent-nox", "Transmission",
                "transmission-daemon", "aria2c", "fdm"
            ],
            "outbound": "direct"
        })
        route_rules.append({
            "domain_keyword": ["tracker", "torrent", "peer"],
            "outbound": "direct"
        })

    # 3. LAN Direct rule
    if rules_cfg.get("direct_lan", True):
        route_rules.append({
            "ip_cidr": [
                "127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
                "::1/128", "fc00::/7", "fe80::/10"
            ],
            "outbound": "direct"
        })

    # 4. Ad blocking
    if rules_cfg.get("block_ads", False):
        route_rules.append({
            "domain_keyword": ["adservice", "googleads", "pagead", "doubleclick"],
            "outbound": "block"
        })

    # 5. AI Services
    if rules_cfg.get("proxy_ai"):
        t_ai = safe_sb_target(rules_cfg.get("target_ai"), "PROXY")
        route_rules.append({
            "domain_suffix": [
                "chatgpt.com", "openai.com", "oaistatic.com", "oaiusercontent.com",
                "anthropic.com", "claude.ai", "gemini.google.com", "copilot.microsoft.com"
            ],
            "outbound": t_ai
        })

    # 6. Telegram
    if rules_cfg.get("proxy_tg"):
        t_tg = safe_sb_target(rules_cfg.get("target_tg"), "PROXY")
        route_rules.append({
            "ip_cidr": [
                "91.108.4.0/22", "91.108.8.0/22", "91.108.12.0/22", "91.108.16.0/22",
                "91.108.56.0/22", "149.154.160.0/20", "149.154.164.0/22",
                "149.154.168.0/22", "149.154.172.0/22"
            ],
            "outbound": t_tg
        })

    # 7. Media
    if rules_cfg.get("proxy_media"):
        t_media = safe_sb_target(rules_cfg.get("target_media"), "PROXY")
        route_rules.append({
            "domain_suffix": [
                "youtube.com", "googlevideo.com", "netflix.com", "nflxvideo.net", "spotify.com"
            ],
            "outbound": t_media
        })

    # 8. Developer
    if rules_cfg.get("proxy_dev"):
        t_dev = safe_sb_target(rules_cfg.get("target_dev"), "PROXY")
        route_rules.append({
            "domain_suffix": [
                "github.com", "githubusercontent.com", "docker.com", "docker.io", "huggingface.co"
            ],
            "outbound": t_dev
        })

    # 9. Game platforms
    if rules_cfg.get("direct_games"):
        t_games = safe_sb_target(rules_cfg.get("target_games"), "direct")
        route_rules.append({
            "domain_suffix": [
                "steamserver.net", "steamcontent.com", "epicgames.com"
            ],
            "outbound": t_games
        })

    # 10. China Direct
    if rules_cfg.get("direct_cn", True):
        route_rules.append({
            "domain_suffix": [
                ".cn", "baidu.com", "qq.com", "163.com", "aliyun.com", "taobao.com", "jd.com", "bilibili.com",
                "zhihu.com", "weibo.com", "sina.com.cn", "sohu.com", "douyin.com", "xiaohongshu.com"
            ],
            "outbound": "direct"
        })

    final_match = rules_cfg.get("final_match") or "PROXY"
    final_outbound = "direct" if final_match == "DIRECT" else "PROXY"

    return {
        "log": {"level": "info", "timestamp": True},
        "dns": {
            "servers": [
                {"tag": "dns-remote", "type": "tcp", "server": "1.1.1.1", "detour": "PROXY"},
                {"tag": "dns-direct", "type": "udp", "server": "223.5.5.5", "detour": "direct"}
            ],
            "rules": [
                {"clash_mode": "Global", "server": "dns-remote"},
                {"clash_mode": "Direct", "server": "dns-direct"}
            ],
            "strategy": "prefer_ipv4"
        },
        "inbounds": [
            {
                "type": "mixed",
                "tag": "mixed-in",
                "listen": "127.0.0.1",
                "listen_port": 2080
            },
            {
                "type": "tun",
                "tag": "tun-in",
                "interface_name": "tun0",
                "address": ["172.19.0.1/30", "fdfe:dcba:9876::1/126"],
                "auto_route": True,
                "strict_route": True,
                "stack": "system"
            }
        ],
        "outbounds": final_outbounds,
        "route": {
            "auto_detect_interface": True,
            "default_domain_resolver": "dns-direct",
            "final": final_outbound,
            "rules": route_rules
        }
    }

_traffic_lock = threading.Lock()

def record_user_traffic(traffic_dict):
    """
    traffic_dict: dict of { sub_id (int or str): delta_bytes (int) }
    Updates subscriptions table with real-time consumed bytes, and enforces quota cutoffs.
    """
    if not traffic_dict:
        return
    with _traffic_lock:
        try:
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            quota_exceeded = False
            for sub_id, delta in traffic_dict.items():
                try:
                    sid = int(sub_id)
                    delta_b = int(delta or 0)
                except (ValueError, TypeError):
                    continue
                if delta_b <= 0:
                    continue
                c.execute(
                    "UPDATE subscriptions SET traffic_used_bytes = COALESCE(traffic_used_bytes, 0) + ? WHERE id = ?",
                    (delta_b, sid)
                )
                if c.rowcount == 0:
                    # Fallback to the first active subscription if sid not explicitly matched
                    c.execute(
                        "UPDATE subscriptions SET traffic_used_bytes = COALESCE(traffic_used_bytes, 0) + ? WHERE id = (SELECT id FROM subscriptions ORDER BY id ASC LIMIT 1)",
                        (delta_b,)
                    )
                    c.execute("SELECT traffic_limit_bytes, traffic_used_bytes FROM subscriptions ORDER BY id ASC LIMIT 1")
                else:
                    c.execute("SELECT traffic_limit_bytes, traffic_used_bytes FROM subscriptions WHERE id = ?", (sid,))
                row = c.fetchone()
                if row and row[0] is not None and row[1] is not None:
                    limit_b = int(row[0] or 0)
                    used_b = int(row[1] or 0)
                    if limit_b > 0 and used_b >= limit_b:
                        quota_exceeded = True
            conn.commit()
            conn.close()

            if quota_exceeded:
                get_active_users(force_refresh=True)
                terminate_clash_connections()
        except Exception as e:
            print(f"[Traffic] Failed to record traffic: {e}")

def terminate_clash_connections():
    try:
        req = urllib.request.Request("http://127.0.0.1:9090/connections", method="DELETE")
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass

class TrafficCollector:
    def __init__(self, clash_api_url="http://127.0.0.1:9090"):
        self.clash_api_url = clash_api_url
        self.tracked_conns = {}  # conn_id: (upload, download, sub_id)
        self.last_global_total = None
        self.last_active_sub_id = None
        self.recent_subs = {}  # sub_id_str: timestamp

    def extract_sub_id(self, c):
        meta = c.get("metadata") or {}
        meta_user = str(meta.get("user") or "")
        if meta_user.startswith("sub_"):
            try: return int(meta_user.replace("sub_", ""))
            except ValueError: pass
        elif meta_user == "default": return 1

        u = str(c.get("user") or "")
        if u.startswith("sub_"):
            try: return int(u.replace("sub_", ""))
            except ValueError: pass
        elif u == "default": return 1

        for ch in c.get("chains") or []:
            s_ch = str(ch)
            if "out-sub-" in s_ch:
                m = re.search(r"out-sub-(\d+)", s_ch)
                if m: return int(m.group(1))

        rule = str(c.get("rule") or "")
        m = re.search(r"sub_(\d+)", rule)
        if m: return int(m.group(1))

        rp = str(c.get("rulePayload") or "")
        m = re.search(r"sub_(\d+)", rp)
        if m: return int(m.group(1))
        return None

    def poll_once(self):
        try:
            req = urllib.request.Request(f"{self.clash_api_url}/connections")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
        except Exception:
            self.tracked_conns.clear()
            self.last_global_total = None
            return {}

        dl_total = int(data.get("downloadTotal") or 0)
        up_total = int(data.get("uploadTotal") or 0)
        global_total = dl_total + up_total

        connections = data.get("connections", [])
        current_ids = set()
        user_deltas = {}
        sum_active_deltas = 0
        now = time.time()

        for c in connections:
            conn_id = c.get("id")
            if not conn_id:
                continue
            current_ids.add(conn_id)

            sub_id = self.extract_sub_id(c)
            if sub_id is None and conn_id in self.tracked_conns:
                sub_id = self.tracked_conns[conn_id][2]

            u = int(c.get("upload") or 0)
            d = int(c.get("download") or 0)

            if conn_id in self.tracked_conns:
                last_u, last_d, _ = self.tracked_conns[conn_id]
                delta_u = max(0, u - last_u)
                delta_d = max(0, d - last_d)
            else:
                delta_u = u
                delta_d = d

            self.tracked_conns[conn_id] = (u, d, sub_id)
            delta = delta_u + delta_d

            if sub_id is not None:
                sid_str = str(sub_id)
                self.recent_subs[sid_str] = now
                self.last_active_sub_id = sub_id
                if delta > 0:
                    user_deltas[sub_id] = user_deltas.get(sub_id, 0) + delta
                    sum_active_deltas += delta
            else:
                sum_active_deltas += delta

        # Clean closed connections
        closed_ids = [cid for cid in self.tracked_conns if cid not in current_ids]
        for cid in closed_ids:
            del self.tracked_conns[cid]

        # Attribute unaccounted bytes from short-lived connections
        if self.last_global_total is not None:
            if global_total < self.last_global_total:
                # Core restarted
                self.tracked_conns.clear()
                self.last_global_total = global_total
            elif global_total >= self.last_global_total:
                global_delta = global_total - self.last_global_total
                if global_delta > sum_active_deltas:
                    unaccounted = global_delta - sum_active_deltas
                    if len(user_deltas) == 1:
                        target_sub = next(iter(user_deltas.keys()))
                        user_deltas[target_sub] = user_deltas.get(target_sub, 0) + unaccounted
                    elif len(user_deltas) > 1:
                        total_active = sum(user_deltas.values()) or 1
                        for uid in list(user_deltas.keys()):
                            user_deltas[uid] += int(unaccounted * (user_deltas[uid] / total_active))
                    else:
                        target_sub = self.last_active_sub_id
                        if not target_sub and self.recent_subs:
                            try:
                                target_sub = int(max(self.recent_subs.keys(), key=lambda k: self.recent_subs[k]))
                            except Exception:
                                target_sub = 1
                        if not target_sub:
                            target_sub = 1
                        user_deltas[target_sub] = user_deltas.get(target_sub, 0) + unaccounted

        self.last_global_total = global_total
        self.recent_subs = {k: v for k, v in self.recent_subs.items() if now - v < 300}
        return user_deltas

def run_traffic_collector():
    collector = TrafficCollector(clash_api_url="http://127.0.0.1:9090")
    while True:
        try:
            deltas = collector.poll_once()
            if deltas:
                record_user_traffic(deltas)
        except Exception:
            pass
        time.sleep(2)

def build_sing_box_config(nodes_for_server):
    inbounds = []
    seen_ports = set()
    cert_path = "/etc/sing-box/cert.pem"
    key_path = "/etc/sing-box/cert.key"

    # Gather all active users from subscriptions to allow multi-user authorization
    active_users = get_active_users()
    user_outbound_tags = set()

    for n in nodes_for_server:
        if not n.get("enabled"):
            continue
        if n.get("is_external") or n.get("server_uuid") == "external":
            continue
        proto = n.get("protocol")
        port = n.get("port")
        if port in seen_ports:
            continue
        seen_ports.add(port)
        tag = f"{proto}-{n.get('id')}"
        default_u = n.get("uuid_or_passwd")
        sni = n.get("sni") or "addons.mozilla.org"

        users_list = []
        active_uuids = set()
        for u in active_users:
            active_uuids.add(u["uuid"])
            user_outbound_tags.add(u["id"])
            if proto == "vless_reality":
                users_list.append({"name": f"sub_{u['id']}", "uuid": u["uuid"], "flow": n.get("flow") or "xtls-rprx-vision"})
            elif proto == "hysteria2":
                users_list.append({"name": f"sub_{u['id']}", "password": u["uuid"]})
            elif proto == "tuic":
                users_list.append({"name": f"sub_{u['id']}", "uuid": u["uuid"], "password": u["uuid"]})
            elif proto == "trojan":
                users_list.append({"name": f"sub_{u['id']}", "password": u["uuid"]})
            elif proto == "vmess_ws":
                users_list.append({"name": f"sub_{u['id']}", "uuid": u["uuid"]})

        if default_u and default_u not in active_uuids:
            if proto == "vless_reality":
                users_list.append({"name": "default", "uuid": default_u, "flow": n.get("flow") or "xtls-rprx-vision"})
            elif proto == "hysteria2":
                users_list.append({"name": "default", "password": default_u})
            elif proto == "tuic":
                users_list.append({"name": "default", "uuid": default_u, "password": default_u})
            elif proto == "trojan":
                users_list.append({"name": "default", "password": default_u})
            elif proto == "vmess_ws":
                users_list.append({"name": "default", "uuid": default_u})
        
        if proto == "vless_reality":
            inbounds.append({
                "type": "vless",
                "tag": tag,
                "listen": "::",
                "listen_port": port,
                "users": users_list,
                "tls": {
                    "enabled": True,
                    "server_name": sni,
                    "reality": {
                        "enabled": True,
                        "handshake": {
                            "server": sni,
                            "server_port": 443
                        },
                        "private_key": n.get("private_key"),
                        "short_id": [n.get("short_id") or ""]
                    }
                }
            })
        elif proto == "hysteria2":
            inbounds.append({
                "type": "hysteria2",
                "tag": tag,
                "listen": "::",
                "listen_port": port,
                "users": users_list,
                "tls": {
                    "enabled": True,
                    "certificate_path": cert_path,
                    "key_path": key_path
                }
            })
        elif proto == "tuic":
            inbounds.append({
                "type": "tuic",
                "tag": tag,
                "listen": "::",
                "listen_port": port,
                "users": users_list,
                "congestion_control": "bbr",
                "tls": {
                    "enabled": True,
                    "certificate_path": cert_path,
                    "key_path": key_path
                }
            })
        elif proto == "trojan":
            inbounds.append({
                "type": "trojan",
                "tag": tag,
                "listen": "::",
                "listen_port": port,
                "users": users_list,
                "tls": {
                    "enabled": True,
                    "certificate_path": cert_path,
                    "key_path": key_path
                }
            })
        elif proto == "vmess_ws":
            inbounds.append({
                "type": "vmess",
                "tag": tag,
                "listen": "::",
                "listen_port": port,
                "users": users_list,
                "transport": {
                    "type": "ws",
                    "path": n.get("ws_path") or "/vmess"
                }
            })

    outbounds = [{"type": "direct", "tag": f"out-sub-{uid}"} for uid in sorted(user_outbound_tags)]
    outbounds.append({"type": "direct", "tag": "direct"})

    route_rules = [{"auth_user": [f"sub_{uid}"], "outbound": f"out-sub-{uid}"} for uid in sorted(user_outbound_tags)]
    if user_outbound_tags:
        route_rules.append({"auth_user": ["default"], "outbound": f"out-sub-{min(user_outbound_tags)}"})

    config = {
        "log": {"level": "warn", "timestamp": True},
        "experimental": {
            "clash_api": {
                "external_controller": "127.0.0.1:9090"
            }
        },
        "inbounds": inbounds,
        "outbounds": outbounds
    }
    if route_rules:
        config["route"] = {
            "rules": route_rules,
            "final": "direct"
        }
    return config

INSTALL_SCRIPT_TEMPLATE = r'''#!/bin/bash
set -e

# Komari & Sing-box All-In-One Installer (Universal: systemd & OpenRC/Alpine musl/glibc)
# Domain: {DOMAIN}

TOKEN=""
MASTER_URL="https://{DOMAIN}"
INSTALL_PROBE=1
INSTALL_SINGBOX=1
INSTALL_REALM=0
ENABLE_BBR=1
CUSTOM_IP=""

EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --token|-t)
      TOKEN="$2"
      shift 2
      ;;
    -e|--endpoint)
      MASTER_URL="$2"
      shift 2
      ;;
    --ip|-ip|--custom-ipv4)
      CUSTOM_IP="$2"
      shift 2
      ;;
    --skip-probe)
      INSTALL_PROBE=0
      shift
      ;;
    --skip-singbox)
      INSTALL_SINGBOX=0
      shift
      ;;
    --with-realm|--install-realm)
      INSTALL_REALM=1
      shift
      ;;
    --skip-bbr)
      ENABLE_BBR=0
      shift
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

if [ -z "$TOKEN" ]; then
  echo "[Error] --token is required!"
  echo "Usage: curl -fsSL $MASTER_URL/install-node.sh | bash -s -- --token <KOMARI_SERVER_TOKEN>"
  exit 1
fi

# 0. Intelligent IP Detection & Cloudflare WARP Shield (永恒防错机制)
if [ -z "$CUSTOM_IP" ]; then
  DEF_IF=$(ip route show default 2>/dev/null | grep -v 'warp\|wgcf' | head -n1 | awk '{for(i=1;i<=NF;i++) if($i=="dev") print $(i+1)}')
  if [ -n "$DEF_IF" ]; then
    NIC_IP=$(ip -4 addr show dev "$DEF_IF" scope global 2>/dev/null | grep -oE 'inet [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -n1 | awk '{print $2}')
    EGRESS_IP=$(curl -s4 -m 3 https://api.ipify.org 2>/dev/null || curl -s4 -m 3 https://ifconfig.me 2>/dev/null || true)
    if [[ "$EGRESS_IP" =~ ^104\.28\. ]] || [[ "$EGRESS_IP" =~ ^162\.158\. ]] || [[ "$EGRESS_IP" =~ ^172\.(6[4-9]|7[0-1])\. ]]; then
      if [ -n "$NIC_IP" ] && ! [[ "$NIC_IP" =~ ^(10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|100\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7])\.) ]]; then
        CUSTOM_IP="$NIC_IP"
        echo "[WARP Shield] 检测到当前出口为 Cloudflare WARP 虚拟 IP ($EGRESS_IP)，已自动锁定物理网卡公网 IP: $CUSTOM_IP"
      fi
    fi
  fi
fi

if [ -n "$CUSTOM_IP" ]; then
  echo "[Info] 本机公网入站 IP 锁定为: $CUSTOM_IP"
  curl -s -k -m 6 "$MASTER_URL/api/node-mgr/agent/set-server-ip?token=$TOKEN&ip=$CUSTOM_IP" >/dev/null 2>&1 || true
fi

echo "======================================================"
echo " Starting Komari + Sing-box Node Agent Installation   "
echo "======================================================"

# Detect init system & libc type
INIT_SYSTEM="systemd"
if [ -f /etc/alpine-release ] || (command -v rc-service >/dev/null 2>&1 && ! command -v systemctl >/dev/null 2>&1); then
  INIT_SYSTEM="openrc"
fi
echo "[Info] Detected init system: $INIT_SYSTEM"

# 1. Install prerequisites
echo "[1/5] Installing system dependencies..."
if [ -x "$(command -v apt-get)" ]; then
  apt-get update -qq && apt-get install -y -qq curl wget tar openssl jq python3 ca-certificates >/dev/null 2>&1 || true
elif [ -x "$(command -v yum)" ]; then
  yum install -y curl wget tar openssl jq python3 ca-certificates >/dev/null 2>&1 || true
elif [ -x "$(command -v dnf)" ]; then
  dnf install -y curl wget tar openssl jq python3 ca-certificates >/dev/null 2>&1 || true
elif [ -x "$(command -v apk)" ]; then
  apk update >/dev/null 2>&1 || true
  apk add --no-cache curl wget tar openssl jq python3 bash ca-certificates gcompat >/dev/null 2>&1 || true
fi

# 2. Enable TCP BBR Congestion Control
if [ "$ENABLE_BBR" -eq 1 ]; then
  echo "[2/5] Optimizing TCP congestion control: Checking & Enabling BBR..."
  CURRENT_CC=$(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || true)
  if [ "$CURRENT_CC" = "bbr" ]; then
    echo "[Info] TCP BBR is already enabled and active."
  else
    modprobe tcp_bbr >/dev/null 2>&1 || true
    if [ -d /etc/modules-load.d ]; then
      echo "tcp_bbr" > /etc/modules-load.d/bbr.conf 2>/dev/null || true
    fi

    sed -i '/net.core.default_qdisc/d' /etc/sysctl.conf 2>/dev/null || true
    sed -i '/net.ipv4.tcp_congestion_control/d' /etc/sysctl.conf 2>/dev/null || true
    echo "net.core.default_qdisc = fq" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_congestion_control = bbr" >> /etc/sysctl.conf

    if [ -d /etc/sysctl.d ]; then
      echo "net.core.default_qdisc = fq" > /etc/sysctl.d/99-bbr.conf 2>/dev/null || true
      echo "net.ipv4.tcp_congestion_control = bbr" >> /etc/sysctl.d/99-bbr.conf 2>/dev/null || true
    fi

    sysctl -w net.core.default_qdisc=fq >/dev/null 2>&1 || true
    sysctl -w net.ipv4.tcp_congestion_control=bbr >/dev/null 2>&1 || true
    sysctl -e -p /etc/sysctl.conf >/dev/null 2>&1 || sysctl --system >/dev/null 2>&1 || true

    NEW_CC=$(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || true)
    if [ "$NEW_CC" = "bbr" ]; then
      echo "[Success] TCP BBR congestion control successfully enabled and persisted!"
    else
      echo "[Notice] Failed to activate BBR (current: ${NEW_CC:-unknown}), kernel may lack tcp_bbr module or virtualization container (LXC/OpenVZ) is restricted."
    fi
  fi
fi

# 3. Install Sing-box core
if [ "$INSTALL_SINGBOX" -eq 1 ]; then
  echo "[3/5] Installing Sing-box high performance core..."
ARCH=$(uname -m)
case $ARCH in
  x86_64) SING_ARCH="amd64" ;;
  aarch64|arm64) SING_ARCH="arm64" ;;
  *) echo "Unsupported arch: $ARCH"; exit 1 ;;
esac

MUSL_SUFFIX=""
if [ -f /etc/alpine-release ] || (ldd --version 2>&1 | grep -qi musl); then
  MUSL_SUFFIX="-musl"
  echo "[Info] Musl libc detected (Alpine), using musl binary build"
fi

mkdir -p /etc/sing-box
if [ ! -f /etc/sing-box/cert.key ] || [ ! -f /etc/sing-box/cert.pem ]; then
  if command -v openssl >/dev/null 2>&1; then
    openssl req -x509 -newkey rsa:2048 -nodes -keyout /etc/sing-box/cert.key -out /etc/sing-box/cert.pem -days 3650 \
      -subj "/CN=bing.com" \
      -addext "subjectAltName=DNS:bing.com,DNS:*.bing.com,DNS:addons.mozilla.org,DNS:gateway.icloud.com,DNS:www.apple.com,DNS:komari.yohoo.xyz,IP:127.0.0.1" >/dev/null 2>&1 || \
    openssl req -x509 -newkey rsa:2048 -nodes -keyout /etc/sing-box/cert.key -out /etc/sing-box/cert.pem -days 3650 \
      -subj "/CN=bing.com" >/dev/null 2>&1 || true
  fi
fi

# Ensure sing-box binary is valid and runnable
if [ ! -f /usr/local/bin/sing-box ] || ! /usr/local/bin/sing-box version >/dev/null 2>&1; then
  echo "Downloading Sing-box binary (${SING_ARCH}${MUSL_SUFFIX})..."
  mkdir -p /usr/local/bin
  TAR_URL="https://github.com/SagerNet/sing-box/releases/download/v1.14.4/sing-box-1.14.4-linux-${SING_ARCH}${MUSL_SUFFIX}.tar.gz"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$TAR_URL" -o /tmp/sing-box.tar.gz
  elif command -v wget >/dev/null 2>&1; then
    wget -qO /tmp/sing-box.tar.gz "$TAR_URL"
  fi
  tar -xzf /tmp/sing-box.tar.gz -C /tmp
  cp /tmp/sing-box-*/sing-box /usr/local/bin/sing-box
  chmod +x /usr/local/bin/sing-box
  rm -rf /tmp/sing-box*
fi

# Ensure base empty config
if [ ! -f /etc/sing-box/config.json ]; then
  echo '{"log":{"level":"warn"},"inbounds":[],"outbounds":[{"type":"direct","tag":"direct"}]}' > /etc/sing-box/config.json
fi

# Configure Sing-box Service
if [ "$INIT_SYSTEM" = "openrc" ]; then
  cat << 'EOF' > /etc/init.d/sing-box
#!/sbin/openrc-run
name="Sing-box Service"
description="Sing-box Service"
command="/usr/local/bin/sing-box"
command_args="run -c /etc/sing-box/config.json"
pidfile="/run/sing-box.pid"
supervisor=supervise-daemon
supervise_daemon_args="--respawn-max 0 --respawn-delay 5"

depend() {
    need net
    after network
}
EOF
  chmod +x /etc/init.d/sing-box
  rc-update add sing-box default >/dev/null 2>&1 || true
  rc-service sing-box restart >/dev/null 2>&1 || rc-service sing-box start >/dev/null 2>&1 || true
else
  mkdir -p /etc/systemd/system
  cat << EOF > /etc/systemd/system/sing-box.service
[Unit]
Description=Sing-box Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c /etc/sing-box/config.json
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable sing-box.service >/dev/null 2>&1 || true
  systemctl restart sing-box.service || true
fi

fi

# 4. Install Komari Monitor Agent using official installer
if [ "$INSTALL_PROBE" -eq 1 ]; then
  echo "[4/5] Installing Komari Monitor Agent..."
DOWNLOADER=""
if command -v curl >/dev/null 2>&1; then
  DOWNLOADER="curl -fsSL"
elif command -v wget >/dev/null 2>&1; then
  DOWNLOADER="wget -qO-"
fi
PROBE_ARGS=("-e" "$MASTER_URL" "-t" "$TOKEN")
if [ -n "$CUSTOM_IP" ]; then
  PROBE_ARGS+=("--custom-ipv4" "$CUSTOM_IP")
fi
$DOWNLOADER https://raw.githubusercontent.com/komari-monitor/komari-agent/refs/heads/main/install.sh | bash -s -- "${PROBE_ARGS[@]}" "${EXTRA_ARGS[@]}"

fi

# 5. Install Node-Sync Agent Daemon
if [ "$INSTALL_SINGBOX" -eq 1 ] || [ "$INSTALL_REALM" -eq 1 ]; then
  echo "[5/5] Installing Node Configuration Sync Daemon..."
  if [ "$INIT_SYSTEM" = "openrc" ]; then
    rc-service komari-pro-node-sync stop >/dev/null 2>&1 || true
    rc-service komari-pro-node-sync stop >/dev/null 2>&1 || true
  else
    systemctl stop komari-pro-node-sync.service >/dev/null 2>&1 || true
    systemctl stop komari-pro-node-sync.service >/dev/null 2>&1 || true
  fi
  pkill -f komari-pro-node-sync.sh >/dev/null 2>&1 || true
  pkill -f komari-node-sync.sh >/dev/null 2>&1 || true

cat << 'EOF' > /usr/local/bin/komari-pro-node-sync.sh
#!/bin/bash
# Komari Pro Node Sync Service (komari-pro-node-sync)
MASTER_URL="__MASTER_URL__"
TOKEN="__TOKEN__"
CONFIG_FILE="/etc/sing-box/config.json"
MD5_FILE="/etc/sing-box/config.md5"

restart_sing_box() {
  if [ -f "$CONFIG_FILE" ]; then
    PORTS=$(grep -oE '"listen_port"[[:space:]]*:[[:space:]]*[0-9]+' "$CONFIG_FILE" 2>/dev/null | grep -oE '[0-9]+' | sort -u)
    for p in $PORTS; do
      fuser -k -9 ${p}/tcp >/dev/null 2>&1 || true
    done
  fi
  if command -v systemctl >/dev/null 2>&1; then
    systemctl restart sing-box.service >/dev/null 2>&1 || systemctl start sing-box.service >/dev/null 2>&1 || true
  elif command -v rc-service >/dev/null 2>&1; then
    rc-service sing-box restart >/dev/null 2>&1 || {
      killall -9 sing-box >/dev/null 2>&1 || true
      rc-service sing-box zap >/dev/null 2>&1 || true
      rc-service sing-box start >/dev/null 2>&1 || true
    }
  fi
}

restart_realm() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl restart realm.service >/dev/null 2>&1 || systemctl start realm.service >/dev/null 2>&1 || true
  elif command -v rc-service >/dev/null 2>&1 && [ -f /etc/init.d/realm ]; then
    rc-service realm restart >/dev/null 2>&1 || {
      killall -9 realm >/dev/null 2>&1 || pkill -9 -f "realm -c" >/dev/null 2>&1 || true
      rc-service realm zap >/dev/null 2>&1 || true
      rc-service realm start >/dev/null 2>&1 || true
    }
  fi
  if ! is_process_running realm && [ -x /usr/local/bin/realm ] && [ -f /etc/realm/config.toml ]; then
    killall -9 realm >/dev/null 2>&1 || pkill -9 -f "realm -c" >/dev/null 2>&1 || true
    nohup /usr/local/bin/realm -c /etc/realm/config.toml >/dev/null 2>&1 &
  fi
}

is_process_running() {
  pidof "$1" >/dev/null 2>&1 || killall -0 "$1" >/dev/null 2>&1 || pgrep -x "$1" >/dev/null 2>&1
}

TICK=0
UNAUTH_FAIL_COUNT=0
while true; do
  TICK=$((TICK + 1))
  if [ $TICK -ge 300 ]; then TICK=1; fi

  # 1. Fast Traffic Reporting Loop (Runs EVERY 2 seconds)
  if curl -s -m 2 http://127.0.0.1:9090/connections >/dev/null 2>&1; then
    if command -v python3 >/dev/null 2>&1; then
      python3 -c '
import urllib.request, json, sys, os, re, time

STATE_FILE = "/tmp/sb_traffic_state.json"
try:
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
except Exception:
    state = {}

ip_to_sub = state.get("ip_to_sub") or {}
ipport_to_sub = state.get("ipport_to_sub") or {}
pending = state.get("pending_sessions") or {}
log_offset = int(state.get("log_offset") or 0)
tracked = state.get("conns") or {}
recent_subs = state.get("recent_subs") or {}
last_sub = state.get("last_sub")
now = time.time()

# 1. Parse sing-box access log to map IP/Port directly to user ID
sb_log = "/var/log/sing-box/access.log"
if os.path.exists(sb_log):
    try:
        sz = os.path.getsize(sb_log)
        if sz < log_offset:
            log_offset = 0
        elif sz > 10 * 1024 * 1024:
            with open(sb_log, "w") as f_trunc: pass
            log_offset = 0
        with open(sb_log, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(log_offset)
            for line in f:
                m_cid = re.search(r"\[(\d+)\s+[^\]]+\]", line)
                m_conn = re.search(r"inbound connection from ([\d\.:a-fA-F]+):(\d+)", line)
                m_user = re.search(r"\[(sub_\d+|default)\]", line)
                m_ukw = re.search(r"user:\s*(sub_\d+|default)", line)
                if m_cid:
                    cid = m_cid.group(1)
                    if m_conn:
                        ip = m_conn.group(1).strip()
                        port = m_conn.group(2).strip()
                        if cid in pending and "sub" in pending[cid]:
                            sub = pending.pop(cid)["sub"]
                            ip_to_sub[ip] = sub
                            ipport_to_sub[f"{ip}:{port}"] = sub
                            last_sub = sub
                            recent_subs[str(sub)] = now
                        else:
                            pending[cid] = {"ip": ip, "port": port, "time": now}
                    elif m_user or m_ukw:
                        u_str = (m_user or m_ukw).group(1)
                        sub = 1 if u_str == "default" else int(u_str.replace("sub_", ""))
                        if cid in pending and "ip" in pending[cid]:
                            sess = pending.pop(cid)
                            ip = sess["ip"]
                            port = sess["port"]
                            ip_to_sub[ip] = sub
                            ipport_to_sub[f"{ip}:{port}"] = sub
                            last_sub = sub
                            recent_subs[str(sub)] = now
                        else:
                            pending[cid] = {"sub": sub, "time": now}
                elif m_conn and (m_user or m_ukw):
                    ip = m_conn.group(1).strip()
                    port = m_conn.group(2).strip()
                    u_str = (m_user or m_ukw).group(1)
                    sub = 1 if u_str == "default" else int(u_str.replace("sub_", ""))
                    ip_to_sub[ip] = sub
                    ipport_to_sub[f"{ip}:{port}"] = sub
                    last_sub = sub
                    recent_subs[str(sub)] = now
            log_offset = f.tell()
    except Exception:
        pass

for k in list(pending.keys()):
    if now - pending[k].get("time", 0) > 60:
        pending.pop(k, None)
if len(ip_to_sub) > 500:
    ip_to_sub = dict(list(ip_to_sub.items())[-200:])
if len(ipport_to_sub) > 2000:
    ipport_to_sub = dict(list(ipport_to_sub.items())[-500:])

# 2. Query Clash API for active sockets and global byte totals
try:
    req = urllib.request.Request("http://127.0.0.1:9090/connections")
    with urllib.request.urlopen(req, timeout=2) as resp:
        data = json.loads(resp.read().decode())
except Exception:
    sys.exit(0)

dl_total = int(data.get("downloadTotal") or 0)
up_total = int(data.get("uploadTotal") or 0)
global_total = dl_total + up_total

current_ids = set()
deltas = {}
sum_active_deltas = 0

def extract_sub_id(c):
    for ch in c.get("chains") or []:
        s_ch = str(ch)
        if "out-sub-" in s_ch:
            m = re.search(r"out-sub-(\d+)", s_ch)
            if m: return int(m.group(1))

    rule = str(c.get("rule") or "")
    m = re.search(r"sub_(\d+)", rule)
    if m: return int(m.group(1))

    rp = str(c.get("rulePayload") or "")
    m = re.search(r"sub_(\d+)", rp)
    if m: return int(m.group(1))

    meta = c.get("metadata") or {}
    src_ip = meta.get("sourceIP") or ""
    src_port = str(meta.get("sourcePort") or "")
    if src_ip and src_port and f"{src_ip}:{src_port}" in ipport_to_sub:
        return ipport_to_sub[f"{src_ip}:{src_port}"]
    if src_ip and src_ip in ip_to_sub:
        return ip_to_sub[src_ip]

    meta_user = str(meta.get("user") or "")
    if meta_user.startswith("sub_"):
        try: return int(meta_user.replace("sub_", ""))
        except ValueError: pass
    elif meta_user == "default": return 1

    u = str(c.get("user") or "")
    if u.startswith("sub_"):
        try: return int(u.replace("sub_", ""))
        except ValueError: pass
    elif u == "default": return 1
    return None

for c in data.get("connections", []):
    cid = c.get("id")
    if not cid: continue
    current_ids.add(cid)

    sub_id = extract_sub_id(c)
    if sub_id is None and cid in tracked:
        sub_id = tracked[cid][2]

    u = int(c.get("upload") or 0)
    d = int(c.get("download") or 0)

    if cid in tracked:
        lu, ld, _ = tracked[cid]
        du = max(0, u - lu)
        dd = max(0, d - ld)
    else:
        du = u
        dd = d

    tracked[cid] = [u, d, sub_id]
    d_total = du + dd

    if sub_id is not None:
        sid_str = str(sub_id)
        recent_subs[sid_str] = now
        last_sub = sub_id
        if d_total > 0:
            deltas[sid_str] = deltas.get(sid_str, 0) + d_total
            sum_active_deltas += d_total
    else:
        sum_active_deltas += d_total

closed = [cid for cid in tracked if cid not in current_ids]
for cid in closed:
    del tracked[cid]

last_global = int(state.get("global_total") or 0)
if global_total < last_global:
    tracked.clear()
    last_global = global_total
elif last_global > 0 and global_total >= last_global:
    g_delta = global_total - last_global
    if g_delta > sum_active_deltas:
        unacc = g_delta - sum_active_deltas
        if len(deltas) == 1:
            uid = next(iter(deltas.keys()))
            deltas[uid] = deltas.get(uid, 0) + unacc
        elif len(deltas) > 1:
            total_active = sum(deltas.values()) or 1
            for uid in list(deltas.keys()):
                deltas[uid] += int(unacc * (deltas[uid] / total_active))
        else:
            target = str(last_sub) if last_sub else None
            if not target and recent_subs:
                target = max(recent_subs.keys(), key=lambda k: recent_subs[k])
            if target:
                deltas[target] = deltas.get(target, 0) + unacc

recent_subs = {k: v for k, v in recent_subs.items() if now - v < 600}

state["conns"] = tracked
state["global_total"] = global_total
state["last_sub"] = last_sub
state["recent_subs"] = recent_subs
state["ip_to_sub"] = ip_to_sub
state["ipport_to_sub"] = ipport_to_sub
state["pending_sessions"] = pending
state["log_offset"] = log_offset
try:
    with open(STATE_FILE, "w") as f: json.dump(state, f)
except Exception: pass

if deltas:
    try:
        master_url = sys.argv[1]
        token = sys.argv[2]
        post_data = json.dumps({"token": token, "traffic": deltas}).encode()
        post_req = urllib.request.Request(
            f"{master_url}/api/node-mgr/agent/report-traffic?token={token}",
            data=post_data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(post_req, timeout=5)
    except Exception: pass
' "$MASTER_URL" "$TOKEN" >/dev/null 2>&1 || true
    fi
  fi

  # 2. Config & Health Checks (Runs every 30 seconds or on first tick)
  if [ $TICK -eq 1 ] || [ $((TICK % 6)) -eq 0 ]; then
    # Ensure TLS certificate exists for Hysteria2 / TUIC / Trojan
    if [ ! -f /etc/sing-box/cert.key ] || [ ! -f /etc/sing-box/cert.pem ]; then
      if command -v openssl >/dev/null 2>&1; then
        mkdir -p /etc/sing-box
        openssl req -x509 -newkey rsa:2048 -nodes -keyout /etc/sing-box/cert.key -out /etc/sing-box/cert.pem -days 3650 \
          -subj "/CN=bing.com" \
          -addext "subjectAltName=DNS:bing.com,DNS:*.bing.com,DNS:addons.mozilla.org,DNS:gateway.icloud.com,DNS:www.apple.com,IP:127.0.0.1" >/dev/null 2>&1 || \
        openssl req -x509 -newkey rsa:2048 -nodes -keyout /etc/sing-box/cert.key -out /etc/sing-box/cert.pem -days 3650 \
          -subj "/CN=bing.com" >/dev/null 2>&1 || true
      fi
    fi

    HTTP_CODE=$(curl -k -s -m 10 -o /tmp/node_cfg.tmp -w "%{http_code}" "$MASTER_URL/api/node-mgr/agent/config?token=$TOKEN" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
      UNAUTH_FAIL_COUNT=$((UNAUTH_FAIL_COUNT + 1))
      echo "[NodeSync] Token unauthorized ($HTTP_CODE). Server might be deleted on master (attempt $UNAUTH_FAIL_COUNT/5)."
      if [ $UNAUTH_FAIL_COUNT -ge 5 ]; then
        echo "[NodeSync Defense] Server confirmed deleted from master! Auto-terminating service to eliminate resource usage."
        if command -v systemctl >/dev/null 2>&1; then
          systemctl stop komari-pro-node-sync.service >/dev/null 2>&1 &
        elif command -v rc-service >/dev/null 2>&1; then
          rc-service komari-pro-node-sync stop >/dev/null 2>&1 &
        fi
        exit 0
      fi
      sleep 20
      continue
    fi

    if [ "$HTTP_CODE" = "200" ]; then
      UNAUTH_FAIL_COUNT=0
      RES=$(cat /tmp/node_cfg.tmp 2>/dev/null || true)
      if [ -n "$RES" ] && echo "$RES" | grep -q '"inbounds"'; then
      NEW_MD5=$(echo "$RES" | md5sum | awk '{print $1}')
      OLD_MD5=$(cat "$MD5_FILE" 2>/dev/null || true)
      if [ "$NEW_MD5" != "$OLD_MD5" ]; then
        echo "[NodeSync] New config received, validating..."
        echo "$RES" > /tmp/new_config.json
        if /usr/local/bin/sing-box check -c /tmp/new_config.json >/dev/null 2>&1; then
          mv /tmp/new_config.json "$CONFIG_FILE"
          echo "$NEW_MD5" > "$MD5_FILE"

          # Auto open firewall ports for all inbounds only when port list changes
          PORTS=$(grep -oE '"listen_port"[[:space:]]*:[[:space:]]*[0-9]+' "$CONFIG_FILE" | grep -oE '[0-9]+' | sort -u)
          OLD_PORTS=$(cat /etc/sing-box/ports.txt 2>/dev/null || true)
          if [ "$PORTS" != "$OLD_PORTS" ]; then
            echo "$PORTS" > /etc/sing-box/ports.txt
            for p in $PORTS; do
              if command -v firewall-cmd >/dev/null 2>&1 && systemctl is-active --quiet firewalld 2>/dev/null; then
                firewall-cmd --add-port=${p}/tcp --permanent >/dev/null 2>&1 || true
                firewall-cmd --add-port=${p}/udp --permanent >/dev/null 2>&1 || true
              fi
              if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
                ufw allow ${p}/tcp >/dev/null 2>&1 || true
                ufw allow ${p}/udp >/dev/null 2>&1 || true
              fi
              iptables -C INPUT -p tcp --dport ${p} -j ACCEPT 2>/dev/null || iptables -I INPUT 1 -p tcp --dport ${p} -j ACCEPT >/dev/null 2>&1 || true
              iptables -C INPUT -p udp --dport ${p} -j ACCEPT 2>/dev/null || iptables -I INPUT 1 -p udp --dport ${p} -j ACCEPT >/dev/null 2>&1 || true
              ip6tables -C INPUT -p tcp --dport ${p} -j ACCEPT 2>/dev/null || ip6tables -I INPUT 1 -p tcp --dport ${p} -j ACCEPT >/dev/null 2>&1 || true
              ip6tables -C INPUT -p udp --dport ${p} -j ACCEPT 2>/dev/null || ip6tables -I INPUT 1 -p udp --dport ${p} -j ACCEPT >/dev/null 2>&1 || true
            done
            if command -v firewall-cmd >/dev/null 2>&1 && systemctl is-active --quiet firewalld 2>/dev/null; then
              firewall-cmd --reload >/dev/null 2>&1 || true
            fi
          fi

          restart_sing_box
          echo "[NodeSync] Sing-box restarted successfully!"
        else
          echo "[NodeSync] Invalid config from master, skipping."
        fi
      fi
    fi
  fi

    # Sync Realm port forward rules
    REALM_RES=$(curl -k -s -m 10 "$MASTER_URL/api/node-mgr/agent/realm-config?token=$TOKEN" 2>/dev/null || true)
    if [ -n "$REALM_RES" ] && echo "$REALM_RES" | grep -q '\[network\]'; then
      if [ ! -x /usr/local/bin/realm ]; then
        ARCH=$(uname -m)
        case "$ARCH" in
          x86_64|amd64) REALM_ARCH="x86_64-unknown-linux-musl" ;;
          aarch64|arm64) REALM_ARCH="aarch64-unknown-linux-musl" ;;
          *) REALM_ARCH="x86_64-unknown-linux-musl" ;;
        esac
        mkdir -p /etc/realm
        curl -fsSL "https://github.com/zhboner/realm/releases/latest/download/realm-${REALM_ARCH}.tar.gz" -o /tmp/realm.tar.gz 2>/dev/null || \
        wget -qO /tmp/realm.tar.gz "https://github.com/zhboner/realm/releases/latest/download/realm-${REALM_ARCH}.tar.gz" 2>/dev/null
        tar -xzf /tmp/realm.tar.gz -C /usr/local/bin/ realm 2>/dev/null
        chmod +x /usr/local/bin/realm 2>/dev/null
        rm -f /tmp/realm.tar.gz
      fi
      REALM_MD5=$(echo "$REALM_RES" | md5sum | awk '{print $1}')
      OLD_REALM_MD5=$(cat /etc/realm/config.md5 2>/dev/null || true)
      if [ "$REALM_MD5" != "$OLD_REALM_MD5" ]; then
        mkdir -p /etc/realm
        echo "$REALM_RES" > /etc/realm/config.toml
        echo "$REALM_MD5" > /etc/realm/config.md5
        R_PORTS=$(grep -oE ':[0-9]+"' /etc/realm/config.toml | tr -d ':"' | sort -u)
        for rp in $R_PORTS; do
          iptables -I INPUT 1 -p tcp --dport ${rp} -j ACCEPT >/dev/null 2>&1 || true
          iptables -I INPUT 1 -p udp --dport ${rp} -j ACCEPT >/dev/null 2>&1 || true
        done
        restart_realm
        echo "[RealmSync] Realm forwarded endpoints updated and service reloaded!"
      fi
    fi

    # Active Health Check & Self-Healing
    if [ -f "$CONFIG_FILE" ] && grep -q '"listen_port"' "$CONFIG_FILE"; then
      if ! is_process_running sing-box; then
        echo "[AutoHeal] Sing-box down detected, restarting..."
        restart_sing_box
      fi
    fi
    if [ -f /etc/realm/config.toml ] && grep -q '\[\[endpoints\]\]' /etc/realm/config.toml; then
      if ! is_process_running realm; then
        echo "[AutoHeal] Realm down detected, restarting..."
        restart_realm
      fi
    fi
  fi

  # 3. Auto-update Sync Script Check (every 60s, i.e., TICK % 12 == 0)
  if [ $((TICK % 12)) -eq 0 ]; then
    NEW_SYNC=$(curl -k -s -m 10 "$MASTER_URL/api/node-mgr/agent/sync-script?token=$TOKEN" 2>/dev/null || true)
    if [ -n "$NEW_SYNC" ] && echo "$NEW_SYNC" | grep -q 'komari-pro-node-sync'; then
      SYNC_MD5=$(echo "$NEW_SYNC" | md5sum | awk '{print $1}')
      CUR_MD5=$(md5sum /usr/local/bin/komari-pro-node-sync.sh 2>/dev/null | awk '{print $1}')
      if [ "$SYNC_MD5" != "$CUR_MD5" ]; then
        echo "$NEW_SYNC" > /usr/local/bin/komari-pro-node-sync.sh.new
        chmod +x /usr/local/bin/komari-pro-node-sync.sh.new
        mv /usr/local/bin/komari-pro-node-sync.sh.new /usr/local/bin/komari-pro-node-sync.sh
        if command -v systemctl >/dev/null 2>&1; then
          systemctl restart komari-pro-node-sync.service >/dev/null 2>&1 &
        elif command -v rc-service >/dev/null 2>&1; then
          rc-service komari-pro-node-sync restart >/dev/null 2>&1 &
        fi
        exit 0
      fi
    fi
  fi

  sleep 5
done
EOF

sed -i "s|__MASTER_URL__|$MASTER_URL|g" /usr/local/bin/komari-pro-node-sync.sh
sed -i "s|__TOKEN__|$TOKEN|g" /usr/local/bin/komari-pro-node-sync.sh
chmod +x /usr/local/bin/komari-pro-node-sync.sh

# Fetch and apply initial config immediately
echo "Fetching initial proxy configuration..."
INIT_CFG=$(curl -k -s -m 10 "$MASTER_URL/api/node-mgr/agent/config?token=$TOKEN" 2>/dev/null || true)
if [ -n "$INIT_CFG" ] && echo "$INIT_CFG" | grep -q '"inbounds"'; then
  echo "$INIT_CFG" > /etc/sing-box/config.json
  echo "$INIT_CFG" | md5sum | awk '{print $1}' > /etc/sing-box/config.md5
  PORTS=$(grep -oE '"listen_port"[[:space:]]*:[[:space:]]*[0-9]+' /etc/sing-box/config.json | grep -oE '[0-9]+' | sort -u)
  for p in $PORTS; do
    iptables -I INPUT 1 -p tcp --dport ${p} -j ACCEPT >/dev/null 2>&1 || true
    iptables -I INPUT 1 -p udp --dport ${p} -j ACCEPT >/dev/null 2>&1 || true
  done
  if [ "$INIT_SYSTEM" = "openrc" ]; then
    rc-service sing-box restart >/dev/null 2>&1 || rc-service sing-box start >/dev/null 2>&1 || true
  else
    systemctl restart sing-box.service >/dev/null 2>&1 || true
  fi
  echo "[Success] Sing-box initial configuration applied!"
fi

if [ "$INIT_SYSTEM" = "openrc" ]; then
  cat << 'EOF' > /etc/init.d/komari-pro-node-sync
#!/sbin/openrc-run
name="Komari Node Sync Service"
description="Komari Node Sync Service"
command="/bin/bash"
command_args="/usr/local/bin/komari-pro-node-sync.sh"
pidfile="/run/komari-node-sync.pid"
supervisor=supervise-daemon
supervise_daemon_args="--respawn-max 0 --respawn-delay 5"

depend() {
    need net
    after network sing-box
}
EOF
  chmod +x /etc/init.d/komari-pro-node-sync
  rc-update add komari-pro-node-sync default >/dev/null 2>&1 || true
  rc-service komari-pro-node-sync restart >/dev/null 2>&1 || rc-service komari-pro-node-sync start >/dev/null 2>&1 || true
else
  cat << EOF > /etc/systemd/system/komari-pro-node-sync.service
[Unit]
Description=Komari Node Configuration Sync Service
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash /usr/local/bin/komari-pro-node-sync.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable komari-pro-node-sync.service >/dev/null 2>&1 || true
  systemctl restart komari-pro-node-sync.service
fi
fi

# 6. Install Realm High-Performance Port Forwarder
if [ "$INSTALL_REALM" -eq 1 ]; then
  echo ""
  echo "[6/6] Installing Realm high-performance port forwarder..."
  ARCH=$(uname -m)
  case $ARCH in
    x86_64) REALM_ARCH="x86_64" ;;
    aarch64|arm64) REALM_ARCH="aarch64" ;;
    *) echo "[Warn] Unsupported arch for Realm: $ARCH, skipping Realm installation"; REALM_ARCH="" ;;
  esac

  if [ -n "$REALM_ARCH" ]; then
    mkdir -p /etc/realm /usr/local/bin
    if [ ! -f /etc/realm/config.toml ]; then
      cat << 'EOF' > /etc/realm/config.toml
[log]
level = "warn"

[network]
no_tcp = false
use_udp = true

endpoints = []
EOF
    fi

    echo "Downloading Realm binary (realm-${REALM_ARCH}-unknown-linux-musl.tar.gz)..."
    REALM_URL="https://github.com/zhboner/realm/releases/download/v2.9.6/realm-${REALM_ARCH}-unknown-linux-musl.tar.gz"
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL "$REALM_URL" -o /tmp/realm.tar.gz
    elif command -v wget >/dev/null 2>&1; then
      wget -qO /tmp/realm.tar.gz "$REALM_URL"
    fi
    tar -xzf /tmp/realm.tar.gz -C /usr/local/bin/ realm
    chmod +x /usr/local/bin/realm
    rm -f /tmp/realm.tar.gz

    # Fetch and apply initial Realm rules immediately
    echo "Fetching initial Realm forwarding configuration..."
    INIT_REALM=$(curl -k -s -m 10 "$MASTER_URL/api/node-mgr/agent/realm-config?token=$TOKEN" 2>/dev/null || true)
    if [ -n "$INIT_REALM" ] && echo "$INIT_REALM" | grep -q '\[network\]'; then
      echo "$INIT_REALM" > /etc/realm/config.toml
      echo "$INIT_REALM" | md5sum | awk '{print $1}' > /etc/realm/config.md5
      R_PORTS=$(grep -oE ':[0-9]+"' /etc/realm/config.toml | tr -d ':"' | sort -u)
      for rp in $R_PORTS; do
        iptables -I INPUT 1 -p tcp --dport ${rp} -j ACCEPT >/dev/null 2>&1 || true
        iptables -I INPUT 1 -p udp --dport ${rp} -j ACCEPT >/dev/null 2>&1 || true
      done
    fi

    if [ "$INIT_SYSTEM" = "openrc" ]; then
      cat << 'EOF' > /etc/init.d/realm
#!/sbin/openrc-run
name="Realm Forwarder"
description="Realm Port Forwarding Service"
command="/usr/local/bin/realm"
command_args="-c /etc/realm/config.toml"
pidfile="/run/realm.pid"
supervisor=supervise-daemon
supervise_daemon_args="--respawn-max 0 --respawn-delay 5"
depend() { need net; after network; }
EOF
      chmod +x /etc/init.d/realm
      rc-update add realm default >/dev/null 2>&1 || true
      rc-service realm restart >/dev/null 2>&1 || rc-service realm start >/dev/null 2>&1 || true
    else
      cat << 'EOF' > /etc/systemd/system/realm.service
[Unit]
Description=Realm Port Forwarding Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/realm -c /etc/realm/config.toml
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
      systemctl daemon-reload
      systemctl enable realm.service >/dev/null 2>&1 || true
      systemctl restart realm.service || true
    fi
    echo "[Success] Realm port forwarding service successfully installed and running!"
  fi
fi

echo ""
echo "======================================================"
echo " Installation Complete! Node is connected to Master!  "
echo "======================================================"
'''

def format_bytes(b):
    if not b or b <= 0:
        return "0 B"
    b = float(b)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while b >= 1024.0 and i < len(units) - 1:
        b /= 1024.0
        i += 1
    return f"{b:.2f} {units[i]}"

def parse_iso_or_ts(val):
    if not val:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    val_str = str(val).strip()
    try:
        dt = datetime.fromisoformat(val_str)
        if dt.tzinfo is None:
            # Naive timestamps from SQLite CURRENT_TIMESTAMP are UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        pass
    s = val_str.split(".")[0].replace("Z", "").replace("+00:00", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(s, fmt)
            dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except Exception:
            pass
    return 0

def dispatch_notification(title, message, level="info", rule_key=""):
    """
    Sends notification to all enabled channels and logs result in notification_logs.
    """
    conn = sqlite3.connect(NODES_DB)
    c = conn.cursor()
    c.execute("SELECT id, type, name, config FROM notification_channels WHERE enabled = 1")
    channels = c.fetchall()
    conn.close()

    if not channels:
        return {"ok": False, "msg": "没有已启用的通知渠道"}

    results = []
    for ch_id, ch_type, ch_name, ch_cfg_str in channels:
        success = False
        err_msg = ""
        try:
            cfg = json.loads(ch_cfg_str) if isinstance(ch_cfg_str, str) else ch_cfg_str
            if ch_type == "telegram":
                bot_token = cfg.get("bot_token", "").strip()
                chat_id = cfg.get("chat_id", "").strip()
                if not bot_token or not chat_id:
                    raise Exception("缺少 Telegram Bot Token 或 Chat ID")

                icon = "🔔"
                if level in ("danger", "error"):
                    icon = "🔴"
                elif level == "warning":
                    icon = "⚠️"
                elif level == "success":
                    icon = "🟢"
                elif level == "report":
                    icon = "📊"

                text = f"{icon} <b>{title}</b>\n\n{message}\n\n<i>Komari 监控运维 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode("utf-8")
                req = urllib.request.Request(url, data=data)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp_data = json.loads(resp.read().decode())
                    if resp_data.get("ok"):
                        success = True
                    else:
                        err_msg = str(resp_data)

            elif ch_type == "webhook":
                webhook_url = cfg.get("url", "").strip()
                if webhook_url:
                    payload = json.dumps({
                        "title": title,
                        "message": message,
                        "level": level,
                        "rule_key": rule_key,
                        "timestamp": datetime.now().isoformat()
                    }).encode("utf-8")
                    req = urllib.request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        if resp.status < 400:
                            success = True
                        else:
                            err_msg = f"HTTP {resp.status}"

            elif ch_type == "wechat":
                pp_token = cfg.get("token", "").strip()
                if pp_token:
                    url = "https://www.pushplus.plus/send"
                    payload = json.dumps({
                        "token": pp_token,
                        "title": title,
                        "content": message.replace("\n", "<br>"),
                        "template": "html"
                    }).encode("utf-8")
                    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        success = True

            elif ch_type == "feishu":
                fs_url = cfg.get("url", "").strip()
                if fs_url:
                    payload = json.dumps({
                        "msg_type": "text",
                        "content": {"text": f"{title}\n\n{message}"}
                    }).encode("utf-8")
                    req = urllib.request.Request(fs_url, data=payload, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        success = True

            elif ch_type == "dingtalk":
                dt_url = cfg.get("url", "").strip()
                if dt_url:
                    payload = json.dumps({
                        "msgtype": "text",
                        "text": {"content": f"【Komari 监控】{title}\n\n{message}"}
                    }).encode("utf-8")
                    req = urllib.request.Request(dt_url, data=payload, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        success = True

        except Exception as e:
            err_msg = str(e)

        results.append({"channel": ch_name, "success": success, "error": err_msg})

        # Save record to notification_logs
        try:
            conn_l = sqlite3.connect(NODES_DB)
            cl = conn_l.cursor()
            cl.execute("""
                INSERT INTO notification_logs (rule_key, title, message, channel, status, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """, (rule_key, title, message, ch_name, "success" if success else "failed", err_msg))
            cl.execute("DELETE FROM notification_logs WHERE id NOT IN (SELECT id FROM notification_logs ORDER BY id DESC LIMIT 200)")
            conn_l.commit()
            conn_l.close()
        except Exception:
            pass

    return {"ok": True, "results": results}

def check_and_notify_events():
    if not os.path.exists(NODES_DB) or not os.path.exists(KOMARI_DB):
        return

    conn_n = sqlite3.connect(NODES_DB)
    c_n = conn_n.cursor()
    c_n.execute("SELECT rule_key, config FROM notification_rules WHERE enabled = 1")
    enabled_rules = {}
    for r in c_n.fetchall():
        try:
            enabled_rules[r[0]] = json.loads(r[1])
        except Exception:
            enabled_rules[r[0]] = {}

    def get_state(key, default=""):
        c_n.execute("SELECT state_val FROM notification_states WHERE state_key = ?", (key,))
        row = c_n.fetchone()
        return row[0] if row else default

    def set_state(key, val):
        c_n.execute("INSERT OR REPLACE INTO notification_states (state_key, state_val, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (key, str(val)))
        conn_n.commit()

    now = int(time.time())
    now_dt = datetime.now()

    # 1. Fetch live servers stats
    try:
        stats = get_servers_with_stats()
        servers = stats.get("servers", [])
    except Exception as e:
        conn_n.close()
        return

    # A. Check Server Status, Singbox Status, Resource Exhaustion, Traffic Surge
    for s in servers:
        uuid_val = s["uuid"]
        s_name = s["name"]
        ip = s.get("ipv4") or s.get("ipv6") or "未知 IP"

        # Host Agent Online / Offline (rule: server_status)
        cfg_srv_st = enabled_rules.get("server_status", {})
        host_timeout = int(cfg_srv_st.get("offline_timeout", 120))
        notify_host_rec = bool(cfg_srv_st.get("notify_recovery", True))
        last_rec_time = parse_iso_or_ts(s.get("updated_at"))
        host_online = (now - last_rec_time) <= host_timeout if last_rec_time > 0 else True

        if "server_status" in enabled_rules:
            last_host_st = get_state(f"host_st:{uuid_val}")
            if not last_host_st:
                set_state(f"host_st:{uuid_val}", "online" if host_online else "offline")
            elif last_host_st == "online" and not host_online:
                set_state(f"host_st:{uuid_val}", "offline")
                set_state(f"host_off_time:{uuid_val}", str(now))
                timeout_desc = f"{host_timeout // 60} 分钟" if host_timeout >= 60 else f"{host_timeout} 秒"
                dispatch_notification(
                    title="🔴 服务器系统离线告警",
                    message=f"<b>服务器名称</b>: <code>{s_name}</code>\n<b>IP 地址</b>: <code>{ip}</code>\n<b>状态</b>: 探针心跳已失联超过 {timeout_desc}！主机可能已宕机、断网或被服务商关机。",
                    level="danger",
                    rule_key="server_status"
                )
            elif last_host_st == "offline" and host_online:
                set_state(f"host_st:{uuid_val}", "online")
                if notify_host_rec:
                    off_time = int(get_state(f"host_off_time:{uuid_val}", str(now)))
                    dur_s = max(0, now - off_time)
                    dur_txt = f"{dur_s // 60} 分 {dur_s % 60} 秒" if dur_s >= 60 else f"{dur_s} 秒"
                    dispatch_notification(
                        title="🟢 服务器探针恢复上线",
                        message=f"<b>服务器名称</b>: <code>{s_name}</code>\n<b>IP 地址</b>: <code>{ip}</code>\n<b>状态</b>: 探针心跳已恢复正常响应。\n<b>本次离线持续时长</b>: {dur_txt}",
                        level="success",
                        rule_key="server_status"
                    )

        # Sing-box Core Online / Offline (rule: singbox_status)
        cfg_sb = enabled_rules.get("singbox_status") or {}
        sb_timeout = max(60, int(cfg_sb.get("offline_timeout", 75)))
        s_last_seen = s.get("last_seen") or 0
        sb_online = (now - s_last_seen) <= sb_timeout if s_last_seen > 0 else False
        notify_sb_rec = bool(cfg_sb.get("notify_recovery", True))

        if host_online and s.get("singbox_installed", False) and "singbox_status" in enabled_rules:
            last_sb_st = get_state(f"sb_st:{uuid_val}")
            if not last_sb_st:
                set_state(f"sb_st:{uuid_val}", "online" if sb_online else "offline")
            elif last_sb_st == "online" and not sb_online:
                set_state(f"sb_st:{uuid_val}", "offline")
                set_state(f"sb_off_time:{uuid_val}", str(now))
                dispatch_notification(
                    title="🔴 Sing-box 核心离线告警",
                    message=f"<b>服务器</b>: <code>{s_name}</code> ({ip})\n<b>异常事件</b>: 主机在线但 Sing-box 核心代理已中断连接超过 {sb_timeout} 秒！\n<b>排查建议</b>: 请登录节点后台或执行 <code>systemctl status sing-box</code> 查看日志排查。",
                    level="danger",
                    rule_key="singbox_status"
                )
            elif last_sb_st == "offline" and sb_online:
                set_state(f"sb_st:{uuid_val}", "online")
                if notify_sb_rec:
                    off_time = int(get_state(f"sb_off_time:{uuid_val}", str(now)))
                    dur_s = max(0, now - off_time)
                    dur_txt = f"{dur_s // 60} 分 {dur_s % 60} 秒" if dur_s >= 60 else f"{dur_s} 秒"
                    dispatch_notification(
                        title="🟢 Sing-box 核心已恢复运行",
                        message=f"<b>服务器</b>: <code>{s_name}</code> ({ip})\n<b>事件</b>: Sing-box 核心代理已重新恢复运行，分流节点就绪。\n<b>本次中断时长</b>: {dur_txt}",
                        level="success",
                        rule_key="singbox_status"
                    )

        # Traffic Burst Surge (rule: traffic_surge)
        if "traffic_surge" in enabled_rules:
            in_rate = s.get("in_rate", 0)
            out_rate = s.get("out_rate", 0)
            cur_mbps = (in_rate + out_rate) * 8 / 1_000_000
            cfg_surge = enabled_rules["traffic_surge"] or {}
            burst_limit = float(cfg_surge.get("burst_mbps", 100))
            burst_gb = float(cfg_surge.get("burst_gb", 5))
            window_min = int(cfg_surge.get("window_min", 10))
            cooldown_sec = int(cfg_surge.get("cooldown_sec", 3600))
            last_surge = int(get_state(f"surge_sent:{uuid_val}", "0"))

            # 1. 实时吞吐流速激增判定
            if burst_limit > 0 and cur_mbps >= burst_limit:
                if now - last_surge > cooldown_sec:
                    set_state(f"surge_sent:{uuid_val}", str(now))
                    dispatch_notification(
                        title="⚡ 突发大流量激增告警",
                        message=f"<b>服务器</b>: <code>{s_name}</code> ({ip})\n<b>实时吞吐</b>: ↓ {format_bytes(in_rate)}/s · ↑ {format_bytes(out_rate)}/s\n<b>实时速率</b>: <b>{cur_mbps:.1f} Mbps</b> (突破设定的 {burst_limit:.0f} Mbps 阈值)\n<b>提示</b>: 检测到短时间内吞吐暴涨，请排查是否有异常大文件下载或订阅被盗刷！",
                        level="warning",
                        rule_key="traffic_surge"
                    )

            # 2. 统计时间窗口内突发消耗 (防盗刷/跑量监测) 判定
            if burst_gb > 0:
                cur_raw_traffic = s.get("raw_total") or s.get("traffic_total") or 0
                snap_key = f"surge_snap:{uuid_val}"
                snap_str = get_state(snap_key, "")
                if not snap_str:
                    set_state(snap_key, json.dumps({"ts": now, "raw": cur_raw_traffic}))
                else:
                    try:
                        snap_obj = json.loads(snap_str)
                        snap_ts = snap_obj.get("ts", now)
                        snap_raw = snap_obj.get("raw", cur_raw_traffic)
                        time_passed = max(1, now - snap_ts)
                        traffic_delta = max(0, cur_raw_traffic - snap_raw)

                        if traffic_delta >= burst_gb * (1024 ** 3):
                            if now - last_surge > cooldown_sec:
                                set_state(f"surge_sent:{uuid_val}", str(now))
                                window_desc = f"{int(time_passed // 60)} 分钟" if time_passed >= 60 else f"{time_passed} 秒"
                                dispatch_notification(
                                    title="🚨 突发巨额流量盗刷预警",
                                    message=f"<b>服务器</b>: <code>{s_name}</code> ({ip})\n<b>突发累计消耗</b>: <b>{format_bytes(traffic_delta)}</b> (在 {window_desc} 内消耗超过 {burst_gb} GB)\n<b>提示</b>: 短时间爆发异常巨额流量，极可能出现订阅链接泄露盗刷或高并发爬虫，请尽快检查节点连接！",
                                    level="danger",
                                    rule_key="traffic_surge"
                                )
                            set_state(snap_key, json.dumps({"ts": now, "raw": cur_raw_traffic}))
                        elif time_passed >= window_min * 60:
                            set_state(snap_key, json.dumps({"ts": now, "raw": cur_raw_traffic}))
                    except Exception:
                        set_state(snap_key, json.dumps({"ts": now, "raw": cur_raw_traffic}))

        # Resource Exhaustion (rule: resource_exhaustion)
        if "resource_exhaustion" in enabled_rules:
            cpu_val = s.get("cpu_usage", 0)
            ram_val = s.get("ram_pct", 0)
            disk_val = s.get("disk_pct", 0)
            cfg_res = enabled_rules["resource_exhaustion"] or {}
            c_limit = float(cfg_res.get("cpu_pct", 90))
            m_limit = float(cfg_res.get("mem_pct", 90))
            d_limit = float(cfg_res.get("disk_pct", 90))
            cooldown_sec = int(cfg_res.get("cooldown_sec", 1800))

            res_alerts = []
            if c_limit > 0 and cpu_val >= c_limit: res_alerts.append(f"CPU 使用率已达 {cpu_val:.1f}% (设定阈值: {c_limit}%)")
            if m_limit > 0 and ram_val >= m_limit: res_alerts.append(f"内存使用率已达 {ram_val:.1f}% (设定阈值: {m_limit}%)")
            if d_limit > 0 and disk_val >= d_limit: res_alerts.append(f"磁盘空间占用已达 {disk_val:.1f}% (设定阈值: {d_limit}%)")

            if res_alerts:
                last_res_sent = int(get_state(f"res_sent:{uuid_val}", "0"))
                if now - last_res_sent > cooldown_sec:
                    set_state(f"res_sent:{uuid_val}", str(now))
                    dispatch_notification(
                        title="⚠️ 硬件资源枯竭预警",
                        message=f"<b>服务器</b>: <code>{s_name}</code> ({ip})\n" + "\n".join([f"• {a}" for a in res_alerts]) + "\n<b>建议</b>: 请登录服务器清理临时文件或排查高负载进程。",
                        level="danger",
                        rule_key="resource_exhaustion"
                    )

    # B. Check Server Expiration & Monthly Traffic Limit (from komari.db)
    if "server_expiration" in enabled_rules or "traffic_threshold" in enabled_rules:
        try:
            conn_k = sqlite3.connect(KOMARI_DB)
            ck = conn_k.cursor()
            ck.execute("SELECT uuid, name, ipv4, expired_at, traffic_limit FROM clients")
            client_rows = ck.fetchall()
            conn_k.close()

            for c_uuid, c_name, c_ip, c_exp, c_limit in client_rows:
                # Expiration
                if c_exp and "server_expiration" in enabled_rules:
                    exp_ts = parse_iso_or_ts(c_exp)
                    if exp_ts > 0:
                        exp_dt = datetime.fromtimestamp(exp_ts)
                        days_left = (exp_dt.date() - now_dt.date()).days
                        remind_days = enabled_rules["server_expiration"].get("remind_days", [30, 15, 7, 3, 1])
                        if days_left in remind_days:
                            st_key = f"exp_sent:{c_uuid}:{days_left}:{exp_dt.strftime('%Y%m%d')}"
                            if not get_state(st_key):
                                set_state(st_key, "1")
                                dispatch_notification(
                                    title=f"⏳ 服务器到期续费提醒 (仅剩 {days_left} 天)",
                                    message=f"<b>服务器名称</b>: <code>{c_name}</code>\n<b>IP 地址</b>: <code>{c_ip or '未知'}</code>\n<b>到期时间</b>: <code>{exp_dt.strftime('%Y-%m-%d')}</code>\n<b>剩余天数</b>: <b>{days_left} 天</b>\n<b>提示</b>: 请及时前往服务商平台续费，防止机器被回收释放！",
                                    level="danger" if days_left <= 3 else "warning",
                                    rule_key="server_expiration"
                                )

                # Traffic Limit Threshold
                if c_limit and c_limit > 0 and "traffic_threshold" in enabled_rules:
                    match_s = next((x for x in servers if x["uuid"] == c_uuid), None)
                    if match_s:
                        used_bytes = match_s.get("traffic_total", 0)
                        pct = (used_bytes / c_limit) * 100
                        cur_ym = now_dt.strftime("%Y-%m")
                        for th in enabled_rules["traffic_threshold"].get("thresholds", [80, 90, 100]):
                            if pct >= th:
                                th_key = f"th_sent:{c_uuid}:{th}:{cur_ym}"
                                if not get_state(th_key):
                                    set_state(th_key, "1")
                                    dispatch_notification(
                                        title=f"📊 服务器流量使用已达 {th}% 预警",
                                        message=f"<b>服务器</b>: <code>{c_name}</code>\n<b>已用流量</b>: {format_bytes(used_bytes)}\n<b>配额上限</b>: {format_bytes(c_limit)}\n<b>消耗比例</b>: <b>{pct:.1f}%</b>\n<b>注意</b>: 超出配额可能面临断网或限速，请留意流量分配！",
                                        level="danger" if th >= 100 else "warning",
                                        rule_key="traffic_threshold"
                                    )
        except Exception:
            pass

    # C. Monthly Cycle Reset Notification (rule: traffic_threshold)
    if "traffic_threshold" in enabled_rules:
        if now_dt.day == 1 and now_dt.hour == 0 and now_dt.minute < 10:
            cur_ym = now_dt.strftime("%Y-%m")
            m_key = f"monthly_reset_notify:{cur_ym}"
            if not get_state(m_key):
                set_state(m_key, "1")
                dispatch_notification(
                    title="📅 月度流量统计周期重置提醒",
                    message=f"<b>通知</b>: 新月份 <b>{cur_ym}</b> 周期已开启！\n各节点当月流量配额重置，监控数据进入新一轮统计周期。",
                    level="info",
                    rule_key="traffic_threshold"
                )

    # D. Check Admin Panel Login Security (rule: admin_login)
    if "admin_login" in enabled_rules:
        try:
            conn_k = sqlite3.connect(KOMARI_DB)
            ck = conn_k.cursor()
            ck.execute("SELECT session, ip, user_agent, created_at FROM sessions ORDER BY created_at DESC LIMIT 1")
            row = ck.fetchone()
            conn_k.close()
            if row:
                s_id, s_ip, s_ua, s_created = row
                last_s_id = get_state("last_known_session")
                if not last_s_id:
                    set_state("last_known_session", s_id)
                elif last_s_id != s_id:
                    set_state("last_known_session", s_id)
                    ua_short = (s_ua[:60] + "...") if s_ua and len(s_ua) > 60 else (s_ua or "未知终端")
                    dispatch_notification(
                        title="🛡️ 管理后台新登录安全提醒",
                        message=f"<b>登录 IP</b>: <code>{s_ip}</code>\n<b>操作时间</b>: <code>{s_created}</code>\n<b>终端信息</b>: <code>{ua_short}</code>\n<i>如非管理员本人操作，请立即登录服务器排查凭据安全！</i>",
                        level="info",
                        rule_key="admin_login"
                    )
        except Exception:
            pass

    # E. Daily Health Report (rule: daily_report)
    if "daily_report" in enabled_rules:
        cfg = enabled_rules["daily_report"]
        rep_time = cfg.get("report_time", "09:00")
        today_str = now_dt.strftime("%Y-%m-%d")
        cur_hhmm = now_dt.strftime("%H:%M")

        if cur_hhmm == rep_time and get_state("last_daily_report_date") != today_str:
            set_state("last_daily_report_date", today_str)
            on_count = sum(1 for s in servers if s.get("singbox_online"))
            tot_s = len(servers)
            tot_traffic = sum(s.get("traffic_total", 0) for s in servers)

            dispatch_notification(
                title="📊 Komari 每日运维健康简报",
                message=f"<b>监控服务器总数</b>: {tot_s} 台\n<b>Sing-box 在线</b>: {on_count} / {tot_s} 台\n<b>全网累计消耗</b>: {format_bytes(tot_traffic)}\n\n<i>所有节点监控服务运行正常，祝您今天使用愉快！</i>",
                level="report",
                rule_key="daily_report"
            )

    # F. Check Node TCP Connectivity / GFW Block (rule: network_block)
    if "network_block" in enabled_rules:
        rule_cfg = enabled_rules.get("network_block") or {}
        fail_threshold = int(rule_cfg.get("fail_threshold", 2))
        notify_recovery = bool(rule_cfg.get("notify_on_recovery", True))
        try:
            c_n.execute("SELECT id, name, server_name, server_ip, port, protocol, sni FROM nodes WHERE enabled = 1")
            nodes_to_check = c_n.fetchall()
            if nodes_to_check:
                def check_single_node(n_row):
                    nid, nname, sname, ip, port, proto, sni = n_row
                    res = ping_node_handshake(ip, port, protocol=proto, sni=sni, timeout=3.5)
                    return n_row, res

                with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(nodes_to_check))) as pool:
                    results = list(pool.map(check_single_node, nodes_to_check))

                for (nid, nname, sname, ip, port, proto, sni), res in results:
                    last_tcp_st = get_state(f"node_tcp_st:{nid}")
                    fail_cnt = int(get_state(f"node_tcp_fail:{nid}", "0"))

                    if not res.get("success"):
                        fail_cnt += 1
                        set_state(f"node_tcp_fail:{nid}", str(fail_cnt))
                        if fail_cnt >= fail_threshold and last_tcp_st != "blocked":
                            set_state(f"node_tcp_st:{nid}", "blocked")
                            set_state(f"node_tcp_block_time:{nid}", str(now))
                            err_msg = res.get("error") or "连接超时 (Connection timed out)"
                            dispatch_notification(
                                title="🚫 节点 TCP 疑似被墙 / 无法连通告警",
                                message=(
                                    f"<b>节点名称</b>: <code>{nname}</code>\n"
                                    f"<b>归属主机</b>: <code>{sname}</code>\n"
                                    f"<b>目标节点</b>: <code>{ip}:{port}</code>\n"
                                    f"<b>节点协议</b>: <code>{(proto or 'TCP').upper()}</code>\n"
                                    f"<b>检测结果</b>: <b>TCP 握手失败</b> ({err_msg})\n"
                                    f"<b>判定说明</b>: 端口连续 {fail_cnt} 次握手失败，疑似该 IP 或端口已被 GFW 阻断/被墙。\n"
                                    f"<i>建议检查服务器运行状态或更换监听端口。</i>"
                                ),
                                level="danger",
                                rule_key="network_block"
                            )
                    else:
                        set_state(f"node_tcp_fail:{nid}", "0")
                        if last_tcp_st == "blocked":
                            set_state(f"node_tcp_st:{nid}", "ok")
                            if notify_recovery:
                                block_start = int(get_state(f"node_tcp_block_time:{nid}", str(now)))
                                dur_s = max(0, now - block_start)
                                dur_txt = f"{dur_s // 60} 分 {dur_s % 60} 秒" if dur_s >= 60 else f"{dur_s} 秒"
                                lat = res.get("latency_ms", 0)
                                dispatch_notification(
                                    title="🟢 节点 TCP 阻断已恢复解除",
                                    message=(
                                        f"<b>节点名称</b>: <code>{nname}</code>\n"
                                        f"<b>归属主机</b>: <code>{sname}</code>\n"
                                        f"<b>目标节点</b>: <code>{ip}:{port}</code>\n"
                                        f"<b>节点协议</b>: <code>{(proto or 'TCP').upper()}</code>\n"
                                        f"<b>恢复状态</b>: <b>TCP 握手成功</b> (延时: <code>{lat} ms</code>)\n"
                                        f"<b>阻断持续时长</b>: {dur_txt}\n"
                                        f"<i>该节点已恢复正常访问与转发能力。</i>"
                                    ),
                                    level="success",
                                    rule_key="network_block"
                                )
                        elif not last_tcp_st:
                            set_state(f"node_tcp_st:{nid}", "ok")
        except Exception as e:
            print("Check node TCP block error:", e)

    conn_n.close()

def run_notification_engine():
    time.sleep(15)
    print("Notification Engine started successfully.")
    while True:
        try:
            check_and_notify_events()
        except Exception as e:
            print("Notification Engine tick error:", e)
        time.sleep(30)

BLOCKED_IPS_FILE = "/opt/komari/data/blocked_ips.txt"
_token_fail_tracker = {}
_fail_tracker_lock = threading.Lock()

def block_ip_permanently(ip_str):
    """
    Blocks an abandoned/deleted server IP or rogue attacker at the kernel firewall level (iptables).
    Saves to /opt/komari/data/blocked_ips.txt for persistent reboot recovery.
    Zero CPU cost on future incoming packets (dropped directly at kernel level).
    """
    if not ip_str:
        return
    ip = ip_str.strip()
    # Skip private, loopback, or self IPs
    if ip in ["127.0.0.1", "::1", "localhost"] or ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172."):
        return

    # 1. Save to persistent file
    try:
        os.makedirs(os.path.dirname(BLOCKED_IPS_FILE), exist_ok=True)
        existing = set()
        if os.path.exists(BLOCKED_IPS_FILE):
            with open(BLOCKED_IPS_FILE, "r") as f:
                existing = set(line.strip() for line in f if line.strip())
        if ip not in existing:
            with open(BLOCKED_IPS_FILE, "a") as f:
                f.write(f"{ip}\n")
    except Exception as e:
        print(f"[Security Defense] Failed to write {ip} to {BLOCKED_IPS_FILE}: {e}")

    # 2. Apply iptables rule immediately (check if already in iptables first)
    try:
        is_v6 = ":" in ip
        cmd = "ip6tables" if is_v6 else "iptables"
        check_proc = subprocess.run(["sudo", cmd, "-C", "INPUT", "-s", ip, "-j", "DROP"], capture_output=True)
        if check_proc.returncode != 0:
            subprocess.run(["sudo", cmd, "-I", "INPUT", "1", "-s", ip, "-j", "DROP"], capture_output=True)
            print(f"[Security Defense] Auto-blocked abandoned/rogue IP at firewall level: {ip}")
    except Exception as e:
        print(f"[Security Defense] Error applying iptables for {ip}: {e}")

def get_blocked_ips_list():
    """
    Returns list of all currently blocked IPs from the persistent file.
    """
    if not os.path.exists(BLOCKED_IPS_FILE):
        return []
    try:
        with open(BLOCKED_IPS_FILE, "r") as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except Exception:
        return []

def unblock_ip(ip_str):
    """
    Safely unblocks an IP from kernel firewall (iptables/ip6tables) and removes from persistent blocked_ips.txt.
    Called automatically when a server is re-added, edited, or re-associated in admin panel.
    """
    if not ip_str:
        return True
    target = ip_str.strip()
    if not target:
        return True

    # If "all", unblock all historical blocked IPs
    if target.lower() == "all":
        ips_to_clear = get_blocked_ips_list()
        for one_ip in ips_to_clear:
            unblock_ip(one_ip)
        try:
            if os.path.exists(BLOCKED_IPS_FILE):
                with open(BLOCKED_IPS_FILE, "w") as f:
                    f.write("")
        except Exception:
            pass
        return True

    # 1. Remove from persistent file
    if os.path.exists(BLOCKED_IPS_FILE):
        try:
            with open(BLOCKED_IPS_FILE, "r") as f:
                lines = [line.strip() for line in f if line.strip() and line.strip() != target]
            with open(BLOCKED_IPS_FILE, "w") as f:
                for l in lines:
                    f.write(f"{l}\n")
        except Exception as e:
            print(f"[Security Defense] Error updating {BLOCKED_IPS_FILE} during unblock: {e}")

    # 2. Delete iptables DROP rules (both IPv4 and IPv6, loop until all duplicate rules are removed)
    try:
        is_v6 = ":" in target
        cmd = "ip6tables" if is_v6 else "iptables"
        while True:
            check_proc = subprocess.run(["sudo", cmd, "-C", "INPUT", "-s", target, "-j", "DROP"], capture_output=True)
            if check_proc.returncode == 0:
                subprocess.run(["sudo", cmd, "-D", "INPUT", "-s", target, "-j", "DROP"], capture_output=True)
                print(f"[Security Defense] Successfully unblocked IP from firewall: {target}")
            else:
                break
    except Exception as e:
        print(f"[Security Defense] Error removing iptables rule for {target}: {e}")

    with _fail_tracker_lock:
        _token_fail_tracker.pop(target, None)
    return True

def load_blocked_ips_on_startup():
    """
    Reloads all persistent blocked IPs on service startup to guarantee firewall protection.
    """
    if not os.path.exists(BLOCKED_IPS_FILE):
        return
    try:
        with open(BLOCKED_IPS_FILE, "r") as f:
            for line in f:
                ip = line.strip()
                if ip and not ip.startswith("#"):
                    try:
                        is_v6 = ":" in ip
                        cmd = "ip6tables" if is_v6 else "iptables"
                        check_proc = subprocess.run(["sudo", cmd, "-C", "INPUT", "-s", ip, "-j", "DROP"], capture_output=True)
                        if check_proc.returncode != 0:
                            subprocess.run(["sudo", cmd, "-I", "INPUT", "1", "-s", ip, "-j", "DROP"], capture_output=True)
                    except Exception:
                        pass
        print("[Security Defense] Persistent firewall blacklist rules loaded successfully.")
    except Exception as e:
        print(f"[Security Defense] Error loading {BLOCKED_IPS_FILE}: {e}")

def record_token_failure(client_ip):
    """
    Dynamic 401 Rate-Limiter (Jail):
    If any IP triggers 8 or more unauthorized/invalid token requests in 60s,
    it is automatically identified as an uninstalled abandoned agent or brute-force attack
    and instantly blocked at the kernel iptables level.
    """
    if not client_ip or client_ip in ["127.0.0.1", "::1"]:
        return
    now = time.time()
    with _fail_tracker_lock:
        fails = [t for t in _token_fail_tracker.get(client_ip, []) if now - t < 60]
        fails.append(now)
        _token_fail_tracker[client_ip] = fails
        if len(fails) >= 8:
            print(f"[Security Auto-Jail] IP {client_ip} triggered {len(fails)} unauthorized requests within 60s! Auto-blocking at firewall...")
            block_ip_permanently(client_ip)
            _token_fail_tracker.pop(client_ip, None)

def delete_server_fully(server_uuid):
    """
    Completely and cleanly deletes a server and its associated resources:
    1. Collects all known IPs of the server (ipv4, ipv6, custom_ip) and auto-blocks them at firewall
    2. Removes all child records in KOMARI_DB (offline_notifications, task_results)
    3. Removes the server from KOMARI_DB clients table
    4. Cleans up ping_tasks client lists
    5. Deletes associated nodes, baselines, and realm configs from NODES_DB
    6. Cleans up agent/realm heartbeats
    7. Re-routes any routing rules referencing the deleted nodes to PROXY
    """
    server_token = ""
    candidate_ips = set()

    # 1. Fetch server token & IPs, then delete from KOMARI_DB
    if os.path.exists(KOMARI_DB):
        try:
            conn_k = sqlite3.connect(KOMARI_DB)
            c_k = conn_k.cursor()
            c_k.execute("SELECT token, ipv4, ipv6 FROM clients WHERE uuid = ?", (server_uuid,))
            row = c_k.fetchone()
            if row:
                server_token = row[0] or ""
                if row[1]: candidate_ips.add(row[1].strip())
                if row[2]: candidate_ips.add(row[2].strip())
            c_k.execute("DELETE FROM offline_notifications WHERE client = ?", (server_uuid,))
            c_k.execute("DELETE FROM task_results WHERE client = ?", (server_uuid,))
            c_k.execute("DELETE FROM clients WHERE uuid = ?", (server_uuid,))
            conn_k.commit()

            # Clean dead UUID from ping_tasks
            c_k.execute("SELECT id, clients FROM ping_tasks")
            ptasks = c_k.fetchall()
            for tid, cjson in ptasks:
                try:
                    clist = json.loads(cjson) if cjson else []
                    if server_uuid in clist:
                        clist = [u for u in clist if u != server_uuid]
                        c_k.execute("UPDATE ping_tasks SET clients = ? WHERE id = ?", (json.dumps(clist), tid))
                except Exception:
                    pass
            conn_k.commit()
            conn_k.close()
        except Exception as e:
            print(f"[Error] Failed to remove server {server_uuid} from KOMARI_DB: {e}")

    # 2. Delete from NODES_DB (deleting both target/landing nodes AND relay nodes referencing this server)
    deleted_names = []
    if os.path.exists(NODES_DB):
        try:
            conn_n = sqlite3.connect(NODES_DB)
            c_n = conn_n.cursor()
            # Collect custom_ip from realm configs and server_ip from nodes
            try:
                c_n.execute("SELECT custom_ip FROM server_realm_configs WHERE uuid = ?", (server_uuid,))
                for r in c_n.fetchall():
                    if r[0]: candidate_ips.add(r[0].strip())
            except Exception:
                pass
            try:
                c_n.execute("SELECT server_ip FROM nodes WHERE server_uuid = ?", (server_uuid,))
                for r in c_n.fetchall():
                    if r[0]: candidate_ips.add(r[0].strip())
            except Exception:
                pass

            c_n.execute("SELECT name FROM nodes WHERE server_uuid = ? OR (is_relay = 1 AND relay_server_uuid = ?)", (server_uuid, server_uuid))
            deleted_names = [r[0] for r in c_n.fetchall()]
            c_n.execute("DELETE FROM nodes WHERE server_uuid = ? OR (is_relay = 1 AND relay_server_uuid = ?)", (server_uuid, server_uuid))
            c_n.execute("DELETE FROM server_traffic_baselines WHERE uuid = ?", (server_uuid,))
            try:
                c_n.execute("DELETE FROM server_realm_configs WHERE uuid = ?", (server_uuid,))
            except Exception:
                pass
            if server_token:
                try:
                    c_n.execute("DELETE FROM agent_heartbeats WHERE token = ?", (server_token,))
                    c_n.execute("DELETE FROM realm_heartbeats WHERE token = ?", (server_token,))
                except Exception:
                    pass
            conn_n.commit()
            conn_n.close()
        except Exception as e:
            print(f"[Error] Failed to remove server {server_uuid} from NODES_DB: {e}")

    # 3. Clean up routing rules for deleted nodes
    for nname in deleted_names:
        try:
            redirect_rules_for_node(nname, "PROXY")
        except Exception:
            pass

    # 4. Kernel Firewall Defense: Automatically block all IP addresses of the deleted server
    # This completely eliminates wasted CPU cycles and rogue request storms from uninstalled agents.
    for ip in candidate_ips:
        block_ip_permanently(ip)

    return len(deleted_names)

    return len(deleted_names)

def get_user_portal_payload(token):
    conn = sqlite3.connect(NODES_DB)
    c = conn.cursor()
    c.execute("PRAGMA table_info(subscriptions)")
    sub_cols = [r[1] for r in c.fetchall()]
    has_user_cols = ('username' in sub_cols and 'password' in sub_cols)

    if has_user_cols:
        c.execute("SELECT id, name, token, enabled, remark, created_at, user_uuid, traffic_limit_bytes, traffic_used_bytes, expire_time, username, password FROM subscriptions WHERE token = ?", (token,))
    else:
        c.execute("SELECT id, name, token, enabled, remark, created_at, user_uuid, traffic_limit_bytes, traffic_used_bytes, expire_time FROM subscriptions WHERE token = ?", (token,))
    sub_row = c.fetchone()
    if not sub_row:
        conn.close()
        return None, None

    uid, uname, tok, en, rmk, cat, u_uuid = (
        sub_row[0], sub_row[1] or "专属用户", sub_row[2], bool(sub_row[3]), sub_row[4] or "",
        str(sub_row[5]), sub_row[6] or ""
    )
    limit_b = int(sub_row[7] or 0) if len(sub_row) > 7 and sub_row[7] is not None else 0
    used_b = int(sub_row[8] or 0) if len(sub_row) > 8 and sub_row[8] is not None else 0
    exp = str(sub_row[9] or "").strip() if len(sub_row) > 9 and sub_row[9] is not None else ""
    username = sub_row[10] if len(sub_row) > 10 and sub_row[10] else uname
    password = sub_row[11] if len(sub_row) > 11 and sub_row[11] else "password123"

    rem_b = max(0, limit_b - used_b) if limit_b > 0 else 0
    pct = round((used_b / limit_b) * 100, 1) if limit_b > 0 else 0
    today_str = datetime.now().strftime("%Y-%m-%d")
    is_exh = (limit_b > 0 and used_b >= limit_b)
    is_exp = bool(exp and today_str > exp.split("T")[0])

    days_left = None
    if exp:
        try:
            days_left = (datetime.strptime(exp.split("T")[0], "%Y-%m-%d").date() - datetime.now().date()).days
        except Exception:
            pass

    if not en:
        st = "disabled"
        st_text = "已暂停服务"
    elif is_exh:
        st = "exhausted"
        st_text = "流量已耗尽"
    elif is_exp:
        st = "expired"
        st_text = "订阅已过期"
    else:
        st = "normal"
        st_text = "正常使用中"

    c.execute("SELECT * FROM nodes WHERE enabled = 1 ORDER BY is_external ASC, id DESC")
    cols = [d[0] for d in c.description]
    raw_nodes = [dict(zip(cols, row)) for row in c.fetchall()]
    conn.close()

    servers_data = get_cached_servers_with_stats()
    all_server_uuids = set(s["uuid"] for s in servers_data.get("servers", []))
    online_server_uuids = set(
        s["uuid"] for s in servers_data.get("servers", [])
        if s.get("server_online") or s.get("probe_online") or s.get("singbox_online")
    )

    user_nodes = []
    for n in raw_nodes:
        if not n.get("is_external") and n.get("server_uuid") != "external":
            if n.get("server_uuid") not in all_server_uuids:
                continue
            if n.get("is_relay") and n.get("relay_server_uuid") and n.get("relay_server_uuid") not in all_server_uuids:
                continue

        n_copy = dict(n)
        if not n.get("is_external") and n.get("server_uuid") != "external" and u_uuid:
            n_copy["uuid_or_passwd"] = u_uuid
        is_on = bool(n.get("is_external") or n.get("server_uuid") == "external" or (
            n.get("server_uuid") in online_server_uuids and (
                not n.get("is_relay") or not n.get("relay_server_uuid") or n.get("relay_server_uuid") in online_server_uuids
            )
        ))
        user_nodes.append({
            "id": n.get("id"),
            "name": n.get("name"),
            "protocol": n.get("protocol"),
            "server_ip": n.get("server_ip"),
            "port": n.get("port"),
            "online": is_on,
            "share_link": build_node_share_link(n_copy)
        })

    rules_cfg = get_subscription_rules()
    base_title = rules_cfg.get("sub_title") or "Komari Pro 优质节点"
    p_title = f"{base_title} - {uname}" if (uname and uname != "default") else base_title
    frag = f"#{urllib.parse.quote(p_title)}"

    user_info = {
        "id": uid,
        "name": uname,
        "username": username,
        "password": password,
        "token": tok,
        "enabled": en,
        "remark": rmk,
        "created_at": cat,
        "user_uuid": u_uuid,
        "traffic_limit_bytes": limit_b,
        "traffic_limit_gb": round(limit_b / (1024**3), 2) if limit_b > 0 else 0,
        "traffic_limit_formatted": format_bytes(limit_b) if limit_b > 0 else "无限制",
        "traffic_used_bytes": used_b,
        "traffic_used_gb": round(used_b / (1024**3), 2),
        "traffic_used_formatted": format_bytes(used_b),
        "traffic_remaining_bytes": rem_b,
        "traffic_remaining_formatted": format_bytes(rem_b) if limit_b > 0 else "无限制",
        "traffic_percent": min(100.0, pct),
        "expire_time": exp,
        "expire_remaining_days": days_left,
        "status": st,
        "status_text": st_text,
        "profile_title": p_title,
        "sub_url": f"https://{DOMAIN}/sub/{tok}{frag}",
        "clash_url": f"https://{DOMAIN}/sub/{tok}?clash=1{frag}",
        "singbox_url": f"https://{DOMAIN}/sub/{tok}?singbox=1{frag}"
    }
    return user_info, user_nodes

def build_node_sync_script(master_url, token):
    marker_start = "cat << 'EOF' > /usr/local/bin/komari-pro-node-sync.sh\n"
    marker_end = "\nEOF\n"
    if marker_start in INSTALL_SCRIPT_TEMPLATE:
        part = INSTALL_SCRIPT_TEMPLATE.split(marker_start, 1)[1]
        raw_script = part.split(marker_end, 1)[0]
    else:
        raw_script = ""
    return raw_script.replace("__MASTER_URL__", master_url).replace("__TOKEN__", token)

class NodeMgrHandler(BaseHTTPRequestHandler):
    def get_client_ip(self):
        xff = self.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(",")[0].strip()
        xri = self.headers.get("X-Real-IP")
        if xri:
            return xri.strip()
        if self.client_address and len(self.client_address) > 0:
            return str(self.client_address[0])
        return ""

    def _send_json(self, data, status=200, extra_headers=None):
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            if extra_headers:
                for k, v in extra_headers.items():
                    self.send_header(k, str(v))
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_text(self, text, status=200, content_type="text/plain; charset=utf-8", extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, str(v))
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        
        # Notifications API endpoints
        if path in ["/api/notifications/config", "/api/node-mgr/notifications/config"]:
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT id, type, name, enabled, config, updated_at FROM notification_channels ORDER BY id ASC")
            channels = []
            for r in c.fetchall():
                try:
                    cfg = json.loads(r[4])
                except Exception:
                    cfg = {}
                channels.append({
                    "id": r[0],
                    "type": r[1],
                    "name": r[2],
                    "enabled": bool(r[3]),
                    "config": cfg,
                    "updated_at": str(r[5])
                })

            c.execute("SELECT rule_key, name, category, description, enabled, config, updated_at FROM notification_rules ORDER BY category ASC, rule_key ASC")
            rules = []
            for r in c.fetchall():
                try:
                    cfg = json.loads(r[5])
                except Exception:
                    cfg = {}
                rules.append({
                    "rule_key": r[0],
                    "name": r[1],
                    "category": r[2],
                    "description": r[3],
                    "enabled": bool(r[4]),
                    "config": cfg,
                    "updated_at": str(r[6])
                })
            conn.close()
            self._send_json({"ok": True, "channels": channels, "rules": rules})
            return

        if path in ["/api/notifications/logs", "/api/node-mgr/notifications/logs"]:
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT id, rule_key, title, message, channel, status, error, created_at FROM notification_logs ORDER BY id DESC LIMIT 50")
            logs = []
            for r in c.fetchall():
                logs.append({
                    "id": r[0],
                    "rule_key": r[1],
                    "title": r[2],
                    "message": r[3],
                    "channel": r[4],
                    "status": r[5],
                    "error": r[6],
                    "created_at": str(r[7])
                })
            conn.close()
            self._send_json({"ok": True, "logs": logs})
            return

        # User Portal SPA and Assets Route
        if path in ["/user", "/user/", "/portal", "/portal/", "/pro/user", "/pro/user/"]:
            portal_path = os.path.join(BASE_DIR, "user-portal", "index.html")
            if not os.path.exists(portal_path):
                portal_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "user-portal", "index.html")
            if os.path.exists(portal_path):
                with open(portal_path, "r", encoding="utf-8") as f:
                    self._send_text(f.read(), 200, "text/html; charset=utf-8")
                return

        if path.startswith("/user/assets/"):
            fname = os.path.basename(path)
            fpath = os.path.join(BASE_DIR, "user-portal", "assets", fname)
            if not os.path.exists(fpath):
                fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "user-portal", "assets", fname)
            if not os.path.exists(fpath):
                fpath = os.path.join(BASE_DIR, "data", "plugin", "node-manager", "panel", "assets", fname)
            if os.path.exists(fpath):
                ctype = "application/javascript" if fname.endswith(".js") else "text/css"
                with open(fpath, "rb") as f:
                    content_bytes = f.read()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(content_bytes)
                return

        if path in ["/install-node.sh", "/install-node-pro.sh"]:
            req_host = self.headers.get("Host", DOMAIN).split(":")[0]
            script = INSTALL_SCRIPT_TEMPLATE.replace("{DOMAIN}", req_host)
            self._send_text(script, 200, "text/x-shellscript")
            return

        if path.startswith("/sub/"):
            sub_raw = path.split("/sub/")[1].strip("/")
            parts = sub_raw.split("/")
            token = parts[0]
            sub_format = parts[1].lower() if len(parts) > 1 else ""

            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT id, enabled, name, user_uuid, traffic_limit_bytes, traffic_used_bytes, expire_time FROM subscriptions WHERE token = ?", (token,))
            sub = c.fetchone()
            if not sub:
                conn.close()
                self._send_text("Invalid Subscription Token", 404)
                return

            uid = sub[0]
            enabled = bool(sub[1])
            sub_name = sub[2] or "用户"
            sub_uuid = sub[3] if len(sub) > 3 and sub[3] else None
            traffic_limit = int(sub[4] or 0) if len(sub) > 4 and sub[4] is not None else 0
            traffic_used = int(sub[5] or 0) if len(sub) > 5 and sub[5] is not None else 0
            expire_time = str(sub[6] or "").strip() if len(sub) > 6 and sub[6] is not None else ""

            # Quota and Expiration Hard Enforcement
            today_str = datetime.now().strftime("%Y-%m-%d")
            is_exhausted = (traffic_limit > 0 and traffic_used >= traffic_limit)
            is_expired = bool(expire_time and today_str > expire_time.split("T")[0])
            is_disabled = (not enabled)

            # Expiration timestamp for client apps (Clash, Shadowrocket)
            exp_ts = 0
            if expire_time:
                try:
                    exp_ts = int(datetime.strptime(expire_time.split("T")[0], "%Y-%m-%d").timestamp())
                except Exception:
                    exp_ts = 0

            rules_cfg = get_subscription_rules()
            base_title = rules_cfg.get("sub_title") or "Komari Pro 优质节点"
            profile_title = f"{base_title} - {sub_name}" if (sub_name and sub_name != "default") else base_title
            quoted_title = urllib.parse.quote(profile_title)
            safe_ascii = re.sub(r'[^a-zA-Z0-9_\-]', '', profile_title) or "komari-sub"

            ua = self.headers.get("User-Agent", "").lower()
            fmt = query.get("format", [""])[0].lower() or sub_format
            clash_flag = query.get("clash", [""])[0]
            singbox_flag = query.get("singbox", [""])[0]
            sb_flag = query.get("sb", [""])[0]

            is_singbox_req = (fmt in ["singbox", "sing-box", "json", "sb"] or singbox_flag == "1" or sb_flag == "1" or any(k in ua for k in ["sing-box", "singbox", "sfa", "sfi"]))
            is_clash_req = (fmt in ["clash", "meta"] or clash_flag == "1" or any(k in ua for k in ["clash", "mihomo", "meta", "stash", "verge"]))

            ext = "json" if is_singbox_req else ("txt" if fmt == "raw" else "yaml")
            extra_hdrs = {
                "Subscription-Userinfo": f"upload=0; download={traffic_used}; total={traffic_limit}; expire={exp_ts}",
                "Profile-Update-Interval": "60" if (is_exhausted or is_expired or is_disabled) else "7200",
                "Profile-Title": quoted_title,
                "Content-Disposition": f"attachment; filename=\"{safe_ascii}.{ext}\"; filename*=UTF-8''{quoted_title}.{ext}"
            }

            # Block if exhausted, expired, or disabled
            if is_exhausted or is_expired or is_disabled:
                conn.close()
                if is_disabled:
                    alert_tag = "🚫 订阅已暂停 - 请联系管理员启用"
                elif is_exhausted:
                    alert_tag = f"⛔ 流量已用尽 ({format_bytes(traffic_used)} / {format_bytes(traffic_limit)}) - 请联系管理员续费"
                else:
                    alert_tag = f"⏰ 订阅已到期 ({expire_time}) - 请联系管理员续期"

                if is_singbox_req:
                    blocked_profile = {
                        "outbounds": [
                            {"type": "block", "tag": alert_tag}
                        ]
                    }
                    self._send_text(json.dumps(blocked_profile, indent=2, ensure_ascii=False), 200, "application/json; charset=utf-8", extra_headers=extra_hdrs)
                elif is_clash_req:
                    yaml_mock = f"""port: 7890
socks-port: 7891
allow-lan: false
mode: rule
log-level: info
proxies:
  - name: "{alert_tag}"
    type: socks5
    server: 127.0.0.1
    port: 0
proxy-groups:
  - name: "PROXIES"
    type: select
    proxies:
      - "{alert_tag}"
rules:
  - MATCH,PROXIES
"""
                    self._send_text(yaml_mock, 200, "text/yaml; charset=utf-8", extra_headers=extra_hdrs)
                elif fmt == "raw":
                    dummy_link = f"vless://00000000-0000-0000-0000-000000000000@127.0.0.1:0?security=none#{urllib.parse.quote(alert_tag)}"
                    self._send_text(dummy_link, 200, "text/plain; charset=utf-8", extra_headers=extra_hdrs)
                else:
                    dummy_link = f"vless://00000000-0000-0000-0000-000000000000@127.0.0.1:0?security=none#{urllib.parse.quote(alert_tag)}"
                    b64 = base64.b64encode(dummy_link.encode()).decode()
                    self._send_text(b64, 200, "text/plain; charset=utf-8", extra_headers=extra_hdrs)
                return

            c.execute("SELECT * FROM nodes WHERE enabled = 1 ORDER BY is_external ASC, id DESC")
            cols = [d[0] for d in c.description]
            all_nodes = [dict(zip(cols, row)) for row in c.fetchall()]
            conn.close()

            # Personalize nodes with this user's dedicated UUID
            if sub_uuid:
                personalized_all_nodes = []
                for n in all_nodes:
                    if n.get("is_external") or n.get("server_uuid") == "external":
                        personalized_all_nodes.append(n)
                    else:
                        n_copy = dict(n)
                        n_copy["uuid_or_passwd"] = sub_uuid
                        personalized_all_nodes.append(n_copy)
                all_nodes = personalized_all_nodes

            # Dynamic health filter: omit self-hosted nodes whose server / Sing-box core is offline
            servers_data = get_cached_servers_with_stats()
            online_server_uuids = set(
                s["uuid"] for s in servers_data.get("servers", [])
                if s.get("server_online") or s.get("probe_online") or s.get("singbox_online")
            )
            nodes = [
                n for n in all_nodes
                if n.get("is_external") or n.get("server_uuid") == "external" or (
                    n.get("server_uuid") in online_server_uuids and (
                        not n.get("is_relay") or not n.get("relay_server_uuid") or n.get("relay_server_uuid") in online_server_uuids
                    )
                )
            ]

            rules_cfg = get_subscription_rules()

            if is_singbox_req:
                sb_profile = build_sing_box_client_profile(nodes, rules_cfg, sub_title=profile_title)
                self._send_text(json.dumps(sb_profile, indent=2, ensure_ascii=False), 200, "application/json; charset=utf-8", extra_headers=extra_hdrs)
            elif is_clash_req:
                yaml_data = build_clash_meta_yaml(nodes, rules_cfg, sub_title=profile_title)
                self._send_text(yaml_data, 200, "text/yaml; charset=utf-8", extra_headers=extra_hdrs)
            elif fmt == "raw":
                links = [build_node_share_link(n) for n in nodes if build_node_share_link(n)]
                self._send_text("\n".join(links), 200, "text/plain; charset=utf-8", extra_headers=extra_hdrs)
            else:
                links = [build_node_share_link(n) for n in nodes if build_node_share_link(n)]
                b64 = base64.b64encode("\n".join(links).encode()).decode()
                self._send_text(b64, 200, "text/plain; charset=utf-8", extra_headers=extra_hdrs)
            return

        # API routes:
        if path in ["/api/sub/rules", "/api/node-mgr/sub/rules"]:
            rules = get_subscription_rules()
            self._send_json({"ok": True, "rules": rules})
            return

        if path in ["/api/sub/rules/presets", "/api/node-mgr/sub/rules/presets"]:
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT id, name, protocol FROM nodes WHERE enabled = 1 ORDER BY is_external ASC, id DESC")
            nodes = [{"id": r[0], "name": r[1], "protocol": r[2]} for r in c.fetchall()]
            conn.close()
            self._send_json({"ok": True, "nodes": nodes})
            return

        if path in ["/api/sub/rules/preview", "/api/node-mgr/sub/rules/preview"]:
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM nodes WHERE enabled = 1 ORDER BY is_external ASC, id DESC")
            cols = [d[0] for d in c.description]
            all_nodes = [dict(zip(cols, row)) for row in c.fetchall()]
            conn.close()

            servers_data = get_cached_servers_with_stats()
            online_server_uuids = set(
                s["uuid"] for s in servers_data.get("servers", [])
                if s.get("server_online") or s.get("probe_online") or s.get("singbox_online")
            )
            nodes = [
                n for n in all_nodes
                if n.get("is_external") or n.get("server_uuid") == "external" or (
                    n.get("server_uuid") in online_server_uuids and (
                        not n.get("is_relay") or not n.get("relay_server_uuid") or n.get("relay_server_uuid") in online_server_uuids
                    )
                )
            ]

            rules_cfg = get_subscription_rules()
            yaml_data = build_clash_meta_yaml(nodes, rules_cfg)
            self._send_json({
                "ok": True,
                "yaml": yaml_data,
                "total_nodes": len(all_nodes),
                "active_nodes": len(nodes),
                "offline_nodes": len(all_nodes) - len(nodes)
            })
            return

        if path in ["/api/security/blocked-ips", "/api/node-mgr/security/blocked-ips"]:
            self._send_json({"ok": True, "blocked_ips": get_blocked_ips_list()})
            return

        if path == "/api/servers" or path == "/api/node-mgr/servers":
            servers_data = get_cached_servers_with_stats()
            self._send_json(servers_data)
            return

        if path in ["/api/bbr/status", "/api/node-mgr/bbr/status"]:
            try:
                res = subprocess.run(["sysctl", "-n", "net.ipv4.tcp_congestion_control"], capture_output=True, text=True, timeout=2)
                cc = res.stdout.strip()
                q_res = subprocess.run(["sysctl", "-n", "net.core.default_qdisc"], capture_output=True, text=True, timeout=2)
                qdisc = q_res.stdout.strip()
                self._send_json({"ok": True, "enabled": cc == "bbr", "congestion_control": cc, "qdisc": qdisc})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)})
            return

        if path in ["/api/system/status", "/api/node-mgr/system/status"]:
            has_ssl = os.path.exists(f"/etc/letsencrypt/live/{DOMAIN}/fullchain.pem") or os.path.exists(f"{CERT_DIR}/cert.pem")
            self._send_json({
                "ok": True,
                "domain": DOMAIN,
                "port": PORT,
                "ssl": has_ssl,
                "master_url": f"https://{DOMAIN}" if has_ssl else f"http://{DOMAIN}"
            })
            return

        if path in ["/api/ping-tasks", "/api/node-mgr/ping-tasks"]:
            tasks = []
            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("SELECT id, weight, name, clients, all_clients, type, target, interval FROM ping_tasks ORDER BY weight DESC, id ASC")
                for r in c_k.fetchall():
                    try:
                        c_list = json.loads(r[3]) if r[3] else []
                    except:
                        c_list = []
                    tasks.append({
                        "id": r[0],
                        "weight": r[1],
                        "name": r[2],
                        "clients": c_list,
                        "all_clients": bool(r[4]),
                        "type": r[5] or "tcp",
                        "target": r[6],
                        "interval": r[7] or 60
                    })
                conn_k.close()
            self._send_json({"ok": True, "tasks": tasks})
            return

        if path in ["/api/system/configs", "/api/node-mgr/system/configs"]:
            configs = {}
            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("SELECT key, value FROM configs")
                for k, v in c_k.fetchall():
                    try:
                        configs[k] = json.loads(v)
                    except:
                        configs[k] = v
                conn_k.close()
            self._send_json({"ok": True, "configs": configs})
            return

        # Theme Management & Market GET Endpoints
        if path in ["/api/theme/list", "/api/node-mgr/theme/list"]:
            active_theme = "default"
            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("SELECT value FROM configs WHERE key = 'theme'")
                row = c_k.fetchone()
                if row and row[0]:
                    try:
                        active_theme = json.loads(row[0])
                    except Exception:
                        active_theme = str(row[0]).strip('"')
                conn_k.close()
            themes = get_installed_themes_list(active_theme)
            self._send_json({"ok": True, "active_theme": active_theme, "themes": themes})
            return

        if path in ["/api/theme/market", "/api/node-mgr/theme/market"]:
            active_theme = "default"
            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("SELECT value FROM configs WHERE key = 'theme'")
                row = c_k.fetchone()
                if row and row[0]:
                    try:
                        active_theme = json.loads(row[0])
                    except Exception:
                        active_theme = str(row[0]).strip('"')
                conn_k.close()
            installed_list = get_installed_themes_list(active_theme)
            installed_map = {t["short"]: t.get("version", "1.0.0") for t in installed_list}
            market_themes = get_theme_market_catalog()
            
            # Enrich market themes with installed status
            res_themes = []
            for m in market_themes:
                m_copy = dict(m)
                m_short = m.get("short")
                m_copy["download_url"] = m.get("download") or m.get("download_url") or ""
                m_copy["preview_url"] = m.get("preview") or m.get("preview_url") or ""
                m_copy["homepage"] = m.get("url") or m.get("homepage") or ""
                if m_short in installed_map:
                    m_copy["is_installed"] = True
                    m_copy["installed_version"] = installed_map[m_short]
                    m_copy["has_update"] = (m.get("version", "") != installed_map[m_short])
                else:
                    m_copy["is_installed"] = False
                    m_copy["installed_version"] = ""
                    m_copy["has_update"] = False
                res_themes.append(m_copy)

            self._send_json({
                "ok": True,
                "active_theme": active_theme,
                "catalog": res_themes,
                "themes": res_themes,
                "installed_count": len(installed_list),
                "total_market_count": len(market_themes)
            })
            return

        if path in ["/api/theme/preview", "/api/node-mgr/theme/preview"]:
            theme_short = query.get("theme", [""])[0]
            if not theme_short:
                self.send_error(400, "Missing theme parameter")
                return
            theme_short = re.sub(r"[^a-zA-Z0-9_-]", "", theme_short)
            if theme_short.lower() in ["default", ""]:
                svg_data = DEFAULT_THEME_PREVIEW_SVG.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
                self.send_header("Content-Length", str(len(svg_data)))
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(svg_data)
                return

            dp = os.path.join(THEME_DIR, theme_short)
            for fname, mime in [("preview.png", "image/png"), ("preview.webp", "image/webp"), ("preview.jpg", "image/jpeg"), ("preview.svg", "image/svg+xml")]:
                fpath = os.path.join(dp, fname)
                if os.path.exists(fpath):
                    try:
                        with open(fpath, "rb") as f:
                            data = f.read()
                        self.send_response(200)
                        self.send_header("Content-Type", mime)
                        self.send_header("Content-Length", str(len(data)))
                        self.send_header("Cache-Control", "public, max-age=86400")
                        self.end_headers()
                        self.wfile.write(data)
                        return
                    except Exception:
                        pass
            # Fallback SVG for any other theme that doesn't have an image file
            fallback_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" width="800" height="450">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#475569"/><stop offset="100%" stop-color="#1E293B"/>
    </linearGradient>
  </defs>
  <rect width="800" height="450" fill="url(#bg)"/>
  <text x="400" y="210" text-anchor="middle" font-family="sans-serif" font-size="48">🎨</text>
  <text x="400" y="260" text-anchor="middle" font-family="sans-serif" font-size="22" font-weight="bold" fill="#F8FAFC">{html.escape(theme_short)}</text>
  <text x="400" y="295" text-anchor="middle" font-family="sans-serif" font-size="14" fill="#94A3B8">Komari Monitor Theme</text>
</svg>""".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
            self.send_header("Content-Length", str(len(fallback_svg)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(fallback_svg)
            return

        # Theme Configuration GET Endpoint (Legacy / compatibility)
        if path in ["/api/theme/config", "/api/node-mgr/theme/config"]:
            active_theme = "default"
            installed_themes = [
                {
                    "short": "default",
                    "name": "Komari 默认主题 (Default)",
                    "description": "Komari 官方原生极简监控大屏",
                    "version": "1.0.0",
                    "author": "Komari",
                    "builtin": True
                }
            ]
            theme_config = {}

            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("SELECT value FROM configs WHERE key = 'theme'")
                row = c_k.fetchone()
                if row and row[0]:
                    try:
                        active_theme = json.loads(row[0])
                    except Exception:
                        active_theme = str(row[0]).strip('"')

                # Scan theme directory
                theme_dir = "/opt/komari/data/theme"
                if not os.path.exists(theme_dir) and os.path.exists("./data/theme"):
                    theme_dir = "./data/theme"

                if os.path.exists(theme_dir):
                    for d in os.listdir(theme_dir):
                        dp = os.path.join(theme_dir, d)
                        if os.path.isdir(dp):
                            cfg_path = os.path.join(dp, "komari-theme.json")
                            if os.path.exists(cfg_path):
                                try:
                                    with open(cfg_path, "r", encoding="utf-8") as f:
                                        tinfo = json.load(f)
                                        tinfo["short"] = tinfo.get("short") or d
                                        installed_themes.append(tinfo)
                                except Exception:
                                    installed_themes.append({"short": d, "name": d})
                            else:
                                installed_themes.append({"short": d, "name": d})

                # Fetch theme configuration for active theme (or LuminaPlus)
                target_short = active_theme if active_theme != "default" else "LuminaPlus"
                c_k.execute("SELECT data FROM theme_configurations WHERE short = ?", (target_short,))
                t_row = c_k.fetchone()
                if not t_row and target_short != "LuminaPlus":
                    c_k.execute("SELECT data FROM theme_configurations WHERE short = 'LuminaPlus'")
                    t_row = c_k.fetchone()
                if t_row and t_row[0]:
                    try:
                        theme_config = json.loads(t_row[0])
                    except Exception:
                        pass
                conn_k.close()

            self._send_json({
                "ok": True,
                "active_theme": active_theme,
                "installed_themes": installed_themes,
                "theme_config": theme_config
            })
            return

        if path == "/api/nodes" or path == "/api/node-mgr/nodes":
            try:
                auto_repair_node_ips()
            except Exception:
                pass
            servers_data = get_cached_servers_with_stats()
            servers_map = {s["uuid"]: s for s in servers_data.get("servers", [])}

            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM nodes ORDER BY is_external ASC, id DESC")
            cols = [d[0] for d in c.description]
            nodes = [dict(zip(cols, row)) for row in c.fetchall()]
            conn.close()

            # Filter out orphan nodes whose server no longer exists & auto-populate missing server IP/name
            valid_nodes = []
            for n in nodes:
                if n.get("is_external") or n.get("server_uuid") == "external":
                    valid_nodes.append(n)
                elif n.get("server_uuid") in servers_map:
                    srv = servers_map[n.get("server_uuid")]
                    if not n.get("server_ip"):
                        n["server_ip"] = srv.get("ipv4") or srv.get("ipv6") or ""
                    if not n.get("server_name"):
                        n["server_name"] = srv.get("name") or ""
                    if n.get("is_relay") and n.get("relay_server_uuid"):
                        if n.get("relay_server_uuid") not in servers_map:
                            # Relay server was deleted, omit orphan relay node
                            continue
                        rsrv = servers_map[n["relay_server_uuid"]]
                        if not n.get("relay_server_ip"):
                            n["relay_server_ip"] = rsrv.get("ipv4") or rsrv.get("ipv6") or ""
                        if not n.get("relay_server_name"):
                            n["relay_server_name"] = rsrv.get("name") or ""
                    valid_nodes.append(n)
            nodes = valid_nodes

            for n in nodes:
                n["link"] = build_node_share_link(n)
                if n["id"] in _node_latency_cache:
                    cached_p = _node_latency_cache[n["id"]]
                    if cached_p.get("latency_ms"):
                        n["ping_ms"] = cached_p["latency_ms"]

                if n.get("is_external") or n.get("server_uuid") == "external":
                    n["is_external"] = 1
                    n["server_online"] = True
                    n["singbox_online"] = True
                    n["node_status"] = "online"
                    n["status_text"] = "外部节点"
                else:
                    srv = servers_map.get(n.get("server_uuid"))
                    if not srv or not srv.get("server_online"):
                        n["server_online"] = False
                        n["singbox_online"] = False
                        n["node_status"] = "offline"
                        n["status_text"] = "服务器离线"
                    else:
                        is_sb = bool(srv.get("singbox_online"))
                        is_srv = bool(srv.get("server_online"))
                        n["server_online"] = is_srv
                        n["singbox_online"] = is_sb
                        n["probe_online"] = bool(srv.get("probe_online"))
                        n["node_status"] = "online"
                        n["status_text"] = "正常在线"

            self._send_json({"ok": True, "nodes": nodes})
            return

        # Check if node has referencing subscription rules before deletion
        if "/rules-check" in path and (path.startswith("/api/nodes/") or path.startswith("/api/node-mgr/nodes/")):
            parts = path.rstrip("/").split("/")
            idx = parts.index("rules-check")
            node_id = parts[idx - 1]
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT name FROM nodes WHERE id = ?", (node_id,))
            row = c.fetchone()
            conn.close()
            if not row:
                self._send_json({"ok": False, "error": "节点不存在"}, 404)
                return
            node_name = row[0]
            refs = get_rules_referencing_node(node_name)
            self._send_json({
                "ok": True,
                "node_id": node_id,
                "node_name": node_name,
                "references": refs,
                "has_references": len(refs) > 0
            })
            return

        # Comprehensive manual health check: refresh Komari recent stats + concurrent node TCP ping
        if path in ["/api/nodes/check-all", "/api/node-mgr/nodes/check-all"]:
            global _stats_cache
            _stats_cache["data"] = None
            servers_data = get_servers_with_stats()
            _stats_cache["ts"] = time.time()
            _stats_cache["data"] = servers_data
            servers_map = {s["uuid"]: s for s in servers_data.get("servers", [])}

            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT id, name, server_ip, port, protocol, sni FROM nodes WHERE enabled = 1")
            rows = c.fetchall()
            conn.close()

            ping_results = {}
            def _check_one(r):
                nid, name, server_ip, port, proto, sni = r
                res = ping_node_handshake(server_ip, port, protocol=proto, sni=sni, timeout=2.5)
                p_item = {
                    "ok": res["success"],
                    "node_id": nid,
                    "node_name": name,
                    "latency_ms": res.get("latency_ms"),
                    "handshake_type": res.get("handshake_type", "TCP"),
                    "error": res.get("error", None)
                }
                _node_latency_cache[nid] = p_item
                return nid, p_item

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(12, max(1, len(rows)))) as executor:
                for nid, data in executor.map(_check_one, rows):
                    ping_results[nid] = data

            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM nodes ORDER BY is_external ASC, id DESC")
            cols = [d[0] for d in c.description]
            nodes = [dict(zip(cols, row)) for row in c.fetchall()]
            conn.close()

            # Filter out orphan nodes whose server no longer exists
            nodes = [n for n in nodes if n.get("is_external") or n.get("server_uuid") == "external" or n.get("server_uuid") in servers_map]

            online_node_count = 0
            for n in nodes:
                n["link"] = build_node_share_link(n)
                p_res = ping_results.get(n["id"]) or _node_latency_cache.get(n["id"])
                if p_res and p_res.get("latency_ms"):
                    n["ping_ms"] = p_res["latency_ms"]

                if n.get("is_external") or n.get("server_uuid") == "external":
                    n["is_external"] = 1
                    n["server_online"] = True
                    n["singbox_online"] = True
                    n["node_status"] = "online"
                    n["status_text"] = "外部节点"
                    online_node_count += 1
                else:
                    srv = servers_map.get(n.get("server_uuid"))
                    if not srv or not srv.get("server_online"):
                        n["server_online"] = False
                        n["singbox_online"] = False
                        n["node_status"] = "offline"
                        n["status_text"] = "服务器离线"
                    else:
                        is_sb = bool(srv.get("singbox_online"))
                        is_srv = bool(srv.get("server_online"))
                        n["server_online"] = is_srv
                        n["singbox_online"] = is_sb
                        n["probe_online"] = bool(srv.get("probe_online"))
                        n["node_status"] = "online"
                        n["status_text"] = "正常在线"
                        online_node_count += 1

            self._send_json({
                "ok": True,
                "servers": servers_data.get("servers", []),
                "nodes": nodes,
                "ping_results": ping_results,
                "total_servers": len(servers_data.get("servers", [])),
                "online_servers": servers_data.get("singbox_online_count", 0),
                "total_nodes": len(nodes),
                "online_nodes": online_node_count
            })
            return

        # Real TCP/TLS handshake ping endpoint for all enabled nodes (concurrent)
        if path in ["/api/nodes/ping-all", "/api/node-mgr/nodes/ping-all"]:
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT id, name, server_ip, port, protocol, sni, is_relay, relay_server_ip, relay_port FROM nodes WHERE enabled = 1")
            rows = c.fetchall()
            conn.close()

            results = {}
            def _check(r):
                nid, name, server_ip, port, proto, sni, is_relay, relay_server_ip, relay_port = r
                target_ip = relay_server_ip if (is_relay and relay_server_ip) else server_ip
                target_port = (relay_port or port) if is_relay else port
                res = ping_node_handshake(target_ip, target_port, protocol=proto, sni=sni, timeout=2.5)
                p_item = {
                    "ok": res["success"],
                    "node_id": nid,
                    "node_name": name,
                    "latency_ms": res.get("latency_ms"),
                    "handshake_type": res.get("handshake_type", "TCP"),
                    "error": res.get("error", None)
                }
                _node_latency_cache[nid] = p_item
                return nid, p_item

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(12, max(1, len(rows)))) as executor:
                for nid, data in executor.map(_check, rows):
                    results[nid] = data

            self._send_json({"ok": True, "results": results})
            return

        # Real TCP/TLS handshake ping endpoint for single node: /api/nodes/<id>/ping
        m_ping = re.match(r"^/api/(?:node-mgr/)?nodes/(\d+)/ping/?$", path)
        if m_ping:
            node_id = m_ping.group(1)
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT id, name, server_ip, port, protocol, sni, is_relay, relay_server_ip, relay_port FROM nodes WHERE id = ?", (node_id,))
            row = c.fetchone()
            conn.close()
            if not row:
                self._send_json({"ok": False, "error": "节点不存在"}, 404)
                return

            nid, name, server_ip, port, proto, sni, is_relay, relay_server_ip, relay_port = row
            target_ip = relay_server_ip if (is_relay and relay_server_ip) else server_ip
            target_port = (relay_port or port) if is_relay else port
            result = ping_node_handshake(target_ip, target_port, protocol=proto, sni=sni)
            p_data = {
                "ok": result["success"],
                "node_id": nid,
                "node_name": name,
                "latency_ms": result["latency_ms"],
                "handshake_type": result.get("handshake_type", "TCP"),
                "error": result.get("error", None)
            }
            _node_latency_cache[nid] = p_data
            self._send_json(p_data)
            return

        if path in ["/api/sub/title", "/api/node-mgr/sub/title"]:
            rules = get_subscription_rules()
            self._send_json({"ok": True, "sub_title": rules.get("sub_title", "Komari Pro 优质节点")})
            return

        if path == "/api/sub/token" or path == "/api/node-mgr/sub/token":
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT token FROM subscriptions ORDER BY id ASC LIMIT 1")
            row = c.fetchone()
            conn.close()
            token = row[0] if row else ""
            rules_cfg = get_subscription_rules()
            base_title = rules_cfg.get("sub_title") or "Komari Pro 优质节点"
            frag = f"#{urllib.parse.quote(base_title)}"
            self._send_json({"ok": True, "token": token, "sub_url": f"https://{DOMAIN}/sub/{token}{frag}", "profile_title": base_title})
            return

        # Public User Portal Info Endpoint
        if path in ["/api/user/info", "/api/node-mgr/user/info"]:
            token = query.get("token", [""])[0].strip()
            if not token:
                self._send_json({"ok": False, "error": "缺少订阅 Token 参数"}, 400)
                return
            user_info, user_nodes = get_user_portal_payload(token)
            if not user_info:
                self._send_json({"ok": False, "error": "无效的订阅凭证 (用户不存在)"}, 404)
                return
            self._send_json({"ok": True, "user": user_info, "nodes": user_nodes})
            return

        # User subscriptions list endpoint (Admin)
        if path in ["/api/sub/users", "/api/node-mgr/sub/users"]:
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("PRAGMA table_info(subscriptions)")
            sub_cols = [r[1] for r in c.fetchall()]
            has_creds = ('username' in sub_cols and 'password' in sub_cols)
            if has_creds:
                c.execute("SELECT id, name, token, enabled, remark, created_at, user_uuid, traffic_limit_bytes, traffic_used_bytes, expire_time, username, password FROM subscriptions ORDER BY id ASC")
            else:
                c.execute("SELECT id, name, token, enabled, remark, created_at, user_uuid, traffic_limit_bytes, traffic_used_bytes, expire_time FROM subscriptions ORDER BY id ASC")
            users = []
            today_str = datetime.now().strftime("%Y-%m-%d")
            rules_cfg = get_subscription_rules()
            base_title = rules_cfg.get("sub_title") or "Komari Pro 优质节点"
            for r in c.fetchall():
                uid = r[0]
                uname = r[1] or "默认用户"
                tok = r[2]
                en = bool(r[3])
                rmk = r[4] or ""
                cat = str(r[5])
                u_uuid = r[6] if len(r) > 6 and r[6] else ""
                limit_b = int(r[7] or 0) if len(r) > 7 and r[7] is not None else 0
                used_b = int(r[8] or 0) if len(r) > 8 and r[8] is not None else 0
                exp = str(r[9] or "").strip() if len(r) > 9 and r[9] is not None else ""
                username = r[10] if len(r) > 10 and r[10] else uname
                password = r[11] if len(r) > 11 and r[11] else "password123"

                rem_b = max(0, limit_b - used_b) if limit_b > 0 else 0
                pct = round((used_b / limit_b) * 100, 1) if limit_b > 0 else 0
                is_exh = (limit_b > 0 and used_b >= limit_b)
                is_exp = bool(exp and today_str > exp.split("T")[0])

                days_left = None
                if exp:
                    try:
                        days_left = (datetime.strptime(exp.split("T")[0], "%Y-%m-%d").date() - datetime.now().date()).days
                    except Exception:
                        pass

                if not en:
                    st = "disabled"
                    st_text = "已封禁"
                elif is_exh:
                    st = "exhausted"
                    st_text = "流量已耗尽"
                elif is_exp:
                    st = "expired"
                    st_text = "已到期"
                else:
                    st = "normal"
                    st_text = "正常使用中"

                p_title = f"{base_title} - {uname}" if (uname and uname != "default") else base_title
                frag = f"#{urllib.parse.quote(p_title)}"

                users.append({
                    "id": uid,
                    "name": uname,
                    "username": username,
                    "password": password,
                    "token": tok,
                    "enabled": en,
                    "remark": rmk,
                    "created_at": cat,
                    "user_uuid": u_uuid,
                    "traffic_limit_bytes": limit_b,
                    "traffic_limit_gb": round(limit_b / (1024**3), 2) if limit_b > 0 else 0,
                    "traffic_limit_formatted": format_bytes(limit_b) if limit_b > 0 else "无限制",
                    "traffic_used_bytes": used_b,
                    "traffic_used_gb": round(used_b / (1024**3), 2),
                    "traffic_used_formatted": format_bytes(used_b),
                    "traffic_remaining_bytes": rem_b,
                    "traffic_remaining_formatted": format_bytes(rem_b) if limit_b > 0 else "无限制",
                    "traffic_percent": min(100.0, pct),
                    "expire_time": exp,
                    "expire_remaining_days": days_left,
                    "is_exhausted": is_exh,
                    "is_expired": is_exp,
                    "status": st,
                    "status_text": st_text,
                    "profile_title": p_title,
                    "sub_url": f"https://{DOMAIN}/sub/{tok}{frag}",
                    "portal_url": f"https://{DOMAIN}/user?token={tok}"
                })
            conn.close()
            self._send_json({"ok": True, "users": users})
            return

        # Full Data Export endpoint (Servers, Ping tasks, Nodes, Subscriptions, Rules)
        if path in ["/api/data/export", "/api/node-mgr/data/export"]:
            def _clean_val(v):
                if isinstance(v, bytes):
                    try:
                        return v.decode("utf-8")
                    except UnicodeDecodeError:
                        import base64
                        return "__b64__:" + base64.b64encode(v).decode("ascii")
                if hasattr(v, "isoformat"):
                    return v.isoformat()
                return v

            def _clean_row(d):
                return {k: _clean_val(v) for k, v in d.items()}

            export_data = {
                "version": "1.0",
                "export_time": datetime.now().isoformat(),
                "domain": DOMAIN,
                "servers": [],
                "ping_tasks": [],
                "nodes": [],
                "subscriptions": [],
                "subscription_rules": {},
                "notification_channels": [],
                "notification_rules": []
            }
            if os.path.exists(KOMARI_DB):
                try:
                    k_conn = sqlite3.connect(KOMARI_DB)
                    k_conn.row_factory = sqlite3.Row
                    k_c = k_conn.cursor()
                    k_c.execute("SELECT * FROM clients")
                    export_data["servers"] = [_clean_row(dict(r)) for r in k_c.fetchall()]
                    try:
                        k_c.execute("SELECT * FROM ping_tasks")
                        export_data["ping_tasks"] = [_clean_row(dict(r)) for r in k_c.fetchall()]
                    except Exception:
                        pass
                    k_conn.close()
                except Exception as e:
                    print(f"Export komari.db error: {e}")

            if os.path.exists(NODES_DB):
                try:
                    n_conn = sqlite3.connect(NODES_DB)
                    n_conn.row_factory = sqlite3.Row
                    n_c = n_conn.cursor()
                    n_c.execute("SELECT * FROM nodes")
                    export_data["nodes"] = [_clean_row(dict(r)) for r in n_c.fetchall()]

                    n_c.execute("SELECT * FROM subscriptions")
                    export_data["subscriptions"] = [_clean_row(dict(r)) for r in n_c.fetchall()]

                    n_c.execute("SELECT * FROM subscription_rules WHERE id = 1")
                    rule_row = n_c.fetchone()
                    if rule_row:
                        export_data["subscription_rules"] = _clean_row(dict(rule_row))

                    n_c.execute("SELECT * FROM notification_channels")
                    export_data["notification_channels"] = [_clean_row(dict(r)) for r in n_c.fetchall()]

                    n_c.execute("SELECT * FROM notification_rules")
                    export_data["notification_rules"] = [_clean_row(dict(r)) for r in n_c.fetchall()]

                    n_conn.close()
                except Exception as e:
                    print(f"Export nodes.db error: {e}")

            json_bytes = json.dumps(export_data, indent=2, ensure_ascii=False).encode("utf-8")
            filename = f"komari_full_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(json_bytes)))
            self.end_headers()
            self.wfile.write(json_bytes)
            return

        # Realm config sync endpoint for relay servers
        if path == "/api/agent/realm-config" or path == "/api/node-mgr/agent/realm-config":
            token = query.get("token", [""])[0]
            if not token:
                self._send_text("# error: missing token\n", 400)
                return

            # Record Realm heartbeat
            try:
                conn_hb = sqlite3.connect(NODES_DB)
                c_hb = conn_hb.cursor()
                c_hb.execute("CREATE TABLE IF NOT EXISTS realm_heartbeats (token TEXT PRIMARY KEY, last_seen INTEGER)")
                c_hb.execute("INSERT OR REPLACE INTO realm_heartbeats (token, last_seen) VALUES (?, ?)", (token, int(time.time())))
                conn_hb.commit()
                conn_hb.close()
            except Exception:
                pass

            servers = get_servers()
            matched = None
            for s in servers:
                if s["token"] == token or s["uuid"] == token:
                    matched = s
                    break

            suuid = matched["uuid"] if matched else token
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT id, name, port, server_ip, relay_port FROM nodes WHERE relay_server_uuid = ? AND is_relay = 1 AND enabled = 1", (suuid,))
            rows = c.fetchall()
            conn.close()

            toml_lines = [
                "[log]",
                'level = "warn"',
                "",
                "[network]",
                "no_tcp = false",
                "use_udp = true",
                ""
            ]
            if not rows:
                toml_lines.append("endpoints = []")
                toml_lines.append("")
            for r in rows:
                nid, nname, port, target_ip, rport = r
                lport = rport or port
                if target_ip and lport and port:
                    toml_lines.append(f"# {nname}")
                    toml_lines.append("[[endpoints]]")
                    toml_lines.append(f'listen = "0.0.0.0:{lport}"')
                    toml_lines.append(f'remote = "{target_ip}:{port}"')
                    toml_lines.append("")

            self._send_text("\n".join(toml_lines), 200, "text/plain; charset=utf-8")
            return

        # Agent config sync endpoint
        if path == "/api/agent/config" or path == "/api/node-mgr/agent/config":
            token = query.get("token", [""])[0]
            if not token:
                self._send_json({"error": "missing token"}, 400)
                return
            
            # Record heartbeat
            try:
                conn_hb = sqlite3.connect(NODES_DB)
                c_hb = conn_hb.cursor()
                c_hb.execute("INSERT OR REPLACE INTO agent_heartbeats (token, last_seen) VALUES (?, ?)", (token, int(time.time())))
                conn_hb.commit()
                conn_hb.close()
            except Exception as e:
                pass

            # Find client by token in komari.db
            servers = get_servers()
            matched = None
            for s in servers:
                if s["token"] == token or s["uuid"] == token:
                    matched = s
                    break
            
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            if matched:
                c.execute("SELECT * FROM nodes WHERE server_uuid = ? AND enabled = 1", (matched["uuid"],))
            else:
                # Fallback: token might directly match server_uuid
                c.execute("SELECT * FROM nodes WHERE server_uuid = ? AND enabled = 1", (token,))
            
            cols = [d[0] for d in c.description]
            nodes = [dict(zip(cols, row)) for row in c.fetchall()]
            conn.close()

            config = build_sing_box_config(nodes)
            self._send_json(config)
            return

        # Agent Register/Lock Server IP Endpoint (永恒防错机制)
        if path in ["/api/agent/set-server-ip", "/api/node-mgr/agent/set-server-ip"]:
            token = query.get("token", [""])[0]
            custom_ip = query.get("ip", [""])[0]
            ok, err, suuid = set_authoritative_server_ip(token, custom_ip)
            if ok:
                if custom_ip:
                    unblock_ip(custom_ip)
                self._send_json({"ok": True, "uuid": suuid, "custom_ip": custom_ip})
            else:
                self._send_json({"ok": False, "error": err or "server not found"}, 400 if err != "server not found" else 404)
            return

        # Agent sync script endpoint (for live auto-update of komari-pro-node-sync.sh)
        if path in ["/api/agent/sync-script", "/api/node-mgr/agent/sync-script"]:
            token = query.get("token", [""])[0]
            if not token:
                self._send_text("# error: missing token", 400)
                return

            req_host = self.headers.get("Host", DOMAIN).split(":")[0]
            servers = get_servers()
            matched = any(s.get("token") == token or s.get("uuid") == token for s in servers)
            if not matched and token != "MASTER_SECRET":
                try:
                    conn_hb = sqlite3.connect(NODES_DB)
                    c_hb = conn_hb.cursor()
                    c_hb.execute("SELECT 1 FROM agent_heartbeats WHERE token = ? LIMIT 1", (token,))
                    found = c_hb.fetchone()
                    conn_hb.close()
                    if not found:
                        record_token_failure(self.get_client_ip())
                        self._send_text("# error: unauthorized token", 401)
                        return
                except Exception:
                    pass

            script_text = build_node_sync_script(f"https://{req_host}", token)
            self._send_text(script_text, 200, "text/x-shellscript; charset=utf-8")
            return

        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}

        # Agent Register/Lock Server IP Endpoint (永恒防错机制 POST)
        if path in ["/api/agent/set-server-ip", "/api/node-mgr/agent/set-server-ip"]:
            token = str(query.get("token", [""])[0] or body.get("token") or "")
            custom_ip = str(query.get("ip", [""])[0] or body.get("ip") or "").strip()
            ok, err, suuid = set_authoritative_server_ip(token, custom_ip)
            if ok:
                if custom_ip:
                    unblock_ip(custom_ip)
                self._send_json({"ok": True, "uuid": suuid, "custom_ip": custom_ip})
            else:
                self._send_json({"ok": False, "error": err or "server not found"}, 400 if err != "server not found" else 404)
            return

        # Node Agent Traffic Reporting Endpoint
        if path in ["/api/agent/report-traffic", "/api/node-mgr/agent/report-traffic"]:
            token = str(query.get("token", [""])[0] or body.get("token") or "")
            if not token:
                self._send_json({"error": "missing token"}, 400)
                return

            servers = get_servers()
            matched = any(s.get("token") == token or s.get("uuid") == token for s in servers)
            if not matched and token != "MASTER_SECRET":
                try:
                    conn_hb = sqlite3.connect(NODES_DB)
                    c_hb = conn_hb.cursor()
                    c_hb.execute("SELECT 1 FROM agent_heartbeats WHERE token = ? LIMIT 1", (token,))
                    found = c_hb.fetchone()
                    conn_hb.close()
                    if not found:
                        record_token_failure(self.get_client_ip())
                        self._send_json({"error": "unauthorized token"}, 401)
                        return
                except Exception:
                    pass

            # Update heartbeat timestamp
            try:
                conn_hb = sqlite3.connect(NODES_DB)
                c_hb = conn_hb.cursor()
                c_hb.execute("INSERT OR REPLACE INTO agent_heartbeats (token, last_seen) VALUES (?, ?)", (token, int(time.time())))
                conn_hb.commit()
                conn_hb.close()
            except Exception:
                pass

            traffic_data = body.get("traffic") or {}
            if traffic_data and isinstance(traffic_data, dict):
                record_user_traffic(traffic_data)

            self._send_json({"ok": True})
            return

        # Public User Portal Login Endpoint
        if path in ["/api/user/login", "/api/node-mgr/user/login"]:
            username = str(body.get("username") or "").strip()
            password = str(body.get("password") or "").strip()
            if not username or not password:
                self._send_json({"ok": False, "error": "请输入用户名和密码"}, 400)
                return

            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("PRAGMA table_info(subscriptions)")
            cols = [r[1] for r in c.fetchall()]
            if 'username' in cols and 'password' in cols:
                c.execute("SELECT token FROM subscriptions WHERE (LOWER(username) = LOWER(?) OR LOWER(name) = LOWER(?)) AND password = ? LIMIT 1",
                          (username, username, password))
            else:
                c.execute("SELECT token FROM subscriptions WHERE LOWER(name) = LOWER(?) LIMIT 1", (username,))
            row = c.fetchone()
            conn.close()

            if not row:
                self._send_json({"ok": False, "error": "用户名或密码错误"}, 401)
                return

            token = row[0]
            user_info, user_nodes = get_user_portal_payload(token)
            if not user_info:
                self._send_json({"ok": False, "error": "用户账号异常或已被删除"}, 404)
                return

            self._send_json({
                "ok": True,
                "token": token,
                "user": user_info,
                "nodes": user_nodes
            })
            return

        # Save subscription rules
        
        # Notifications API endpoints
        if path in ["/api/notifications/channels/save", "/api/node-mgr/notifications/channels/save"]:
            ch_id = body.get("id")
            ch_type = body.get("type", "telegram")
            name = body.get("name", "Telegram 机器人")
            enabled = 1 if body.get("enabled", True) else 0
            config = json.dumps(body.get("config", {}))

            try:
                conn = sqlite3.connect(NODES_DB)
                c = conn.cursor()
                if not ch_id:
                    c.execute("SELECT id FROM notification_channels WHERE type = ? LIMIT 1", (ch_type,))
                    row = c.fetchone()
                    if row:
                        ch_id = row[0]

                if ch_id:
                    c.execute("UPDATE notification_channels SET type=?, name=?, enabled=?, config=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                              (ch_type, name, enabled, config, ch_id))
                else:
                    c.execute("INSERT INTO notification_channels (type, name, enabled, config) VALUES (?, ?, ?, ?)",
                              (ch_type, name, enabled, config))
                conn.commit()
                conn.close()
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
            return

        if path in ["/api/notifications/channels/toggle", "/api/node-mgr/notifications/channels/toggle"]:
            ch_id = body.get("id")
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("UPDATE notification_channels SET enabled = (1 - enabled), updated_at=CURRENT_TIMESTAMP WHERE id = ?", (ch_id,))
            conn.commit()
            conn.close()
            self._send_json({"ok": True})
            return

        if path in [
            "/api/notifications/rules",
            "/api/node-mgr/notifications/rules",
            "/api/notifications/rules/toggle",
            "/api/node-mgr/notifications/rules/toggle",
            "/api/notifications/rules/config",
            "/api/node-mgr/notifications/rules/config"
        ]:
            rule_key = body.get("rule_key")
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            if "enabled" in body:
                enabled = 1 if body.get("enabled", True) else 0
                c.execute("UPDATE notification_rules SET enabled=?, updated_at=CURRENT_TIMESTAMP WHERE rule_key=?", (enabled, rule_key))
            if "config" in body:
                cfg = json.dumps(body.get("config", {}))
                c.execute("UPDATE notification_rules SET config=?, updated_at=CURRENT_TIMESTAMP WHERE rule_key=?", (cfg, rule_key))
            conn.commit()
            conn.close()
            self._send_json({"ok": True})
            return

        if path in ["/api/notifications/test", "/api/node-mgr/notifications/test"]:
            title = body.get("title", "⚡ 通知通道即时测试")
            message = body.get("message", "这是一条由 Komari 节点管理后台发送的即时测试通知！\n\n各项智能告警规则正在全天候守护您的节点与服务器。")
            level = body.get("level", "info")
            rule_key = body.get("rule_key", "manual_test")
            res = dispatch_notification(title, message, level=level, rule_key=rule_key)
            self._send_json(res)
            return

        if path in ["/api/notifications/logs/clear", "/api/node-mgr/notifications/logs/clear"]:
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("DELETE FROM notification_logs")
            conn.commit()
            conn.close()
            self._send_json({"ok": True})
            return

        if path in ["/api/sub/title", "/api/node-mgr/sub/title"]:
            title = str(body.get("sub_title") or "").strip()
            if not title:
                self._send_json({"ok": False, "error": "订阅标题不能为空"}, 400)
                return
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("UPDATE subscription_rules SET sub_title = ? WHERE id = 1", (title,))
            conn.commit()
            conn.close()
            self._send_json({"ok": True, "sub_title": title, "msg": f"客户端订阅名称已成功保存为：{title}"})
            return

        if path in ["/api/sub/rules", "/api/node-mgr/sub/rules"]:
            direct_bt = 1 if body.get("direct_bt", True) else 0
            direct_cn = 1 if body.get("direct_cn", True) else 0
            direct_lan = 1 if body.get("direct_lan", True) else 0
            block_ads = 1 if body.get("block_ads", False) else 0
            enable_auto_group = 1 if body.get("enable_auto_group", True) else 0
            final_match = body.get("final_match") or "PROXY"
            custom_rules = body.get("custom_rules", "")
            proxy_ai = 1 if body.get("proxy_ai", False) else 0
            proxy_tg = 1 if body.get("proxy_tg", False) else 0
            proxy_media = 1 if body.get("proxy_media", False) else 0
            proxy_dev = 1 if body.get("proxy_dev", False) else 0
            direct_games = 1 if body.get("direct_games", False) else 0
            target_ai = body.get("target_ai") or "PROXY"
            target_tg = body.get("target_tg") or "PROXY"
            target_media = body.get("target_media") or "PROXY"
            target_dev = body.get("target_dev") or "PROXY"
            target_games = body.get("target_games") or "DIRECT"

            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            if "sub_title" in body:
                st = str(body.get("sub_title") or "").strip()
                if st:
                    c.execute("UPDATE subscription_rules SET sub_title = ? WHERE id = 1", (st,))
            c.execute("""
                UPDATE subscription_rules
                SET direct_bt=?, direct_cn=?, direct_lan=?, block_ads=?, enable_auto_group=?,
                    final_match=?, custom_rules=?, proxy_ai=?, proxy_tg=?, proxy_media=?,
                    proxy_dev=?, direct_games=?, target_ai=?, target_tg=?, target_media=?,
                    target_dev=?, target_games=?, updated_at=CURRENT_TIMESTAMP
                WHERE id = 1
            """, (direct_bt, direct_cn, direct_lan, block_ads, enable_auto_group,
                  final_match, custom_rules, proxy_ai, proxy_tg, proxy_media,
                  proxy_dev, direct_games, target_ai, target_tg, target_media,
                  target_dev, target_games))
            conn.commit()
            conn.close()
            self._send_json({"ok": True, "msg": "订阅规则已保存生效"})
            return

        if path in ["/api/sub/rules/fix-dangling", "/api/node-mgr/sub/rules/fix-dangling"]:
            fallback = body.get("fallback", "PROXY")
            res = fix_all_dangling_rules(fallback)
            self._send_json({"ok": True, "fixed_count": res["fixed"], "msg": f"已将 {res['fixed']} 条失效规则安全修复为 {fallback}"})
            return

        # Reset traffic baselines (calibrate to current)
        if path == "/api/traffic/reset" or path == "/api/node-mgr/traffic/reset":
            target_uuid = body.get("uuid", "")
            metrics_by_uuid = {}
            if os.path.exists(METRICS_DB):
                try:
                    conn_m = sqlite3.connect(METRICS_DB)
                    c_m = conn_m.cursor()
                    c_m.execute("""
                        SELECT s.entity_id, s.metric_name, r.last_val
                        FROM metric_series s
                        JOIN metric_rollups r ON s.id = r.series_id
                        WHERE s.metric_name IN ('net.total.up', 'net.total.down')
                        ORDER BY r.bucket_milli DESC
                    """)
                    for eid, mname, val in c_m.fetchall():
                        if eid not in metrics_by_uuid:
                            metrics_by_uuid[eid] = {}
                        if mname not in metrics_by_uuid[eid]:
                            metrics_by_uuid[eid][mname] = val
                    conn_m.close()
                except Exception:
                    pass

            conn_b = sqlite3.connect(NODES_DB)
            if target_uuid == "all" or not target_uuid:
                for eid, vals in metrics_by_uuid.items():
                    conn_b.execute("INSERT OR REPLACE INTO server_traffic_baselines (uuid, baseline_up, baseline_down) VALUES (?, ?, ?)",
                                   (eid, int(vals.get('net.total.up', 0)), int(vals.get('net.total.down', 0))))
            else:
                vals = metrics_by_uuid.get(target_uuid, {})
                conn_b.execute("INSERT OR REPLACE INTO server_traffic_baselines (uuid, baseline_up, baseline_down) VALUES (?, ?, ?)",
                               (target_uuid, int(vals.get('net.total.up', 0)), int(vals.get('net.total.down', 0))))
            conn_b.commit()
            conn_b.close()
            self._send_json({"ok": True, "msg": "流量统计已重置归零"})
            return

        # Import external nodes
        if path == "/api/nodes/import" or path == "/api/node-mgr/nodes/import":
            raw_text = body.get("content", "")
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            imported_count = 0
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            for line in lines:
                parsed_node = parse_proxy_link(line)
                if parsed_node:
                    c.execute('''
                        INSERT INTO nodes (server_uuid, server_name, server_ip, name, protocol, port,
                                          uuid_or_passwd, sni, public_key, private_key, short_id, flow, ws_path, raw_link, is_external, enabled)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    ''', (
                        parsed_node["server_uuid"], parsed_node["server_name"], parsed_node["server_ip"], parsed_node["name"],
                        parsed_node["protocol"], parsed_node["port"], parsed_node["uuid_or_passwd"], parsed_node["sni"],
                        parsed_node["public_key"], parsed_node["private_key"], parsed_node["short_id"], parsed_node["flow"],
                        parsed_node["ws_path"], parsed_node["raw_link"], parsed_node["is_external"]
                    ))
                    imported_count += 1
            conn.commit()
            conn.close()
            self._send_json({"ok": True, "count": imported_count})
            return

        if path == "/api/sub/reset" or path == "/api/node-mgr/sub/reset":
            new_token = secrets.token_hex(16)
            new_uuid = str(uuid.uuid4())
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("UPDATE subscriptions SET token = ?, user_uuid = ? WHERE name = 'default' OR id = (SELECT id FROM subscriptions ORDER BY id ASC LIMIT 1)", (new_token, new_uuid))
            if c.rowcount == 0:
                c.execute("INSERT INTO subscriptions (token, name, user_uuid) VALUES (?, 'default', ?)", (new_token, new_uuid))
            # Also rotate the default uuid_or_passwd on all self-hosted nodes
            c.execute("UPDATE nodes SET uuid_or_passwd = ? WHERE is_external = 0", (new_uuid,))
            conn.commit()
            conn.close()
            get_active_user_uuids(force_refresh=True)
            rules_cfg = get_subscription_rules()
            base_title = rules_cfg.get("sub_title") or "Komari Pro 优质节点"
            frag = f"#{urllib.parse.quote(base_title)}"
            new_sub_url = f"https://{DOMAIN}/sub/{new_token}{frag}"
            self._send_json({"ok": True, "token": new_token, "user_uuid": new_uuid, "sub_url": new_sub_url, "profile_title": base_title})
            return

        # User subscriptions management endpoints
        if path in ["/api/sub/users/create", "/api/node-mgr/sub/users/create"]:
            name = str(body.get("name") or "").strip()
            username = str(body.get("username") or "").strip() or name
            password = str(body.get("password") or "").strip() or secrets.token_hex(4)
            remark = str(body.get("remark") or "").strip()
            if not username:
                self._send_json({"ok": False, "error": "用户名或账号不能为空"}, 400)
                return
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                self._send_json({"ok": False, "error": "用户名只能由英文字母和数字组成（不支持中文及特殊符号）"}, 400)
                return
            if not name:
                name = username

            traffic_limit_gb = float(body.get("traffic_limit_gb") or 0)
            limit_bytes = int(traffic_limit_gb * (1024**3)) if traffic_limit_gb > 0 else 0
            expire_time = str(body.get("expire_time") or "").strip()
            new_tok = secrets.token_hex(16)
            new_uuid = str(uuid.uuid4())
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("PRAGMA table_info(subscriptions)")
            cols = [r[1] for r in c.fetchall()]

            # Check duplicate username
            if 'username' in cols:
                c.execute("SELECT id FROM subscriptions WHERE LOWER(username) = LOWER(?) LIMIT 1", (username,))
                if c.fetchone():
                    conn.close()
                    self._send_json({"ok": False, "error": f"用户名 '{username}' 已存在，请更换"}, 400)
                    return

            if 'username' in cols and 'password' in cols:
                c.execute("INSERT INTO subscriptions (token, name, username, password, enabled, remark, user_uuid, traffic_limit_bytes, traffic_used_bytes, expire_time) VALUES (?, ?, ?, ?, 1, ?, ?, ?, 0, ?)",
                          (new_tok, name, username, password, remark, new_uuid, limit_bytes, expire_time))
            else:
                c.execute("INSERT INTO subscriptions (token, name, enabled, remark, user_uuid, traffic_limit_bytes, traffic_used_bytes, expire_time) VALUES (?, ?, 1, ?, ?, ?, 0, ?)",
                          (new_tok, name, remark, new_uuid, limit_bytes, expire_time))
            new_id = c.lastrowid
            conn.commit()
            conn.close()
            get_active_user_uuids(force_refresh=True)
            rules_cfg = get_subscription_rules()
            base_title = rules_cfg.get("sub_title") or "Komari Pro 优质节点"
            p_title = f"{base_title} - {name}" if (name and name != "default") else base_title
            frag = f"#{urllib.parse.quote(p_title)}"
            self._send_json({
                "user": {
                    "id": new_id,
                    "name": name,
                    "username": username,
                    "password": password,
                    "token": new_tok,
                    "enabled": True,
                    "remark": remark,
                    "user_uuid": new_uuid,
                    "traffic_limit_bytes": limit_bytes,
                    "traffic_limit_gb": traffic_limit_gb,
                    "traffic_used_bytes": 0,
                    "expire_time": expire_time,
                    "profile_title": p_title,
                    "sub_url": f"https://{DOMAIN}/sub/{new_tok}{frag}",
                    "portal_url": f"https://{DOMAIN}/user?token={new_tok}"
                },
                "ok": True
            })
            return

        if path in ["/api/sub/users/edit", "/api/node-mgr/sub/users/edit"]:
            uid = body.get("id")
            if not uid:
                self._send_json({"ok": False, "error": "缺少用户 ID"}, 400)
                return
            name = str(body.get("name") or "").strip()
            username = str(body.get("username") or "").strip() or name
            if not username:
                self._send_json({"ok": False, "error": "用户名或账号不能为空"}, 400)
                return
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                self._send_json({"ok": False, "error": "用户名只能由英文字母和数字组成（不支持中文及特殊符号）"}, 400)
                return
            if not name:
                name = username

            password = str(body.get("password") or "").strip()
            remark = str(body.get("remark") or "").strip()
            traffic_limit_gb = float(body.get("traffic_limit_gb") or 0)
            limit_bytes = int(traffic_limit_gb * (1024**3)) if traffic_limit_gb > 0 else 0
            expire_time = str(body.get("expire_time") or "").strip()
            traffic_used_gb = body.get("traffic_used_gb")

            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("PRAGMA table_info(subscriptions)")
            cols = [r[1] for r in c.fetchall()]
            has_creds = ('username' in cols and 'password' in cols)

            # Check duplicate username for other users
            if has_creds:
                c.execute("SELECT id FROM subscriptions WHERE LOWER(username) = LOWER(?) AND id != ? LIMIT 1", (username, uid))
                if c.fetchone():
                    conn.close()
                    self._send_json({"ok": False, "error": f"用户名 '{username}' 已被其他用户占用"}, 400)
                    return

            if has_creds:
                if password:
                    if traffic_used_gb is not None:
                        used_bytes = int(float(traffic_used_gb) * (1024**3))
                        c.execute("UPDATE subscriptions SET name=?, username=?, password=?, remark=?, traffic_limit_bytes=?, traffic_used_bytes=?, expire_time=? WHERE id=?",
                                  (name, username, password, remark, limit_bytes, used_bytes, expire_time, uid))
                    else:
                        c.execute("UPDATE subscriptions SET name=?, username=?, password=?, remark=?, traffic_limit_bytes=?, expire_time=? WHERE id=?",
                                  (name, username, password, remark, limit_bytes, expire_time, uid))
                else:
                    if traffic_used_gb is not None:
                        used_bytes = int(float(traffic_used_gb) * (1024**3))
                        c.execute("UPDATE subscriptions SET name=?, username=?, remark=?, traffic_limit_bytes=?, traffic_used_bytes=?, expire_time=? WHERE id=?",
                                  (name, username, remark, limit_bytes, used_bytes, expire_time, uid))
                    else:
                        c.execute("UPDATE subscriptions SET name=?, username=?, remark=?, traffic_limit_bytes=?, expire_time=? WHERE id=?",
                                  (name, username, remark, limit_bytes, expire_time, uid))
            else:
                if traffic_used_gb is not None:
                    used_bytes = int(float(traffic_used_gb) * (1024**3))
                    c.execute("UPDATE subscriptions SET name=?, remark=?, traffic_limit_bytes=?, traffic_used_bytes=?, expire_time=? WHERE id=?",
                              (name, remark, limit_bytes, used_bytes, expire_time, uid))
                else:
                    c.execute("UPDATE subscriptions SET name=?, remark=?, traffic_limit_bytes=?, expire_time=? WHERE id=?",
                              (name, remark, limit_bytes, expire_time, uid))
            conn.commit()
            conn.close()
            get_active_user_uuids(force_refresh=True)
            self._send_json({"ok": True})
            return

        if path in ["/api/sub/users/reset-traffic", "/api/node-mgr/sub/users/reset-traffic"]:
            uid = body.get("id")
            token = body.get("token")
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            if uid:
                c.execute("UPDATE subscriptions SET traffic_used_bytes = 0 WHERE id = ?", (uid,))
            elif token:
                c.execute("UPDATE subscriptions SET traffic_used_bytes = 0 WHERE token = ?", (token,))
            conn.commit()
            conn.close()
            get_active_user_uuids(force_refresh=True)
            self._send_json({"ok": True})
            return

        if path in ["/api/sub/users/add-traffic", "/api/node-mgr/sub/users/add-traffic"]:
            uid = body.get("id")
            token = body.get("token")
            gb = float(body.get("gb") or 0)
            bytes_to_add = int(gb * (1024**3)) if gb else int(body.get("bytes") or 0)
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            if uid:
                c.execute("UPDATE subscriptions SET traffic_used_bytes = traffic_used_bytes + ? WHERE id = ?", (bytes_to_add, uid))
            elif token:
                c.execute("UPDATE subscriptions SET traffic_used_bytes = traffic_used_bytes + ? WHERE token = ?", (bytes_to_add, token))
            conn.commit()
            conn.close()
            get_active_user_uuids(force_refresh=True)
            self._send_json({"ok": True})
            return

        if path in ["/api/sub/users/reset", "/api/node-mgr/sub/users/reset"]:
            uid = body.get("id")
            token = body.get("token")
            new_tok = secrets.token_hex(16)
            new_uuid = str(uuid.uuid4())
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            if uid is not None:
                c.execute("UPDATE subscriptions SET token = ?, user_uuid = ? WHERE id = ?", (new_tok, new_uuid, uid))
            elif token:
                c.execute("UPDATE subscriptions SET token = ?, user_uuid = ? WHERE token = ?", (new_tok, new_uuid, token))
            else:
                c.execute("UPDATE subscriptions SET token = ?, user_uuid = ? WHERE id = (SELECT id FROM subscriptions ORDER BY id ASC LIMIT 1)", (new_tok, new_uuid))
            conn.commit()
            conn.close()
            get_active_user_uuids(force_refresh=True)
            rules_cfg = get_subscription_rules()
            base_title = rules_cfg.get("sub_title") or "Komari Pro 优质节点"
            frag = f"#{urllib.parse.quote(base_title)}"
            self._send_json({"ok": True, "token": new_tok, "user_uuid": new_uuid, "sub_url": f"https://{DOMAIN}/sub/{new_tok}{frag}", "profile_title": base_title})
            return

        if path in ["/api/sub/users/toggle", "/api/node-mgr/sub/users/toggle"]:
            uid = body.get("id")
            enabled = 1 if body.get("enabled", True) else 0
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("UPDATE subscriptions SET enabled = ? WHERE id = ?", (enabled, uid))
            conn.commit()
            conn.close()
            get_active_user_uuids(force_refresh=True)
            self._send_json({"ok": True})
            return

        if path in ["/api/sub/users/delete", "/api/node-mgr/sub/users/delete"]:
            uid = body.get("id")
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("DELETE FROM subscriptions WHERE id = ?", (uid,))
            conn.commit()
            conn.close()
            get_active_user_uuids(force_refresh=True)
            self._send_json({"ok": True})
            return

        if path in ["/api/security/unblock-ip", "/api/node-mgr/security/unblock-ip"]:
            target_ip = str(body.get("ip") or query.get("ip", [""])[0] or "").strip()
            if not target_ip:
                self._send_json({"ok": False, "error": "missing ip"}, 400)
                return
            unblock_ip(target_ip)
            self._send_json({"ok": True, "message": f"IP {target_ip} 已成功从防火墙解封并允许连接", "blocked_ips": get_blocked_ips_list()})
            return

        if path in ["/api/servers/add", "/api/node-mgr/servers/add"]:
            name = str(body.get("name") or "New Server").strip()
            custom_ip = str(body.get("custom_ip") or body.get("ip") or "").strip()
            # If this IP was previously blocked, unblock it immediately so the re-added server connects smoothly
            if custom_ip:
                unblock_ip(custom_ip)
            new_uuid = str(uuid.uuid4())
            new_token = secrets.token_hex(16)
            now_iso = datetime.now().isoformat()
            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("INSERT INTO clients (uuid, token, name, created_at, updated_at, ipv4) VALUES (?, ?, ?, ?, ?, ?)",
                            (new_uuid, new_token, name, now_iso, now_iso, custom_ip))
                conn_k.commit()
                conn_k.close()
                try:
                    sync_ping_tasks_all_clients()
                except Exception:
                    pass
            if custom_ip and os.path.exists(NODES_DB):
                conn_r = sqlite3.connect(NODES_DB)
                c_r = conn_r.cursor()
                c_r.execute("CREATE TABLE IF NOT EXISTS server_realm_configs (uuid TEXT PRIMARY KEY, has_realm INTEGER DEFAULT 0, custom_ip TEXT DEFAULT '', is_landing INTEGER DEFAULT 0, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                c_r.execute("INSERT OR REPLACE INTO server_realm_configs (uuid, has_realm, custom_ip, is_landing, updated_at) VALUES (?, 0, ?, 0, CURRENT_TIMESTAMP)", (new_uuid, custom_ip))
                conn_r.commit()
                conn_r.close()
            ip_flag = f" --ip {custom_ip}" if custom_ip else ""
            install_cmd = f"wget -qO- https://{DOMAIN}/install-node.sh | sudo bash -s -- -e https://{DOMAIN} -t {new_token}{ip_flag}"
            self._send_json({"ok": True, "uuid": new_uuid, "token": new_token, "name": name, "custom_ip": custom_ip, "install_cmd": install_cmd})
            return

        if path in ["/api/servers/edit", "/api/node-mgr/servers/edit"]:
            suuid = body.get("uuid")
            if not suuid or not os.path.exists(KOMARI_DB):
                self._send_json({"ok": False, "error": "invalid params"}, 400)
                return

            fields = []
            vals = []
            allowed = [
                ("name", str), ("price", float), ("billing_cycle", int),
                ("currency", str), ("auto_renewal", int), ("expired_at", str),
                ("traffic_limit", int), ("traffic_limit_type", str),
                ("group", str), ("tags", str), ("hidden", int),
                ("weight", int), ("remark", str), ("public_remark", str)
            ]
            for f_name, f_type in allowed:
                if f_name in body:
                    val = body[f_name]
                    if val is not None and f_name in ["auto_renewal", "hidden"]:
                        val = 1 if val else 0
                    elif val is not None and f_type == float:
                        try: val = float(val)
                        except: val = 0.0
                    elif val is not None and f_type == int:
                        try: val = int(val)
                        except: val = 0
                    fields.append(f"`{f_name}` = ?")
                    vals.append(val)

            fields.append("`updated_at` = ?")
            vals.append(datetime.now().isoformat())
            vals.append(suuid)

            conn_k = sqlite3.connect(KOMARI_DB)
            c_k = conn_k.cursor()
            c_k.execute(f"UPDATE clients SET {', '.join(fields)} WHERE uuid = ?", vals)
            conn_k.commit()
            conn_k.close()

            if "name" in body and body["name"]:
                conn_n = sqlite3.connect(NODES_DB)
                c_n = conn_n.cursor()
                c_n.execute("UPDATE nodes SET server_name = ? WHERE server_uuid = ?", (body["name"], suuid))
                conn_n.commit()
                conn_n.close()

            if "has_realm" in body or "custom_ip" in body or "is_landing" in body:
                conn_r = sqlite3.connect(NODES_DB)
                c_r = conn_r.cursor()
                c_r.execute("CREATE TABLE IF NOT EXISTS server_realm_configs (uuid TEXT PRIMARY KEY, has_realm INTEGER DEFAULT 0, custom_ip TEXT DEFAULT '', is_landing INTEGER DEFAULT 0, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                try:
                    c_r.execute("ALTER TABLE server_realm_configs ADD COLUMN custom_ip TEXT DEFAULT ''")
                except Exception:
                    pass
                try:
                    c_r.execute("ALTER TABLE server_realm_configs ADD COLUMN is_landing INTEGER DEFAULT 0")
                except Exception:
                    pass
                c_r.execute("SELECT has_realm, custom_ip, is_landing FROM server_realm_configs WHERE uuid = ?", (suuid,))
                row_r = c_r.fetchone()
                cur_hr = row_r[0] if row_r else 0
                cur_cip = row_r[1] if row_r and len(row_r) > 1 else ''
                cur_land = row_r[2] if row_r and len(row_r) > 2 else 0
                new_hr = (1 if body["has_realm"] else 0) if "has_realm" in body else cur_hr
                new_cip = str(body["custom_ip"]).strip() if "custom_ip" in body else cur_cip
                new_land = (1 if body["is_landing"] else 0) if "is_landing" in body else cur_land
                c_r.execute("INSERT OR REPLACE INTO server_realm_configs (uuid, has_realm, custom_ip, is_landing, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", (suuid, new_hr, new_cip, new_land))
                conn_r.commit()
                conn_r.close()
                if "custom_ip" in body and new_cip:
                    unblock_ip(new_cip)
                    if os.path.exists(KOMARI_DB):
                        conn_k = sqlite3.connect(KOMARI_DB)
                        c_k = conn_k.cursor()
                        c_k.execute("UPDATE clients SET ipv4 = ? WHERE uuid = ?", (new_cip, suuid))
                        conn_k.commit()
                        conn_k.close()
                    conn_n = sqlite3.connect(NODES_DB)
                    c_n = conn_n.cursor()
                    c_n.execute("UPDATE nodes SET server_ip = ? WHERE server_uuid = ?", (new_cip, suuid))
                    conn_n.commit()
                    conn_n.close()
                _stats_cache["ts"] = 0

            self._send_json({"ok": True})
            return

        if path in ["/api/servers/delete", "/api/node-mgr/servers/delete"]:
            suuid = body.get("uuid") or body.get("id")
            if not suuid:
                self._send_json({"ok": False, "error": "缺少服务器 UUID"}, 400)
                return
            deleted_nodes_count = delete_server_fully(suuid)
            self._send_json({"ok": True, "deleted_nodes": deleted_nodes_count, "message": "服务器已彻底删除"})
            return

        if path in ["/api/ping-tasks/save", "/api/node-mgr/ping-tasks/save"]:
            tid = body.get("id")
            name = str(body.get("name", "")).strip()
            target = str(body.get("target", "")).strip()
            ttype = body.get("type", "tcp")
            interval = int(body.get("interval", 60))
            all_clients = 1 if body.get("all_clients", True) else 0
            clients_json = json.dumps(body.get("clients", []))
            weight = int(body.get("weight", 0))

            if not name or not target:
                self._send_json({"ok": False, "error": "任务名称和目标地址不能为空"}, 400)
                return

            conn_k = sqlite3.connect(KOMARI_DB)
            c_k = conn_k.cursor()
            if tid:
                c_k.execute("""
                    UPDATE ping_tasks SET name=?, target=?, type=?, interval=?, all_clients=?, clients=?, weight=? WHERE id=?
                """, (name, target, ttype, interval, all_clients, clients_json, weight, tid))
            else:
                c_k.execute("""
                    INSERT INTO ping_tasks (name, target, type, interval, all_clients, clients, weight)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, target, ttype, interval, all_clients, clients_json, weight))
                tid = c_k.lastrowid
            conn_k.commit()
            conn_k.close()

            # Hot-restart Komari probe so agent scheduler dispatches new clients list immediately
            def _restart_komari():
                try:
                    subprocess.run(["systemctl", "restart", "komari"], timeout=5)
                except Exception:
                    pass
            threading.Thread(target=_restart_komari, daemon=True).start()

            self._send_json({"ok": True, "id": tid})
            return

        if path in ["/api/ping-tasks/delete", "/api/node-mgr/ping-tasks/delete"]:
            tid = body.get("id")
            if tid and os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("DELETE FROM ping_tasks WHERE id = ?", (tid,))
                conn_k.commit()
                conn_k.close()
                self._send_json({"ok": True})
                return
            self._send_json({"ok": False, "error": "缺少任务ID"}, 400)
            return

        if path in ["/api/ping-tasks/test", "/api/node-mgr/ping-tasks/test"]:
            target = body.get("target", "")
            if not target:
                self._send_json({"ok": False, "error": "缺少目标地址"}, 400)
                return
            host = target
            port = 80
            if ":" in target:
                parts = target.split(":")
                host = parts[0]
                try: port = int(parts[1])
                except: port = 80

            t0 = time.time()
            success = False
            latency_ms = None
            err = None
            try:
                family = socket.AF_INET6 if (":" in host or "[" in host) else socket.AF_INET
                s = socket.socket(family, socket.SOCK_STREAM)
                s.settimeout(2.5)
                s.connect((host.strip("[]"), port))
                latency_ms = round((time.time() - t0) * 1000, 1)
                success = True
                s.close()
            except Exception as e:
                err = str(e)

            self._send_json({"ok": success, "latency_ms": latency_ms, "error": err, "target": target})
            return

        if path in ["/api/system/configs", "/api/node-mgr/system/configs"]:
            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                for k, v in body.items():
                    val_str = json.dumps(v)
                    c_k.execute("INSERT OR REPLACE INTO configs (key, value) VALUES (?, ?)", (k, val_str))
                conn_k.commit()
                conn_k.close()
            self._send_json({"ok": True})
            return

        # Theme Management & Market POST Endpoints
        if path in ["/api/theme/set", "/api/node-mgr/theme/set", "/api/theme/switch", "/api/node-mgr/theme/switch"]:
            target_theme = str(body.get("short") or body.get("theme") or "").strip()
            if not target_theme:
                self._send_json({"ok": False, "error": "主题标识不能为空"}, 400)
                return
            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("INSERT OR REPLACE INTO configs (key, value) VALUES ('theme', ?)", (json.dumps(target_theme),))
                conn_k.commit()
                conn_k.close()
            self._send_json({"ok": True, "active_theme": target_theme})
            return

        if path in ["/api/theme/delete", "/api/node-mgr/theme/delete"]:
            short = str(body.get("short") or "").strip()
            if not short or short in ["default", ""]:
                self._send_json({"ok": False, "error": "官方原生默认主题不可删除"}, 400)
                return
            short = re.sub(r"[^a-zA-Z0-9_-]", "", short)
            target_dir = os.path.join(THEME_DIR, short)
            if os.path.exists(target_dir):
                try:
                    shutil.rmtree(target_dir)
                except Exception as e:
                    self._send_json({"ok": False, "error": f"删除主题文件失败: {e}"}, 500)
                    return

            # If current active theme was deleted, reset to default
            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("SELECT value FROM configs WHERE key = 'theme'")
                row = c_k.fetchone()
                if row and row[0]:
                    try:
                        cur = json.loads(row[0])
                        if cur == short:
                            c_k.execute("INSERT OR REPLACE INTO configs (key, value) VALUES ('theme', ?)", (json.dumps("default"),))
                            conn_k.commit()
                    except Exception:
                        pass
                conn_k.close()
            self._send_json({"ok": True})
            return

        if path in ["/api/theme/import", "/api/node-mgr/theme/import"]:
            url = str(body.get("url") or "").strip()
            if not url:
                self._send_json({"ok": False, "error": "主题下载链接或 GitHub 仓库地址不能为空"}, 400)
                return
            try:
                real_url = resolve_theme_download_url(url)
                req = urllib.request.Request(
                    real_url,
                    headers={"User-Agent": "Komari-Theme-Manager/1.0 (+https://github.com/komari-monitor)"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    zip_bytes = resp.read()

                theme_info = install_theme_from_zip_bytes(zip_bytes)
                self._send_json({"ok": True, "theme": theme_info})
            except Exception as e:
                self._send_json({"ok": False, "error": f"导入主题失败: {e}"}, 500)
            return

        if path in ["/api/theme/market/install", "/api/node-mgr/theme/market/install"]:
            download_url = str(body.get("download_url") or "").strip()
            short = str(body.get("short") or "").strip()
            if not download_url:
                self._send_json({"ok": False, "error": "缺少主题下载地址"}, 400)
                return
            try:
                req = urllib.request.Request(
                    download_url,
                    headers={"User-Agent": "Komari-Theme-Manager/1.0"}
                )
                with urllib.request.urlopen(req, timeout=35) as resp:
                    zip_bytes = resp.read()

                theme_info = install_theme_from_zip_bytes(zip_bytes, custom_short=short)
                self._send_json({"ok": True, "theme": theme_info})
            except Exception as e:
                self._send_json({"ok": False, "error": f"安装主题失败: {e}"}, 500)
            return

        if path in ["/api/theme/upload", "/api/node-mgr/theme/upload"]:
            data_b64 = str(body.get("data_base64") or body.get("data") or "").strip()
            if not data_b64:
                self._send_json({"ok": False, "error": "上传的主题文件数据为空"}, 400)
                return
            try:
                zip_bytes = base64.b64decode(data_b64)
                theme_info = install_theme_from_zip_bytes(zip_bytes)
                self._send_json({"ok": True, "theme": theme_info})
            except Exception as e:
                self._send_json({"ok": False, "error": f"解析并安装主题失败: {e}"}, 500)
            return

        if path in ["/api/theme/config", "/api/node-mgr/theme/config"]:
            target_theme = str(body.get("theme") or "LuminaPlus").strip()
            cfg_data = body.get("config")
            if cfg_data is None:
                self._send_json({"ok": False, "error": "配置内容不能为空"}, 400)
                return
            data_str = json.dumps(cfg_data, ensure_ascii=False)
            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("INSERT OR REPLACE INTO theme_configurations (short, data) VALUES (?, ?)", (target_theme, data_str))
                conn_k.commit()
                conn_k.close()
            self._send_json({"ok": True})
            return

        if path in ["/api/bbr/enable", "/api/node-mgr/bbr/enable"]:
            try:
                subprocess.run(["modprobe", "tcp_bbr"], check=False, timeout=5)
                if os.path.exists("/etc/sysctl.d"):
                    with open("/etc/sysctl.d/99-bbr.conf", "w") as f:
                        f.write("net.core.default_qdisc = fq\nnet.ipv4.tcp_congestion_control = bbr\n")
                subprocess.run(["sysctl", "-w", "net.core.default_qdisc=fq"], check=False, timeout=5)
                subprocess.run(["sysctl", "-w", "net.ipv4.tcp_congestion_control=bbr"], check=False, timeout=5)
                if os.path.exists("/etc/sysctl.d/99-bbr.conf"):
                    subprocess.run(["sysctl", "-p", "/etc/sysctl.d/99-bbr.conf"], check=False, timeout=5)
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
            return

        if path in ["/api/admin/password/change", "/api/node-mgr/admin/password/change"]:
            new_pwd = str(body.get("password") or "").strip()
            if not new_pwd:
                self._send_json({"ok": False, "error": "密码不能为空"}, 400)
                return
            import hashlib, base64
            # SHA256 base64 hash
            hashed = base64.b64encode(hashlib.sha256(new_pwd.encode('utf-8')).digest()).decode('utf-8')
            if os.path.exists(KOMARI_DB):
                conn_k = sqlite3.connect(KOMARI_DB)
                c_k = conn_k.cursor()
                c_k.execute("UPDATE users SET passwd = ?, updated_at = ? WHERE username = 'admin' OR rowid = 1",
                            (hashed, datetime.now().isoformat()))
                conn_k.commit()
                conn_k.close()
                self._send_json({"ok": True})
                return
            self._send_json({"ok": False, "error": "database not found"}, 500)
            return

        # Full Data Import endpoint
        if path in ["/api/data/import", "/api/node-mgr/data/import"]:
            def _import_val(v):
                if isinstance(v, str) and v.startswith("__b64__:"):
                    import base64
                    try:
                        return base64.b64decode(v[8:])
                    except Exception:
                        return v
                return v

            data = body
            imported_counts = {"servers": 0, "ping_tasks": 0, "nodes": 0, "subscriptions": 0}

            if "servers" in data and os.path.exists(KOMARI_DB):
                try:
                    k_conn = sqlite3.connect(KOMARI_DB)
                    k_c = k_conn.cursor()
                    for s in data.get("servers", []):
                        cols = list(s.keys())
                        placeholders = ",".join(["?"] * len(cols))
                        col_names = ",".join([f"`{c}`" for c in cols])
                        vals = [_import_val(v) for v in s.values()]
                        k_c.execute(f"INSERT OR REPLACE INTO clients ({col_names}) VALUES ({placeholders})", vals)
                        imported_counts["servers"] += 1

                    for p in data.get("ping_tasks", []):
                        cols = list(p.keys())
                        placeholders = ",".join(["?"] * len(cols))
                        col_names = ",".join([f"`{c}`" for c in cols])
                        vals = [_import_val(v) for v in p.values()]
                        k_c.execute(f"INSERT OR REPLACE INTO ping_tasks ({col_names}) VALUES ({placeholders})", vals)
                        imported_counts["ping_tasks"] += 1

                    k_conn.commit()
                    k_conn.close()
                except Exception as e:
                    print(f"Import komari.db error: {e}")

            if os.path.exists(NODES_DB):
                try:
                    n_conn = sqlite3.connect(NODES_DB)
                    n_c = n_conn.cursor()
                    for n in data.get("nodes", []):
                        cols = [k for k in n.keys() if k != "id"]
                        placeholders = ",".join(["?"] * len(cols))
                        col_names = ",".join([f"`{c}`" for c in cols])
                        vals = [_import_val(n[k]) for k in cols]
                        n_c.execute(f"INSERT OR REPLACE INTO nodes ({col_names}) VALUES ({placeholders})", vals)
                        imported_counts["nodes"] += 1

                    for sub in data.get("subscriptions", []):
                        cols = [k for k in sub.keys() if k != "id"]
                        placeholders = ",".join(["?"] * len(cols))
                        col_names = ",".join([f"`{c}`" for c in cols])
                        vals = [_import_val(sub[k]) for k in cols]
                        n_c.execute(f"INSERT OR REPLACE INTO subscriptions ({col_names}) VALUES ({placeholders})", vals)
                        imported_counts["subscriptions"] += 1

                    rules = data.get("subscription_rules")
                    if rules:
                        cols = [k for k in rules.keys() if k != "id"]
                        set_clause = ",".join([f"`{c}`=?" for c in cols])
                        vals = [_import_val(rules[k]) for k in cols]
                        n_c.execute(f"UPDATE subscription_rules SET {set_clause} WHERE id = 1", vals)

                    n_conn.commit()
                    n_conn.close()
                except Exception as e:
                    print(f"Import nodes.db error: {e}")

            self._send_json({"ok": True, "imported": imported_counts, "msg": "数据已成功导入并恢复！"})
            return

        # System Hot Update endpoint
        if path in ["/api/system/hot-update", "/api/node-mgr/system/hot-update"]:
            def _async_hot_update():
                try:
                    web_patch_dir = "/opt/komari/web-patch"
                    cmd = f"""
                    curl -fsSL https://raw.githubusercontent.com/2290145679/komari-node-manager/main/web-patch/assets/chunk-index-BfURcdSr.js -o {web_patch_dir}/assets/chunk-index-BfURcdSr.js
                    curl -fsSL https://raw.githubusercontent.com/2290145679/komari-node-manager/main/web-patch/assets/chunk-_layout-KM9Ke-Y5.js -o {web_patch_dir}/assets/chunk-_layout-KM9Ke-Y5.js
                    curl -fsSL https://raw.githubusercontent.com/2290145679/komari-node-manager/main/web-patch/assets/chunk-plugin_page-Xen4h3Tc.js -o {web_patch_dir}/assets/chunk-plugin_page-Xen4h3Tc.js
                    curl -fsSL https://raw.githubusercontent.com/2290145679/komari-node-manager/main/web-patch/assets/komari-singbox-helper.js -o {web_patch_dir}/assets/komari-singbox-helper.js
                    curl -fsSL https://raw.githubusercontent.com/2290145679/komari-node-manager/main/plugin/node-manager/panel/index.html -o /opt/komari/data/plugin/node-manager/panel/index.html
                    curl -fsSL https://raw.githubusercontent.com/2290145679/komari-node-manager/main/bin/hhub -o /usr/local/bin/hhub && chmod +x /usr/local/bin/hhub
                    chmod 644 {web_patch_dir}/assets/*
                    nginx -s reload || systemctl reload nginx
                    """
                    subprocess.run(cmd, shell=True, check=True)
                except Exception as e:
                    print(f"Hot update failed: {e}")
            threading.Thread(target=_async_hot_update, daemon=True).start()
            self._send_json({"ok": True, "msg": "热更新已在后台触发，约 3 秒后重载生效（主控监控零停机）"})
            return

        if path == "/api/nodes" or path == "/api/node-mgr/nodes":
            server_uuid = body.get("server_uuid", "")
            server_name = body.get("server_name", "")
            server_ip = body.get("server_ip", "")
            name = str(body.get("name") or "Node").strip()

            # Auto-resolve server name and IP from komari clients table if missing
            if server_uuid and (not server_ip or not server_name) and os.path.exists(KOMARI_DB):
                try:
                    conn_k = sqlite3.connect(KOMARI_DB)
                    c_k = conn_k.cursor()
                    c_k.execute("SELECT name, ipv4, ipv6 FROM clients WHERE uuid = ?", (server_uuid,))
                    crow = c_k.fetchone()
                    conn_k.close()
                    if crow:
                        if not server_name:
                            server_name = crow[0] or ""
                        if not server_ip:
                            server_ip = crow[1] or crow[2] or ""
                except Exception as e:
                    print(f"Error resolving client info for new node: {e}")

            # Duplicate name check
            conn_chk = sqlite3.connect(NODES_DB)
            c_chk = conn_chk.cursor()
            c_chk.execute("SELECT id FROM nodes WHERE LOWER(TRIM(name)) = LOWER(?)", (name,))
            dup = c_chk.fetchone()
            conn_chk.close()
            if dup:
                self._send_json({"error": f"已存在名为【{name}】的节点，请更换节点名称"}, 400)
                return

            protocol = body.get("protocol", "vless_reality")
            port = int(body.get("port") or secrets.randbelow(45000) + 15000)
            u = body.get("uuid_or_passwd") or str(uuid.uuid4())
            sni = body.get("sni") or "addons.mozilla.org"
            flow = body.get("flow", "xtls-rprx-vision") if protocol == "vless_reality" else ""
            ws_path = body.get("ws_path", "/vmess")
            
            pub_key = body.get("public_key", "")
            priv_key = body.get("private_key", "")
            short_id = body.get("short_id", "")

            # Realm Relay configuration
            is_relay = 1 if body.get("is_relay") else 0
            relay_server_uuid = str(body.get("relay_server_uuid") or "").strip()
            relay_server_name = str(body.get("relay_server_name") or "").strip()
            relay_server_ip = str(body.get("relay_server_ip") or "").strip()
            relay_port = int(body.get("relay_port") or port)

            # Inherit existing credentials if landing server already has a node on this port
            if is_relay and server_uuid and port:
                try:
                    conn_land = sqlite3.connect(NODES_DB)
                    c_land = conn_land.cursor()
                    c_land.execute("SELECT uuid_or_passwd, public_key, private_key, short_id, sni, flow FROM nodes WHERE server_uuid = ? AND port = ? LIMIT 1", (server_uuid, port))
                    land_row = c_land.fetchone()
                    conn_land.close()
                    if land_row and land_row[0] and land_row[1] and land_row[2]:
                        u = land_row[0]
                        pub_key = land_row[1]
                        priv_key = land_row[2]
                        if land_row[3]:
                            short_id = land_row[3]
                        if land_row[4]:
                            sni = land_row[4]
                        if land_row[5]:
                            flow = land_row[5]
                except Exception as e:
                    print(f"Error inheriting landing credentials: {e}")

            if protocol == "vless_reality" and (not pub_key or not priv_key):
                priv, pub = get_reality_keypair()
                priv_key, pub_key = priv, pub
                short_id = get_short_id()

            if is_relay and relay_server_uuid and (not relay_server_ip or not relay_server_name) and os.path.exists(KOMARI_DB):
                try:
                    conn_k = sqlite3.connect(KOMARI_DB)
                    c_k = conn_k.cursor()
                    c_k.execute("SELECT name, ipv4, ipv6 FROM clients WHERE uuid = ?", (relay_server_uuid,))
                    crow = c_k.fetchone()
                    conn_k.close()
                    if crow:
                        if not relay_server_name:
                            relay_server_name = crow[0] or ""
                        if not relay_server_ip:
                            relay_server_ip = crow[1] or crow[2] or ""
                except Exception as e:
                    print(f"Error resolving relay client info: {e}")
                
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute('''
                INSERT INTO nodes (server_uuid, server_name, server_ip, name, protocol, port,
                                  uuid_or_passwd, sni, public_key, private_key, short_id, flow, ws_path, raw_link, is_external, enabled,
                                  is_relay, relay_server_uuid, relay_server_name, relay_server_ip, relay_port)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', 0, 1, ?, ?, ?, ?, ?)
            ''', (server_uuid, server_name, server_ip, name, protocol, port, u, sni, pub_key, priv_key, short_id, flow, ws_path,
                  is_relay, relay_server_uuid, relay_server_name, relay_server_ip, relay_port))
            node_id = c.lastrowid
            conn.commit()
            conn.close()

            self._send_json({"ok": True, "id": node_id})
            return

        if path in ["/api/nodes/toggle", "/api/node-mgr/nodes/toggle"] or ((path.startswith("/api/nodes/") or path.startswith("/api/node-mgr/nodes/")) and path.endswith("/toggle")):
            if path.endswith("/toggle") and "/" in path.strip("/")[10:]:
                parts = path.strip("/").split("/")
                node_id = parts[-2]
                val = None
            else:
                node_id = body.get("id")
                val = body.get("enabled")
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            if val is not None:
                c.execute("UPDATE nodes SET enabled = ? WHERE id = ?", (1 if val else 0, node_id))
            else:
                c.execute("UPDATE nodes SET enabled = (1 - enabled) WHERE id = ?", (node_id,))
            conn.commit()
            conn.close()
            self._send_json({"ok": True})
            return

        if path in ["/api/nodes/ipv6", "/api/node-mgr/nodes/ipv6"] or ((path.startswith("/api/nodes/") or path.startswith("/api/node-mgr/nodes/")) and path.endswith("/clone-ipv6")):
            if "clone-ipv6" in path:
                parts = path.strip("/").split("/")
                node_id = parts[-2]
            else:
                node_id = body.get("id")
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
            cols = [d[0] for d in c.description]
            row = c.fetchone()
            if not row:
                conn.close()
                self._send_json({"error": "节点不存在"}, 404)
                return
            node = dict(zip(cols, row))
            conn.close()

            servers_data = get_servers_with_stats()
            servers = servers_data.get("servers", [])
            server = next((s for s in servers if s.get("uuid") == node.get("server_uuid")), None)
            if not server or not server.get("ipv6"):
                self._send_json({"error": "该节点所属服务器未检测到有效 IPv6 地址"}, 400)
                return

            ipv6 = server["ipv6"]
            clone_name = node["name"] if "[IPv6]" in node["name"] else f"{node['name']} [IPv6]"

            # Check duplicate clone name
            conn_dup = sqlite3.connect(NODES_DB)
            c_dup = conn_dup.cursor()
            c_dup.execute("SELECT id FROM nodes WHERE LOWER(TRIM(name)) = LOWER(?)", (clone_name,))
            if c_dup.fetchone():
                conn_dup.close()
                self._send_json({"error": f"已存在名为【{clone_name}】的 IPv6 节点，无需重复创建"}, 400)
                return
            conn_dup.close()

            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute('''
                INSERT INTO nodes (server_uuid, server_name, server_ip, name, protocol, port,
                                  uuid_or_passwd, sni, public_key, private_key, short_id, flow, ws_path, raw_link, is_external, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', 0, 1)
            ''', (node["server_uuid"], node["server_name"], ipv6, clone_name, node["protocol"], node["port"],
                  node["uuid_or_passwd"], node["sni"], node["public_key"], node["private_key"],
                  node["short_id"], node["flow"], node["ws_path"]))
            new_id = c.lastrowid
            conn.commit()
            conn.close()

            self._send_json({"ok": True, "id": new_id, "name": clone_name, "ipv6": ipv6})
            return

        if path in ["/api/nodes/edit", "/api/node-mgr/nodes/edit"]:
            node_id = body.get("id")
            if not node_id:
                self._send_json({"ok": False, "error": "缺少节点 ID"}, 400)
                return
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT id, name, server_ip, port, uuid_or_passwd, sni, public_key, short_id FROM nodes WHERE id = ?", (node_id,))
            row = c.fetchone()
            if not row:
                conn.close()
                self._send_json({"ok": False, "error": "节点不存在"}, 404)
                return

            name = str(body.get("name") or "").strip()
            server_ip = str(body.get("server_ip") or "").strip()
            port = int(body.get("port") or 0)
            uuid_or_passwd = str(body.get("uuid_or_passwd") or "").strip()
            sni = str(body.get("sni") or "").strip()
            public_key = str(body.get("public_key") or "").strip()
            short_id = str(body.get("short_id") or "").strip()

            is_relay = body.get("is_relay")
            relay_server_uuid = str(body.get("relay_server_uuid") or "").strip()
            relay_server_name = str(body.get("relay_server_name") or "").strip()
            relay_server_ip = str(body.get("relay_server_ip") or "").strip()
            relay_port = int(body.get("relay_port") or 0)

            # Auto-resolve relay server if uuid provided
            if is_relay and relay_server_uuid and (not relay_server_ip or not relay_server_name) and os.path.exists(KOMARI_DB):
                try:
                    conn_k = sqlite3.connect(KOMARI_DB)
                    c_k = conn_k.cursor()
                    c_k.execute("SELECT name, ipv4, ipv6 FROM clients WHERE uuid = ?", (relay_server_uuid,))
                    crow = c_k.fetchone()
                    conn_k.close()
                    if crow:
                        if not relay_server_name:
                            relay_server_name = crow[0] or ""
                        if not relay_server_ip:
                            relay_server_ip = crow[1] or crow[2] or ""
                except Exception as e:
                    pass

            if is_relay is not None:
                is_relay_val = 1 if is_relay else 0
                c.execute("""
                    UPDATE nodes SET
                        name = coalesce(nullif(?, ''), name),
                        server_ip = coalesce(nullif(?, ''), server_ip),
                        port = case when ? > 0 then ? else port end,
                        uuid_or_passwd = coalesce(nullif(?, ''), uuid_or_passwd),
                        sni = ?,
                        public_key = ?,
                        short_id = ?,
                        is_relay = ?,
                        relay_server_uuid = coalesce(nullif(?, ''), relay_server_uuid),
                        relay_server_name = coalesce(nullif(?, ''), relay_server_name),
                        relay_server_ip = coalesce(nullif(?, ''), relay_server_ip),
                        relay_port = case when ? > 0 then ? else relay_port end
                    WHERE id = ?
                """, (name, server_ip, port, port, uuid_or_passwd, sni, public_key, short_id,
                      is_relay_val, relay_server_uuid, relay_server_name, relay_server_ip, relay_port, relay_port, node_id))
            else:
                c.execute("""
                    UPDATE nodes SET
                        name = coalesce(nullif(?, ''), name),
                        server_ip = coalesce(nullif(?, ''), server_ip),
                        port = case when ? > 0 then ? else port end,
                        uuid_or_passwd = coalesce(nullif(?, ''), uuid_or_passwd),
                        sni = ?,
                        public_key = ?,
                        short_id = ?,
                        relay_port = case when ? > 0 then ? else relay_port end
                    WHERE id = ?
                """, (name, server_ip, port, port, uuid_or_passwd, sni, public_key, short_id, relay_port, relay_port, node_id))
            conn.commit()
            conn.close()
            self._send_json({"ok": True, "message": "节点配置已更新"})
            return

        self._send_json({"error": "not found"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path.startswith("/api/servers/") or path.startswith("/api/node-mgr/servers/"):
            server_uuid = path.rstrip("/").split("/")[-1]
            deleted_nodes_count = delete_server_fully(server_uuid)
            self._send_json({"ok": True, "deleted_nodes": deleted_nodes_count, "message": "服务器已彻底删除"})
            return
        if path.startswith("/api/nodes/") or path.startswith("/api/node-mgr/nodes/"):
            node_id = path.rstrip("/").split("/")[-1]
            redirect_to = query.get("redirect_to", ["PROXY"])[0]

            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT name FROM nodes WHERE id = ?", (node_id,))
            row = c.fetchone()
            node_name = row[0] if row else ""
            c.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
            conn.commit()
            conn.close()

            redirected_count = 0
            if node_name:
                redirected_count = redirect_rules_for_node(node_name, redirect_to)

            self._send_json({"ok": True, "redirected_count": redirected_count, "redirected_to": redirect_to})
            return
        self._send_json({"error": "not found"}, 404)

if __name__ == "__main__":
    load_blocked_ips_on_startup()
    threading.Thread(target=run_notification_engine, daemon=True).start()
    threading.Thread(target=run_traffic_collector, daemon=True).start()
    print(f"Starting Node Manager server on 127.0.0.1:{PORT} (ThreadingHTTPServer)...")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), NodeMgrHandler)
    server.daemon_threads = True
    server.serve_forever()