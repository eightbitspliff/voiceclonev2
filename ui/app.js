/* VoiceClone v2 – Oberflächenlogik */
"use strict";

// ------------------------------------------------------------------ Icons
const ICONS = {
  wave: '<path d="M2 12h2M6 8v8M10 4v16M14 7v10M18 10v4M22 12h0"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  gear: '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
  moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9z"/>',
  monitor: '<rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8M12 17v4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  play: '<path d="M7 4.5v15a1 1 0 0 0 1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z" fill="currentColor" stroke="none"/>',
  pause: '<rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor" stroke="none"/><rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor" stroke="none"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
  folder: '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
  sliders: '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  trash: '<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
  edit: '<path d="M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
  mic: '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3"/>',
  file: '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
  sparkle: '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>',
  speak: '<path d="M11 5 6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 0 1 0 7.07M19.07 4.93a10 10 0 0 1 0 14.14"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>',
  alert: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>',
};
function iconSvg(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[name] || ""}</svg>`;
}
function hydrateIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((el) => {
    if (!el.firstChild) el.innerHTML = iconSvg(el.dataset.icon);
  });
}
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtTime = (s) => { s = Math.max(0, Math.round(s || 0)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ------------------------------------------------------------------ API
async function api(path, opts = {}) {
  const init = { method: opts.method || "GET", headers: {} };
  if (opts.form) init.body = opts.form;
  else if (opts.body !== undefined) { init.body = JSON.stringify(opts.body); init.headers["Content-Type"] = "application/json"; }
  const res = await fetch(path, init);
  let data = null;
  try { data = await res.json(); } catch (e) { /* leer */ }
  if (!res.ok) throw new Error((data && data.detail) || `Fehler ${res.status}`);
  return data;
}
async function pollJob(job, onUpdate) {
  while (true) {
    job = await api(`/api/jobs/${job.id}`);
    onUpdate && onUpdate(job);
    if (job.status !== "running") return job;
    await sleep(400);
  }
}

// ------------------------------------------------------------------ Toasts
function toast(msg, type = "info", ms = 4200) {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span data-icon="${type === "success" ? "check" : type === "error" ? "alert" : "info"}"></span><div>${esc(msg)}</div>`;
  hydrateIcons(el);
  $("#toasts").appendChild(el);
  setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 300); }, ms);
}

// ------------------------------------------------------------------ Dialoge
function confirmDialog(title, text, okLabel = "Löschen") {
  const dlg = $("#confirmDialog");
  $("#confirmTitle").textContent = title;
  $("#confirmText").textContent = text;
  dlg.querySelector('button[value="ok"]').textContent = okLabel;
  dlg.returnValue = "";
  dlg.showModal();
  return new Promise((resolve) => dlg.addEventListener("close", () => resolve(dlg.returnValue === "ok"), { once: true }));
}

// ------------------------------------------------------------------ Theme
const mq = matchMedia("(prefers-color-scheme: dark)");
let settings = {};
function applyTheme(pref) {
  const dark = pref === "dark" || (pref === "system" && mq.matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  $("#themeLabel").textContent = dark ? "Dark Mode" : "Light Mode";
  $$("#themeSeg button").forEach((b) => b.classList.toggle("active", b.dataset.value === pref));
  try { localStorage.setItem("vc-theme", dark ? "dark" : "light"); } catch (e) { /* ignorieren */ }
  Player.redrawAll();
}
async function setTheme(pref) {
  settings.theme = pref;
  applyTheme(pref);
  try { await api("/api/settings", { method: "PUT", body: { theme: pref } }); } catch (e) { /* ignorieren */ }
}
mq.addEventListener("change", () => settings.theme === "system" && applyTheme("system"));
$("#themeToggle").addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
$$("#themeSeg button").forEach((b) => b.addEventListener("click", () => setTheme(b.dataset.value)));

// ------------------------------------------------------------------ Navigation
function showPage(name) {
  $$(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.page === name));
  $$(".page").forEach((p) => p.classList.toggle("active", p.id === `page-${name}`));
  if (name === "history") loadHistory();
  if (name === "settings") loadDevices();
  $(".content").scrollTop = 0;
}
$$(".nav-item").forEach((b) => b.addEventListener("click", () => showPage(b.dataset.page)));
$$("[data-goto]").forEach((b) => b.addEventListener("click", () => { showPage(b.dataset.goto); openCreate(); }));
$$("[data-folder]").forEach((b) => b.addEventListener("click", () => api(`/api/open-folder/${b.dataset.folder}`, { method: "POST" }).catch((e) => toast(e.message, "error"))));

