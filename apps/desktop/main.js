const {
  app,
  BrowserWindow,
  ipcMain,
  shell,
  Menu,
  Tray,
  nativeImage,
  Notification,
  dialog,
} = require("electron");
const path = require("path");
// const Store = require('electron-store'); // ESM-only, switch to dynamic import
const keytar = require("keytar");
let autoUpdater;
try {
  autoUpdater = require("electron-updater").autoUpdater;
} catch (_) {
  autoUpdater = null;
}

// Defer electron-store ESM import until runtime
let Store;
let store;
async function initStore() {
  if (!Store) {
    const mod = await import("electron-store");
    Store = mod.default;
  }
  if (!store) {
    store = new Store({
      name: "builder",
      encryptionKey: process.env.BUILDER_STORE_KEY || undefined,
    });
  }
}

const SERVICE = "BuilderDesktop";
const ACCOUNT = "auth-token";
let cachedToken = "";

async function loadCachedToken() {
  try {
    cachedToken = (await keytar.getPassword(SERVICE, ACCOUNT)) || "";
  } catch {
    cachedToken = "";
  }
}

function injectStyle(win) {
  const css = `
    :root {
      --builder-accent: #0ea5e9; /* sky-500 */
      --builder-bg: #0b1220; /* deep slate */
      --builder-fg: #e5e7eb; /* gray-200 */
    }
    @media (prefers-color-scheme: dark) {
      html, body { background: var(--builder-bg) !important; }
      a { color: var(--builder-accent) !important; }
      ::-webkit-scrollbar { width: 10px; height: 10px; }
      ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 8px; }
      ::-webkit-scrollbar-track { background: #0b1220; }
    }
    .builder-fab { position: fixed; right: 20px; bottom: 24px; z-index: 2147483000; }
    .builder-fab button { background: linear-gradient(135deg, #0f172a 0%, #0ea5e9 100%);
      color: white; width: 56px; height: 56px; border-radius: 9999px; border: none; box-shadow: 0 10px 25px rgba(0,0,0,.35);
      font-size: 20px; cursor: pointer; transition: transform .12s ease; }
    .builder-fab button:hover { transform: translateY(-1px) scale(1.02); }
    .builder-modal { position: fixed; inset: 0; background: rgba(2,6,23,.55); display: flex; align-items: center; justify-content: center; z-index: 2147483640; }
    .builder-card { width: min(560px, 92vw); background: #0f172a; color: #e5e7eb; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; box-shadow: 0 20px 60px rgba(0,0,0,.5); }
    .builder-card h3 { margin: 0 0 10px; font-weight: 600; }
    .builder-card input { width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid #334155; background: #0b1220; color: #e5e7eb; }
    .builder-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 12px; }
    .builder-btn { padding: 8px 12px; border-radius: 8px; border: 1px solid #334155; background: #111827; color: #e5e7eb; cursor: pointer; }
    .builder-btn.primary { background: #0ea5e9; border-color: #0284c7; color: #031018; font-weight: 600; }
    .builder-toast { position: fixed; right: 20px; bottom: 96px; background: #0f172a; color: #e5e7eb; border: 1px solid #1f2937; border-radius: 10px; padding: 10px 12px; z-index: 2147483646; box-shadow: 0 10px 35px rgba(0,0,0,.4);}
  `;
  win.webContents.insertCSS(css).catch(() => {});
}

function injectFab(win) {
  const js = `
    (function(){
      try {
        if (document.querySelector('.builder-fab')) return;
        const fab = document.createElement('div'); fab.className='builder-fab';
        const btn = document.createElement('button'); btn.title='Quick Research'; btn.textContent='⚡';
        fab.appendChild(btn); document.body.appendChild(fab);
        const showToast = (msg) => { const t = document.createElement('div'); t.className='builder-toast'; t.textContent = msg; document.body.appendChild(t); setTimeout(()=>{ t.remove(); }, 3000); };
        const showModal = () => {
          const overlay = document.createElement('div'); overlay.className='builder-modal';
          const card = document.createElement('div'); card.className='builder-card';
          const h = document.createElement('h3'); h.textContent = 'Quick Research';
          const p = document.createElement('p'); p.textContent = 'Enter a topic to research using your local agents.'; p.style.margin='0 0 8px'; p.style.opacity='.85';
          const input = document.createElement('input'); input.placeholder='e.g. AI-driven investigation tooling';
          const actions = document.createElement('div'); actions.className='builder-actions';
          const cancel = document.createElement('button'); cancel.className='builder-btn'; cancel.textContent='Cancel';
          const run = document.createElement('button'); run.className='builder-btn primary'; run.textContent='Run';
          actions.appendChild(cancel); actions.appendChild(run);
          card.appendChild(h); card.appendChild(p); card.appendChild(input); card.appendChild(actions); overlay.appendChild(card); document.body.appendChild(overlay);
          const close = ()=> overlay.remove(); cancel.addEventListener('click', close);
          run.addEventListener('click', async ()=>{
            const topic = String(input.value||'').trim(); if(!topic){ input.focus(); return; }
            try {
              const res = await (window.builder?.quickResearch ? window.builder.quickResearch(topic) : Promise.resolve({error:'bridge_unavailable'}));
              if(res?.status==='queued' || res?.status==='completed'){ showToast('Research started'); } else { showToast('Queued'); }
            } catch(e){ showToast('Failed: '+String(e)); }
            close();
          });
        };
        btn.addEventListener('click', showModal);
      } catch (e) { /* no-op */ }
    })();
  `;
  win.webContents.executeJavaScript(js).catch(() => {});
}

