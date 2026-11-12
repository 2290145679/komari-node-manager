#!/bin/bash
# Komari Pro Node Sync Service (komari-pro-node-sync)
MASTER_URL="https://jgw2.yohoo.xyz"
TOKEN="RxSnvOK9YfW63atsq6HqAw"
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
  elif command -v rc-service >/dev/null 2>&1; then
    rc-service realm restart >/dev/null 2>&1 || {
      killall -9 realm >/dev/null 2>&1 || pkill -9 -f "realm -c" >/dev/null 2>&1 || true
      rc-service realm zap >/dev/null 2>&1 || true
      rc-service realm start >/dev/null 2>&1 || true
    }
  fi
}

is_process_running() {
  pidof "$1" >/dev/null 2>&1 || killall -0 "$1" >/dev/null 2>&1 || pgrep -x "$1" >/dev/null 2>&1
}

TICK=0
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

# 1. Parse sing-box access log to map IP/Port directly to user ID (like ProxyProbe)
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

    RES=$(curl -k -s -m 10 "$MASTER_URL/api/node-mgr/agent/config?token=$TOKEN" 2>/dev/null || true)
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

    # Sync Realm port forward rules if realm is installed
    if [ -x /usr/local/bin/realm ] || [ -f /etc/realm/config.toml ]; then
      REALM_RES=$(curl -k -s -m 10 "$MASTER_URL/api/node-mgr/agent/realm-config?token=$TOKEN" 2>/dev/null || true)
      if [ -n "$REALM_RES" ] && echo "$REALM_RES" | grep -q '\[network\]'; then
        REALM_MD5=$(echo "$REALM_RES" | md5sum | awk '{print $1}')
        OLD_REALM_MD5=$(cat /etc/realm/config.md5 2>/dev/null || true)
        if [ "$REALM_MD5" != "$OLD_REALM_MD5" ]; then
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