// ------------------------------------------------------------------ Player mit Wellenform
const audio = new Audio();
class Player {
  static all = new Set();
  static current = null;
  constructor(container, src, peaks = [], { duration = 0 } = {}) {
    this.src = src;
    this.peaks = peaks && peaks.length ? peaks : null;
    this.duration = duration;
    this.progress = 0;
    container.innerHTML = `<button class="play-btn" title="Abspielen"><span data-icon="play"></span></button>
      ${this.peaks ? '<canvas class="wave"></canvas>' : '<div class="spacer"></div>'}
      <span class="p-time">${duration ? fmtTime(duration) : ""}</span>`;
    hydrateIcons(container);
    this.btn = container.querySelector(".play-btn");
    this.canvas = container.querySelector("canvas");
    this.timeEl = container.querySelector(".p-time");
    this.btn.addEventListener("click", () => this.toggle());
    if (this.canvas) {
      this.canvas.addEventListener("click", (e) => {
        const r = this.canvas.getBoundingClientRect();
        this.seek((e.clientX - r.left) / r.width);
      });
      new ResizeObserver(() => this.draw()).observe(this.canvas);
    }
    Player.all.add(this);
    this.draw();
  }
  static redrawAll() { Player.all.forEach((p) => (!p.canvas || !p.canvas.isConnected ? Player.all.delete(p) : p.draw())); }
  get playing() { return Player.current === this && !audio.paused; }
  toggle() {
    if (Player.current === this) { audio.paused ? audio.play() : audio.pause(); return; }
    if (Player.current) Player.current.reset();
    Player.current = this;
    audio.src = this.src;
    audio.play().catch((e) => toast(`Wiedergabe fehlgeschlagen: ${e.message}`, "error"));
  }
  seek(frac) {
    if (Player.current !== this) { this.toggle(); audio.addEventListener("loadedmetadata", () => { audio.currentTime = frac * audio.duration; }, { once: true }); return; }
    if (audio.duration) audio.currentTime = frac * audio.duration;
  }
  reset() { this.progress = 0; this.setIcon(false); this.draw(); if (this.duration) this.timeEl.textContent = fmtTime(this.duration); }
  setIcon(playing) { const i = this.btn.querySelector("[data-icon]"); i.dataset.icon = playing ? "pause" : "play"; i.innerHTML = iconSvg(i.dataset.icon); }
  update() {
    this.setIcon(!audio.paused);
    if (audio.duration) {
      this.duration = audio.duration;
      this.progress = audio.currentTime / audio.duration;
      this.timeEl.textContent = `${fmtTime(audio.currentTime)} / ${fmtTime(audio.duration)}`;
    }
    this.draw();
  }
  draw() {
    const c = this.canvas;
    if (!c || !this.peaks) return;
    const dpr = window.devicePixelRatio || 1;
    const w = c.clientWidth, h = c.clientHeight;
    if (!w || !h) return;
    c.width = w * dpr; c.height = h * dpr;
    const ctx = c.getContext("2d");
    ctx.scale(dpr, dpr);
    const css = getComputedStyle(document.documentElement);
    const base = css.getPropertyValue("--wave").trim();
    const grad = ctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, css.getPropertyValue("--accent").trim());
    grad.addColorStop(1, css.getPropertyValue("--accent-2").trim());
    const n = this.peaks.length, bw = w / n, gap = Math.max(1, bw * 0.35);
    for (let i = 0; i < n; i++) {
      const v = Math.max(0.06, this.peaks[i]);
      const bh = v * (h - 4);
      ctx.fillStyle = i / n < this.progress ? grad : base;
      const x = i * bw, y = (h - bh) / 2, ww = Math.max(1, bw - gap);
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(x, y, ww, bh, ww / 2); else ctx.rect(x, y, ww, bh);
      ctx.fill();
    }
  }
}
["timeupdate", "play", "pause", "loadedmetadata"].forEach((ev) => audio.addEventListener(ev, () => Player.current && Player.current.update()));
audio.addEventListener("ended", () => { if (Player.current) { Player.current.reset(); Player.current = null; } });
function stopAudio() { audio.pause(); if (Player.current) { Player.current.reset(); Player.current = null; } }

// ------------------------------------------------------------------ Modellstatus
let statusTimer = null;
async function refreshStatus() {
  try {
    const s = await api("/api/status");
    lastStatus = s;
    const q = s.qwen || {};
    const useQwen = currentEngine === "qwen";
    const st = useQwen ? (q.installed ? q.state : "idle") : s.state;
    const msg = useQwen ? (q.installed ? q.message : "Qwen3-TTS ist noch nicht installiert") : s.message;
    const el = $("#modelStatus");
    el.className = `model-status ${st}`;
    const titles = { idle: "Modell nicht geladen", loading: "Modell lädt …", ready: "Modell bereit", error: "Modellfehler" };
    $("#msTitle").textContent = titles[st] || "Modell";
    const dev = s.gpu ? s.gpu : s.device ? (s.device.startsWith("cuda") ? "Grafikkarte" : s.device.toUpperCase()) : "";
    const name = useQwen ? "Qwen3-TTS" : "VoxCPM2";
    $("#msSub").textContent = st === "ready" ? `${name} · ${dev || "Grafikkarte"}${!useQwen && s.compiled ? " · ⚡ beschleunigt" : ""}`
      : st === "loading" ? (useQwen ? "Erster Start: Download ca. 4,5 GB" : "Erster Start: Download ca. 5 GB")
        : useQwen && st === "idle" ? (q.installed ? "Lädt beim ersten Sprechen" : "Nicht installiert") : msg;
    renderHardware(s);
    renderQwen(q);
    updateEngineUi();
    el.title = msg;
    $("#infoVersion").textContent = `VoiceClone ${s.version} · VoxCPM2${q.installed ? " + Qwen3-TTS" : ""}`;
    $("#infoDevice").textContent = st === "ready" ? `Läuft auf: ${s.gpu || s.device || dev}` : titles[st];
    clearTimeout(statusTimer);
    const busy = st === "loading" || (q.install && q.install.state === "running");
    statusTimer = setTimeout(refreshStatus, busy ? 2000 : 15000);
  } catch (e) {
    clearTimeout(statusTimer);
    statusTimer = setTimeout(refreshStatus, 3000);
  }
}
$("#modelStatus").addEventListener("click", async () => {
  if (currentEngine === "qwen") { if (!(lastStatus.qwen || {}).installed) showPage("settings"); return; }
  if ($("#modelStatus").classList.contains("error") || $("#modelStatus").classList.contains("idle")) {
    await api("/api/model/load", { method: "POST" }); refreshStatus();
  }
});

