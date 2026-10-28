import{ag as n,ad as e,F as a,M as r}from"./entry-index-ufwhoi3w.js";

// Clean inline SVG Icons
const svg = (path, cls="w-4 h-4") => a.jsx("svg", {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "2",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  className: cls,
  dangerouslySetInnerHTML: { __html: path }
});

const Icons = {
  Server: (cls) => svg('<rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/>', cls),
  Activity: (cls) => svg('<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>', cls),
  Sliders: (cls) => svg('<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/>', cls),
  Bell: (cls) => svg('<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>', cls),
  Copy: (cls) => svg('<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>', cls),
  Check: (cls) => svg('<polyline points="20 6 9 17 4 12"/>', cls),
  QrCode: (cls) => svg('<rect width="5" height="5" x="3" y="3" rx="1"/><rect width="5" height="5" x="16" y="3" rx="1"/><rect width="5" height="5" x="3" y="16" rx="1"/><path d="M21 16h-3a2 2 0 0 0-2 2v3"/><path d="M21 21v.01"/><path d="M12 7v3a2 2 0 0 1-2 2H7"/><path d="M3 12h.01"/><path d="M12 3h.01"/><path d="M12 16v.01"/><path d="M16 12h1"/><path d="M21 12v.01"/><path d="M12 21v-1"/>', cls),
  Trash: (cls) => svg('<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>', cls),
  Plus: (cls) => svg('<path d="M5 12h14"/><path d="M12 5v14"/>', cls),
  Refresh: (cls) => svg('<path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 21h5v-5"/>', cls),
  Zap: (cls) => svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>', cls),
  Shield: (cls) => svg('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>', cls),
  Send: (cls) => svg('<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>', cls),
  Globe: (cls) => svg('<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>', cls),
  X: (cls) => svg('<path d="M18 6 6 18"/><path d="m6 6 12 12"/>', cls),
  RotateCcw: (cls) => svg('<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>', cls),
  Search: (cls) => svg('<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>', cls)
};

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024, sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
}

