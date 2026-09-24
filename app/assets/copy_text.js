// LeafCare AI "Copy text" button. Injected once per page by utils/ui.py:page_scripts().
//
// The button (ui.copy_button) is plain HTML carrying the text in data-text and its labels in
// data-copy / data-copied / data-failed. This document-level click handler copies the text and
// shows the result on the button for two seconds.
//
// Keep this file free of markup in strings: see the note at the top of theme_switch.js.
(() => {
  if (window.__lcCopyText) return;
  window.__lcCopyText = true;

  // For browsers without the async clipboard API (older phones, or a page that isn't https).
  function legacyCopy(text) {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch { ok = false; }
    area.remove();
    return ok;
  }

  async function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      try { await navigator.clipboard.writeText(text); return true; } catch { /* fall through */ }
    }
    return legacyCopy(text);
  }

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".lc-copy");
    if (!button) return;
    const label = button.querySelector(".lc-copy-label");
    const ok = await copy(button.dataset.text);
    button.classList.toggle("lc-copied", ok);
    button.classList.toggle("lc-copy-failed", !ok);
    label.textContent = ok ? button.dataset.copied : button.dataset.failed;
    clearTimeout(button.__lcReset);
    button.__lcReset = setTimeout(() => {
      button.classList.remove("lc-copied", "lc-copy-failed");
      label.textContent = button.dataset.copy;
    }, 2000);
  });
})();