// ------------------------------------------------------------------ Stimmen
let voices = [];
let selectedVoice = "";
const AVATAR_COLORS = [["#6d5efc", "#9b5cf6"], ["#ec4899", "#f97316"], ["#0ea5e9", "#22d3ee"], ["#10b981", "#84cc16"], ["#f59e0b", "#ef4444"], ["#8b5cf6", "#ec4899"], ["#14b8a6", "#3b82f6"]];
function avatar(name, cls = "") {
  let h = 0; for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const [a1, a2] = AVATAR_COLORS[h % AVATAR_COLORS.length];
  const initials = name.split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase();
  return `<span class="avatar ${cls}" style="--a1:${a1};--a2:${a2}">${esc(initials)}</span>`;
}
const vUrl = (name) => `/api/voices/${encodeURIComponent(name)}/audio`;

async function loadVoices() {
  try { voices = await api("/api/voices"); } catch (e) { toast(e.message, "error"); voices = []; }
  if (selectedVoice && !voices.some((v) => v.name === selectedVoice)) selectedVoice = "";
  if (!selectedVoice && voices.length && !localStorage.getItem("vc-voice-chosen")) selectedVoice = voices[0].name;
  $("#voiceCount").textContent = voices.length;
  renderPicker();
  renderVoiceGrid();
}

function renderPicker() {
  const items = [`<button class="vp-item ${selectedVoice ? "" : "active"}" data-voice="">
      <span class="avatar default"><span data-icon="user"></span></span>
      <span><div class="vp-name">Standardstimme</div><div class="vp-sub">ohne Klonen</div></span></button>`];
  for (const v of voices) {
    items.push(`<button class="vp-item ${v.name === selectedVoice ? "active" : ""}" data-voice="${esc(v.name)}">
      ${avatar(v.name)}<span><div class="vp-name">${esc(v.name)}</div><div class="vp-sub">${v.duration.toFixed(0)} s Referenz${v.transcript_trusted ? " · Transkript" : ""}</div></span></button>`);
  }
  $("#voicePicker").innerHTML = items.join("");
  hydrateIcons($("#voicePicker"));
  $$("#voicePicker .vp-item").forEach((b) => b.addEventListener("click", () => {
    selectedVoice = b.dataset.voice;
    try { localStorage.setItem("vc-voice-chosen", "1"); } catch (e) { /* ignorieren */ }
    renderPicker();
  }));
  updateEngineUi();
}

// ------------------------------------------------------------------ Modellwahl
let currentEngine = "voxcpm";
let lastStatus = {};
function updateEngineUi() {
  const qwen = currentEngine === "qwen";
  $$("#engineSeg button").forEach((b) => b.classList.toggle("active", b.dataset.value === currentEngine));
  $("#styleField").classList.toggle("hidden", qwen);
  $$(".voxcpm-only").forEach((e) => e.classList.toggle("hidden", qwen));
  $$(".qwen-only").forEach((e) => e.classList.toggle("hidden", !qwen));
  const hint = $("#engineHint");
  const q = lastStatus.qwen || {};
  let text = "", warn = false;
  if (qwen) {
    if (!q.installed) { text = q.install && q.install.state === "running" ? "Wird gerade installiert …" : "Noch nicht installiert – unter Einstellungen mit einem Klick einrichten."; warn = !(q.install && q.install.state === "running"); }
    else if (!selectedVoice) { text = "Braucht eine geklonte Stimme."; warn = true; }
    else text = "24 kHz · 1.7B · eigener Klang – gut zum Vergleichen.";
  } else text = "48 kHz · 2B · Stil-Anweisungen möglich.";
  hint.textContent = text;
  hint.classList.toggle("warn", warn);
  updateUltimate();
}
$$("#engineSeg button").forEach((b) => b.addEventListener("click", () => {
  if (currentEngine === b.dataset.value) return;
  currentEngine = b.dataset.value;
  updateEngineUi();
  saveSetting({ engine: currentEngine });
  refreshStatus();
}));

function updateUltimate() {
  const v = voices.find((x) => x.name === selectedVoice);
  const row = $("#ultimateRow");
  const can = !!(v && v.transcript_trusted) && currentEngine !== "qwen";
  row.classList.toggle("disabled", !can);
  row.querySelector(".sr-sub").textContent = !v
    ? "Nur bei geklonten Stimmen verfügbar."
    : currentEngine === "qwen" ? "Qwen3-TTS nutzt den Stimmabdruck der Referenz – mit Transkript setzte es im Deutsch-Test Wörter aus der Referenz vor den Satz."
    : can ? "Nutzt das Transkript der Referenz („Ultimate Cloning“). Stil-Anweisungen werden dann ignoriert. Bei unverständlicher Ausgabe ausschalten."
      : v.transcript ? "Das Transkript stammt von der alten Spracherkennung und ist vermutlich falsch – unter „Stimmen“ neu erkennen."
        : "Diese Stimme hat noch kein Transkript – unter „Stimmen“ ergänzen.";
}

