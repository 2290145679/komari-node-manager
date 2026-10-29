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
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

KOMARI_DB = "/opt/komari/data/komari.db"
NODES_DB = "/opt/komari/data/nodes.db"
METRICS_DB = "/opt/komari/data/metrics.db"
CERT_DIR = "/opt/komari/data/certs"
PORT = 25775
DOMAIN = "komari.yohoo.xyz"

os.makedirs(CERT_DIR, exist_ok=True)
os.makedirs("/opt/komari/data", exist_ok=True)

def init_db():
    conn = sqlite3.connect(NODES_DB)
    c = conn.cursor()
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

    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT 'default',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS agent_heartbeats (
            token TEXT PRIMARY KEY,
            last_seen INTEGER
        )
    ''')
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
        ("target_games", "TEXT DEFAULT 'DIRECT'")
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

    # Seed Telegram channel with user credentials if empty
    c.execute("SELECT count(*) FROM notification_channels")
    if c.fetchone()[0] == 0:
        tg_conf = json.dumps({
            "bot_token": "8731954829:AAG6HlNgKnth8_2yIYAtMyV4gPx_c-I2bJY",
            "chat_id": "791298471"
        })
        c.execute("INSERT INTO notification_channels (type, name, enabled, config) VALUES (?, ?, ?, ?)",
                  ("telegram", "Telegram 机器人 (@vpssend_bot)", 1, tg_conf))

    default_rules = [
        ("traffic_threshold", "流量消耗预警", "core", "单节点或全网流量达到 80%/90%/100% 阈值提醒；每月1号清零提醒", 1, json.dumps({"thresholds": [80, 90, 100], "cycle_reset_notify": True})),
        ("singbox_status", "Sing-box 离线 / 恢复通知", "core", "Sing-box 核心进程异常挂掉或重启恢复上线时即时告警", 1, json.dumps({"offline_timeout": 60})),
        ("server_status", "服务器系统离线 / 恢复通知", "core", "探针失联超过 2 分钟时触发宕机报警，恢复时发送上线通知及离线时长", 1, json.dumps({"offline_timeout": 120})),
        ("server_expiration", "服务器到期续费提醒", "core", "按到期时间提前 30/15/7/3/1 天阶梯预警，防止机器被回收", 1, json.dumps({"remind_days": [30, 15, 7, 3, 1]})),
        ("traffic_surge", "突发大流量激增 / 盗刷告警", "monitor", "10分钟突发流量 > 5GB 或流速持续 > 100Mbps 异常大流量拦截预警", 1, json.dumps({"burst_mbps": 100, "cooldown_sec": 3600})),
        ("resource_exhaustion", "物理硬件资源枯竭告警", "monitor", "CPU / 内存 / 磁盘使用率持续超过 90% 时预警，防止 OOM 崩溃或日志爆盘", 1, json.dumps({"cpu_pct": 90, "mem_pct": 90, "disk_pct": 90, "cooldown_sec": 1800})),
        ("network_block", "节点网络恶化 / GFW 阻断疑似预警", "monitor", "丢包率持续 > 70% 或节点代理端口从外部无法连通时预警", 1, json.dumps({"loss_pct": 70, "cooldown_sec": 3600})),
        ("cert_reality_check", "Reality 伪装域名 / 证书失效预警", "monitor", "Reality 伪装 SNI 域名握手异常或 SSL 证书到期前 7 天预警", 1, json.dumps({"remind_days": 7, "cooldown_sec": 86400})),
        ("admin_login", "管理面板安全登录提醒", "security", "管理员账号从新设备 / 异地 IP 登录时即时推送安全日志", 1, json.dumps({"notify_all_login": True})),
        ("daily_report", "每日定时运维简报", "report", "每天固定时间推送全网运行状态、在线率、当日总消耗与即将到期概览", 1, json.dumps({"report_time": "09:00"}))
    ]
    for r_key, r_name, r_cat, r_desc, r_en, r_cfg in default_rules:
        c.execute("""
            INSERT OR IGNORE INTO notification_rules (rule_key, name, category, description, enabled, config)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (r_key, r_name, r_cat, r_desc, r_en, r_cfg))

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
            "direct_games": False
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
        "target_games": d.get("target_games") or "DIRECT"
    }

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

def get_cached_servers_with_stats():
    global _stats_cache
    now = time.time()
    if _stats_cache["data"] and (now - _stats_cache["ts"]) < 1.2:
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
    c_k = conn_k.cursor()
    c_k.execute("SELECT uuid, name, ipv4, ipv6, os, arch, token, updated_at FROM clients ORDER BY name ASC")
    clients = c_k.fetchall()
    conn_k.close()

    conn_n = sqlite3.connect(NODES_DB)
    c_n = conn_n.cursor()
    c_n.execute("SELECT token, last_seen FROM agent_heartbeats")
    heartbeats = dict(c_n.fetchall())
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
            recent_metrics = dict(executor.map(fetch_recent, [r[0] for r in clients]))
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
        uuid_val = row[0]
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
        uuid_val, name, ip4, ip6, os_name, arch, token, updated_at = row
        last_seen = heartbeats.get(token, 0)
        is_online = (now - last_seen) <= 35 if last_seen > 0 else False
        if is_online:
            online_count += 1

        rec = recent_metrics.get(uuid_val)
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

        servers.append({
            "uuid": uuid_val,
            "name": name or ip4 or "Server-" + uuid_val[:6],
            "ipv4": ip4 or "",
            "ipv6": ip6 or "",
            "os": os_name or "",
            "arch": arch or "",
            "token": token or "",
            "updated_at": str(rec_updated) if rec_updated else "",
            "singbox_online": is_online,
            "singbox_installed": last_seen > 0,
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
    return get_servers_with_stats().get("servers", [])

def build_node_share_link(node):
    if node.get("raw_link"):
        return node["raw_link"]

    proto = node.get("protocol")
    ip = node.get("server_ip") or DOMAIN
    port = node.get("port")
    name = node.get("name")
    u = node.get("uuid_or_passwd")
    sni = node.get("sni") or "addons.mozilla.org"
    url_ip = f"[{ip}]" if (":" in ip and not ip.startswith("[")) else ip
    
    if proto == "vless_reality":
        pbk = node.get("public_key")
        sid = node.get("short_id") or ""
        flow = node.get("flow") or "xtls-rprx-vision"
        return f"vless://{u}@{url_ip}:{port}?encryption=none&flow={flow}&security=reality&sni={sni}&fp=chrome&pbk={pbk}&sid={sid}&type=tcp#{name}"
    elif proto == "hysteria2":
        return f"hysteria2://{u}@{url_ip}:{port}/?insecure=1&sni={sni}#{name}"
    elif proto == "tuic":
        return f"tuic://{u}:{u}@{url_ip}:{port}?congestion_control=bbr&alpn=h3&sni={sni}&allow_insecure=1#{name}"
    elif proto == "trojan":
        return f"trojan://{u}@{url_ip}:{port}?security=tls&sni={sni}&allowInsecure=1#{name}"
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

def build_clash_meta_yaml(nodes, rules_cfg=None):
    if rules_cfg is None:
        rules_cfg = get_subscription_rules()

    proxies = []
    names = []
    for n in nodes:
        proto = n.get("protocol")
        name = n.get("name")
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
    uuid: {u}
    network: tcp
    tls: true
    udp: true
    flow: {n.get('flow') or 'xtls-rprx-vision'}
    servername: {sni}
    reality-opts:
      public-key: {n.get('public_key')}
      short-id: "{n.get('short_id') or ''}"
    client-fingerprint: chrome""")
        elif proto == "hysteria2":
            proxies.append(f"""  - name: "{name}"
    type: hysteria2
    server: "{ip}"
    port: {port}
    password: "{u}"
    sni: {sni}
    skip-cert-verify: true""")
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
                rules_list.append(f"  {line}")

    # 2. AI services
    if rules_cfg.get("proxy_ai"):
        t_ai = rules_cfg.get("target_ai") or "PROXY"
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
        t_tg = rules_cfg.get("target_tg") or "PROXY"
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
        t_media = rules_cfg.get("target_media") or "PROXY"
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
        t_dev = rules_cfg.get("target_dev") or "PROXY"
        rules_list.append(f"  # === 💻 开发者服务加速 (GitHub / Docker / Hugging Face) -> {t_dev} ===")
        rules_list.append(f"  - GEOSITE,github,{t_dev}")
        rules_list.append(f"  - DOMAIN-SUFFIX,github.com,{t_dev}")
        rules_list.append(f"  - DOMAIN-SUFFIX,githubusercontent.com,{t_dev}")
        rules_list.append(f"  - DOMAIN-SUFFIX,docker.com,{t_dev}")
        rules_list.append(f"  - DOMAIN-SUFFIX,docker.io,{t_dev}")
        rules_list.append(f"  - DOMAIN-SUFFIX,huggingface.co,{t_dev}")

    # 6. Game Platforms Direct
    if rules_cfg.get("direct_games"):
        t_games = rules_cfg.get("target_games") or "DIRECT"
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
        rules_list.append("  - GEOSITE,cn,DIRECT")
        rules_list.append("  - GEOIP,CN,DIRECT,no-resolve")

    # 6. Final match
    final = rules_cfg.get("final_match") or "PROXY"
    rules_list.append(f"  - MATCH,{final}")

    rules_yaml = "\n".join(rules_list)

    return f"""port: 7890
socks-port: 7891
allow-lan: true
mode: rule
log-level: info
ipv6: false

proxies:
{proxies_text}

proxy-groups:
{groups_text}

rules:
{rules_yaml}
"""

def build_sing_box_config(nodes_for_server):
    inbounds = []
    seen_ports = set()
    cert_path = "/etc/sing-box/cert.pem"
    key_path = "/etc/sing-box/cert.key"
    
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
        u = n.get("uuid_or_passwd")
        sni = n.get("sni") or "addons.mozilla.org"
        
        if proto == "vless_reality":
            inbounds.append({
                "type": "vless",
                "tag": tag,
                "listen": "::",
                "listen_port": port,
                "users": [
                    {
                        "uuid": u,
                        "flow": n.get("flow") or "xtls-rprx-vision"
                    }
                ],
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
                "users": [{"password": u}],
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
                "users": [{"uuid": u, "password": u}],
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
                "users": [{"password": u}],
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
                "users": [{"uuid": u}],
                "transport": {
                    "type": "ws",
                    "path": n.get("ws_path") or "/vmess"
                }
            })
            
    return {
        "log": {"level": "warn", "timestamp": True},
        "inbounds": inbounds,
        "outbounds": [{"type": "direct", "tag": "direct"}]
    }

INSTALL_SCRIPT_TEMPLATE = '''#!/bin/bash
set -e