function injectControlPanel(win) {
  const js =
    `
    (function(){
      try {
        if (document.querySelector('.builder-panel')) return;
        const panel = document.createElement('div');
        panel.className='builder-panel';
        panel.innerHTML = ` +
    "`" +
    `
          <style>
            .builder-panel { position: fixed; top: 0; right: 0; height: 100vh; width: 380px; background: #0f172a; color: #e5e7eb; border-left: 1px solid #1f2937; z-index: 2147483645; box-shadow: -8px 0 30px rgba(0,0,0,.35); display: flex; flex-direction: column; }
            .builder-panel header { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-bottom: 1px solid #1f2937; }
            .builder-panel header h3 { margin: 0; font-weight: 600; }
            .builder-panel .body { padding: 12px 14px; gap: 10px; display: flex; flex-direction: column; }
            .builder-panel input, .builder-panel textarea { width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid #334155; background: #0b1220; color: #e5e7eb; }
            .builder-row { display: flex; gap: 8px; }
            .builder-btn { padding: 8px 12px; border-radius: 8px; border: 1px solid #334155; background: #111827; color: #e5e7eb; cursor: pointer; }
            .builder-btn.primary { background: #0ea5e9; border-color: #0284c7; color: #031018; font-weight: 600; }
            .builder-pill { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; background: #0b1220; border: 1px solid #334155; color: #93c5fd; border-radius: 999px; padding: 4px 8px; }
            .builder-muted { color: #9ca3af; font-size: 12px; }
          </style>
          <header>
            <h3>Builder Control</h3>
            <button class="builder-btn" id="builder-close">Close</button>
          </header>
          <div class="body">
            <div>
              <div class="builder-muted">Ask an agent</div>
              <div class="builder-row">
                <input id="agent-goal" placeholder="e.g. plan an osint autopilot" />
                <button class="builder-btn primary" id="agent-run">Run</button>
              </div>
              <textarea id="agent-out" rows="4" readonly placeholder="agent output will appear here"></textarea>
            </div>
            <div>
              <div class="builder-muted">Quick research</div>
              <div class="builder-row">
                <input id="research-topic" placeholder="e.g. digital forensics timeline" />
                <button class="builder-btn primary" id="research-run">Run</button>
              </div>
              <div><span class="builder-muted">Task:</span> <span class="builder-pill" id="research-task">—</span></div>
              <textarea id="research-out" rows="6" readonly placeholder="research result/status"></textarea>
            </div>
          </div>
        ` +
    "`" +
    `;
        document.body.appendChild(panel);
        const $ = (id)=>panel.querySelector(id);
        $('#builder-close').addEventListener('click', ()=> panel.remove());
        $('#agent-run').addEventListener('click', async ()=>{
          const goal = String($('#agent-goal').value||'').trim(); if(!goal) return;
          try {
            const res = await (window.builder?.runAgent ? window.builder.runAgent(goal, 'planner') : Promise.resolve({error:'bridge_unavailable'}));
            $('#agent-out').value = JSON.stringify(res, null, 2);
          } catch (e) { $('#agent-out').value = String(e); }
        });
        $('#research-run').addEventListener('click', async ()=>{
          const topic = String($('#research-topic').value||'').trim(); if(!topic) return;
          $('#research-out').value = '';
          try {
            const res = await (window.builder?.runResearch ? window.builder.runResearch(topic) : Promise.resolve({error:'bridge_unavailable'}));
            const taskId = res?.task_id || '';
            $('#research-task').textContent = taskId || '—';
            $('#research-out').value = JSON.stringify(res, null, 2);
            if (taskId && window.builder?.getPersonalRun) {
              let tries = 0;
              const tick = async () => {
                tries++;
                try {
                  const st = await window.builder.getPersonalRun(taskId);
                  $('#research-out').value = JSON.stringify(st, null, 2);
                  if (st?.status === 'completed' || st?.status === 'error') return;
                } catch {}
                if (tries < 120) setTimeout(tick, 1000);
              };
              setTimeout(tick, 1000);
            }
          } catch (e) { $('#research-out').value = String(e); }
        });
      } catch (e) { /* no-op */ }
    })();
  `;
  win.webContents.executeJavaScript(js).catch(() => {});
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    title: "Builder Desktop",
    titleBarStyle: "hiddenInset",
    backgroundColor: "#0b1220",
    trafficLightPosition: { x: 12, y: 12 },
    ...(process.platform === "darwin"
      ? {
          titleBarOverlay: {
            color: "#0b1220",
            symbolColor: "#93c5fd",
            height: 34,
          },
        }
      : {}),
  });
  const webUrl = process.env.WEB_URL || "http://127.0.0.1:3000";
  win.loadURL(webUrl);
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("did-finish-load", () => {
    injectStyle(win);
    injectFab(win);
  });

  // Inject X-API-Key for API requests made by the web UI
  const ses = win.webContents.session;
  const apiBase = (process.env.API_URL || "http://127.0.0.1:8001").replace(
    /\/$/,
    "",
  );
  ses.webRequest.onBeforeSendHeaders((details, callback) => {
    try {
      if (details.url.startsWith(apiBase)) {
        const headers = { ...details.requestHeaders };
        const key = cachedToken || process.env.INTERNAL_API_KEY || "";
        if (key) headers["X-API-Key"] = key;
        callback({ requestHeaders: headers });
        return;
      }
    } catch {}
    callback({ requestHeaders: details.requestHeaders });
  });

  const menu = Menu.buildFromTemplate([
    ...(process.platform === "darwin"
      ? [
          {
            label: app.name,
            submenu: [
              { role: "about" },
              { type: "separator" },
              { role: "quit" },
            ],
          },
        ]
      : []),
    {
      label: "Navigate",
      submenu: [
        {
          label: "Personal",
          click: () =>
            win.loadURL(
              (process.env.WEB_URL || "http://127.0.0.1:3000") + "/personal",
            ),
        },
        {
          label: "Investigations",
          click: () =>
            win.loadURL(
              (process.env.WEB_URL || "http://127.0.0.1:3000") +
                "/investigations",
            ),
        },
        {
          label: "Dashboard",
          click: () =>
            win.loadURL(
              (process.env.WEB_URL || "http://127.0.0.1:3000") + "/dashboard",
            ),
        },
        {
          label: "Marketplace",
          click: () =>
            win.loadURL(
              (process.env.WEB_URL || "http://127.0.0.1:3000") + "/marketplace",
            ),
        },
        {
          label: "Self-Build",
          click: () =>
            win.loadURL(
              (process.env.WEB_URL || "http://127.0.0.1:3000") +
                "/admin/self-build",
            ),
        },
      ],
    },
    {
      label: "Actions",
      submenu: [
        {
          label: "Quick Research…",
          accelerator: "CmdOrCtrl+K",
          click: () => injectFab(win),
        },
        {
          label: "Open Control Panel",
          accelerator: "CmdOrCtrl+Shift+K",
          click: () => injectControlPanel(win),
        },
        {
          label: "Expand Coverage (sync)",
          click: async () => {
            const base = process.env.API_URL || "http://127.0.0.1:8001";
            const keyFromKeychain =
              cachedToken ||
              (await keytar.getPassword(SERVICE, ACCOUNT).catch(() => ""));
            const key = keyFromKeychain || process.env.INTERNAL_API_KEY || "";
            try {
              const res = await fetch(`${base}/assistant/expand_coverage`, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  ...(key ? { "X-API-Key": key } : {}),
                },
                body: JSON.stringify({
                  topics: [
                    "digital forensics timeline",
                    "apt tracking",
                    "insurance fraud signals",
                  ],
                }),
              });
              const json = await res.json();
              win.webContents
                .executeJavaScript(
                  `(function(){ const t=document.createElement('div'); t.className='builder-toast'; t.textContent='Expand: ${'${JSON.stringify(json).replace(/`/g, "\\`")'}'; document.body.appendChild(t); setTimeout(()=>t.remove(), 3500); })();`,
                )
                .catch(() => {});
            } catch (e) {
              win.webContents
                .executeJavaScript(
                  `(function(){ const t=document.createElement('div'); t.className='builder-toast'; t.textContent='Expand failed: ${'${String(e).replace(/`/g, "\\`")'}'; document.body.appendChild(t); setTimeout(()=>t.remove(), 3500); })();`,
                )
                .catch(() => {});
            }
          },
        },
        {
          label: "Open Prometheus",
          click: () => shell.openExternal("http://127.0.0.1:9090"),
        },
        {
          label: "Open Grafana",
          click: () => shell.openExternal("http://127.0.0.1:3001"),
        },
        { type: "separator" },
        { role: "reload" },
        { role: "toggleDevTools" },
      ],
    },
    { label: "Window", role: "windowMenu" },
  ]);
  Menu.setApplicationMenu(menu);

  try {
    const icon = nativeImage.createFromPath(
      path.join(__dirname, "iconTemplate.png"),
    );
    const tray = new Tray(icon.isEmpty() ? undefined : icon);
    const ctx = Menu.buildFromTemplate([
      {
        label: "Open",
        click: () => {
          if (win.isMinimized()) win.restore();
          win.show();
        },
      },
      {
        label: "Expand Coverage",
        click: () => win.webContents.send("tray-expand"),
      },
      { type: "separator" },
      { label: "Quit", click: () => app.quit() },
    ]);
    tray.setToolTip("Builder Desktop");
    tray.setContextMenu(ctx);
  } catch {}
}

