#!/bin/bash
MASTER_URL="https://jgw2.yohoo.xyz"
TOKEN="RxSnvOK9YfW63atsq6HqAw"
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
  # Ensure TLS certificate exists for Hysteria2 / TUIC / Trojan
  if [ ! -f /etc/sing-box/cert.key ] || [ ! -f /etc/sing-box/cert.pem ]; then
    if command -v openssl >/dev/null 2>&1; then
      mkdir -p /etc/sing-box
      openssl req -x509 -newkey rsa:2048 -nodes -keyout /etc/sing-box/cert.key -out /etc/sing-box/cert.pem -days 3650 \
        -subj "/CN=bing.com" \
        -addext "subjectAltName=DNS:bing.com,DNS:*.bing.com,DNS:addons.mozilla.org,DNS:gateway.icloud.com,DNS:www.apple.com,DNS:komari.yohoo.xyz,IP:127.0.0.1" >/dev/null 2>&1 || \
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

  # Report proxy traffic from sing-box clash_api
  if curl -s -m 2 http://127.0.0.1:9090/connections >/dev/null 2>&1; then
    if command -v python3 >/dev/null 2>&1; then
      python3 -c '
import urllib.request, json, sys, os, re

STATE_FILE = "/tmp/sb_traffic_state.json"
try:
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
except Exception:
    state = {"conns": {}, "global_total": 0, "last_sub": None}

try:
    req = urllib.request.Request("http://127.0.0.1:9090/connections")
    with urllib.request.urlopen(req, timeout=2) as resp:
        data = json.loads(resp.read().decode())
except Exception:
    sys.exit(0)

dl_total = int(data.get("downloadTotal") or 0)
up_total = int(data.get("uploadTotal") or 0)
global_total = dl_total + up_total

tracked = state.get("conns", {})
current_ids = set()
deltas = {}
sum_deltas = 0
last_sub = state.get("last_sub")

for c in data.get("connections", []):
    cid = c.get("id")
    if not cid: continue
    current_ids.add(cid)
    sub_id = None
    for ch in c.get("chains", []):
        s_ch = str(ch)
        if s_ch.startswith("out-sub-"):
            sub_id = s_ch.replace("out-sub-", "")
            break
    if not sub_id:
        rule = str(c.get("rule") or "")
        m = re.search(r"sub_(\d+)", rule)
        if m: sub_id = m.group(1)
    if not sub_id: continue
    last_sub = sub_id
    u = int(c.get("upload") or 0)
    d = int(c.get("download") or 0)
    if cid in tracked:
        lu, ld = tracked[cid][:2]
        du = max(0, u - lu)
        dd = max(0, d - ld)
    else:
        du = u
        dd = d
    tracked[cid] = [u, d, sub_id]
    d_total = du + dd
    if d_total > 0:
        deltas[sub_id] = deltas.get(sub_id, 0) + d_total
        sum_deltas += d_total

closed = [cid for cid in tracked if cid not in current_ids]
for cid in closed: del tracked[cid]

last_global = state.get("global_total", 0)
if last_global > 0 and global_total >= last_global:
    g_delta = global_total - last_global
    if g_delta > sum_deltas:
        unacc = g_delta - sum_deltas
        target = next(iter(deltas.keys())) if len(deltas) == 1 else last_sub
        if target:
            deltas[target] = deltas.get(target, 0) + unacc

state["conns"] = tracked
state["global_total"] = global_total
state["last_sub"] = last_sub
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

  sleep 5
done