function renderVoiceGrid() {
  const grid = $("#voiceGrid");
  $("#voicesEmpty").classList.toggle("hidden", voices.length > 0 || !$("#createCard").classList.contains("hidden"));
  grid.innerHTML = voices.map((v, i) => `
    <div class="card voice-card" data-i="${i}">
      <div class="vc-head">
        ${avatar(v.name, "lg")}
        <div><div class="vc-name">${esc(v.name)}${v.transcript_trusted ? '<span class="tag">Transkript</span>' : v.transcript ? '<span class="tag warn">Transkript prüfen</span>' : ""}</div>
          <div class="vc-meta">${v.duration.toFixed(1)} s · ${v.sources.length} Quelle(n) · ${esc(v.created.slice(0, 10))}</div></div>
        <button class="icon-btn danger" data-act="delete" title="Löschen"><span data-icon="trash"></span></button>
      </div>
      <div class="player small"></div>
      ${v.transcript && !v.transcript_trusted ? '<div class="vc-warn"><span data-icon="alert"></span>Altes Transkript – vermutlich fehlerhaft. Bitte „Transkript“ → „Automatisch erkennen“.</div>' : ""}
      <div class="vc-transcript ${v.transcript ? "" : "none"}">${v.transcript ? esc(v.transcript) : "Kein Transkript – für maximale Ähnlichkeit hinzufügen."}</div>
      <div class="vc-actions">
        <button class="btn ghost small" data-act="edit"><span data-icon="edit"></span>Transkript</button>
        <button class="btn small primary" data-act="use"><span data-icon="speak"></span>Verwenden</button>
      </div>
    </div>`).join("");
  hydrateIcons(grid);
  $$(".voice-card", grid).forEach((card) => {
    const v = voices[+card.dataset.i];
    new Player(card.querySelector(".player"), vUrl(v.name), v.peaks, { duration: v.duration });
    card.querySelector('[data-act="delete"]').addEventListener("click", async () => {
      if (!(await confirmDialog(`„${v.name}“ löschen?`, "Die Stimme und ihre Referenzaufnahme werden dauerhaft entfernt."))) return;
      stopAudio();
      await api(`/api/voices/${encodeURIComponent(v.name)}`, { method: "DELETE" });
      toast(`Stimme „${v.name}“ gelöscht.`, "success");
      loadVoices();
    });
    card.querySelector('[data-act="edit"]').addEventListener("click", () => editTranscript(v));
    card.querySelector('[data-act="use"]').addEventListener("click", () => { selectedVoice = v.name; renderPicker(); showPage("speak"); $("#ttsText").focus(); });
  });
}

async function editTranscript(v) {
  const dlg = $("#transcriptDialog");
  new Player($("#dialogPlayer"), vUrl(v.name), v.peaks, { duration: v.duration });
  $("#transcriptText").value = v.transcript;
  dlg.returnValue = "";
  dlg.showModal();
  const result = await new Promise((r) => dlg.addEventListener("close", () => r(dlg.returnValue), { once: true }));
  stopAudio();
  try {
    if (result === "save") {
      await api(`/api/voices/${encodeURIComponent(v.name)}/transcript`, { method: "PUT", body: { transcript: $("#transcriptText").value } });
      toast("Transkript gespeichert.", "success");
    } else if (result === "auto") {
      toast("Spracherkennung läuft …", "info");
      const job = await pollJob(await api(`/api/voices/${encodeURIComponent(v.name)}/transcribe`, { method: "POST" }));
      if (job.status !== "done") throw new Error(job.error || "Spracherkennung fehlgeschlagen");
      toast("Transkript automatisch erkannt.", "success");
    } else return;
    loadVoices();
  } catch (e) { toast(e.message, "error"); }
}

// ------------------------------------------------------------------ Neue Stimme
let clips = []; // {kind:'file'|'mic', name, file?, id?, url, duration}
function openCreate() {
  $("#createCard").classList.remove("hidden");
  $("#voicesEmpty").classList.add("hidden");
  $("#voiceName").focus();
}
function closeCreate() { $("#createCard").classList.add("hidden"); renderVoiceGrid(); }
$("#btnNewVoice").addEventListener("click", openCreate);
$("#btnNewVoice2").addEventListener("click", openCreate);
$("#btnCloseCreate").addEventListener("click", closeCreate);