app.whenReady().then(async () => {
  await initStore();
  await loadCachedToken();
  try {
    if (autoUpdater) {
      const feedUrl = process.env.UPDATE_FEED_URL || "";
      if (feedUrl) {
        autoUpdater.setFeedURL({ url: feedUrl });
      }
      autoUpdater.autoDownload = true;
      autoUpdater.on("error", () => {});
      autoUpdater.on("update-available", () => {
        new Notification({
          title: "Update Available",
          body: "Downloading in background…",
        }).show();
      });
      autoUpdater.on("update-downloaded", () => {
        new Notification({
          title: "Update Ready",
          body: "Will install on quit",
        }).show();
      });
      setTimeout(() => {
        try {
          autoUpdater.checkForUpdatesAndNotify();
        } catch {}
      }, 3000);
    }
  } catch {}
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

ipcMain.handle("quick-research", async (_evt, topic) => {
  const base = process.env.API_URL || "http://127.0.0.1:8001";
  const token =
    cachedToken || (await keytar.getPassword(SERVICE, ACCOUNT).catch(() => ""));
  try {
    const res = await fetch(`${base}/personal/run/research_assistant`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "X-API-Key": token } : {}),
      },
      body: JSON.stringify({ topic: String(topic || "") }),
    });
    return await res.json();
  } catch (e) {
    return { error: String(e) };
  }
});