# Komari & Sing-box All-In-One Installer (Universal: systemd & OpenRC/Alpine musl/glibc)
# Domain: {DOMAIN}

TOKEN=""
MASTER_URL="https://{DOMAIN}"

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
echo "[1/4] Installing system dependencies..."
if [ -x "$(command -v apt-get)" ]; then
  apt-get update -qq && apt-get install -y -qq curl wget tar openssl jq ca-certificates >/dev/null 2>&1 || true
elif [ -x "$(command -v yum)" ]; then
  yum install -y curl wget tar openssl jq ca-certificates >/dev/null 2>&1 || true
elif [ -x "$(command -v dnf)" ]; then
  dnf install -y curl wget tar openssl jq ca-certificates >/dev/null 2>&1 || true
elif [ -x "$(command -v apk)" ]; then
  apk update >/dev/null 2>&1 || true
  apk add --no-cache curl wget tar openssl jq bash ca-certificates gcompat >/dev/null 2>&1 || true
fi

# 2. Install Sing-box core
echo "[2/4] Installing Sing-box high performance core..."
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
if [ ! -f /etc/sing-box/cert.key ]; then
  if command -v openssl >/dev/null 2>&1; then
    openssl req -x509 -newkey rsa:2048 -nodes -keyout /etc/sing-box/cert.key -out /etc/sing-box/cert.pem -days 3650 -subj "/CN=bing.com" >/dev/null 2>&1 || true
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
  systemctl enable --now sing-box.service || true