function addFiles(list) {
  for (const f of list) {
    if (!/^audio\//.test(f.type) && !/\.(wav|mp3|flac|ogg|m4a|aac|opus|webm|wma)$/i.test(f.name)) { toast(`„${f.name}“ ist keine Audiodatei.`, "error"); continue; }
    const clip = { kind: "file", name: f.name, file: f, url: URL.createObjectURL(f), duration: 0 };
    const a = new Audio(); a.preload = "metadata"; a.src = clip.url;
    a.addEventListener("loadedmetadata", () => { clip.duration = a.duration; renderClips(); });
    clips.push(clip);
  }
  renderClips();
}
function renderClips() {
  const list = $("#clipList");
  if (!clips.length) {
    list.innerHTML = '<div class="clip-empty">Noch keine Aufnahmen – lade Dateien hoch oder nimm etwas auf.</div>';
    $("#clipTotal").textContent = "";
    return;
  }
  list.innerHTML = clips.map((c, i) => `
    <div class="clip" data-i="${i}">
      <span class="clip-icon ${c.kind === "mic" ? "mic" : ""}"><span data-icon="${c.kind === "mic" ? "mic" : "file"}"></span></span>
      <span class="clip-name" title="${esc(c.name)}">${esc(c.name)}</span>
      <span class="clip-meta">${c.duration ? fmtTime(c.duration) : "…"}</span>
      <button class="play-btn sm" title="Anhören"><span data-icon="play"></span></button>
      <button class="icon-btn danger" title="Entfernen"><span data-icon="x"></span></button>
    </div>`).join("");
  hydrateIcons(list);
  const total = clips.reduce((s, c) => s + (c.duration || 0), 0);
  $("#clipTotal").textContent = `${clips.length} · ${fmtTime(total)} gesamt`;
  $$(".clip", list).forEach((row) => {
    const c = clips[+row.dataset.i];
    const holder = document.createElement("div");
    const p = new Player(holder, c.url, [], {});
    p.btn = row.querySelector(".play-btn");
    p.timeEl = row.querySelector(".clip-meta");
    p.btn.addEventListener("click", () => p.toggle());
    p.reset = function () { this.setIcon(false); this.timeEl.textContent = c.duration ? fmtTime(c.duration) : "…"; };
    row.querySelector(".icon-btn").addEventListener("click", () => {
      if (Player.current === p) stopAudio();
      if (c.kind === "mic") api(`/api/recordings/${c.id}`, { method: "DELETE" }).catch(() => {});
      else URL.revokeObjectURL(c.url);
      clips.splice(+row.dataset.i, 1);
      renderClips();
    });
  });
}

const dz = $("#dropzone");
dz.addEventListener("click", () => $("#fileInput").click());
dz.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("#fileInput").click(); } });
$("#fileInput").addEventListener("change", (e) => { addFiles(e.target.files); e.target.value = ""; });
["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("over"); }));
dz.addEventListener("drop", (e) => addFiles(e.dataTransfer.files));
window.addEventListener("dragover", (e) => e.preventDefault());
window.addEventListener("drop", (e) => e.preventDefault());

// Mikrofon
let recTimer = null;
async function toggleRecording() {
  const box = $("#recorder");
  if (!box.classList.contains("recording")) {
    try {
      stopAudio();
      await api("/api/record/start", { method: "POST" });
    } catch (e) { toast(e.message, "error", 6000); return; }
    box.classList.add("recording");
    $("#recTitle").textContent = "Aufnahme läuft …";
    $("#recSub").textContent = "Klicke erneut, um die Aufnahme zu beenden.";
    recTimer = setInterval(async () => {
      try {
        const l = await api("/api/record/level");
        $("#recMeter").style.width = `${Math.round(l.level * 100)}%`;
        $("#recTime").textContent = fmtTime(l.elapsed);
      } catch (e) { /* ignorieren */ }
    }, 90);
  } else {
    clearInterval(recTimer);
    box.classList.remove("recording");
    $("#recMeter").style.width = "0";
    $("#recTitle").textContent = "Mit dem Mikrofon aufnehmen";
    $("#recSub").textContent = "Klicke auf den Knopf und sprich 10–30 Sekunden.";
    try {
      const r = await api("/api/record/stop", { method: "POST" });
      const n = clips.filter((c) => c.kind === "mic").length + 1;
      clips.push({ kind: "mic", id: r.id, name: `Mikrofon-Aufnahme ${n}`, url: `/api/recordings/${r.id}/audio`, duration: r.duration });
      renderClips();
      toast("Aufnahme hinzugefügt.", "success", 2500);
    } catch (e) { toast(e.message, "error"); }
    $("#recTime").textContent = "0:00";
  }
}
$("#btnRec").addEventListener("click", toggleRecording);

$("#maxSeconds").addEventListener("input", (e) => { $("#maxSecondsVal").textContent = `${e.target.value} s`; });

$("#btnCreate").addEventListener("click", async () => {
  const name = $("#voiceName").value.trim();
  if (!name) { toast("Bitte gib der Stimme einen Namen.", "error"); $("#voiceName").focus(); return; }
  if (!clips.length) { toast("Bitte lade Audiodateien hoch oder nimm etwas auf.", "error"); return; }
  if ($("#recorder").classList.contains("recording")) await toggleRecording();
  const fd = new FormData();
  fd.append("name", name);
  fd.append("max_seconds", $("#maxSeconds").value);
  fd.append("auto_transcript", $("#autoTranscript").checked ? "true" : "false");
  fd.append("recordings", clips.filter((c) => c.kind === "mic").map((c) => c.id).join(","));
  clips.filter((c) => c.kind === "file").forEach((c) => fd.append("files", c.file, c.name));

  const btn = $("#btnCreate");
  btn.disabled = true;
  $("#createProgress").classList.remove("hidden");
  $("#createBar").classList.add("indeterminate");
  $("#createMsg").textContent = "Lade Dateien hoch …";
  try {
    let job = await api("/api/voices", { method: "POST", form: fd });
    job = await pollJob(job, (j) => { $("#createMsg").textContent = j.message; });
    if (job.status !== "done") throw new Error(job.error || "Fehlgeschlagen");
    if (job.result.warning) toast(job.result.warning, "error", 7000);
    toast(`Stimme „${job.result.name}“ wurde erstellt.`, "success");
    stopAudio();
    clips.forEach((c) => c.kind === "file" && URL.revokeObjectURL(c.url));
    clips = [];
    renderClips();
    $("#voiceName").value = "";
    selectedVoice = job.result.name;
    closeCreate();
    await loadVoices();
  } catch (e) {
    toast(e.message, "error", 7000);
  } finally {
    btn.disabled = false;
    $("#createProgress").classList.add("hidden");
    $("#createBar").classList.remove("indeterminate");
  }
});

// ------------------------------------------------------------------ Sprechen
const ttsText = $("#ttsText");
ttsText.addEventListener("input", () => { $("#charCount").textContent = `${ttsText.value.length} Zeichen`; });
ttsText.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); speak(); } });
$$("#styleChips .chip").forEach((c) => c.addEventListener("click", () => {
  const cur = $("#ttsStyle").value.trim();
  const active = c.classList.toggle("active");
  const parts = cur ? cur.split(/\s*,\s*/).filter(Boolean) : [];
  const en = c.dataset.en || c.textContent;
  const next = active ? [...parts, en] : parts.filter((p) => p !== en);
  $("#ttsStyle").value = next.join(", ");
}));
$("#ttsStyle").addEventListener("input", () => {
  const parts = $("#ttsStyle").value.split(/\s*,\s*/);
  $$("#styleChips .chip").forEach((c) => c.classList.toggle("active", parts.includes(c.dataset.en || c.textContent)));
});
$("#ttsCfg").addEventListener("input", (e) => { $("#ttsCfgVal").textContent = (+e.target.value).toFixed(1); });
$("#ttsSteps").addEventListener("input", (e) => { $("#ttsStepsVal").textContent = e.target.value; });
$("#ttsTemp").addEventListener("input", (e) => { $("#ttsTempVal").textContent = (+e.target.value).toFixed(2); });