ipcMain.handle("run-research", async (_evt, topic) => {
  const base = process.env.API_URL || "http://127.0.0.1:8001";
  const token =
    cachedToken || (await keytar.getPassword(SERVICE, ACCOUNT).catch(() => ""));
  try {
    const res = await fetch(`${base}/personal/run/research_assistant`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "X-API-Key": token } : {}),
      },
      body: JSON.stringify({ topic: String(topic || "") }),
    });
    return await res.json();
  } catch (e) {
    return { error: String(e) };
  }
});

ipcMain.handle("get-personal-run", async (_evt, taskId) => {
  const base = process.env.API_URL || "http://127.0.0.1:8001";
  const token =
    cachedToken || (await keytar.getPassword(SERVICE, ACCOUNT).catch(() => ""));
  try {
    const r = await fetch(
      `${base}/personal/result/${encodeURIComponent(String(taskId))}`,
      { headers: { ...(token ? { "X-API-Key": token } : {}) } },
    );
    return await r.json();
  } catch (e) {
    return { error: String(e) };
  }
});

ipcMain.handle("run-agent", async (_evt, goal, agent) => {
  const base = process.env.API_URL || "http://127.0.0.1:8001";
  const token =
    cachedToken || (await keytar.getPassword(SERVICE, ACCOUNT).catch(() => ""));
  try {
    const r = await fetch(`${base}/ai/agents/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "X-API-Key": token } : {}),
      },
      body: JSON.stringify({
        goal: String(goal || ""),
        agent: String(agent || "planner"),
        context: {},
      }),
    });
    return await r.json();
  } catch (e) {
    return { error: String(e) };
  }
});

ipcMain.handle("expand-coverage", async (_evt, topics) => {
  const base = process.env.API_URL || "http://127.0.0.1:8001";
  const key =
    cachedToken ||
    (await keytar.getPassword(SERVICE, ACCOUNT).catch(() => "")) ||
    process.env.INTERNAL_API_KEY ||
    "";
  try {
    const r = await fetch(`${base}/assistant/expand_coverage`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(key ? { "X-API-Key": key } : {}),
      },
      body: JSON.stringify({ topics: Array.isArray(topics) ? topics : [] }),
    });
    return await r.json();
  } catch (e) {
    return { error: String(e) };
  }
});

ipcMain.handle("auth-sign-in", async (_evt, { email, password, remember }) => {
  const base = process.env.API_URL || "http://127.0.0.1:8001";
  try {
    const res = await fetch(`${base}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        username: String(email || ""),
        password: String(password || ""),
      }),
    });
    if (!res.ok) {
      return { ok: false, error: `Login failed (${res.status})` };
    }
    const json = await res.json();
    const token = json?.access_token || "";
    if (!token) return { ok: false, error: "No token returned" };
    await keytar.setPassword(SERVICE, ACCOUNT, token);
    cachedToken = token;
    if (remember) store.set("remember", true);
    else store.delete("remember");
    new Notification({
      title: "Signed In",
      body: "Authentication successful",
    }).show();
    return { ok: true };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});

