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
  Search: (cls) => svg('<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>', cls),
  ChevronRight: (cls) => svg('<path d="m9 18 6-6-6-6"/>', cls),
  MoreHorizontal: (cls) => svg('<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>', cls)
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

  // iOS-style Bottom Action Sheet state
  const [actionNode, setActionNode] = r.useState(null);

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

  const fetchRules = async () => {
    try {
      const res = await fetch("/api/node-mgr/sub/rules").then(r => r.json());
      if (res && res.rules) setRules(res.rules);
    } catch (e) {}
  };

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
      if (actionNode && actionNode.id === id) setActionNode(null);
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

  const filteredNodes = nodes.filter(n => {
    if (filter === "native" && (n.is_external || n.server_uuid === 'external')) return false;
    if (filter === "external" && (!n.is_external && n.server_uuid !== 'external')) return false;
    if (search) {
      const s = search.toLowerCase();
      return (n.name || "").toLowerCase().includes(s) || (n.server_ip || "").includes(s) || (n.port || "").toString().includes(s);
    }
    return true;
  });

  let sumInRate = 0, sumOutRate = 0;
  servers.forEach(s => {
    sumInRate += (s.in_rate || 0);
    sumOutRate += (s.out_rate || 0);
  });

  const tabItems = [
    { id: "nodes", label: "节点", icon: Icons.Server },
    { id: "traffic", label: "监控", icon: Icons.Activity },
    { id: "rules", label: "分流", icon: Icons.Sliders },
    { id: "notifications", label: "通知", icon: Icons.Bell }
  ];

  return a.jsxs("div", {
    className: "p-3 sm:p-6 max-w-5xl mx-auto space-y-4 pb-28 md:pb-6 select-none animate-in fade-in duration-200",
    children: [
      // Desktop Top Segmented Pill Bar (hidden on mobile, visible on desktop)
      a.jsxs("div", {
        className: "hidden md:flex items-center justify-between gap-3 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md p-1.5 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 shadow-xs",
        children: [
          a.jsx("div", {
            className: "flex items-center gap-1",
            children: tabItems.map(t => a.jsxs("button", {
              key: t.id,
              onClick: () => switchTab(t.id),
              className: `flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                currentTab === t.id
                  ? "bg-indigo-600 text-white shadow-sm shadow-indigo-500/25"
                  : "text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-zinc-200 hover:bg-slate-100/60 dark:hover:bg-zinc-800/50"
              }`,
              children: [t.icon("w-4 h-4"), t.label]
            }))
          }),
          a.jsxs("div", {
            className: "flex items-center gap-2",
            children: [
              a.jsx("button", {
                onClick: fetchData,
                className: "p-2 rounded-xl text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 border border-slate-200/60 dark:border-zinc-800 transition active:scale-95",
                title: "刷新全部数据",
                children: Icons.Refresh("w-4 h-4")
              }),
              a.jsxs("button", {
                onClick: () => setQrModal({ open: true, title: "通用全能订阅二维码", url: subUrl }),
                className: "px-3.5 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-xs hover:opacity-95 flex items-center gap-1.5 transition active:scale-95",
                children: [Icons.QrCode("w-3.5 h-3.5"), "订阅导入"]
              })
            ]
          })
        ]
      }),

      // TAB 1: 节点列表 (iOS 极简原生风: 紧凑行列表 + 底部抽屉)
      currentTab === "nodes" && a.jsxs("div", {
        className: "space-y-3",
        children: [
          // Mobile Top Quick Header
          a.jsxs("div", {
            className: "flex items-center justify-between px-1",
            children: [
              a.jsxs("div", {
                children: [
                  a.jsx("h2", { className: "text-lg font-black tracking-tight text-slate-900 dark:text-white", children: "节点管理" }),
                  a.jsxs("p", { className: "text-xs text-slate-500 font-medium", children: [`共 ${nodes.length} 个节点 · 在线 `, a.jsx("span", { className: "text-emerald-600 dark:text-emerald-400 font-bold", children: `${serverStats.singbox_online_count} 台` })] })
                ]
              }),
              a.jsxs("div", {
                className: "flex items-center gap-1.5",
                children: [
                  a.jsxs("button", {
                    onClick: testAllPings,
                    disabled: pinging,
                    className: "px-2.5 py-1.5 text-xs font-semibold rounded-xl bg-slate-100 dark:bg-zinc-800 text-slate-700 dark:text-zinc-200 flex items-center gap-1 active:scale-95 transition",
                    children: [Icons.Zap("w-3.5 h-3.5 text-amber-500"), pinging ? "测速中" : "测速"]
                  }),
                  a.jsxs("button", {
                    onClick: () => setImportModal(true),
                    className: "px-3 py-1.5 text-xs font-bold rounded-xl bg-indigo-600 text-white flex items-center gap-1 shadow-xs active:scale-95 transition",
                    children: [Icons.Plus("w-3.5 h-3.5"), "导入"]
                  })
                ]
              })
            ]
          }),

          // Search & Filter Pill Row
          a.jsxs("div", {
            className: "flex items-center gap-2",
            children: [
              a.jsxs("div", {
                className: "relative flex-1",
                children: [
                  a.jsx("div", { className: "absolute inset-y-0 left-3 flex items-center text-slate-400 pointer-events-none", children: Icons.Search("w-3.5 h-3.5") }),
                  a.jsx("input", {
                    type: "text",
                    placeholder: "搜索节点名称、IP或端口...",
                    value: search,
                    onChange: e => setSearch(e.target.value),
                    className: "w-full pl-9 pr-3 py-2 text-xs bg-white dark:bg-zinc-900 border border-slate-200/80 dark:border-zinc-800 rounded-xl shadow-2xs focus:outline-hidden focus:border-indigo-500 transition"
                  })
                ]
              }),
              a.jsx("div", {
                className: "flex items-center bg-slate-100 dark:bg-zinc-800 p-0.5 rounded-xl text-xs font-semibold shrink-0",
                children: [
                  { id: "all", label: "全部" },
                  { id: "native", label: "自建" },
                  { id: "external", label: "外部" }
                ].map(f => a.jsx("button", {
                  key: f.id,
                  onClick: () => setFilter(f.id),
                  className: `px-2.5 py-1.5 rounded-lg transition ${filter === f.id ? "bg-white dark:bg-zinc-700 text-indigo-600 dark:text-indigo-400 shadow-2xs" : "text-slate-500"}` ,
                  children: f.label
                }))
              })
            ]
          }),

          // iOS Inset Grouped List (圆角分组紧凑列表)
          filteredNodes.length === 0 ? a.jsxs("div", {
            className: "py-16 text-center text-slate-400 bg-white/70 dark:bg-zinc-900/70 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 space-y-1",
            children: [
              a.jsx("p", { className: "text-sm font-medium", children: "暂无节点" }),
              a.jsx("p", { className: "text-xs text-slate-400", children: "点击右上角“导入”快速添加节点" })
            ]
          }) : a.jsx("div", {
            className: "bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 divide-y divide-slate-100 dark:divide-zinc-800/60 overflow-hidden shadow-2xs",
            children: filteredNodes.map(node => {
              const pingVal = pings[node.id];
              const proto = (node.protocol || "vless").toUpperCase();
              const protoBadge = proto === "VLESS" ? "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400" :
                                proto === "HYSTERIA2" ? "bg-purple-500/10 text-purple-600 dark:text-purple-400" :
                                proto === "SHADOWSOCKS" ? "bg-sky-500/10 text-sky-600 dark:text-sky-400" :
                                proto === "TROJAN" ? "bg-amber-500/10 text-amber-600 dark:text-amber-400" : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400";

              return a.jsxs("div", {
                key: node.id,
                onClick: () => setActionNode(node),
                className: `flex items-center justify-between p-3.5 transition-colors cursor-pointer active:bg-slate-50 dark:active:bg-zinc-800/50 ${
                  node.enabled ? "" : "opacity-50"
                }`,
                children: [
                  // Left: Protocol badge + Name & Port
                  a.jsxs("div", {
                    className: "flex items-center gap-3 flex-1 min-w-0 pr-2",
                    children: [
                      a.jsx("div", {
                        className: `w-9 h-9 rounded-xl flex items-center justify-center font-black text-[10px] shrink-0 ${protoBadge}`,
                        children: proto.slice(0, 3)
                      }),
                      a.jsxs("div", {
                        className: "min-w-0 space-y-0.5",
                        children: [
                          a.jsx("p", { className: "font-bold text-xs sm:text-sm text-slate-900 dark:text-zinc-100 truncate", children: node.name }),
                          a.jsxs("p", {
                            className: "text-[11px] text-slate-400 dark:text-zinc-500 font-mono flex items-center gap-1",
                            children: [
                              node.server_ip || node.sni || "外部节点",
                              node.port ? `:${node.port}` : ""
                            ]
                          })
                        ]
                      })
                    ]
                  }),

                  // Right: Latency Capsule + iOS Switch
                  a.jsxs("div", {
                    className: "flex items-center gap-2.5 shrink-0",
                    children: [
                      // Latency Capsule (clickable to ping)
                      a.jsxs("button", {
                        onClick: (e) => { e.stopPropagation(); testNodePing(node); },
                        className: `px-2 py-0.5 rounded-full text-[11px] font-mono font-semibold flex items-center gap-1 border transition active:scale-95 ${
                          pingVal === "pinging" ? "bg-amber-50 dark:bg-amber-950/40 text-amber-600 border-amber-200" :
                          typeof pingVal === "number" ? (pingVal < 100 ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border-emerald-200/60" : pingVal < 250 ? "bg-amber-50 dark:bg-amber-950/40 text-amber-600 border-amber-200" : "bg-rose-50 dark:bg-rose-950/40 text-rose-600 border-rose-200") :
                          "bg-slate-100 dark:bg-zinc-800 text-slate-400 border-transparent hover:border-slate-300"
                        }`,
                        title: "点击单点测速",
                        children: [
                          pingVal === "pinging" ? a.jsx("span", { className: "w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping" }) :
                          typeof pingVal === "number" ? a.jsx("span", { className: `w-1.5 h-1.5 rounded-full ${pingVal < 100 ? "bg-emerald-500" : pingVal < 250 ? "bg-amber-500" : "bg-rose-500"}` }) :
                          a.jsx("span", { className: "w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-zinc-600" }),
                          pingVal === "pinging" ? "测速" :
                          typeof pingVal === "number" ? `${pingVal}ms` : (pingVal || "测速")
                        ]
                      }),

                      // Native iOS-style Switch Toggle
                      a.jsx("button", {
                        onClick: (e) => { e.stopPropagation(); toggleNode(node.id, node.enabled); },
                        className: `relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out ${node.enabled ? "bg-emerald-500" : "bg-slate-300 dark:bg-zinc-700"}`,
                        children: a.jsx("span", {
                          className: `pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md transition duration-200 ease-in-out mt-0.5 ml-0.5 ${node.enabled ? "translate-x-5" : "translate-x-0"}`
                        })
                      })
                    ]
                  })
                ]
              });
            })
          })
        ]
      }),

      // TAB 2: 实时流量监控 (iOS 风格: 双通道大流速胶囊 + 紧凑服务器卡片)
      currentTab === "traffic" && a.jsxs("div", {
        className: "space-y-4",
        children: [
          // Live Dual Speed Hero
          a.jsxs("div", {
            className: "p-4 sm:p-5 rounded-3xl bg-zinc-950 text-white shadow-lg space-y-3.5 border border-zinc-800",
            children: [
              a.jsxs("div", {
                className: "flex items-center justify-between",
                children: [
                  a.jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [
                      a.jsx("span", { className: "w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" }),
                      a.jsx("span", { className: "font-bold text-xs sm:text-sm text-zinc-200", children: "全网动态吞吐速率" })
                    ]
                  }),
                  // Polling speed segmented
                  a.jsx("div", {
                    className: "flex items-center bg-zinc-900 p-0.5 rounded-xl text-xs font-semibold border border-zinc-800",
                    children: [
                      [1000, "1s"],
                      [3000, "3s"],
                      [5000, "5s"]
                    ].map(([ms, l]) => a.jsx("button", {
                      key: ms,
                      onClick: () => setPollInterval(ms),
                      className: `px-2 py-0.5 rounded-lg transition ${pollInterval === ms ? "bg-white text-zinc-950 shadow-xs" : "text-zinc-400 hover:text-white"}`,
                      children: l
                    }))
                  })
                ]
              }),

              // Speeds Grid
              a.jsxs("div", {
                className: "grid grid-cols-2 gap-2.5",
                children: [
                  a.jsxs("div", {
                    className: "bg-zinc-900/80 p-3 rounded-2xl border border-zinc-800/80 space-y-0.5",
                    children: [
                      a.jsx("span", { className: "text-[11px] font-semibold text-emerald-400 flex items-center gap-1", children: "↓ 下行网速" }),
                      a.jsx("p", { className: "text-xl sm:text-2xl font-black font-mono text-emerald-400 tracking-tight", children: `${formatBytes(sumInRate)}/s` })
                    ]
                  }),
                  a.jsxs("div", {
                    className: "bg-zinc-900/80 p-3 rounded-2xl border border-zinc-800/80 space-y-0.5",
                    children: [
                      a.jsx("span", { className: "text-[11px] font-semibold text-sky-400 flex items-center gap-1", children: "↑ 上行网速" }),
                      a.jsx("p", { className: "text-xl sm:text-2xl font-black font-mono text-sky-400 tracking-tight", children: `${formatBytes(sumOutRate)}/s` })
                    ]
                  })
                ]
              }),

              a.jsxs("div", {
                className: "flex items-center justify-between text-xs text-zinc-400 pt-1 border-t border-zinc-900 font-mono",
                children: [
                  a.jsxs("span", { children: ["累计接入消耗: ", a.jsx("strong", { className: "text-white font-bold", children: formatBytes(serverStats.total_traffic) })] }),
                  a.jsxs("button", {
                    onClick: () => resetServerTraffic("all"),
                    className: "text-rose-400 hover:text-rose-300 flex items-center gap-1 transition",
                    children: [Icons.RotateCcw("w-3 h-3"), "全部归零"]
                  })
                ]
              })
            ]
          }),

          // Server Traffic Grouped List
          a.jsx("div", {
            className: "space-y-2.5",
            children: servers.map(srv => {
              const consumed = srv.total_traffic || 0;
              return a.jsxs("div", {
                key: srv.uuid,
                className: "p-3.5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200/80 dark:border-zinc-800/80 shadow-2xs space-y-2.5",
                children: [
                  a.jsxs("div", {
                    className: "flex items-center justify-between",
                    children: [
                      a.jsxs("div", {
                        className: "space-y-0.5",
                        children: [
                          a.jsx("h4", { className: "font-bold text-xs sm:text-sm text-slate-900 dark:text-zinc-100", children: srv.name || srv.host || "服务器" }),
                          a.jsx("p", { className: "text-[11px] text-slate-400 font-mono", children: srv.host || srv.ip })
                        ]
                      }),
                      a.jsxs("div", {
                        className: "text-right space-y-0.5",
                        children: [
                          a.jsxs("span", {
                            className: `inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              srv.singbox_online ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" : "bg-slate-100 text-slate-400"
                            }`,
                            children: [
                              a.jsx("span", { className: `w-1.5 h-1.5 rounded-full ${srv.singbox_online ? "bg-emerald-500 animate-pulse" : "bg-slate-400"}` }),
                              srv.singbox_online ? "在线" : "离线"
                            ]
                          }),
                          a.jsxs("p", { className: "text-xs font-mono font-bold text-indigo-600 dark:text-indigo-400", children: [formatBytes(consumed)] })
                        ]
                      })
                    ]
                  }),

                  // Compact Progress Bar
                  a.jsx("div", {
                    className: "h-1.5 w-full bg-slate-100 dark:bg-zinc-800 rounded-full overflow-hidden",
                    children: a.jsx("div", {
                      className: "h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full",
                      style: { width: `${Math.min(100, Math.max(5, (consumed / (serverStats.total_traffic || 1)) * 100))}%` }
                    })
                  }),

                  // Speeds Footer
                  a.jsxs("div", {
                    className: "flex items-center justify-between text-[11px] font-mono text-slate-500 pt-1 border-t border-slate-100 dark:border-zinc-800/60",
                    children: [
                      a.jsxs("div", {
                        className: "flex items-center gap-2",
                        children: [
                          a.jsxs("span", { className: "text-emerald-600 dark:text-emerald-400 font-bold", children: ["↓ ", formatBytes(srv.in_rate || 0), "/s"] }),
                          a.jsxs("span", { className: "text-sky-600 dark:text-sky-400 font-bold", children: ["↑ ", formatBytes(srv.out_rate || 0), "/s"] })
                        ]
                      }),
                      a.jsxs("button", {
                        onClick: () => resetServerTraffic(srv.uuid),
                        className: "text-slate-400 hover:text-rose-500 flex items-center gap-1",
                        children: [Icons.RotateCcw("w-3 h-3"), "单机归零"]
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
        className: "space-y-4",
        children: [
          // Sub Hub
          a.jsxs("div", {
            className: "p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200/80 dark:border-zinc-800/80 shadow-2xs space-y-3",
            children: [
              a.jsxs("div", {
                className: "flex items-center justify-between",
                children: [
                  a.jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [
                      a.jsx("div", { className: "p-2 rounded-xl bg-indigo-500/10 text-indigo-600", children: Icons.Zap("w-4 h-4") }),
                      a.jsx("h3", { className: "font-bold text-sm text-slate-900 dark:text-white", children: "全能订阅导入" })
                    ]
                  }),
                  a.jsxs("button", {
                    onClick: async () => {
                      if (!confirm("确定要重置订阅 Token 吗？")) return;
                      const r = await fetch("/api/node-mgr/sub/token/reset", { method: "POST" }).then(res => res.json());
                      if (r && r.sub_url) setSubUrl(r.sub_url);
                    },
                    className: "text-xs text-rose-500 font-semibold",
                    children: ["重置 Token"]
                  })
                ]
              }),

              // 3 Links
              a.jsx("div", {
                className: "space-y-2",
                children: [
                  { title: "全协议通用订阅", url: subUrl, desc: "自动识别 Clash / Surge / Sing-box" },
                  { title: "Clash / Mihomo 专用", url: subUrl ? `${subUrl}?clash=1` : "", desc: "一键拉取标准 YAML" },
                  { title: "Base64 订阅", url: subUrl ? `${subUrl}?format=b64` : "", desc: "Shadowrocket / V2Ray" }
                ].map((item, idx) => a.jsxs("div", {
                  key: idx,
                  className: "p-3 rounded-xl bg-slate-50 dark:bg-zinc-800/60 border border-slate-100 dark:border-zinc-800 flex items-center justify-between gap-2",
                  children: [
                    a.jsxs("div", {
                      className: "space-y-0.5 min-w-0 flex-1",
                      children: [
                        a.jsx("p", { className: "font-bold text-xs text-slate-800 dark:text-zinc-200 truncate", children: item.title }),
                        a.jsx("p", { className: "text-[10px] text-slate-400 truncate", children: item.desc })
                      ]
                    }),
                    a.jsxs("div", {
                      className: "flex items-center gap-1 shrink-0",
                      children: [
                        a.jsxs("button", {
                          onClick: () => copyToClipboard(item.url),
                          className: "px-2.5 py-1.5 rounded-lg bg-white dark:bg-zinc-700 text-xs font-semibold text-slate-700 dark:text-zinc-200 border border-slate-200 dark:border-zinc-600 flex items-center gap-1 active:scale-95",
                          children: [Icons.Copy("w-3.5 h-3.5"), "复制"]
                        }),
                        a.jsx("button", {
                          onClick: () => setQrModal({ open: true, title: item.title, url: item.url }),
                          className: "p-1.5 rounded-lg bg-white dark:bg-zinc-700 text-slate-600 dark:text-zinc-300 border border-slate-200 dark:border-zinc-600",
                          title: "二维码",
                          children: Icons.QrCode("w-3.5 h-3.5")
                        })
                      ]
                    })
                  ]
                }))
              })
            ]
          }),

          // Presets
          a.jsxs("div", {
            className: "p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200/80 dark:border-zinc-800/80 shadow-2xs space-y-3",
            children: [
              a.jsx("h3", { className: "font-bold text-sm text-slate-900 dark:text-white", children: "一键分流策略预设" }),
              a.jsx("div", {
                className: "grid grid-cols-2 gap-2",
                children: [
                  { title: "绕过大陆", badge: "推荐", desc: "国内直连，国外走代理", active: true },
                  { title: "全局代理", badge: "全局", desc: "全部流量经节点转发", active: false },
                  { title: "流媒体加速", badge: "专线", desc: "YouTube / Netflix 优先", active: false },
                  { title: "广告拦截", badge: "净化", desc: "屏蔽追踪与广告", active: false }
                ].map((p, idx) => a.jsxs("div", {
                  key: idx,
                  className: `p-3 rounded-xl border transition-all cursor-pointer ${
                    p.active ? "border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/30" : "border-slate-200 dark:border-zinc-800"
                  }`,
                  children: [
                    a.jsxs("div", {
                      className: "flex items-center justify-between",
                      children: [
                        a.jsx("span", { className: "font-bold text-xs text-slate-900 dark:text-zinc-100", children: p.title }),
                        a.jsx("span", { className: `px-1.5 py-0.5 rounded text-[9px] font-bold ${p.active ? "bg-indigo-600 text-white" : "bg-slate-200 text-slate-600"}`, children: p.badge })
                      ]
                    }),
                    a.jsx("p", { className: "text-[10px] text-slate-400 mt-1", children: p.desc })
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
          // TG Card
          a.jsxs("div", {
            className: "p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200/80 dark:border-zinc-800/80 shadow-2xs space-y-3",
            children: [
              a.jsxs("div", {
                className: "flex items-center justify-between",
                children: [
                  a.jsxs("div", {
                    className: "flex items-center gap-2",
                    children: [
                      a.jsx("div", { className: "p-2 rounded-xl bg-sky-500/10 text-sky-600", children: Icons.Send("w-4 h-4") }),
                      a.jsx("h3", { className: "font-bold text-sm text-slate-900 dark:text-white", children: "Telegram 告警机器人" })
                    ]
                  }),
                  a.jsx("span", { className: "px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-600", children: "已连接" })
                ]
              }),
              a.jsxs("div", {
                className: "grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs",
                children: [
                  a.jsx("input", {
                    type: "text",
                    defaultValue: "8731954829:AAG6HlNgKnth8_2yIYAtMyV4gPx_c-I2bJY",
                    id: "tgBotTokenInput",
                    placeholder: "Bot Token",
                    className: "w-full text-xs font-mono bg-slate-50 dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl px-3 py-2"
                  }),
                  a.jsx("input", {
                    type: "text",
                    defaultValue: "791298471",
                    id: "tgChatIdInput",
                    placeholder: "Chat ID",
                    className: "w-full text-xs font-mono bg-slate-50 dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl px-3 py-2"
                  })
                ]
              }),
              a.jsxs("div", {
                className: "flex items-center justify-end gap-2 pt-1",
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
                        if (r && r.ok) alert("测试通知已成功发送至 Telegram！");
                        else alert("推送失败: " + (r.error || "请检查配置"));
                      } catch (err) { alert("测试失败: " + err); }
                    },
                    className: "px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-200 dark:border-zinc-700 text-slate-700 dark:text-zinc-300 flex items-center gap-1 active:scale-95 transition",
                    children: [Icons.Send("w-3.5 h-3.5"), "发送测试"]
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
                    },
                    className: "px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-indigo-600 text-white active:scale-95 transition",
                    children: "保存配置"
                  })
                ]
              })
            ]
          }),

          // 10 Alert Switches (iOS Grouped Style)
          a.jsxs("div", {
            className: "bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 divide-y divide-slate-100 dark:divide-zinc-800/60 overflow-hidden shadow-2xs",
            children: (notifConfig.rules || []).map(rItem => a.jsxs("div", {
              key: rItem.rule_key,
              className: "flex items-center justify-between p-3.5 gap-2",
              children: [
                a.jsxs("div", {
                  className: "space-y-0.5 flex-1 min-w-0 pr-2",
                  children: [
                    a.jsx("p", { className: "font-bold text-xs sm:text-sm text-slate-900 dark:text-zinc-100", children: rItem.name }),
                    a.jsx("p", { className: "text-[11px] text-slate-400 leading-tight", children: rItem.description })
                  ]
                }),
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
                  className: `relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors ${rItem.enabled ? "bg-indigo-600" : "bg-slate-300 dark:bg-zinc-700"}`,
                  children: a.jsx("span", {
                    className: `inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition mt-0.5 ml-0.5 ${rItem.enabled ? "translate-x-4" : "translate-x-0"}`
                  })
                })
              ]
            }))
          })
        ]
      }),

      // ========================================================
      // iOS Bottom Action Sheet (底部上滑抽屉: 点击节点弹窗)
      // ========================================================
      actionNode && a.jsxs("div", {
        className: "fixed inset-0 z-50 flex flex-col justify-end bg-black/50 backdrop-blur-xs animate-in fade-in duration-150 select-none",
        onClick: () => setActionNode(null),
        children: [
          a.jsxs("div", {
            className: "w-full max-w-lg mx-auto bg-white dark:bg-zinc-900 rounded-t-3xl p-5 space-y-4 shadow-2xl border-t border-slate-200 dark:border-zinc-800 animate-in slide-in-from-bottom duration-200 pb-8",
            onClick: e => e.stopPropagation(),
            children: [
              // Top drag pill
              a.jsx("div", { className: "w-10 h-1 bg-slate-300 dark:bg-zinc-700 rounded-full mx-auto" }),

              // Node Header
              a.jsxs("div", {
                className: "flex items-start justify-between gap-2 pt-1",
                children: [
                  a.jsxs("div", {
                    className: "space-y-0.5 min-w-0 flex-1",
                    children: [
                      a.jsx("h3", { className: "font-black text-base text-slate-900 dark:text-white truncate", children: actionNode.name }),
                      a.jsxs("p", { className: "text-xs text-slate-400 font-mono", children: [actionNode.protocol?.toUpperCase(), " · ", actionNode.server_ip || actionNode.sni, actionNode.port ? `:${actionNode.port}` : ""] })
                    ]
                  }),
                  a.jsx("button", { onClick: () => setActionNode(null), className: "p-1 rounded-full text-slate-400 hover:text-slate-600", children: Icons.X("w-5 h-5") })
                ]
              }),

              // Action Buttons List
              a.jsxs("div", {
                className: "space-y-2 pt-2",
                children: [
                  a.jsxs("button", {
                    onClick: () => { copyToClipboard(actionNode.link || ""); setActionNode(null); },
                    className: "w-full py-3 px-4 rounded-2xl bg-slate-100 dark:bg-zinc-800 hover:bg-slate-200 dark:hover:bg-zinc-700 font-bold text-xs sm:text-sm text-slate-800 dark:text-zinc-200 flex items-center justify-between active:scale-[0.99] transition",
                    children: [
                      a.jsxs("span", { className: "flex items-center gap-2.5", children: [Icons.Copy("w-4 h-4 text-indigo-500"), "复制节点分享链接"] }),
                      Icons.ChevronRight("w-4 h-4 text-slate-400")
                    ]
                  }),
                  a.jsxs("button", {
                    onClick: () => { setQrModal({ open: true, title: actionNode.name, url: actionNode.link || "" }); setActionNode(null); },
                    className: "w-full py-3 px-4 rounded-2xl bg-slate-100 dark:bg-zinc-800 hover:bg-slate-200 dark:hover:bg-zinc-700 font-bold text-xs sm:text-sm text-slate-800 dark:text-zinc-200 flex items-center justify-between active:scale-[0.99] transition",
                    children: [
                      a.jsxs("span", { className: "flex items-center gap-2.5", children: [Icons.QrCode("w-4 h-4 text-purple-500"), "查看导入二维码"] }),
                      Icons.ChevronRight("w-4 h-4 text-slate-400")
                    ]
                  }),
                  a.jsxs("button", {
                    onClick: () => { testNodePing(actionNode); setActionNode(null); },
                    className: "w-full py-3 px-4 rounded-2xl bg-slate-100 dark:bg-zinc-800 hover:bg-slate-200 dark:hover:bg-zinc-700 font-bold text-xs sm:text-sm text-slate-800 dark:text-zinc-200 flex items-center justify-between active:scale-[0.99] transition",
                    children: [
                      a.jsxs("span", { className: "flex items-center gap-2.5", children: [Icons.Zap("w-4 h-4 text-amber-500"), "立即单点测速"] }),
                      Icons.ChevronRight("w-4 h-4 text-slate-400")
                    ]
                  }),
                  a.jsxs("button", {
                    onClick: () => deleteNode(actionNode.id),
                    className: "w-full py-3 px-4 rounded-2xl bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 text-rose-600 dark:text-rose-400 font-bold text-xs sm:text-sm flex items-center justify-between active:scale-[0.99] transition",
                    children: [
                      a.jsxs("span", { className: "flex items-center gap-2.5", children: [Icons.Trash("w-4 h-4"), "删除此节点"] }),
                      Icons.ChevronRight("w-4 h-4 text-rose-400")
                    ]
                  })
                ]
              })
            ]
          })
        ]
      }),

      // QR Code Modal
      qrModal.open && a.jsx("div", {
        className: "fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150 select-none",
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
        className: "fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150 select-none",
        onClick: () => setImportModal(false),
        children: a.jsxs("form", {
          onSubmit: importExternalNode,
          className: "bg-white dark:bg-zinc-900 rounded-3xl p-6 max-w-md w-full space-y-4 shadow-2xl border border-slate-200 dark:border-zinc-800",
          onClick: e => e.stopPropagation(),
          children: [
            a.jsxs("div", {
              className: "flex items-center justify-between",
              children: [
                a.jsx("h3", { className: "font-bold text-base text-slate-900 dark:text-white", children: "导入外部节点" }),
                a.jsx("button", { type: "button", onClick: () => setImportModal(false), className: "p-1 rounded-full text-slate-400 hover:text-slate-600", children: Icons.X("w-5 h-5") })
              ]
            }),
            a.jsxs("div", {
              className: "space-y-3 text-xs",
              children: [
                a.jsxs("div", {
                  className: "space-y-1",
                  children: [
                    a.jsx("label", { className: "font-semibold text-slate-700 dark:text-zinc-300", children: "自定义别名 (可选)" }),
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
              children: isSubmitting ? "解析导入中..." : "确认导入"
            })
          ]
        })
      }),

      // ========================================================
      // iOS Thumb-Zone Bottom Tab Bar (手机端常驻底部单手操作栏)
      // ========================================================
      a.jsx("div", {
        className: "fixed bottom-0 inset-x-0 z-40 md:hidden bg-white/85 dark:bg-zinc-950/85 backdrop-blur-xl border-t border-slate-200/80 dark:border-zinc-800/80 px-2 py-1.5 flex items-center justify-around shadow-lg select-none",
        children: tabItems.map(t => {
          const isActive = currentTab === t.id;
          return a.jsxs("button", {
            key: t.id,
            onClick: () => switchTab(t.id),
            className: `flex flex-col items-center justify-center py-1 px-3 rounded-2xl transition-all duration-150 ${
              isActive ? "text-indigo-600 dark:text-indigo-400 font-bold" : "text-slate-400 dark:text-zinc-500 hover:text-slate-600"
            }`,
            children: [
              t.icon(`w-5 h-5 transition-transform duration-150 ${isActive ? "scale-110" : ""}`),
              a.jsx("span", { className: "text-[10px] mt-0.5", children: t.label })
            ]
          });
        })
      })
    ]
  });
}

export { NodeManagerApp as default };
