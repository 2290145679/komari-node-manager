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
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_link TEXT DEFAULT '',
    is_external INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    name TEXT DEFAULT 'default',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS node_agents (
    server_uuid TEXT PRIMARY KEY,
    token TEXT,
    last_sync TIMESTAMP,
    status TEXT
);

CREATE TABLE IF NOT EXISTS agent_heartbeats (
    token TEXT PRIMARY KEY,
    last_seen INTEGER
);

CREATE TABLE IF NOT EXISTS server_traffic_baselines (
    uuid TEXT PRIMARY KEY,
    baseline_up INTEGER DEFAULT 0,
    baseline_down INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscription_rules (
    id INTEGER PRIMARY KEY,
    direct_bt INTEGER DEFAULT 1,
    direct_cn INTEGER DEFAULT 1,
    direct_lan INTEGER DEFAULT 1,
    block_ads INTEGER DEFAULT 0,
    enable_auto_group INTEGER DEFAULT 1,
    final_match TEXT DEFAULT 'PROXY',
    custom_rules TEXT DEFAULT '',
    proxy_ai INTEGER DEFAULT 0,
    proxy_tg INTEGER DEFAULT 0,
    proxy_media INTEGER DEFAULT 0,
    proxy_dev INTEGER DEFAULT 0,
    direct_games INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO subscription_rules (id, direct_bt, direct_cn, direct_lan, block_ads, enable_auto_group, final_match, custom_rules)
VALUES (1, 1, 1, 1, 0, 1, 'PROXY', '');