ipcMain.handle("auth-sign-out", async () => {
  try {
    await keytar.deletePassword(SERVICE, ACCOUNT);
    cachedToken = "";
    store.delete("remember");
    new Notification({ title: "Signed Out", body: "Session cleared" }).show();
    return { ok: true };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});

ipcMain.handle("auth-get", async () => {
  const token =
    cachedToken || (await keytar.getPassword(SERVICE, ACCOUNT).catch(() => ""));
  return { remembered: !!store.get("remember"), hasToken: !!token };
});

ipcMain.handle("auth-set-api-key", async (_evt, { key, remember }) => {
  try {
    if (typeof key !== "string" || !key.trim())
      return { ok: false, error: "Empty key" };
    await keytar.setPassword(SERVICE, ACCOUNT, key.trim());
    cachedToken = key.trim();
    if (remember) store.set("remember", true);
    else store.delete("remember");
    new Notification({
      title: "API Key Stored",
      body: "Key saved to secure storage",
    }).show();
    return { ok: true };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});

ipcMain.handle("auth-clear-api-key", async () => {
  try {
    await keytar.deletePassword(SERVICE, ACCOUNT);
    cachedToken = "";
    store.delete("remember");
    return { ok: true };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});

ipcMain.handle("auth-get-api-key-status", async () => {
  const token =
    cachedToken || (await keytar.getPassword(SERVICE, ACCOUNT).catch(() => ""));
  return { hasKey: !!token };
});

ipcMain.handle("finance-upload-csv", async (_evt) => {
  const base = process.env.API_URL || "http://127.0.0.1:8001";
  const key =
    cachedToken ||
    (await keytar.getPassword(SERVICE, ACCOUNT).catch(() => "")) ||
    process.env.INTERNAL_API_KEY ||
    "";
  const win = BrowserWindow.getFocusedWindow();
  const res = await dialog.showOpenDialog(win || null, {
    properties: ["openFile"],
    filters: [{ name: "CSV", extensions: ["csv"] }],
  });
  if (res.canceled || !res.filePaths[0])
    return { ok: false, error: "cancelled" };
  try {
    const filepath = res.filePaths[0];
    const fs = require("fs");
    const data = await fs.promises.readFile(filepath);
    const form = new (require("form-data"))();
    form.append("file", data, {
      filename: require("path").basename(filepath),
      contentType: "text/csv",
    });
    const headers = {
      ...(key ? { "X-API-Key": key } : {}),
      ...form.getHeaders(),
    };
    const r = await fetch(`${base}/personal/finance/import_csv`, {
      method: "POST",
      headers,
      body: form,
    });
    const json = await r.json();
    if (!r.ok) return { ok: false, error: JSON.stringify(json) };
    new Notification({
      title: "Finance CSV Imported",
      body: `Parsed ${json.parsed || 0} rows`,
    }).show();
    return { ok: true, result: json };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});
