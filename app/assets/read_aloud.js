// LeafCare AI read-aloud. Injected once per page by utils/ui.py:page_scripts().
//
// The Listen box (ui.listen_box) is plain HTML: a Listen button that carries what to say in data
// attributes (data-parts, a JSON list of sentences; data-lang, a BCP 47 tag such as hi-IN; its labels),
// Slow / Normal / Fast buttons, and an empty caption. These document-level handlers read the parts
// out with the browser's built-in speech synthesis, one sentence at a time, and show the sentence
// being read in the caption with the current word marked (where the voice reports word positions).
// Nothing is installed and nothing leaves the device.
//
// Keep this file free of markup in strings: see the note at the top of theme_switch.js.
(() => {
  if (window.__lcReadAloud) return;
  window.__lcReadAloud = true;

  const synth = window.speechSynthesis;
  if (!synth) { document.documentElement.classList.add("lc-no-speech"); return; }

  const SPEED_KEY = "lc-speech-speed";
  const RATES = { slow: 0.7, normal: 0.95, fast: 1.2 };
  let speed = (() => {
    try { const saved = localStorage.getItem(SPEED_KEY); return saved in RATES ? saved : "normal"; }
    catch { return "normal"; }
  })();

  let session = null;  // what is being read: { button, caption, queue, index, voice, tag, utterance }
  let run = 0;         // bumped whenever speech is restarted or stopped; stale callbacks compare against it

  const setLabel = (button, text) => { button.querySelector(".lc-listen-label").textContent = text; };

  function stop() {
    run += 1;
    synth.cancel();
    if (!session) return;
    session.button.classList.remove("lc-speaking");
    setLabel(session.button, session.button.dataset.listen);
    if (session.caption) session.caption.textContent = "";  // an empty caption is hidden by CSS
    session = null;
  }

  // The sentence being read, with the word at [start, start + length) marked.
  function showCaption(text, start, length) {
    const caption = session && session.caption;
    if (!caption) return;
    caption.textContent = "";
    if (start == null) { caption.textContent = text; return; }
    const end = start + (length || (text.slice(start).match(/^\S+/) || [""])[0].length);
    const mark = document.createElement("mark");
    mark.textContent = text.slice(start, end);
    caption.append(text.slice(0, start), mark, text.slice(end));
  }

  function speakCurrent(interrupt) {
    const myRun = ++run;
    if (interrupt) synth.cancel();
    const s = session;
    const text = s.queue[s.index];
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = s.tag;
    if (s.voice) utterance.voice = s.voice;
    utterance.rate = RATES[speed];
    utterance.onboundary = (e) => { if (myRun === run && e.name === "word") showCaption(text, e.charIndex, e.charLength); };
    utterance.onend = () => {
      if (myRun !== run) return;
      s.index += 1;
      if (s.index < s.queue.length) speakCurrent(false); else stop();
    };
    utterance.onerror = () => { if (myRun === run) stop(); };
    s.utterance = utterance;  // keep a reference: Chrome can drop events of an utterance that was garbage-collected
    showCaption(text);
    synth.speak(utterance);
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

  // One utterance per sentence: short ones avoid a cut-off some browsers apply after about 15 seconds.
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
    const box = button.closest(".lc-listen-box");
    session = { button, caption: box && box.querySelector(".lc-listen-caption"), index: 0, voice, tag,
                queue: sentences(JSON.parse(button.dataset.parts)) };
    button.classList.add("lc-speaking");
    setLabel(button, button.dataset.stop);
    speakCurrent(false);
  }

  // Mark the chosen speed on every Slow / Normal / Fast group (Streamlit renders them with Normal marked).
  function syncSpeed() {
    document.querySelectorAll(".lc-speed button").forEach((b) => {
      const pressed = String(b.dataset.speed === speed);
      if (b.getAttribute("aria-pressed") !== pressed) b.setAttribute("aria-pressed", pressed);
    });
  }

  function setSpeed(value) {
    if (!(value in RATES)) return;
    speed = value;
    try { localStorage.setItem(SPEED_KEY, value); } catch { /* private mode: not remembered */ }
    syncSpeed();
    if (session) speakCurrent(true);  // restart the current sentence at the new speed
  }

  document.addEventListener("click", (event) => {
    const speedButton = event.target.closest(".lc-speed button");
    if (speedButton) { setSpeed(speedButton.dataset.speed); return; }
    const button = event.target.closest(".lc-listen");
    if (!button) return;
    if (session && session.button === button) stop(); else start(button);
  });

  new MutationObserver(syncSpeed).observe(document.body, { childList: true, subtree: true });
  syncSpeed();

  // Stop talking when the visitor leaves the page or the button disappears (new photo, other page).
  window.addEventListener("pagehide", stop);
  setInterval(() => { if (session && !document.body.contains(session.button)) stop(); }, 500);
})();
