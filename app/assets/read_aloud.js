// LeafCare AI read-aloud. Injected once per page by utils/ui.py:page_scripts().
//
// The Listen button (ui.listen_button) is plain HTML that carries what to say in data attributes:
// data-parts (a JSON list of sentences), data-lang (a BCP 47 tag such as hi-IN) and its labels.
// This one document-level click handler reads the parts out with the browser's built-in speech
// synthesis, so nothing is installed and nothing leaves the device.
//
// Keep this file free of markup in strings: see the note at the top of theme_switch.js.
(() => {
  if (window.__lcReadAloud) return;
  window.__lcReadAloud = true;

  const synth = window.speechSynthesis;
  if (!synth) { document.documentElement.classList.add("lc-no-speech"); return; }

  let active = null;  // the button that is speaking right now
  let run = 0;        // bumped on every start/stop, so callbacks from an older run are ignored

  const setLabel = (button, text) => { button.querySelector(".lc-listen-label").textContent = text; };

  function stop() {
    run += 1;
    synth.cancel();
    if (active) {
      active.classList.remove("lc-speaking");
      setLabel(active, active.dataset.listen);
      active = null;
    }
  }

  // Chrome loads its voice list asynchronously: wait for it briefly on the first click.
  function voices() {
    const list = synth.getVoices();
    if (list.length) return Promise.resolve(list);
    return new Promise((resolve) => {
      const done = () => resolve(synth.getVoices());
      synth.addEventListener("voiceschanged", done, { once: true });
      setTimeout(done, 1000);
    });
  }

  function pickVoice(list, tag) {
    const norm = (lang) => lang.replace("_", "-").toLowerCase();
    const base = tag.split("-")[0].toLowerCase();
    return list.find((v) => norm(v.lang) === tag.toLowerCase())
      || list.find((v) => norm(v.lang).split("-")[0] === base)
      || null;
  }

  // Short utterances: some browsers stop a single long one after about 15 seconds.
  const sentences = (parts) => parts
    .flatMap((part) => part.split(/(?<=[.!?।])\s+/))
    .map((s) => s.trim())
    .filter(Boolean);

  async function start(button) {
    stop();
    const myRun = run;
    const tag = button.dataset.lang;
    const list = await voices();
    if (myRun !== run) return;  // the visitor clicked again while we waited
    const voice = pickVoice(list, tag);
    if (list.length && !voice) {
      setLabel(button, button.dataset.noVoice);
      button.classList.add("lc-no-voice");
      setTimeout(() => { button.classList.remove("lc-no-voice"); setLabel(button, button.dataset.listen); }, 4000);
      return;
    }

    active = button;
    button.classList.add("lc-speaking");
    setLabel(button, button.dataset.stop);
    const queue = sentences(JSON.parse(button.dataset.parts));
    queue.forEach((text, i) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = tag;
      if (voice) utterance.voice = voice;
      utterance.rate = 0.95;
      if (i === queue.length - 1) utterance.onend = () => { if (myRun === run) stop(); };
      utterance.onerror = () => { if (myRun === run) stop(); };
      synth.speak(utterance);
    });
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".lc-listen");
    if (!button) return;
    if (button === active) stop(); else start(button);
  });

  // Stop talking when the visitor leaves the page or the button disappears (new photo, other page).
  window.addEventListener("pagehide", stop);
  setInterval(() => { if (active && !document.body.contains(active)) stop(); }, 500);
})();
