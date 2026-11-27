(function () {
  "use strict";
  var root = document.documentElement;
  var theme = "dark";
  try { var saved = localStorage.getItem("dd-theme"); if (saved === "light" || saved === "dark") theme = saved; } catch (e) { /* storage unavailable */ }
  function apply() {
    root.setAttribute("data-dd-theme", theme);
    var b = document.getElementById("theme-toggle");
    if (b) {
      b.textContent = theme === "dark" ? "Light mode" : "Dark mode";
      b.setAttribute("aria-label", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    }
  }
  apply();
  var tb = document.getElementById("theme-toggle");
  if (tb) tb.addEventListener("click", function () {
    theme = theme === "dark" ? "light" : "dark";
    apply();
    try { localStorage.setItem("dd-theme", theme); } catch (e) { /* not remembered */ }
  });

  var bar = document.getElementById("progress-bar"), ticking = false;
  function progress() {
    if (!bar) return;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.transform = "scaleX(" + (max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0).toFixed(4) + ")";
    ticking = false;
  }
  window.addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(progress); } }, { passive: true });
  progress();

  /* Tap a number's name to show what it means */
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest ? ev.target.closest(".dd-term") : null;
    if (!b) return;
    var d = document.getElementById(b.getAttribute("aria-controls"));
    if (!d) return;
    var open = b.getAttribute("aria-expanded") === "true";
    b.setAttribute("aria-expanded", open ? "false" : "true");
    d.hidden = open;
  });

  /* Out-of-date warning: a "latest" page older than the newest expected read, or an archived read */
  var main = document.querySelector("main[data-read-date]");
  if (main) {
    var rd = main.getAttribute("data-read-date"), kind = main.getAttribute("data-kind");
    var now = new Date();
    var myt = new Date(now.getTime() + (now.getTimezoneOffset() + 480) * 60000);
    var today = myt.getFullYear() + "-" + String(myt.getMonth() + 1).padStart(2, "0") + "-" + String(myt.getDate()).padStart(2, "0");
    var expected = new Date(Date.UTC(myt.getFullYear(), myt.getMonth(), myt.getDate()));
    var beforePublish = myt.getHours() * 60 + myt.getMinutes() < 8 * 60 + 30;
    function back() { do { expected.setUTCDate(expected.getUTCDate() - 1); } while (expected.getUTCDay() === 0 || expected.getUTCDay() === 6); }
    if (expected.getUTCDay() === 0 || expected.getUTCDay() === 6 || beforePublish) back();
    var expStr = expected.toISOString().slice(0, 10);
    var p = /^(\d{4})-(\d{2})-(\d{2})$/.exec(rd || "");
    var label = p ? new Date(Date.UTC(+p[1], +p[2] - 1, +p[3])).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" }) : rd;
    var text = null;
    if (kind === "archive") text = "This is an archived read from " + label + ".";
    else if (rd && rd < expStr) text = "This read is from " + label + ". A newer one should be out by now; it hasn't been published yet.";
    if (text) {
      var banner = document.createElement("p");
      banner.className = "dd-stale"; banner.setAttribute("role", "status");
      banner.appendChild(document.createTextNode(text + " "));
      if (kind === "archive") {
        var a = document.createElement("a"); a.href = main.getAttribute("data-latest-href") || "./"; a.textContent = "Go to the latest read";
        banner.appendChild(a);
      }
      main.insertBefore(banner, main.firstChild);
    }
  }

  var form = document.getElementById("news-form");
  if (form) form.addEventListener("submit", function (ev) {
    if (form.getAttribute("action")) return;
    ev.preventDefault();
    var note = document.getElementById("news-note");
    if (note) note.textContent = "Sign-ups open soon. Nothing was stored.";
  });
})();
