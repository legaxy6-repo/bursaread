(function () {
  "use strict";
  var box = document.getElementById("live");
  if (!box) return;

  function fx(code) { return { fn: "CURRENCY_EXCHANGE_RATE", q: "from_currency=" + code + "&to_currency=MYR" }; }
  var LIVE = [
    Object.assign({ key: "usdmyr", label: "USD/MYR", dp: 4 }, fx("USD")),
    Object.assign({ key: "sgdmyr", label: "SGD/MYR", dp: 4 }, fx("SGD")),
    Object.assign({ key: "eurmyr", label: "EUR/MYR", dp: 4 }, fx("EUR")),
    Object.assign({ key: "gbpmyr", label: "GBP/MYR", dp: 4 }, fx("GBP")),
    Object.assign({ key: "audmyr", label: "AUD/MYR", dp: 4 }, fx("AUD")),
    Object.assign({ key: "cnymyr", label: "CNY/MYR", dp: 4 }, fx("CNY")),
    Object.assign({ key: "jpymyr100", label: "JPY/MYR (per 100)", dp: 4, scale: 100 }, fx("JPY")),
    { key: "gold", label: "Gold (US$/oz)", dp: 2, fn: "GOLD_SILVER_SPOT", q: "symbol=GOLD" }
  ];
  var MIN_GAP = 5 * 60 * 1000;
  var $ = function (id) { return document.getElementById(id); };

  function store(k, v) {
    try {
      if (v === undefined) return localStorage.getItem(k);
      if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v);
    } catch (e) { return null; }
    return null;
  }
  function jget(k, d) { try { var v = JSON.parse(store(k) || "null"); return v == null ? d : v; } catch (e) { return d; } }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = String(text); return e; }
  function fmt(v, dp) { return Number(v).toLocaleString("en-US", { minimumFractionDigits: dp, maximumFractionDigits: dp }).replace(/^-/, "−"); }
  function sgn(v, dp, suf) { var n = Number(v); return (n > 0 ? "+" : n < 0 ? "−" : "") + Math.abs(n).toFixed(dp) + (suf || ""); }
  function mytDay(ms) { return new Date(ms).toLocaleDateString("en-CA", { timeZone: "Asia/Kuala_Lumpur" }); }
  function ago(ms) { var m = Math.round(ms / 60000); if (m < 1) return "just now"; if (m < 60) return m + " min ago"; var h = Math.round(m / 60); return h < 24 ? h + " h ago" : Math.round(h / 24) + " d ago"; }
  function shortDay(d) { var p = /^(\d{4})-(\d{2})-(\d{2})$/.exec(d || ""); return p ? new Date(Date.UTC(+p[1], +p[2] - 1, +p[3])).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" }) : d; }
  function utcIso(t) { var m = /^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})/.exec(String(t || "")); return m ? m[1] + "T" + m[2] + "Z" : null; }

  var closes = {};
  try { closes = JSON.parse(($("dd-closes") || {}).textContent || "{}"); } catch (e) { closes = {}; }
  var key = store("dd-av-key");
  var cache = jget("dd-live-cache", {});
  var picks = jget("dd-live-picks", ["usdmyr", "sgdmyr", "gold"]).filter(function (k) { return LIVE.some(function (c) { return c.key === k; }); });
  var usage = jget("dd-live-usage", { day: "", calls: 0 });
  var busy = false, msg = "";

  function cfg(k) { return LIVE.find(function (c) { return c.key === k; }); }
  function parse(c, j) {
    if (!j || typeof j !== "object") return null;
    if (j["Information"] || j["Note"] || j["Error Message"]) return { limit: true, text: j["Information"] || j["Note"] || j["Error Message"] };
    var v = null, at = null;
    if (c.fn === "CURRENCY_EXCHANGE_RATE") {
      var r = j["Realtime Currency Exchange Rate"];
      if (r) { v = parseFloat(r["5. Exchange Rate"]); at = utcIso(r["6. Last Refreshed"]); }
    } else {
      v = parseFloat(j.price); at = utcIso(j.timestamp);
    }
    return isFinite(v) ? { value: v * (c.scale || 1), at: at } : null;
  }

  function renderPicker() {
    var grid = $("live-pick-grid");
    grid.textContent = "";
    LIVE.forEach(function (c) {
      var lab = el("label"), cb = el("input");
      cb.type = "checkbox"; cb.id = "live-pick-" + c.key; cb.checked = picks.indexOf(c.key) >= 0;
      cb.addEventListener("change", function () {
        picks = LIVE.map(function (x) { return x.key; }).filter(function (k) { var b = $("live-pick-" + k); return b && b.checked; });
        store("dd-live-picks", JSON.stringify(picks));
        render();
      });
      lab.appendChild(cb); lab.appendChild(document.createTextNode(c.label));
      grid.appendChild(lab);
    });
  }

  function render() {
    var now = Date.now();
    $("live-keyform").hidden = !!key;
    $("live-tiles").hidden = !key;
    $("live-pick").hidden = !key;
    var btn = $("live-refresh");
    btn.hidden = !key;
    btn.disabled = busy || !picks.length;
    btn.textContent = busy ? "Refreshing…" : "Refresh " + picks.length + (picks.length === 1 ? " price" : " prices");
    var tiles = $("live-tiles");
    tiles.textContent = "";
    var fresh = false;
    picks.forEach(function (k) {
      var c = cfg(k), d = cache[k];
      if (!c) return;
      var t = el("div", "dd-tile");
      t.appendChild(el("span", "dd-tile-label", c.label));
      t.appendChild(el("span", "dd-tile-value", d ? fmt(d.value, c.dp) : "—"));
      var st = d ? Date.parse(d.at || d.fetched) : NaN;
      t.appendChild(el("span", "dd-tile-meta", isFinite(st)
        ? new Date(st).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Kuala_Lumpur" }) + " MYT · " + ago(now - st)
        : "Not fetched yet"));
      var lc = closes[k];
      if (d && lc && lc.v) {
        var pct = (d.value - lc.v) / lc.v * 100;
        var vs = el("span", "dd-tile-vs", sgn(pct, 2, "%") + " vs " + shortDay(lc.date) + " BNM 5pm");
        vs.setAttribute("data-dir", pct > 0 ? "up" : pct < 0 ? "down" : "flat");
        t.appendChild(vs);
      }
      if (d && now - Date.parse(d.fetched) < 15 * 60 * 1000) fresh = true;
      tiles.appendChild(t);
    });
    $("live-dot").hidden = !(fresh || busy);
    var calls = usage.day === mytDay(now) ? usage.calls : 0;
    $("live-status").textContent = key
      ? (msg || "Each refresh uses one Alpha Vantage call per price. This browser has used " + calls + (calls === 1 ? " call" : " calls") + " today; the free key allows 25 a day.")
      : "";
  }

  function refresh() {
    if (busy || !key) return;
    var now = Date.now();
    var queue = picks.filter(function (k) { var d = cache[k]; return !(d && now - Date.parse(d.fetched) < MIN_GAP); });
    var skipped = picks.length - queue.length;
    if (!queue.length) { msg = "All chosen prices were refreshed in the last 5 minutes. Nothing was called."; render(); return; }
    busy = true; msg = ""; render();
    var done = 0, calls = 0, stop = null, unread = [];
    function next() {
      if (!queue.length || stop) return finish();
      var c = cfg(queue.shift());
      calls++;
      fetch("https://www.alphavantage.co/query?function=" + c.fn + "&" + c.q + "&apikey=" + encodeURIComponent(key))
        .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .then(function (j) {
          var p = parse(c, j);
          if (p && p.limit) { stop = /premium|invalid|api key/i.test(p.text || "") && !/25/.test(p.text || "") ? "Alpha Vantage refused the key: " + p.text : "Alpha Vantage's daily limit is used up. Try again tomorrow."; return; }
          if (!p) { unread.push(c.label); return; }
          cache[c.key] = { value: p.value, at: p.at, fetched: new Date().toISOString() };
          done++;
        })
        .catch(function () { stop = "Couldn't reach Alpha Vantage. Check your connection and try again."; })
        .then(function () { render(); setTimeout(next, 1200); });
    }
    function finish() {
      var day = mytDay(Date.now());
      usage = { day: day, calls: (usage.day === day ? usage.calls : 0) + calls };
      store("dd-live-usage", JSON.stringify(usage));
      store("dd-live-cache", JSON.stringify(cache));
      busy = false;
      var parts = [];
      if (stop) parts.push(stop);
      if (done) parts.push("Updated " + done + (done === 1 ? " price." : " prices."));
      if (unread.length) parts.push("Couldn't read the answer for " + unread.join(", ") + ".");
      if (skipped) parts.push(skipped + " refreshed in the last 5 minutes " + (skipped === 1 ? "was" : "were") + " skipped.");
      msg = parts.join(" ");
      render();
    }
    next();
  }

  $("live-keyform").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var v = ($("live-key").value || "").trim();
    if (!/^[A-Za-z0-9]{6,64}$/.test(v)) { $("live-keyhint").textContent = "That doesn't look like an Alpha Vantage key. It's letters and numbers only."; return; }
    key = v; store("dd-av-key", v); $("live-key").value = ""; msg = "Key saved in this browser. Press Refresh to fetch prices."; render();
  });
  $("live-forget").addEventListener("click", function () { key = null; store("dd-av-key", null); msg = ""; render(); });
  $("live-refresh").addEventListener("click", refresh);
  renderPicker();
  render();
  setInterval(render, 60000);
})();
