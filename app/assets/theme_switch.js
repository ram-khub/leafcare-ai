// LeafCare AI light/dark switch. Injected once per page by utils/ui.py:theme_switch().
//
// Streamlit has no API for changing its theme, but with [theme.light] and [theme.dark] in
// config.toml it shows whichever one window.matchMedia("(prefers-color-scheme: dark)") reports,
// and re-checks on the window "afterprint" event. So the switch answers that query with the
// visitor's choice and fires "afterprint"; our own CSS follows via data-lc-theme on the html element.
// The change is animated with a View Transition: a circle grows out of the switch.
//
// Keep this file free of markup in strings: st.html sanitises with DOMPurify, which drops a
// script whose text contains anything tag-like. Elements are built with createElement; the sun and moon
// icons are CSS masks in styles.css.
(() => {
  if (window.__lcThemeSwitch) { window.__lcThemeSwitch.mount(); return; }

  const KEY = "lc-theme";
  const root = document.documentElement;
  const realMatchMedia = window.matchMedia.bind(window);
  const read = () => { try { return localStorage.getItem(KEY); } catch { return null; } };
  const save = (v) => { try { localStorage.setItem(KEY, v); } catch { /* private mode: not remembered */ } };

  const saved = read();
  let choice = saved === "dark" || saved === "light" ? saved : null;  // null = follow the system
  const isDark = () => (choice ? choice === "dark" : realMatchMedia("(prefers-color-scheme: dark)").matches);

  window.matchMedia = (query) => {
    const mql = realMatchMedia(query);
    if (!choice || !/prefers-color-scheme/.test(query)) return mql;
    const matches = /dark/.test(query) ? choice === "dark" : choice === "light";
    return new Proxy(mql, {
      get: (target, prop) => (prop === "matches" ? matches
        : typeof target[prop] === "function" ? target[prop].bind(target) : target[prop]),
    });
  };

  let button;

  function render() {
    const dark = isDark();
    if (choice) root.dataset.lcTheme = choice; else delete root.dataset.lcTheme;
    button.setAttribute("aria-checked", String(dark));
    button.title = dark ? "Switch to light mode" : "Switch to dark mode";
  }

  // Resolves once Streamlit has restyled with the new theme (or after 600 ms, whichever is first).
  // Polls with setTimeout: the browser pauses requestAnimationFrame inside a View Transition update.
  function streamlitRepainted(before) {
    const app = document.querySelector(".stApp");
    return new Promise((resolve) => {
      const started = performance.now();
      (function check() {
        const now = app && getComputedStyle(app).backgroundColor;
        if (!app || now !== before || performance.now() - started > 600) resolve();
        else setTimeout(check, 16);
      })();
    });
  }

  function applyTheme() {
    const app = document.querySelector(".stApp");
    const before = app && getComputedStyle(app).backgroundColor;
    render();
    window.dispatchEvent(new Event("afterprint"));
    return streamlitRepainted(before);
  }

  function toggle() {
    choice = isDark() ? "light" : "dark";
    save(choice);

    const reduceMotion = realMatchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!document.startViewTransition || reduceMotion) { applyTheme(); return; }

    const box = button.getBoundingClientRect();
    const x = box.left + box.width / 2;
    const y = box.top + box.height / 2;
    const radius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));

    const transition = document.startViewTransition(applyTheme);
    transition.ready.then(() => {
      root.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
        { duration: 650, easing: "cubic-bezier(0.65, 0, 0.35, 1)", pseudoElement: "::view-transition-new(root)" },
      );
    }).catch(() => {});
  }

  function mount() {
    if (button && document.body.contains(button)) return;
    button = document.createElement("button");
    button.type = "button";
    button.className = "lc-theme-switch";
    button.setAttribute("role", "switch");
    button.setAttribute("aria-label", "Dark mode");
    const knob = document.createElement("span");
    knob.className = "lc-theme-knob";
    for (const icon of ["lc-sun", "lc-moon"]) {
      const span = document.createElement("span");
      span.className = icon;
      knob.appendChild(span);
    }
    button.appendChild(knob);
    button.addEventListener("click", toggle);
    document.body.appendChild(button);
    render();
  }

  // Keep the switch in sync if the visitor changes their system theme while following it.
  realMatchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { if (!choice) render(); });

  window.__lcThemeSwitch = { mount };
  mount();
  if (choice) applyTheme();  // a saved choice that differs from the system: switch Streamlit over now
})();