fi

# 3. Install Komari Monitor Agent using official installer
echo "[3/4] Installing Komari Monitor Agent..."
DOWNLOADER=""
if command -v curl >/dev/null 2>&1; then
  DOWNLOADER="curl -fsSL"
elif command -v wget >/dev/null 2>&1; then
  DOWNLOADER="wget -qO-"
fi
$DOWNLOADER https://raw.githubusercontent.com/komari-monitor/komari-agent/refs/heads/main/install.sh | bash -s -- -e "$MASTER_URL" -t "$TOKEN" "${EXTRA_ARGS[@]}"

# 4. Install Node-Sync Agent Daemon
echo "[4/4] Installing Node Configuration Sync Daemon..."
cat << 'EOF' > /usr/local/bin/komari-node-sync.sh
#!/bin/bash
MASTER_URL="''' + f"https://{DOMAIN}" + '''"
TOKEN="''' + '$TOKEN' + '''"
CONFIG_FILE="/etc/sing-box/config.json"
MD5_FILE="/etc/sing-box/config.md5"

restart_sing_box() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl restart sing-box.service >/dev/null 2>&1 || true
  elif command -v rc-service >/dev/null 2>&1; then
    rc-service sing-box restart >/dev/null 2>&1 || true
  fi
}

while true; do
  RES=$(curl -s -m 10 "$MASTER_URL/api/node-mgr/agent/config?token=$TOKEN" 2>/dev/null || true)
  if [ -n "$RES" ] && echo "$RES" | grep -q '"inbounds"'; then
    NEW_MD5=$(echo "$RES" | md5sum | awk '{print $1}')
    OLD_MD5=$(cat "$MD5_FILE" 2>/dev/null || true)
    if [ "$NEW_MD5" != "$OLD_MD5" ]; then
      echo "[NodeSync] New config received, validating..."
      echo "$RES" > /tmp/new_config.json
      if /usr/local/bin/sing-box check -c /tmp/new_config.json >/dev/null 2>&1; then
        mv /tmp/new_config.json "$CONFIG_FILE"
        echo "$NEW_MD5" > "$MD5_FILE"
        restart_sing_box
        echo "[NodeSync] Sing-box restarted successfully!"
      else
        echo "[NodeSync] Invalid config from master, skipping."
      fi
    fi
  fi
  sleep 10
