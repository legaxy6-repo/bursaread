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

  var form = document.getElementById("news-form");
  if (form) form.addEventListener("submit", function (ev) {
    if (form.getAttribute("action")) return;
    ev.preventDefault();
    var note = document.getElementById("news-note");
    if (note) note.textContent = "Sign-ups open soon. Nothing was stored.";
  });
})();