function NodeManagerApp() {
  const [params, setParams] = e();
  const currentTab = params.get("tab") || "nodes";

  const [nodes, setNodes] = r.useState([]);
  const [servers, setServers] = r.useState([]);
  const [serverStats, setServerStats] = r.useState({ total_traffic: 0, singbox_online_count: 0, total_servers: 0 });
  const [subUrl, setSubUrl] = r.useState("");
  const [rules, setRules] = r.useState([]);
  const [notifConfig, setNotifConfig] = r.useState({ channels: [], rules: [] });
  const [notifLogs, setNotifLogs] = r.useState([]);
  
  const [search, setSearch] = r.useState("");
  const [filter, setFilter] = r.useState("all"); // all, native, external
  const [pollInterval, setPollInterval] = r.useState(3000);
  const [pings, setPings] = r.useState({});
  const [pinging, setPinging] = r.useState(false);

  const [qrModal, setQrModal] = r.useState({ open: false, title: "", url: "" });
  const [importModal, setImportModal] = r.useState(false);
  const [externalLink, setExternalLink] = r.useState("");
  const [externalName, setExternalName] = r.useState("");
  const [isSubmitting, setIsSubmitting] = r.useState(false);

  // Tab switch helper
  const switchTab = (tab) => {
    const next = new URLSearchParams(params);
    next.set("tab", tab);
    setParams(next);
  };

  // 1. Fetch full data
  const fetchData = async () => {
    try {
      const [nRes, sRes, subRes] = await Promise.all([
        fetch("/api/node-mgr/nodes").then(r => r.json()).catch(() => ({ nodes: [] })),
        fetch("/api/node-mgr/servers").then(r => r.json()).catch(() => ({ servers: [] })),
        fetch("/api/node-mgr/sub/token").then(r => r.json()).catch(() => ({}))
      ]);
      if (nRes && nRes.nodes) setNodes(nRes.nodes);
      if (sRes && sRes.servers) {
        setServers(sRes.servers);
        setServerStats({
          total_traffic: sRes.total_traffic || 0,
          singbox_online_count: sRes.singbox_online_count || 0,
          total_servers: sRes.total_servers || sRes.servers.length
        });
      }
      if (subRes && subRes.sub_url) setSubUrl(subRes.sub_url);
    } catch (e) {
      console.error(e);
    }
  };

  // 2. Fetch rules
  const fetchRules = async () => {
    try {
      const res = await fetch("/api/node-mgr/sub/rules").then(r => r.json());
      if (res && res.rules) setRules(res.rules);
    } catch (e) {}
  };

  // 3. Fetch notifications
  const fetchNotifs = async () => {
    try {
      const [cfgRes, logRes] = await Promise.all([
        fetch("/api/node-mgr/notifications/config").then(r => r.json()),
        fetch("/api/node-mgr/notifications/logs").then(r => r.json())
      ]);
      if (cfgRes && cfgRes.ok) setNotifConfig(cfgRes);
      if (logRes && logRes.ok) setNotifLogs(logRes.logs || []);
    } catch (e) {}
  };

  // Initial fetch
  r.useEffect(() => {
    fetchData();
    fetchRules();
    fetchNotifs();
  }, []);

  // Real-time silent polling for servers throughput
  r.useEffect(() => {
    if (pollInterval <= 0) return;
    const t = setInterval(async () => {
      try {
        const res = await fetch("/api/node-mgr/servers").then(r => r.json());
        if (res && res.servers) {
          setServers(res.servers);
          setServerStats({
            total_traffic: res.total_traffic || 0,
            singbox_online_count: res.singbox_online_count || 0,
            total_servers: res.total_servers || res.servers.length
          });
        }
      } catch (e) {}
    }, pollInterval);
    return () => clearInterval(t);
  }, [pollInterval]);

  // Operations
  const toggleNode = async (id, currentEnabled) => {
    try {
      setNodes(prev => prev.map(n => n.id === id ? { ...n, enabled: !currentEnabled } : n));
      await fetch(`/api/node-mgr/nodes/${id}/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !currentEnabled })
      });
    } catch (e) {
      fetchData();
    }
  };

  const deleteNode = async (id) => {
    if (!confirm("确定要删除该节点吗？")) return;
    try {
      setNodes(prev => prev.filter(n => n.id !== id));
      await fetch(`/api/node-mgr/nodes/${id}`, { method: "DELETE" });
    } catch (e) {
      fetchData();
    }
  };

  const importExternalNode = async (e) => {
    e.preventDefault();
    if (!externalLink) return;
    setIsSubmitting(true);
    try {
      const res = await fetch("/api/node-mgr/nodes/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ link: externalLink, name: externalName })
      }).then(r => r.json());
      if (res && res.ok) {
        setImportModal(false);
        setExternalLink("");
        setExternalName("");
        fetchData();
      } else {
        alert(res.error || "导入失败，请检查链接格式");
      }
    } catch (err) {
      alert("导入失败: " + err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetServerTraffic = async (uuid) => {
    if (!confirm(uuid === "all" ? "确定将全部服务器的接入流量归零统计吗？" : "确定将此服务器的接入流量归零统计吗？")) return;
    try {
      await fetch("/api/node-mgr/traffic/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uuid })
      });
      fetchData();
    } catch (e) {}
  };

  const copyToClipboard = (text, msg="已复制到剪贴板！") => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text);
      alert(msg);
    }
  };

  // Test ping for a node
  const testNodePing = async (node) => {
    setPings(p => ({ ...p, [node.id]: "pinging" }));
    const t0 = Date.now();
    try {
      const testUrl = (node.server_ip ? `https://${node.server_ip}:${node.port}` : node.link) || "";
      await fetch(testUrl, { mode: 'no-cors', cache: 'no-store' });
      const ms = Date.now() - t0;
      setPings(p => ({ ...p, [node.id]: ms }));
    } catch (err) {
      const ms = Date.now() - t0;
      setPings(p => ({ ...p, [node.id]: ms < 3000 ? ms : "超时" }));
    }
  };

  const testAllPings = async () => {
    setPinging(true);
    const promises = nodes.map(n => testNodePing(n));
    await Promise.allSettled(promises);
    setPinging(false);
  };

  // Filtered nodes
  const filteredNodes = nodes.filter(n => {
    if (filter === "native" && (n.is_external || n.server_uuid === 'external')) return false;
    if (filter === "external" && (!n.is_external && n.server_uuid !== 'external')) return false;
    if (search) {
      const s = search.toLowerCase();
      return (n.name || "").toLowerCase().includes(s) || (n.server_ip || "").includes(s) || (n.port || "").toString().includes(s);
    }
    return true;
  });

  // Calculate live speeds
  let sumInRate = 0, sumOutRate = 0;
  servers.forEach(s => {
    sumInRate += (s.in_rate || 0);
    sumOutRate += (s.out_rate || 0);
  });

  return a.jsxs("div", {
    className: "p-3 sm:p-6 max-w-7xl mx-auto space-y-5 animate-in fade-in duration-200 select-none",
    children: [
      // Top Segmented Bar
      a.jsxs("div", {
        className: "flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white/70 dark:bg-zinc-900/70 backdrop-blur-md p-1.5 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 shadow-xs",
        children: [
          a.jsxs("div", {
            className: "flex items-center gap-1 overflow-x-auto no-scrollbar",
            children: [
              [
                { id: "nodes", label: "节点管理", icon: Icons.Server },
                { id: "traffic", label: "实时流量", icon: Icons.Activity },
                { id: "rules", label: "分流规则", icon: Icons.Sliders },
                { id: "notifications", label: "通知中心", icon: Icons.Bell }
              ].map(t => a.jsxs("button", {
                key: t.id,
                onClick: () => switchTab(t.id),
                className: `flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all shrink-0 ${
                  currentTab === t.id
                    ? "bg-indigo-600 text-white shadow-sm shadow-indigo-500/25"
                    : "text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-zinc-200 hover:bg-slate-100/60 dark:hover:bg-zinc-800/50"
                }`,
                children: [
                  t.icon("w-4 h-4"),
                  t.label
                ]
              }))
            ]
          }),
          a.jsxs("div", {
            className: "flex items-center gap-2 self-end sm:self-auto",
            children: [
              a.jsxs("button", {
                onClick: fetchData,
                className: "p-2 rounded-xl text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 border border-slate-200/60 dark:border-zinc-800 transition active:scale-95",
                title: "刷新全部数据",
                children: [Icons.Refresh("w-4 h-4")]
              }),
              a.jsxs("button", {
                onClick: () => setQrModal({ open: true, title: "通用全能订阅二维码", url: subUrl }),
                className: "px-3 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-xs hover:opacity-95 flex items-center gap-1.5 transition active:scale-95",
                children: [
                  Icons.QrCode("w-3.5 h-3.5"),
                  "订阅导入"
                ]
              })
            ]
          })
        ]
      }),

      // TAB 1: 节点管理
      currentTab === "nodes" && a.jsxs("div", {
        className: "space-y-4",
        children: [
          // Stat Cards
          a.jsxs("div", {
            className: "grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-4",
            children: [
              { label: "全部节点总数", val: nodes.length, color: "text-indigo-600 dark:text-indigo-400", bg: "bg-indigo-50 dark:bg-indigo-950/40", icon: Icons.Server },
              { label: "自建 Sing-box", val: nodes.filter(n => !n.is_external && n.server_uuid !== 'external').length, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-50 dark:bg-emerald-950/40", icon: Icons.Shield },
              { label: "外部接入节点", val: nodes.filter(n => n.is_external || n.server_uuid === 'external').length, color: "text-sky-600 dark:text-sky-400", bg: "bg-sky-50 dark:bg-sky-950/40", icon: Icons.Globe },
              { label: "核心在线运行", val: `${serverStats.singbox_online_count} / ${serverStats.total_servers}`, color: "text-purple-600 dark:text-purple-400", bg: "bg-purple-50 dark:bg-purple-950/40", icon: Icons.Zap }
            ].map((c, i) => a.jsxs("div", {
              key: i,
              className: "bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md p-3.5 sm:p-4 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 shadow-xs flex items-center justify-between",
              children: [
                a.jsxs("div", {
                  className: "space-y-1",
                  children: [
                    a.jsx("p", { className: "text-[11px] sm:text-xs text-slate-500 dark:text-zinc-400 font-medium", children: c.label }),
                    a.jsx("p", { className: `text-xl sm:text-2xl font-black ${c.color}`, children: c.val })
                  ]
                }),
                a.jsx("div", { className: `p-2.5 rounded-xl ${c.bg} ${c.color}`, children: c.icon("w-5 h-5") })
              ]
            }))
          }),

          // Toolbar
          a.jsxs("div", {
            className: "flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white/70 dark:bg-zinc-900/70 p-2.5 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80",
            children: [
              // Filters
              a.jsxs("div", {
                className: "flex items-center gap-1 bg-slate-100 dark:bg-zinc-800/60 p-1 rounded-xl text-xs font-semibold",
                children: [
                  { id: "all", label: "全部" },
                  { id: "native", label: "自建核心" },
                  { id: "external", label: "外部节点" }
                ].map(f => a.jsx("button", {
                  key: f.id,
                  onClick: () => setFilter(f.id),
                  className: `px-3 py-1.5 rounded-lg transition ${filter === f.id ? "bg-white dark:bg-zinc-700 text-indigo-600 dark:text-indigo-400 shadow-xs" : "text-slate-500 hover:text-slate-800"}`,
                  children: f.label
                }))
              }),

              // Search & Actions
              a.jsxs("div", {
                className: "flex items-center gap-2 flex-1 max-w-lg",
                children: [
                  a.jsxs("div", {
                    className: "relative flex-1",
                    children: [
                      a.jsx("div", { className: "absolute inset-y-0 left-3 flex items-center text-slate-400", children: Icons.Search("w-3.5 h-3.5") }),
                      a.jsx("input", {
                        type: "text",
                        placeholder: "快速过滤节点名称、IP或端口...",
                        value: search,
                        onChange: e => setSearch(e.target.value),
                        className: "w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 dark:bg-zinc-800/80 border border-slate-200/80 dark:border-zinc-700/80 rounded-xl focus:outline-hidden focus:border-indigo-500 transition"
                      })
                    ]
                  }),
                  a.jsxs("button", {
                    onClick: testAllPings,
                    disabled: pinging,
                    className: "px-2.5 py-1.5 text-xs font-semibold rounded-xl border border-slate-200 dark:border-zinc-700 hover:bg-slate-50 dark:hover:bg-zinc-800 text-slate-700 dark:text-zinc-300 flex items-center gap-1 transition shrink-0 active:scale-95",
                    children: [
                      Icons.Zap("w-3.5 h-3.5 text-amber-500"),
                      pinging ? "测速中..." : "全员测速"
                    ]
                  }),
                  a.jsxs("button", {
                    onClick: () => setImportModal(true),
                    className: "px-3 py-1.5 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1 transition shrink-0 active:scale-95 shadow-xs",
                    children: [
                      Icons.Plus("w-3.5 h-3.5"),
                      "导入外部节点"
                    ]
                  })
                ]
              })
            ]
          }),

          // Node Grid Cards
          filteredNodes.length === 0 ? a.jsxs("div", {
            className: "py-16 text-center text-slate-400 dark:text-zinc-500 space-y-2",
            children: [
              a.jsx("div", { className: "w-12 h-12 rounded-2xl bg-slate-100 dark:bg-zinc-800 flex items-center justify-center mx-auto text-slate-400", children: Icons.Server("w-6 h-6") }),
              a.jsx("p", { className: "text-sm font-medium", children: "暂无符合条件的节点" }),
              a.jsx("p", { className: "text-xs", children: "可通过“导入外部节点”粘贴链接，或在服务器列表部署 Sing-box 核心节点" })
            ]
          }) : a.jsx("div", {
            className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5",
            children: filteredNodes.map(node => {
              const pingVal = pings[node.id];
              const proto = (node.protocol || "vless").toUpperCase();
              const protoBadge = proto === "VLESS" ? "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400" :
                                proto === "HYSTERIA2" ? "bg-purple-500/10 text-purple-600 dark:text-purple-400" :
                                proto === "SHADOWSOCKS" ? "bg-sky-500/10 text-sky-600 dark:text-sky-400" :
                                proto === "TROJAN" ? "bg-amber-500/10 text-amber-600 dark:text-amber-400" : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400";

              return a.jsxs("div", {
                key: node.id,
                className: `p-4 rounded-2xl border transition-all duration-200 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-md shadow-xs space-y-3 ${
                  node.enabled ? "border-slate-200/90 dark:border-zinc-800/90 hover:border-indigo-500/40" : "border-slate-200/50 dark:border-zinc-800/40 opacity-60"
                }`,
                children: [
                  // Card Header
                  a.jsxs("div", {
                    className: "flex items-start justify-between gap-2",
                    children: [
                      a.jsxs("div", {
                        className: "space-y-1 flex-1 min-w-0",
                        children: [
                          a.jsxs("div", {
                            className: "flex items-center gap-1.5 flex-wrap",
                            children: [
                              a.jsx("span", { className: `px-2 py-0.5 rounded-lg text-[10px] font-bold ${protoBadge}`, children: proto }),
                              a.jsx("span", { className: "font-bold text-sm text-slate-800 dark:text-zinc-100 truncate block", title: node.name, children: node.name })
                            ]
                          }),
                          a.jsxs("p", {
                            className: "text-[11px] text-slate-500 dark:text-zinc-400 font-mono flex items-center gap-1",
                            children: [
                              node.server_ip || node.sni || "外部接入",
                              node.port ? `:${node.port}` : ""
                            ]
                          })
                        ]
                      }),
                      // Toggle Switch
                      a.jsx("button", {
                        onClick: () => toggleNode(node.id, node.enabled),
                        className: `relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out ${node.enabled ? "bg-indigo-600" : "bg-slate-300 dark:bg-zinc-700"}`,
                        children: a.jsx("span", {
                          className: `pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition duration-200 ease-in-out mt-0.5 ml-0.5 ${node.enabled ? "translate-x-4" : "translate-x-0"}`
                        })
                      })
                    ]
                  }),

                  // Latency & Details
                  a.jsxs("div", {
                    className: "flex items-center justify-between text-xs pt-1 border-t border-slate-100 dark:border-zinc-800/60",
                    children: [
                      a.jsxs("button", {
                        onClick: () => testNodePing(node),
                        className: "flex items-center gap-1 text-[11px] font-semibold text-slate-500 hover:text-indigo-600 transition",
                        children: [
                          pingVal === "pinging" ? a.jsx("span", { className: "w-2 h-2 rounded-full bg-amber-400 animate-ping" }) :
                          typeof pingVal === "number" ? a.jsx("span", { className: `w-2 h-2 rounded-full ${pingVal < 100 ? "bg-emerald-500" : pingVal < 250 ? "bg-amber-500" : "bg-rose-500"}` }) :
                          a.jsx("span", { className: "w-2 h-2 rounded-full bg-slate-400" }),
                          pingVal === "pinging" ? "测速中..." :
                          typeof pingVal === "number" ? `${pingVal} ms` : (pingVal || "点击测速")
                        ]
                      }),
                      a.jsx("span", {
                        className: "text-[11px] text-slate-400 dark:text-zinc-500",
                        children: node.is_external ? "外部导入" : "自建探针"
                      })
                    ]
                  }),

                  // Action Buttons
                  a.jsxs("div", {
                    className: "grid grid-cols-3 gap-1.5 pt-1",
                    children: [
                      a.jsxs("button", {
                        onClick: () => copyToClipboard(node.link || ""),
                        className: "py-1.5 px-2 rounded-xl bg-slate-100 dark:bg-zinc-800 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 text-slate-700 dark:text-zinc-300 text-xs font-semibold flex items-center justify-center gap-1 transition active:scale-95",
                        children: [Icons.Copy("w-3 h-3"), "复制"]
                      }),
                      a.jsxs("button", {
                        onClick: () => setQrModal({ open: true, title: node.name, url: node.link || "" }),
                        className: "py-1.5 px-2 rounded-xl bg-slate-100 dark:bg-zinc-800 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 text-slate-700 dark:text-zinc-300 text-xs font-semibold flex items-center justify-center gap-1 transition active:scale-95",
                        children: [Icons.QrCode("w-3 h-3"), "二维码"]
                      }),
                      a.jsxs("button", {
                        onClick: () => deleteNode(node.id),
                        className: "py-1.5 px-2 rounded-xl bg-slate-100 dark:bg-zinc-800 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center justify-center gap-1 transition active:scale-95",
                        children: [Icons.Trash("w-3 h-3"), "删除"]
                      })
                    ]
                  })
                ]
              });
            })
          })
        ]
      }),

      // TAB 2: 实时流量监控
      currentTab === "traffic" && a.jsxs("div", {
        className: "space-y-4",
        children: [
          // Live Throughput Hero
          a.jsxs("div", {
            className: "p-5 sm:p-6 rounded-3xl bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-950 text-white shadow-xl relative overflow-hidden space-y-4",
            children: [
              a.jsxs("div", {
                className: "flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 relative z-10",
                children: [
                  a.jsxs("div", {
                    className: "space-y-1",
                    children: [
                      a.jsxs("div", {
                        className: "flex items-center gap-2",
                        children: [
                          a.jsx("span", { className: "w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" }),
                          a.jsx("h2", { className: "text-base sm:text-lg font-bold tracking-tight", children: "全网核心实时吞吐速率" })
                        ]
                      }),
                      a.jsxs("p", {
                        className: "text-xs text-indigo-200/80",
                        children: [
                          "接入节点总消耗 ",
                          a.jsx("strong", { className: "text-white font-mono", children: formatBytes(serverStats.total_traffic) }),
                          ` · 探针在线 ${serverStats.singbox_online_count} / ${serverStats.total_servers} 台`
                        ]
                      })
                    ]
                  }),
                  // Polling Controls
                  a.jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [
                      a.jsxs("div", {
                        className: "flex items-center bg-white/10 backdrop-blur-md p-0.5 rounded-xl text-xs font-semibold border border-white/10",
                        children: [
                          [1000, "1秒"],
                          [3000, "3秒"],
                          [5000, "5秒"]
                        ].map(([ms, l]) => a.jsx("button", {
                          key: ms,
                          onClick: () => setPollInterval(ms),
                          className: `px-2.5 py-1 rounded-lg transition ${pollInterval === ms ? "bg-white text-indigo-900 shadow-sm" : "text-white/70 hover:text-white"}`,
                          children: l
                        }))
                      }),
                      a.jsxs("button", {
                        onClick: () => resetServerTraffic("all"),
                        className: "px-3 py-1.5 rounded-xl bg-white/10 hover:bg-rose-500/20 text-xs font-semibold border border-white/15 text-rose-300 transition active:scale-95",
                        children: [Icons.RotateCcw("w-3.5 h-3.5 inline mr-1"), "全部归零"]
                      })
                    ]
                  })
                ]
              }),

              // Live Speed Meter
              a.jsxs("div", {
                className: "grid grid-cols-2 gap-3 pt-2 relative z-10",
                children: [
                  a.jsxs("div", {
                    className: "bg-white/5 backdrop-blur-md p-4 rounded-2xl border border-white/10 space-y-1",
                    children: [
                      a.jsx("span", { className: "text-xs text-emerald-300 font-semibold flex items-center gap-1", children: "↓ 全网下行速率" }),
                      a.jsx("div", { className: "text-2xl sm:text-3xl font-black font-mono text-emerald-400 tracking-tight", children: `${formatBytes(sumInRate)}/s` })
                    ]
                  }),
                  a.jsxs("div", {
                    className: "bg-white/5 backdrop-blur-md p-4 rounded-2xl border border-white/10 space-y-1",
                    children: [
                      a.jsx("span", { className: "text-xs text-sky-300 font-semibold flex items-center gap-1", children: "↑ 全网上行速率" }),
                      a.jsx("div", { className: "text-2xl sm:text-3xl font-black font-mono text-sky-400 tracking-tight", children: `${formatBytes(sumOutRate)}/s` })
                    ]
                  })
                ]
              })
            ]
          }),

          // Server Traffic Cards
          a.jsx("div", {
            className: "grid grid-cols-1 md:grid-cols-2 gap-3.5",
            children: servers.map(srv => {
              const consumed = srv.total_traffic || 0;
              return a.jsxs("div", {
                key: srv.uuid,
                className: "p-4 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md shadow-xs space-y-3",
                children: [
                  a.jsxs("div", {
                    className: "flex items-start justify-between gap-2",
                    children: [
                      a.jsxs("div", {
                        className: "space-y-0.5",
                        children: [
                          a.jsx("h3", { className: "font-bold text-sm text-slate-800 dark:text-zinc-100", children: srv.name || srv.host || "服务器" }),
                          a.jsx("p", { className: "text-xs text-slate-500 font-mono", children: srv.host || srv.ip || srv.uuid })
                        ]
                      }),
                      a.jsxs("span", {
                        className: `inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                          srv.singbox_online ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" : "bg-slate-200 dark:bg-zinc-700 text-slate-500"
                        }`,
                        children: [
                          a.jsx("span", { className: `w-2 h-2 rounded-full ${srv.singbox_online ? "bg-emerald-500 animate-pulse" : "bg-slate-400"}` }),
                          srv.singbox_online ? (srv.last_seen_ago !== null ? `${srv.last_seen_ago}s前` : "在线") : "离线"
                        ]
                      })
                    ]
                  }),

                  // Consumed bar
                  a.jsxs("div", {
                    className: "space-y-1.5",
                    children: [
                      a.jsxs("div", {
                        className: "flex items-center justify-between text-xs",
                        children: [
                          a.jsx("span", { className: "text-slate-500 font-medium", children: "接入后累计消耗" }),
                          a.jsx("span", { className: "font-bold font-mono text-indigo-600 dark:text-indigo-400", children: formatBytes(consumed) })
                        ]
                      }),
                      a.jsx("div", {
                        className: "h-2 w-full bg-slate-100 dark:bg-zinc-800 rounded-full overflow-hidden",
                        children: a.jsx("div", {
                          className: "h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full",
                          style: { width: `${Math.min(100, Math.max(5, (consumed / (serverStats.total_traffic || 1)) * 100))}%` }
                        })
                      })
                    ]
                  }),

                  // Speeds Grid
                  a.jsxs("div", {
                    className: "grid grid-cols-2 gap-2 text-xs bg-slate-50 dark:bg-zinc-800/40 p-2.5 rounded-xl font-mono",
                    children: [
                      a.jsxs("div", {
                        children: [
                          a.jsx("span", { className: "text-[10px] text-slate-400 block font-sans", children: "实时速率" }),
                          a.jsxs("span", { className: "font-semibold text-emerald-600 dark:text-emerald-400", children: ["↓ ", formatBytes(srv.in_rate || 0), "/s"] }),
                          a.jsxs("span", { className: "font-semibold text-sky-600 dark:text-sky-400 ml-1.5", children: ["↑ ", formatBytes(srv.out_rate || 0), "/s"] })
                        ]
                      }),
                      a.jsxs("div", {
                        className: "flex items-center justify-between",
                        children: [
                          a.jsxs("div", {
                            children: [
                              a.jsx("span", { className: "text-[10px] text-slate-400 block font-sans", children: "物理网卡" }),
                              a.jsx("span", { className: "text-slate-700 dark:text-zinc-300 font-medium", children: formatBytes(srv.raw_total || 0) })
                            ]
                          }),
                          a.jsx("button", {
                            onClick: () => resetServerTraffic(srv.uuid),
                            className: "p-1.5 rounded-lg border border-slate-200 dark:border-zinc-700 hover:bg-slate-200 text-slate-500",
                            title: "该机统计归零",
                            children: Icons.RotateCcw("w-3 h-3")
                          })
                        ]
                      })
                    ]
                  })
                ]
              });
            })
          })
        ]
      }),

      // TAB 3: 分流规则与全能订阅
      currentTab === "rules" && a.jsxs("div", {
        className: "space-y-5",
        children: [
          // Subscriptions Card
          a.jsxs("div", {
            className: "p-4 sm:p-5 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md shadow-xs space-y-3",
            children: [
              a.jsxs("div", {
                className: "flex items-center justify-between",
                children: [
                  a.jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [
                      a.jsx("span", { className: "p-2 rounded-xl bg-indigo-500/10 text-indigo-600", children: Icons.Zap("w-4 h-4") }),
                      a.jsx("h3", { className: "font-bold text-sm sm:text-base text-slate-800 dark:text-zinc-100", children: "统一全能订阅链接 (Universal Subscription)" })
                    ]
                  }),
                  a.jsxs("button", {
                    onClick: async () => {
                      if (!confirm("重置订阅 Token 会导致已导入的客户端需要更新链接，确认重置吗？")) return;
                      const r = await fetch("/api/node-mgr/sub/token/reset", { method: "POST" }).then(res => res.json());
                      if (r && r.sub_url) setSubUrl(r.sub_url);
                    },
                    className: "text-xs text-slate-500 hover:text-rose-600 font-semibold transition",
                    children: ["重置 Token"]
                  })
                ]
              }),

              // 3 Links Grid
              a.jsxs("div", {
                className: "grid grid-cols-1 md:grid-cols-3 gap-2.5",
                children: [
                  { title: "通用全协议订阅", url: subUrl, desc: "Clash / Surge / Sing-box 客户端自动识别" },
                  { title: "Clash / Mihomo 专用", url: subUrl ? `${subUrl}?clash=1` : "", desc: "一键拉取标准 YAML 配置文件" },
                  { title: "Base64 订阅", url: subUrl ? `${subUrl}?format=b64` : "", desc: "Shadowrocket / V2Ray / 小火箭" }
                ].map((item, idx) => a.jsxs("div", {
                  key: idx,
                  className: "p-3 rounded-xl bg-slate-50 dark:bg-zinc-800/50 border border-slate-100 dark:border-zinc-800 space-y-2",
                  children: [
                    a.jsx("span", { className: "font-bold text-xs text-slate-700 dark:text-zinc-200 block", children: item.title }),
                    a.jsx("input", {
                      type: "text",
                      readOnly: true,
                      value: item.url,
                      className: "w-full text-[11px] font-mono bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-lg px-2 py-1 select-all"
                    }),
                    a.jsxs("div", {
                      className: "flex items-center justify-between text-xs pt-1",
                      children: [
                        a.jsx("span", { className: "text-[10px] text-slate-400 truncate max-w-[140px]", children: item.desc }),
                        a.jsxs("div", {
                          className: "flex items-center gap-1",
                          children: [
                            a.jsxs("button", {
                              onClick: () => copyToClipboard(item.url),
                              className: "p-1 rounded-lg hover:bg-slate-200 dark:hover:bg-zinc-700 text-slate-600 dark:text-zinc-300",
                              title: "复制链接",
                              children: [Icons.Copy("w-3.5 h-3.5")]
                            }),
                            a.jsxs("button", {
                              onClick: () => setQrModal({ open: true, title: item.title, url: item.url }),
                              className: "p-1 rounded-lg hover:bg-slate-200 dark:hover:bg-zinc-700 text-slate-600 dark:text-zinc-300",
                              title: "二维码",
                              children: [Icons.QrCode("w-3.5 h-3.5")]
                            })
                          ]
                        })
                      ]
                    })
                  ]
                }))
              })
            ]
          }),

          // Visual Rules Preset
          a.jsxs("div", {
            className: "p-4 sm:p-5 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md shadow-xs space-y-3",
            children: [
              a.jsxs("div", {
                className: "flex items-center justify-between",
                children: [
                  a.jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [
                      a.jsx("span", { className: "p-2 rounded-xl bg-purple-500/10 text-purple-600", children: Icons.Sliders("w-4 h-4") }),
                      a.jsx("h3", { className: "font-bold text-sm sm:text-base text-slate-800 dark:text-zinc-100", children: "分流预设策略 (Routing Presets)" })
                    ]
                  }),
                  a.jsx("span", { className: "text-xs text-indigo-600 dark:text-indigo-400 font-semibold", children: "一键智能分流生效中" })
                ]
              }),
              a.jsx("div", {
                className: "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5",
                children: [
                  { title: "绕过大陆模式", badge: "推荐", desc: "大陆常见域名和 IP 直连，国外全部走代理", active: true },
                  { title: "全局节点代理", badge: "全局", desc: "所有流量全部通过节点转发，隐藏本地 IP", active: false },
                  { title: "国外流媒体加速", badge: "专线", desc: "YouTube / Netflix / TikTok 自动走优选节点", active: false },
                  { title: "广告拦截过滤", badge: "净化", desc: "自动屏蔽常见隐私追踪与广告弹窗域名", active: false }
                ].map((p, idx) => a.jsxs("div", {
                  key: idx,
                  className: `p-3.5 rounded-xl border transition-all cursor-pointer ${
                    p.active ? "border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/20" : "border-slate-200/80 dark:border-zinc-800 hover:border-slate-300"
                  }`,
                  children: [
                    a.jsxs("div", {
                      className: "flex items-center justify-between",
                      children: [
                        a.jsx("span", { className: "font-bold text-xs text-slate-800 dark:text-zinc-200", children: p.title }),
                        a.jsx("span", { className: `px-1.5 py-0.5 rounded text-[10px] font-bold ${p.active ? "bg-indigo-600 text-white" : "bg-slate-200 text-slate-600"}`, children: p.badge })
                      ]
                    }),
                    a.jsx("p", { className: "text-[11px] text-slate-500 dark:text-zinc-400 mt-1.5 leading-relaxed", children: p.desc })
                  ]
                }))
              })
            ]
          })
        ]
      }),

      // TAB 4: 通知中心
      currentTab === "notifications" && a.jsxs("div", {
        className: "space-y-4",
        children: [
          // Telegram Bot Config
          a.jsxs("div", {
            className: "p-4 sm:p-5 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md shadow-xs space-y-4",
            children: [
              a.jsxs("div", {
                className: "flex items-center justify-between",
                children: [
                  a.jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [
                      a.jsx("span", { className: "p-2 rounded-xl bg-sky-500/10 text-sky-600", children: Icons.Send("w-4 h-4") }),
                      a.jsx("h3", { className: "font-bold text-sm sm:text-base text-slate-800 dark:text-zinc-100", children: "Telegram 机器人即时推送通道" })
                    ]
                  }),
                  a.jsx("span", { className: "px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-600", children: "通道已启用" })
                ]
              }),

              // Inputs Form
              a.jsxs("div", {
                className: "grid grid-cols-1 sm:grid-cols-2 gap-3",
                children: [
                  a.jsxs("div", {
                    className: "space-y-1",
                    children: [
                      a.jsx("label", { className: "text-xs font-semibold text-slate-600 dark:text-zinc-300", children: "Bot Token" }),
                      a.jsx("input", {
                        type: "text",
                        defaultValue: "8731954829:AAG6HlNgKnth8_2yIYAtMyV4gPx_c-I2bJY",
                        id: "tgBotTokenInput",
                        className: "w-full text-xs font-mono bg-slate-50 dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl px-3 py-2"
                      })
                    ]
                  }),
                  a.jsxs("div", {
                    className: "space-y-1",
                    children: [
                      a.jsx("label", { className: "text-xs font-semibold text-slate-600 dark:text-zinc-300", children: "Chat ID" }),
                      a.jsx("input", {
                        type: "text",
                        defaultValue: "791298471",
                        id: "tgChatIdInput",
                        className: "w-full text-xs font-mono bg-slate-50 dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl px-3 py-2"
                      })
                    ]
                  })
                ]
              }),

              a.jsxs("div", {
                className: "flex items-center justify-end gap-2 pt-2 border-t border-slate-100 dark:border-zinc-800",
                children: [
                  a.jsxs("button", {
                    onClick: async () => {
                      const token = document.getElementById("tgBotTokenInput")?.value;
                      const chat = document.getElementById("tgChatIdInput")?.value;
                      try {
                        const r = await fetch("/api/node-mgr/notifications/test", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ type: "telegram", bot_token: token, chat_id: chat })
                        }).then(res => res.json());
                        if (r && r.ok) {
                          alert("测试通知已成功推送到 Telegram！");
                          fetchNotifs();
                        } else {
                          alert("推送失败: " + (r.error || "请检查 Token 和 Chat ID"));
                        }
                      } catch (err) {
                        alert("测试失败: " + err);
                      }
                    },
                    className: "px-3.5 py-2 rounded-xl text-xs font-semibold border border-slate-200 dark:border-zinc-700 hover:bg-slate-50 dark:hover:bg-zinc-800 text-slate-700 dark:text-zinc-300 flex items-center gap-1.5 transition active:scale-95",
                    children: [Icons.Send("w-3.5 h-3.5"), "发送测试通知"]
                  }),
                  a.jsx("button", {
                    onClick: async () => {
                      const token = document.getElementById("tgBotTokenInput")?.value;
                      const chat = document.getElementById("tgChatIdInput")?.value;
                      await fetch("/api/node-mgr/notifications/channels/save", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ id: 1, type: "telegram", name: "Telegram 机器人", enabled: 1, config: { bot_token: token, chat_id: chat } })
                      });
                      alert("配置已成功保存！");
                      fetchNotifs();
                    },
                    className: "px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition active:scale-95 shadow-xs",
                    children: "保存配置"
                  })
                ]
              })
            ]
          }),

          // 10 Rules Grid
          a.jsxs("div", {
            className: "p-4 sm:p-5 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md shadow-xs space-y-3",
            children: [
              a.jsxs("div", {
                className: "flex items-center justify-between",
                children: [
                  a.jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [
                      a.jsx("span", { className: "p-2 rounded-xl bg-amber-500/10 text-amber-600", children: Icons.Bell("w-4 h-4") }),
                      a.jsx("h3", { className: "font-bold text-sm sm:text-base text-slate-800 dark:text-zinc-100", children: "智能告警触发项配置 (10 项细粒度守护)" })
                    ]
                  }),
                  a.jsx("span", { className: "text-xs text-slate-500", children: `已启用 ${notifConfig.rules.filter(r=>r.enabled).length} / ${notifConfig.rules.length || 10} 项` })
                ]
              }),
              a.jsx("div", {
                className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3",
                children: (notifConfig.rules || []).map(rItem => a.jsxs("div", {
                  key: rItem.rule_key,
                  className: "p-3 rounded-xl bg-slate-50 dark:bg-zinc-800/50 border border-slate-100 dark:border-zinc-800 space-y-1.5",
                  children: [
                    a.jsxs("div", {
                      className: "flex items-center justify-between gap-2",
                      children: [
                        a.jsx("span", { className: "font-bold text-xs text-slate-800 dark:text-zinc-100", children: rItem.name }),
                        a.jsx("button", {
                          onClick: async () => {
                            const newStatus = !rItem.enabled;
                            setNotifConfig(prev => ({
                              ...prev,
                              rules: prev.rules.map(x => x.rule_key === rItem.rule_key ? { ...x, enabled: newStatus } : x)
                            }));
                            await fetch("/api/node-mgr/notifications/rules/toggle", {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ rule_key: rItem.rule_key, enabled: newStatus })
                            });
                          },
                          className: `relative inline-flex h-4 w-7 shrink-0 cursor-pointer rounded-full transition-colors ${rItem.enabled ? "bg-indigo-600" : "bg-slate-300 dark:bg-zinc-600"}`,
                          children: a.jsx("span", {
                            className: `inline-block h-3 w-3 transform rounded-full bg-white shadow transition mt-0.5 ml-0.5 ${rItem.enabled ? "translate-x-3" : "translate-x-0"}`
                          })
                        })
                      ]
                    }),
                    a.jsx("p", { className: "text-[11px] text-slate-500 dark:text-zinc-400 leading-relaxed", children: rItem.description })
                  ]
                }))
              })
            ]
          }),

          // Push Audit Logs
          a.jsxs("div", {
            className: "p-4 sm:p-5 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md shadow-xs space-y-3",
            children: [
              a.jsxs("div", {
                className: "flex items-center justify-between",
                children: [
                  a.jsx("h3", { className: "font-bold text-sm text-slate-800 dark:text-zinc-100", children: "最新推送审计日志" }),
                  a.jsx("button", {
                    onClick: fetchNotifs,
                    className: "text-xs text-indigo-600 dark:text-indigo-400 font-semibold",
                    children: "刷新日志"
                  })
                ]
              }),
              notifLogs.length === 0 ? a.jsx("p", { className: "py-6 text-center text-xs text-slate-400", children: "暂无告警记录，系统运行平稳" }) :
              a.jsx("div", {
                className: "space-y-2 max-h-64 overflow-y-auto pr-1",
                children: notifLogs.slice(0, 10).map(l => a.jsxs("div", {
                  key: l.id,
                  className: "p-2.5 rounded-xl bg-slate-50 dark:bg-zinc-800/40 border border-slate-100 dark:border-zinc-800 text-xs flex items-center justify-between gap-2",
                  children: [
                    a.jsxs("div", {
                      className: "space-y-0.5",
                      children: [
                        a.jsx("p", { className: "font-bold text-slate-800 dark:text-zinc-200", children: l.title }),
                        a.jsx("p", { className: "text-[11px] text-slate-500", children: l.message })
                      ]
                    }),
                    a.jsxs("div", {
                      className: "text-right shrink-0",
                      children: [
                        a.jsx("span", {
                          className: `inline-block px-2 py-0.5 rounded text-[10px] font-bold ${l.status === "success" ? "bg-emerald-500/10 text-emerald-600" : "bg-rose-500/10 text-rose-600"}`,
                          children: l.status === "success" ? "已送达" : "失败"
                        }),
                        a.jsx("p", { className: "text-[10px] text-slate-400 mt-1", children: l.created_at ? l.created_at.slice(11, 19) : "" })
                      ]
                    })
                  ]
                }))
              })
            ]
          })
        ]
      }),

      // QR Code Modal
      qrModal.open && a.jsx("div", {
        className: "fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150",
        onClick: () => setQrModal({ open: false, title: "", url: "" }),
        children: a.jsxs("div", {
          className: "bg-white dark:bg-zinc-900 rounded-3xl p-6 max-w-sm w-full space-y-4 shadow-2xl border border-slate-200 dark:border-zinc-800 text-center",
          onClick: e => e.stopPropagation(),
          children: [
            a.jsxs("div", {
              className: "flex items-center justify-between",
              children: [
                a.jsx("h3", { className: "font-bold text-base text-slate-900 dark:text-white truncate", children: qrModal.title }),
                a.jsx("button", { onClick: () => setQrModal({ open: false, title: "", url: "" }), className: "p-1 rounded-full text-slate-400 hover:text-slate-600", children: Icons.X("w-5 h-5") })
              ]
            }),
            a.jsx("div", {
              className: "p-4 bg-white rounded-2xl border border-slate-200 inline-block mx-auto shadow-inner",
              children: a.jsx("img", {
                src: `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(qrModal.url)}`,
                alt: "QR Code",
                className: "w-48 h-48 mx-auto"
              })
            }),
            a.jsx("textarea", {
              readOnly: true,
              value: qrModal.url,
              className: "w-full h-16 text-xs font-mono bg-slate-50 dark:bg-zinc-800/80 p-2 rounded-xl border border-slate-200 dark:border-zinc-700 resize-none select-all"
            }),
            a.jsx("button", {
              onClick: () => copyToClipboard(qrModal.url),
              className: "w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-md transition active:scale-95",
              children: "复制链接"
            })
          ]
        })
      }),

      // Import External Node Modal
      importModal && a.jsx("div", {
        className: "fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150",
        onClick: () => setImportModal(false),
        children: a.jsxs("form", {
          onSubmit: importExternalNode,
          className: "bg-white dark:bg-zinc-900 rounded-3xl p-6 max-w-md w-full space-y-4 shadow-2xl border border-slate-200 dark:border-zinc-800",
          onClick: e => e.stopPropagation(),
          children: [
            a.jsxs("div", {
              className: "flex items-center justify-between",
              children: [
                a.jsx("h3", { className: "font-bold text-base text-slate-900 dark:text-white", children: "导入外部节点链接" }),
                a.jsx("button", { type: "button", onClick: () => setImportModal(false), className: "p-1 rounded-full text-slate-400 hover:text-slate-600", children: Icons.X("w-5 h-5") })
              ]
            }),
            a.jsxs("div", {
              className: "space-y-3 text-xs",
              children: [
                a.jsxs("div", {
                  className: "space-y-1",
                  children: [
                    a.jsx("label", { className: "font-semibold text-slate-700 dark:text-zinc-300", children: "节点自定义名称 (可选)" }),
                    a.jsx("input", {
                      type: "text",
                      placeholder: "例如：自建备用 HK-01",
                      value: externalName,
                      onChange: e => setExternalName(e.target.value),
                      className: "w-full p-2.5 rounded-xl border border-slate-200 dark:border-zinc-700 bg-slate-50 dark:bg-zinc-800"
                    })
                  ]
                }),
                a.jsxs("div", {
                  className: "space-y-1",
                  children: [
                    a.jsx("label", { className: "font-semibold text-slate-700 dark:text-zinc-300", children: "节点分享链接 (URI)" }),
                    a.jsx("textarea", {
                      required: true,
                      placeholder: "粘贴 vless://, hysteria2://, ss://, trojan://, vmess:// 链接...",
                      value: externalLink,
                      onChange: e => setExternalLink(e.target.value),
                      className: "w-full h-24 p-2.5 font-mono text-xs rounded-xl border border-slate-200 dark:border-zinc-700 bg-slate-50 dark:bg-zinc-800 resize-none"
                    })
                  ]
                })
              ]
            }),
            a.jsx("button", {
              type: "submit",
              disabled: isSubmitting,
              className: "w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-md transition active:scale-95",
              children: isSubmitting ? "解析导入中..." : "确认导入并保存"
            })
          ]
        })
      })
    ]
  });
}

export { NodeManagerApp as default };