done
EOF

sed -i "s|\$TOKEN|$TOKEN|g" /usr/local/bin/komari-node-sync.sh
chmod +x /usr/local/bin/komari-node-sync.sh

# Fetch and apply initial config immediately
echo "Fetching initial proxy configuration..."
INIT_CFG=$(curl -s -m 10 "$MASTER_URL/api/node-mgr/agent/config?token=$TOKEN" 2>/dev/null || true)
if [ -n "$INIT_CFG" ] && echo "$INIT_CFG" | grep -q '"inbounds"'; then
  echo "$INIT_CFG" > /etc/sing-box/config.json
  echo "$INIT_CFG" | md5sum | awk '{print $1}' > /etc/sing-box/config.md5
  if [ "$INIT_SYSTEM" = "openrc" ]; then
    rc-service sing-box restart >/dev/null 2>&1 || rc-service sing-box start >/dev/null 2>&1 || true
  else
    systemctl restart sing-box.service >/dev/null 2>&1 || true
  fi
  echo "[Success] Sing-box initial configuration applied!"
fi

if [ "$INIT_SYSTEM" = "openrc" ]; then
  cat << 'EOF' > /etc/init.d/komari-node-sync
#!/sbin/openrc-run
name="Komari Node Sync Service"
description="Komari Node Sync Service"
command="/bin/bash"
command_args="/usr/local/bin/komari-node-sync.sh"
pidfile="/run/komari-node-sync.pid"
supervisor=supervise-daemon

depend() {
    need net
    after network sing-box
}
EOF
  chmod +x /etc/init.d/komari-node-sync
  rc-update add komari-node-sync default >/dev/null 2>&1 || true
  rc-service komari-node-sync restart >/dev/null 2>&1 || rc-service komari-node-sync start >/dev/null 2>&1 || true
