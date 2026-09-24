// LeafCare AI help tips. Injected once per page by utils/ui.py:page_scripts().
//
// A "?" button (class lc-help) is followed by its tip (class lc-tip); CSS shows the tip on hover.
// Phones have no hover, so a click or tap also toggles it open, and a click elsewhere or Escape closes it.
//
// Keep this file free of markup in strings: see the note at the top of theme_switch.js.
(() => {
  if (window.__lcHelpTips) return;
  window.__lcHelpTips = true;

  const close = (except) => document.querySelectorAll(".lc-help.lc-open").forEach((button) => {
    if (button === except) return;
    button.classList.remove("lc-open");
    button.setAttribute("aria-expanded", "false");
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".lc-help");
    close(button);
    if (!button) return;
    const open = button.classList.toggle("lc-open");
    button.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") close(null); });
})();
