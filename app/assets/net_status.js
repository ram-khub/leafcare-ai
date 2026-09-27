// LeafCare AI connection notices. Injected once per page by utils/ui.py:page_scripts().
//
// Offline: the browser's offline event shows a banner and adds lc-offline to the html element, which
// greys out the photo inputs in styles.css (they need the server). The online event shows "Back online" briefly.
// Slow: when a Streamlit spinner stays up for SLOW_AFTER_MS, the page says so and offers a reload,
// instead of leaving the visitor watching a spinner that may never finish on a dropped connection.
//
// Labels come from window.__lcNetLabels, set in the visitor's language by ui.py just before this file.
// Keep this file free of markup in strings: see the note at the top of theme_switch.js.
(() => {
  if (window.__lcNetStatus) return;
  window.__lcNetStatus = true;

  const SLOW_AFTER_MS = 15000;
  const root = document.documentElement;
  const labels = () => window.__lcNetLabels || {};
  let banner = null;
  let backOnlineTimer = null;
  let spinnerSince = null;
  let showing = null;

  function show(kind) {
    if (showing === kind) return;
    showing = kind;
    if (!banner) {
      banner = document.createElement("div");
      banner.className = "lc-net";
      banner.setAttribute("role", "status");
      banner.setAttribute("aria-live", "polite");
      document.body.appendChild(banner);
    }
    const l = labels();
    const title = { offline: l.offlineTitle, slow: l.slowTitle, online: l.backOnline }[kind];
    const body = { offline: l.offlineBody, slow: l.slowBody }[kind];
    banner.replaceChildren();
    banner.dataset.kind = kind;
    const text = document.createElement("div");
    const strong = document.createElement("b");
    strong.textContent = title || "";
    text.appendChild(strong);
    if (body) {
      const p = document.createElement("span");
      p.textContent = body;
      text.appendChild(p);
    }
    banner.appendChild(text);
    if (kind === "slow") {
      const reload = document.createElement("button");
      reload.type = "button";
      reload.className = "lc-net-reload";
      reload.textContent = l.reload || "";
      reload.addEventListener("click", () => location.reload());
      banner.appendChild(reload);
    }
    banner.classList.add("lc-net-open");
  }

  function hide() {
    showing = null;
    if (banner) banner.classList.remove("lc-net-open");
  }

  function goOffline() {
    clearTimeout(backOnlineTimer);
    root.classList.add("lc-offline");
    show("offline");
  }

  function goOnline() {
    root.classList.remove("lc-offline");
    show("online");
    clearTimeout(backOnlineTimer);
    backOnlineTimer = setTimeout(() => { if (showing === "online") hide(); }, 3000);
  }

  window.addEventListener("offline", goOffline);
  window.addEventListener("online", goOnline);
  if (navigator.onLine === false) goOffline();

  setInterval(() => {
    if (!navigator.onLine) return;
    const spinning = document.querySelector('[data-testid="stSpinner"]');
    if (!spinning) {
      spinnerSince = null;
      if (showing === "slow") hide();
      return;
    }
    if (spinnerSince === null) spinnerSince = Date.now();
    if (Date.now() - spinnerSince >= SLOW_AFTER_MS) show("slow");
  }, 1000);
})();