else
  cat << EOF > /etc/systemd/system/komari-node-sync.service
[Unit]
Description=Komari Node Configuration Sync Service
After=network.target sing-box.service

[Service]
Type=simple
ExecStart=/bin/bash /usr/local/bin/komari-node-sync.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable --now komari-node-sync.service
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
    s = str(val).split(".")[0].replace("Z", "").replace("+00:00", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return int(datetime.strptime(s, fmt).timestamp())
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
                INSERT INTO notification_logs (rule_key, title, message, channel, status, error)
                VALUES (?, ?, ?, ?, ?, ?)
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
        last_rec_time = parse_iso_or_ts(s.get("updated_at"))
        host_online = (now - last_rec_time) <= 120 if last_rec_time > 0 else True

        if "server_status" in enabled_rules:
            last_host_st = get_state(f"host_st:{uuid_val}")
            if not last_host_st:
                set_state(f"host_st:{uuid_val}", "online" if host_online else "offline")
            elif last_host_st == "online" and not host_online:
                set_state(f"host_st:{uuid_val}", "offline")
                set_state(f"host_off_time:{uuid_val}", str(now))
                dispatch_notification(
                    title="🔴 服务器系统离线告警",
                    message=f"<b>服务器名称</b>: <code>{s_name}</code>\n<b>IP 地址</b>: <code>{ip}</code>\n<b>状态</b>: 探针心跳已失联超过 2 分钟！主机可能已宕机、断网或被服务商关机。",
                    level="danger",
                    rule_key="server_status"
                )
            elif last_host_st == "offline" and host_online:
                set_state(f"host_st:{uuid_val}", "online")
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
        sb_online = s.get("singbox_online", False)
        if host_online and s.get("singbox_installed", False) and "singbox_status" in enabled_rules:
            last_sb_st = get_state(f"sb_st:{uuid_val}")
            if not last_sb_st:
                set_state(f"sb_st:{uuid_val}", "online" if sb_online else "offline")
            elif last_sb_st == "online" and not sb_online:
                set_state(f"sb_st:{uuid_val}", "offline")
                dispatch_notification(
                    title="🔴 Sing-box 核心离线告警",
                    message=f"<b>服务器</b>: <code>{s_name}</code> ({ip})\n<b>异常事件</b>: 主机在线但 Sing-box 核心代理已中断连接！\n<b>排查建议</b>: 请登录节点后台或执行 <code>systemctl status sing-box</code> 查看日志排查。",
                    level="danger",
                    rule_key="singbox_status"
                )
            elif last_sb_st == "offline" and sb_online:
                set_state(f"sb_st:{uuid_val}", "online")
                dispatch_notification(
                    title="🟢 Sing-box 核心已恢复运行",
                    message=f"<b>服务器</b>: <code>{s_name}</code> ({ip})\n<b>事件</b>: Sing-box 核心代理已重新恢复运行，分流节点就绪。",
                    level="success",
                    rule_key="singbox_status"
                )

        # Traffic Burst Surge (rule: traffic_surge)
        if "traffic_surge" in enabled_rules:
            in_rate = s.get("in_rate", 0)
            out_rate = s.get("out_rate", 0)
            cur_mbps = (in_rate + out_rate) * 8 / 1_000_000
            burst_limit = enabled_rules["traffic_surge"].get("burst_mbps", 100)
            if cur_mbps >= burst_limit:
                last_surge = int(get_state(f"surge_sent:{uuid_val}", "0"))
                if now - last_surge > 3600:
                    set_state(f"surge_sent:{uuid_val}", str(now))
                    dispatch_notification(
                        title="⚡ 突发大流量激增告警",
                        message=f"<b>服务器</b>: <code>{s_name}</code> ({ip})\n<b>实时吞吐</b>: ↓ {format_bytes(in_rate)}/s · ↑ {format_bytes(out_rate)}/s\n<b>实时速率</b>: <b>{cur_mbps:.1f} Mbps</b> (突破 {burst_limit} Mbps 阈值)\n<b>提示</b>: 检测到短时间内吞吐暴涨，请排查是否有异常大文件下载或订阅被盗刷！",
                        level="warning",
                        rule_key="traffic_surge"
                    )

        # Resource Exhaustion (rule: resource_exhaustion)
        if "resource_exhaustion" in enabled_rules:
            cpu_val = s.get("cpu_usage", 0)
            ram_val = s.get("ram_pct", 0)
            disk_val = s.get("disk_pct", 0)
            cfg_res = enabled_rules["resource_exhaustion"]
            c_limit = cfg_res.get("cpu_pct", 90)
            m_limit = cfg_res.get("mem_pct", 90)
            d_limit = cfg_res.get("disk_pct", 90)

            res_alerts = []
            if cpu_val >= c_limit: res_alerts.append(f"CPU 使用率已达 {cpu_val:.1f}%")
            if ram_val >= m_limit: res_alerts.append(f"内存使用率已达 {ram_val:.1f}% (极易导致 OOM Killer 强杀核心)")
            if disk_val >= d_limit: res_alerts.append(f"磁盘空间占用已达 {disk_val:.1f}% (剩余空间不足 10%)")

            if res_alerts:
                last_res_sent = int(get_state(f"res_sent:{uuid_val}", "0"))
                if now - last_res_sent > 1800:
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

class NodeMgrHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_text(self, text, status=200, content_type="text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

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

        if path == "/install-node.sh":
            script = INSTALL_SCRIPT_TEMPLATE.replace("{DOMAIN}", DOMAIN)
            self._send_text(script, 200, "text/x-shellscript")
            return

        if path.startswith("/sub/"):
            token = path.split("/sub/")[1].strip("/")
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT id FROM subscriptions WHERE token = ?", (token,))
            sub = c.fetchone()
            if not sub:
                conn.close()
                self._send_text("Invalid Subscription Token", 404)
                return
            
            c.execute("SELECT * FROM nodes WHERE enabled = 1 ORDER BY is_external ASC, id DESC")
            cols = [d[0] for d in c.description]
            nodes = [dict(zip(cols, row)) for row in c.fetchall()]
            conn.close()

            rules_cfg = get_subscription_rules()
            ua = self.headers.get("User-Agent", "").lower()
            fmt = query.get("format", [""])[0].lower()
            clash_flag = query.get("clash", [""])[0]

            if fmt == "clash" or clash_flag == "1" or any(k in ua for k in ["clash", "mihomo", "meta", "stash", "verge"]):
                yaml_data = build_clash_meta_yaml(nodes, rules_cfg)
                self._send_text(yaml_data, 200, "text/yaml; charset=utf-8")
            elif fmt == "raw":
                links = [build_node_share_link(n) for n in nodes if build_node_share_link(n)]
                self._send_text("\n".join(links), 200, "text/plain; charset=utf-8")
            else:
                links = [build_node_share_link(n) for n in nodes if build_node_share_link(n)]
                b64 = base64.b64encode("\n".join(links).encode()).decode()
                self._send_text(b64, 200, "text/plain; charset=utf-8")
            return

        # API routes:
        if path in ["/api/sub/rules", "/api/node-mgr/sub/rules"]:
            rules = get_subscription_rules()
            self._send_json({"ok": True, "rules": rules})
            return

        if path in ["/api/sub/rules/preview", "/api/node-mgr/sub/rules/preview"]:
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM nodes WHERE enabled = 1 ORDER BY is_external ASC, id DESC")
            cols = [d[0] for d in c.description]
            nodes = [dict(zip(cols, row)) for row in c.fetchall()]
            conn.close()
            rules_cfg = get_subscription_rules()
            yaml_data = build_clash_meta_yaml(nodes, rules_cfg)
            self._send_json({"ok": True, "yaml": yaml_data})
            return

        if path == "/api/servers" or path == "/api/node-mgr/servers":
            servers_data = get_cached_servers_with_stats()
            self._send_json(servers_data)
            return

        if path == "/api/nodes" or path == "/api/node-mgr/nodes":
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT * FROM nodes ORDER BY is_external ASC, id DESC")
            cols = [d[0] for d in c.description]
            nodes = [dict(zip(cols, row)) for row in c.fetchall()]
            conn.close()
            for n in nodes:
                n["link"] = build_node_share_link(n)
            self._send_json({"ok": True, "nodes": nodes})
            return

        if path == "/api/sub/token" or path == "/api/node-mgr/sub/token":
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("SELECT token FROM subscriptions LIMIT 1")
            row = c.fetchone()
            conn.close()
            token = row[0] if row else ""
            self._send_json({"ok": True, "token": token, "sub_url": f"https://{DOMAIN}/sub/{token}"})
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

        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}

        # Save subscription rules
        
        # Notifications API endpoints
        if path in ["/api/notifications/channels/save", "/api/node-mgr/notifications/channels/save"]:
            ch_id = body.get("id")
            ch_type = body.get("type", "telegram")
            name = body.get("name", "Telegram 机器人")
            enabled = 1 if body.get("enabled", True) else 0
            config = json.dumps(body.get("config", {}))

            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            if ch_id:
                c.execute("UPDATE notification_channels SET type=?, name=?, enabled=?, config=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                          (ch_type, name, enabled, config, ch_id))
            else:
                c.execute("INSERT INTO notification_channels (type, name, enabled, config) VALUES (?, ?, ?, ?)",
                          (ch_type, name, enabled, config))
            conn.commit()
            conn.close()
            self._send_json({"ok": True})
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

        if path in ["/api/notifications/rules/toggle", "/api/node-mgr/notifications/rules/toggle"]:
            rule_key = body.get("rule_key")
            enabled = 1 if body.get("enabled", True) else 0
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("UPDATE notification_rules SET enabled=?, updated_at=CURRENT_TIMESTAMP WHERE rule_key=?", (enabled, rule_key))
            conn.commit()
            conn.close()
            self._send_json({"ok": True})
            return

        if path in ["/api/notifications/rules/config", "/api/node-mgr/notifications/rules/config"]:
            rule_key = body.get("rule_key")
            cfg = json.dumps(body.get("config", {}))
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
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

        if path == "/api/nodes" or path == "/api/node-mgr/nodes":
            server_uuid = body.get("server_uuid", "")
            server_name = body.get("server_name", "")
            server_ip = body.get("server_ip", "")
            name = str(body.get("name") or "Node").strip()

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
            
            if protocol == "vless_reality" and (not pub_key or not priv_key):
                priv, pub = get_reality_keypair()
                priv_key, pub_key = priv, pub
                short_id = get_short_id()
                
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute('''
                INSERT INTO nodes (server_uuid, server_name, server_ip, name, protocol, port,
                                  uuid_or_passwd, sni, public_key, private_key, short_id, flow, ws_path, raw_link, is_external, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', 0, 1)
            ''', (server_uuid, server_name, server_ip, name, protocol, port, u, sni, pub_key, priv_key, short_id, flow, ws_path))
            node_id = c.lastrowid
            conn.commit()
            conn.close()

            self._send_json({"ok": True, "id": node_id})
            return

        if path.startswith("/api/nodes/") and path.endswith("/toggle") or path.startswith("/api/node-mgr/nodes/") and path.endswith("/toggle"):
            parts = path.split("/")
            node_id = parts[-2]
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("UPDATE nodes SET enabled = (1 - enabled) WHERE id = ?", (node_id,))
            conn.commit()
            conn.close()
            self._send_json({"ok": True})
            return

        if (path.startswith("/api/nodes/") or path.startswith("/api/node-mgr/nodes/")) and path.endswith("/clone-ipv6"):
            parts = path.split("/")
            node_id = parts[-2]
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

        self._send_json({"error": "not found"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/nodes/") or path.startswith("/api/node-mgr/nodes/"):
            node_id = path.rstrip("/").split("/")[-1]
            conn = sqlite3.connect(NODES_DB)
            c = conn.cursor()
            c.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
            conn.commit()
            conn.close()
            self._send_json({"ok": True})
            return
        self._send_json({"error": "not found"}, 404)

if __name__ == "__main__":
    threading.Thread(target=run_notification_engine, daemon=True).start()
    print(f"Starting Node Manager server on 127.0.0.1:{PORT}...")
    server = HTTPServer(("127.0.0.1", PORT), NodeMgrHandler)
    server.serve_forever()