let currentJob = null;
let lastResult = null;
async function speak() {
  const text = ttsText.value.trim();
  if (!text) { toast("Bitte gib einen Text ein.", "error"); ttsText.focus(); return; }
  if (currentJob) return;
  stopAudio();
  const btn = $("#btnSpeak");
  btn.disabled = true;
  $("#resultEmpty").classList.add("hidden");
  $("#resultBox").classList.add("hidden");
  $("#genProgress").classList.remove("hidden");
  $("#genBar").style.width = "0";
  $("#genBar").classList.add("indeterminate");
  $("#genMsg").textContent = "Starte …";
  $("#genPct").textContent = "";
  try {
    const voice = voices.find((v) => v.name === selectedVoice);
    const qwen = currentEngine === "qwen";
    if (qwen && !voice) throw new Error("Qwen3-TTS braucht eine geklonte Stimme – bitte links eine Stimme auswählen.");
    currentJob = await api("/api/generate", { method: "POST", body: {
      text, voice: selectedVoice, style: qwen ? "" : $("#ttsStyle").value,
      use_transcript: !!(voice && voice.transcript_trusted && $("#ttsUltimate").checked),
      cfg_value: +$("#ttsCfg").value, inference_timesteps: +$("#ttsSteps").value,
      engine: currentEngine, language: $("#ttsQwenLang").value, temperature: qwen ? +$("#ttsTemp").value : null,
    } });
    const job = await pollJob(currentJob, (j) => {
      $("#genMsg").textContent = j.message;
      if (j.progress > 0) {
        $("#genBar").classList.remove("indeterminate");
        $("#genBar").style.width = `${Math.round(j.progress * 100)}%`;
        $("#genPct").textContent = `${Math.round(j.progress * 100)} %`;
      }
    });
    if (job.status === "cancelled") { toast("Abgebrochen.", "info"); $("#resultEmpty").classList.remove("hidden"); return; }
    if (job.status !== "done") throw new Error(job.error || "Fehlgeschlagen");
    showResult(job.result);
    Player.current = null;
    resultPlayer.toggle();
  } catch (e) {
    toast(`Fehler bei der Sprachausgabe: ${e.message}`, "error", 8000);
    $("#resultEmpty").classList.remove("hidden");
  } finally {
    currentJob = null;
    btn.disabled = false;
    $("#genProgress").classList.add("hidden");
  }
}
let resultPlayer = null;
function renderHardware(s) {
  const box = $("#hwBox");
  if (!box) return;
  if (s.state !== "ready" && !(s.vram && s.vram.total_gb)) { box.innerHTML = `<span class="muted">${esc(s.state === "loading" ? "Modell lädt …" : "Modell nicht geladen")}</span>`; return; }
  const rows = [
    ["Gerät", s.gpu || (s.device || "").toUpperCase()],
    ["Grafikspeicher", s.vram_gb ? `${s.vram_gb} GB` : "–"],
    ["Rechengenauigkeit", s.dtype || "–"],
    ["Beschleunigung", s.compiled ? "⚡ aktiv (torch.compile + CUDA-Graphs)" : s.triton ? "aus" : "nicht verfügbar (Triton fehlt)"],
  ];
  if (s.vram && s.vram.total_gb) rows.push(["Grafikspeicher frei", `${s.vram.free_gb.toFixed(1)} von ${s.vram.total_gb.toFixed(1)} GB`]);
  box.innerHTML = rows.map(([k, v]) => `<div><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join("");
}
function renderQwen(q) {
  const btn = $("#btnQwenInstall");
  if (!btn || !q) return;
  const inst = q.install || {};
  const running = inst.state === "running";
  btn.disabled = running;
  btn.innerHTML = running ? `<span data-icon="download"></span>Installiere …` : q.installed ? `<span data-icon="check"></span>Neu einrichten` : `<span data-icon="download"></span>Installieren`;
  hydrateIcons(btn);
  const info = $("#qwenInfo");
  if (running) info.textContent = `Installation läuft: ${q.install_step || inst.message || "…"}`;
  else if (inst.state === "error") info.textContent = inst.message;
  else if (q.installed) info.textContent = `Installiert · ${q.state === "ready" ? "geladen" : q.state === "loading" ? "lädt …" : "lädt beim ersten Sprechen"}. Oben auf der Sprechen-Seite zwischen VoxCPM2 und Qwen3-TTS wechseln.`;
  if (renderQwen.wasRunning && !running && q.installed) toast("Qwen3-TTS ist eingerichtet.", "success");
  renderQwen.wasRunning = running;
}
$("#btnQwenInstall").addEventListener("click", async () => {
  try { const s = await api("/api/qwen/install", { method: "POST" }); renderQwen(s.qwen); refreshStatus(); } catch (e) { toast(e.message, "error"); }
});

function showResult(r) {
  lastResult = r;
  $("#resultBox").classList.remove("hidden");
  $("#resultEmpty").classList.add("hidden");
  resultPlayer = new Player($("#mainPlayer"), `/api/history/${encodeURIComponent(r.file)}/audio`, r.peaks, { duration: r.duration });
  $("#resultText").textContent = r.text;
  $("#resultSpoken").textContent = r.spoken_text ? `Gesprochen als: ${r.spoken_text}` : "";
  $("#resultSpoken").classList.toggle("hidden", !r.spoken_text);
  $("#resultStats").innerHTML = r.gen_seconds
    ? `<span>${r.duration.toFixed(1)} s Audio</span><span>erzeugt in ${r.gen_seconds.toFixed(1)} s</span><span class="${r.rtf <= 1 ? "good" : ""}">${r.rtf <= 1 ? `${(1 / r.rtf).toFixed(1)}× schneller als Echtzeit` : `${r.rtf.toFixed(1)}× Echtzeit`}</span>`
    : "";
}
$("#btnSpeak").addEventListener("click", speak);
$("#btnCancel").addEventListener("click", () => currentJob && api(`/api/jobs/${currentJob.id}/cancel`, { method: "POST" }));

function chooseFormat() {
  const dlg = $("#exportDialog");
  const current = settings.export_format || "wav";
  $$('#formatGrid input[name="fmt"]').forEach((r) => { r.checked = r.value === current; });
  dlg.returnValue = "";
  dlg.showModal();
  return new Promise((resolve) => dlg.addEventListener("close", () => {
    const sel = $('#formatGrid input[name="fmt"]:checked');
    resolve(dlg.returnValue === "save" && sel ? sel.value : null);
  }, { once: true }));
}
async function saveAs(file) {
  const fmt = await chooseFormat();
  if (!fmt) return;
  if (fmt !== settings.export_format) { saveSetting({ export_format: fmt }); $("#setExportFormat").value = fmt; }
  try {
    const r = await api(`/api/history/${encodeURIComponent(file)}/save-as`, { method: "POST", body: { format: fmt } });
    if (r.ok) toast(`Gespeichert: ${r.path}`, "success");
    else if (r.download) {
      const a = document.createElement("a");
      a.href = r.download; a.download = file.replace(/\.wav$/i, `.${fmt}`); a.click();
    }
  } catch (e) { toast(e.message, "error"); }
}
const reveal = (file) => api(`/api/history/${encodeURIComponent(file)}/reveal`, { method: "POST" }).catch((e) => toast(e.message, "error"));
$("#btnSave").addEventListener("click", () => lastResult && saveAs(lastResult.file));
$("#btnReveal").addEventListener("click", () => lastResult && reveal(lastResult.file));

// ------------------------------------------------------------------ Verlauf
let historyItems = [];
async function loadHistory() {
  try { historyItems = await api("/api/history"); } catch (e) { toast(e.message, "error"); historyItems = []; }
  renderHistory();
}
function renderHistory() {
  const q = $("#historySearch").value.trim().toLowerCase();
  const items = historyItems.filter((h) => !q || `${h.text} ${h.voice} ${h.style}`.toLowerCase().includes(q)).slice(0, 200);
  $("#historyEmpty").classList.toggle("hidden", historyItems.length > 0);
  const list = $("#historyList");
  list.innerHTML = items.map((h, i) => `
    <div class="card h-item" data-i="${i}">
      ${avatar(h.voice || "–", h.voice ? "" : "default")}
      <div style="min-width:0">
        <div class="h-text" title="${esc(h.text)}">${esc(h.text || h.file)}</div>
        <div class="h-meta">
          <span><span data-icon="user"></span>${esc(h.voice || "Standardstimme")}</span>
          <span><span data-icon="clock"></span>${esc(h.created)}</span>
          ${h.style ? `<span><span data-icon="sparkle"></span>${esc(h.style)}</span>` : ""}
          ${h.engine ? `<span><span data-icon="wave"></span>${esc(h.engine)}</span>` : ""}
        </div>
        <div class="player small"></div>
      </div>
      <div class="h-actions">
        <button class="icon-btn" data-act="reuse" title="Text wiederverwenden"><span data-icon="edit"></span></button>
        <button class="icon-btn" data-act="save" title="Speichern unter …"><span data-icon="download"></span></button>
        <button class="icon-btn" data-act="reveal" title="Im Ordner zeigen"><span data-icon="folder"></span></button>
        <button class="icon-btn danger" data-act="delete" title="Löschen"><span data-icon="trash"></span></button>
      </div>
    </div>`).join("");
  hydrateIcons(list);
  $$(".h-item", list).forEach(async (row) => {
    const h = items[+row.dataset.i];
    const url = `/api/history/${encodeURIComponent(h.file)}/audio`;
    row.querySelector('[data-act="save"]').addEventListener("click", () => saveAs(h.file));
    row.querySelector('[data-act="reveal"]').addEventListener("click", () => reveal(h.file));
    row.querySelector('[data-act="reuse"]').addEventListener("click", () => {
      ttsText.value = h.text; ttsText.dispatchEvent(new Event("input"));
      $("#ttsStyle").value = h.style || ""; $("#ttsStyle").dispatchEvent(new Event("input"));
      if (voices.some((v) => v.name === h.voice)) selectedVoice = h.voice; else if (!h.voice) selectedVoice = "";
      renderPicker(); showPage("speak");
    });
    row.querySelector('[data-act="delete"]').addEventListener("click", async () => {
      if (!(await confirmDialog("Eintrag löschen?", "Die Audiodatei wird dauerhaft gelöscht."))) return;
      stopAudio();
      await api(`/api/history/${encodeURIComponent(h.file)}`, { method: "DELETE" });
      loadHistory();
    });
    let peaks = [];
    try { peaks = await api(`/api/history/${encodeURIComponent(h.file)}/peaks`); } catch (e) { /* ignorieren */ }
    new Player(row.querySelector(".player"), url, peaks, { duration: h.duration });
  });
}
$("#historySearch").addEventListener("input", renderHistory);

// ------------------------------------------------------------------ Einstellungen
async function loadSettings() {
  try { settings = await api("/api/settings"); } catch (e) { settings = { theme: "system" }; }
  applyTheme(settings.theme || "system");
  $("#setDevice").value = settings.device || "auto";
  $("#setSteps").value = settings.inference_timesteps; $("#setStepsVal").textContent = settings.inference_timesteps;
  $("#setCfg").value = settings.cfg_value; $("#setCfgVal").textContent = (+settings.cfg_value).toFixed(1);
  $("#setNormalize").checked = !!settings.normalize;
  $("#setDenoiser").checked = !!settings.load_denoiser;
  $("#setAccel").value = settings.accel || "auto";
  // Standardwerte für die Sprechen-Seite
  $("#ttsSteps").value = settings.inference_timesteps; $("#ttsStepsVal").textContent = settings.inference_timesteps;
  $("#ttsCfg").value = settings.cfg_value; $("#ttsCfgVal").textContent = (+settings.cfg_value).toFixed(1);
  $("#maxSeconds").value = settings.max_ref_seconds; $("#maxSecondsVal").textContent = `${settings.max_ref_seconds} s`;
  $("#autoTranscript").checked = settings.auto_transcript !== false;
  $("#setAsrLang").value = settings.asr_language || "auto";
  $("#setExportFormat").value = settings.export_format || "wav";
  $("#setFreeVram").checked = settings.free_vram !== false;
  $("#setQwenLang").value = settings.text_language || "de";
  $("#ttsQwenLang").value = settings.text_language || "de";
  $("#setGermanNorm").checked = settings.german_normalize !== false;
  currentEngine = settings.engine === "qwen" ? "qwen" : "voxcpm";
  updateEngineUi();
}
async function saveSetting(values) {
  try {
    const r = await api("/api/settings", { method: "PUT", body: values });
    settings = r.settings;
    if (r.restart_required) $("#restartNote").classList.remove("hidden");
  } catch (e) { toast(e.message, "error"); }
}
$("#setDevice").addEventListener("change", (e) => saveSetting({ device: e.target.value }));
$("#setSteps").addEventListener("input", (e) => { $("#setStepsVal").textContent = e.target.value; });
$("#setSteps").addEventListener("change", (e) => { saveSetting({ inference_timesteps: +e.target.value }); $("#ttsSteps").value = e.target.value; $("#ttsStepsVal").textContent = e.target.value; });
$("#setCfg").addEventListener("input", (e) => { $("#setCfgVal").textContent = (+e.target.value).toFixed(1); });
$("#setCfg").addEventListener("change", (e) => { saveSetting({ cfg_value: +e.target.value }); $("#ttsCfg").value = e.target.value; $("#ttsCfgVal").textContent = (+e.target.value).toFixed(1); });
$("#setNormalize").addEventListener("change", (e) => saveSetting({ normalize: e.target.checked }));
$("#setDenoiser").addEventListener("change", (e) => saveSetting({ load_denoiser: e.target.checked }));
$("#setAccel").addEventListener("change", (e) => saveSetting({ accel: e.target.value }));
$("#maxSeconds").addEventListener("change", (e) => saveSetting({ max_ref_seconds: +e.target.value }));
$("#autoTranscript").addEventListener("change", (e) => saveSetting({ auto_transcript: e.target.checked }));
$("#setAsrLang").addEventListener("change", (e) => saveSetting({ asr_language: e.target.value }));
$("#setExportFormat").addEventListener("change", (e) => saveSetting({ export_format: e.target.value }));
$("#setFreeVram").addEventListener("change", (e) => saveSetting({ free_vram: e.target.checked }));
$("#setQwenLang").addEventListener("change", (e) => { saveSetting({ text_language: e.target.value }); $("#ttsQwenLang").value = e.target.value; });
$("#setGermanNorm").addEventListener("change", (e) => saveSetting({ german_normalize: e.target.checked }));
$("#setInput").addEventListener("change", (e) => saveSetting({ input_device: e.target.value === "" ? null : +e.target.value }));

async function loadDevices() {
  let devs = [];
  try { devs = await api("/api/audio/devices"); } catch (e) { /* ignorieren */ }
  const sel = $("#setInput");
  sel.innerHTML = `<option value="">Standard-Mikrofon</option>` +
    devs.map((d) => `<option value="${d.id}">${esc(d.name)}${d.default ? " (Standard)" : ""}</option>`).join("");
  sel.value = settings.input_device ?? "";
  if (!devs.length) sel.innerHTML = '<option value="">Kein Mikrofon gefunden</option>';
}

// ------------------------------------------------------------------ Start
hydrateIcons();
(async () => {
  await loadSettings();
  await loadVoices();
  refreshStatus();
})();
