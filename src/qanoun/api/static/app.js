// Qanoun AI — the interface. Plain JavaScript, no build step: it runs wherever the API runs.
"use strict";

const STRINGS = {
  ar: {
    heroTitle: "اسأل عن القانون المغربي",
    heroSub: "اكتب سؤالك كما تقوله: بالدارجة، بالعربية أو بالفرنسية. نجيبك من النص الرسمي، مع المادة بالضبط.",
    placeholder: "مثلاً: شحال ديال الكونجي عندي فالعام؟",
    ask: "اسأل",
    scriptsNote: "كل هذه الصيغ مفهومة.",
    corpus: (n) => `${n} مادة من 4 نصوص: مدونة الشغل، مدونة الأسرة، حماية المستهلك، حماية المعطيات الشخصية`,
    stepUnderstand: "فهم السؤال", stepSearch: "البحث في النصوص", stepWrite: "صياغة الجواب", stepCheck: "التحقق من المراجع",
    copy: "نسخ", share: "مشاركة", copied: "تم النسخ مع المراجع",
    topicsTitle: "مواضيع", topicsSub: "أمثلة لأسئلة شائعة، اضغط لطرحها.",
    disclaimer: "قانون AI يقدم معلومات قانونية عامة وليس استشارة قانونية. النص العربي المنشور في الجريدة الرسمية هو النص الرسمي.",
    history: "الأسئلة السابقة", clearHistory: "مسح السجل", emptyHistory: "لا توجد أسئلة بعد.",
    close: "إغلاق", theme: "الوضع الليلي", interfaceLanguage: "لغة الواجهة",
    unverified: "تنبيه: لم يجتز هذا الجواب التحقق الكامل من المراجع. راجع المواد المذكورة قبل الاعتماد عليه.",
    notCovered: "لا يغطي هذا السؤال أي نص من النصوص المتوفرة.",
    article: "المادة", official: "النص الرسمي", translation: "ترجمة", openPdf: "فتح النص الكامل (PDF)",
    seconds: (s) => `${s} ث`, error: "تعذّر الجواب: ",
  },
  fr: {
    heroTitle: "Posez votre question sur le droit marocain",
    heroSub: "Écrivez comme vous parlez : en darija, en arabe ou en français. La réponse vient du texte officiel, avec l'article exact.",
    placeholder: "Par exemple : combien de jours de congé par an ?",
    ask: "Demander",
    scriptsNote: "Toutes ces façons d'écrire sont comprises.",
    corpus: (n) => `${n} articles de 4 textes : Code du travail, Code de la famille, protection du consommateur, données personnelles`,
    stepUnderstand: "Comprendre la question", stepSearch: "Chercher dans les textes", stepWrite: "Rédiger la réponse", stepCheck: "Vérifier les citations",
    copy: "Copier", share: "Partager", copied: "Copié avec les sources",
    topicsTitle: "Thèmes", topicsSub: "Des questions fréquentes, à poser en un clic.",
    disclaimer: "Qanoun AI donne une information juridique générale, pas un conseil juridique. Le texte arabe publié au Bulletin officiel fait foi.",
    history: "Questions précédentes", clearHistory: "Effacer l'historique", emptyHistory: "Aucune question pour l'instant.",
    close: "Fermer", theme: "Mode sombre", interfaceLanguage: "Langue de l'interface",
    unverified: "Attention : cette réponse n'a pas passé toute la vérification des citations. Vérifiez les articles cités avant de vous y fier.",
    notCovered: "Aucun des textes disponibles ne couvre cette question.",
    article: "Article", official: "Texte officiel", translation: "Traduction", openPdf: "Ouvrir le texte complet (PDF)",
    seconds: (s) => `${s} s`, error: "Réponse impossible : ",
  },
  darija: {
    heroTitle: "سول على القانون المغربي",
    heroSub: "كتب السؤال ديالك كيف كتهضر: بالدارجة، بالعربية ولا بالفرنساوية. كنجاوبوك من النص الرسمي، مع المادة بالضبط.",
    placeholder: "بحال: واش الباطرون يقدر يجري عليا بلا سبب؟",
    ask: "سول",
    scriptsNote: "كاع هاد الطرق ديال الكتابة مفهومة.",
    corpus: (n) => `${n} مادة من 4 ديال النصوص: الخدمة، العائلة، المستهلك، المعطيات الشخصية`,
    stepUnderstand: "فهمنا السؤال", stepSearch: "كنقلبو فالنصوص", stepWrite: "كنكتبو الجواب", stepCheck: "كنتأكدو من المواد",
    copy: "نسخ", share: "بارطاجي", copied: "تنسخ مع المواد",
    topicsTitle: "مواضيع", topicsSub: "أسئلة كيتسولو بزاف، ضغط باش تسولها.",
    disclaimer: "قانون AI كيعطي معلومات قانونية عامة، ماشي استشارة ديال محامي. النص العربي ديال الجريدة الرسمية هو اللي كيتعتامد.",
    history: "الأسئلة اللي فاتو", clearHistory: "مسح كلشي", emptyHistory: "مازال ما سولتي والو.",
    close: "سد", theme: "الوضع ديال الليل", interfaceLanguage: "لغة الواجهة",
    unverified: "رد البال: هاد الجواب ما دازش التحقق كامل. شوف المواد المذكورة قبل ما تعتامد عليه.",
    notCovered: "حتى نص من النصوص اللي عندنا ما كيجاوب على هاد السؤال.",
    article: "المادة", official: "النص الرسمي", translation: "ترجمة", openPdf: "حل النص كامل (PDF)",
    seconds: (s) => `${s} ث`, error: "ما قدرناش نجاوبو: ",
  },
};

const ICONS = {
  work: '<path d="M4 8h16v11H4zM9 8V5h6v3M4 13h16"/>',
  family: '<circle cx="8" cy="7" r="3"/><circle cx="17" cy="9" r="2.4"/><path d="M3 20c0-3 2.3-5.5 5-5.5s5 2.5 5 5.5M13.5 20c0-2.4 1.6-4.3 3.5-4.3S20.5 17.6 20.5 20"/>',
  consumer: '<path d="M5 7h14l-1.5 12h-11zM9 7a3 3 0 0 1 6 0"/>',
  data: '<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v2"/>',
};

const TOPICS = [
  { icon: "work", name: { ar: "الشغل", fr: "Travail", darija: "الخدمة" }, law: "مدونة الشغل · 65.99",
    examples: ["chhal dyal lconji 3ndi f l3am?", "ما هي مدة فترة الاختبار في عقد الشغل غير محدد المدة؟", "Mon employeur peut-il me licencier sans motif ?"] },
  { icon: "family", name: { ar: "الأسرة", fr: "Famille", darija: "العائلة" }, law: "مدونة الأسرة · 70.03",
    examples: ["ila chi mra mtel9a tzewjat, wach kaymchiwlha lwlad?", "شحال خاص يكون عمر البنت باش تزوج؟", "Que doit le mari à son épouse après un divorce ?"] },
  { icon: "consumer", name: { ar: "المستهلك", fr: "Consommation", darija: "المستهلك" }, law: "حماية المستهلك · 31.08",
    examples: ["chrit chi haja mn internet, chhal 3ndi bach nraj3ha?", "ما هي حقوقي إذا كان المنتوج الذي اشتريته معيبا؟", "En combien de temps le vendeur doit-il me rembourser ?"] },
  { icon: "data", name: { ar: "المعطيات الشخصية", fr: "Données personnelles", darija: "المعطيات الشخصية" }, law: "القانون 09.08",
    examples: ["wach chi charika t9der tsifti liya messages publicitaires bla idn dyali?", "هل يحق لي أن أطلب تصحيح معطياتي الشخصية؟", "Puis-je m'opposer à l'utilisation de mes données ?"] },
];

const RTL_LANGUAGES = new Set(["ar", "darija-ar"]);
const $ = (id) => document.getElementById(id);
const store = {  // browser storage can be unavailable (private mode): never break the page
  get(key, fallback) { try { const v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); } catch { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* ignore */ } },
};

let lang = store.get("qanoun.lang", navigator.language?.startsWith("fr") ? "fr" : "ar");
let current = null;   // the answer on screen
let openTopic = null;
const t = (key, ...args) => { const v = STRINGS[lang][key]; return typeof v === "function" ? v(...args) : v; };

// ---------- interface language ----------
function applyLanguage() {
  const rtl = lang !== "fr";
  document.documentElement.lang = lang === "fr" ? "fr" : "ar";
  document.documentElement.dir = rtl ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => { el.title = t(el.dataset.i18nTitle); el.setAttribute("aria-label", el.title); });
  document.querySelectorAll("[data-i18n-label]").forEach((el) => el.setAttribute("aria-label", t(el.dataset.i18nLabel)));
  document.querySelectorAll(".lang button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.lang === lang)));
  renderTopics();
  loadCorpus();
  if (current) renderAnswer(current, false);
}
document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {
  lang = b.dataset.lang; store.set("qanoun.lang", lang); applyLanguage();
}));

// ---------- theme ----------
const savedTheme = store.get("qanoun.theme", null);
if (savedTheme) document.documentElement.dataset.theme = savedTheme;
$("theme").addEventListener("click", () => {
  const dark = document.documentElement.dataset.theme
    ? document.documentElement.dataset.theme === "dark"
    : matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.dataset.theme = dark ? "light" : "dark";
  store.set("qanoun.theme", document.documentElement.dataset.theme);
});

// ---------- corpus line ----------
let articleCount = null;
async function loadCorpus() {
  try {
    if (articleCount === null) articleCount = (await (await fetch("/health")).json()).articles;
    $("corpus").textContent = t("corpus", articleCount.toLocaleString(lang === "fr" ? "fr-FR" : "ar-MA"));
  } catch { $("corpus").textContent = ""; }
}

// ---------- topics: a side option ----------
function renderTopics() {
  const list = $("topics");
  list.innerHTML = "";
  TOPICS.forEach((topic, i) => {
    const item = document.createElement("div");
    item.className = "topic";
    item.setAttribute("open-state", String(openTopic === i));
    item.innerHTML = `
      <button aria-expanded="${openTopic === i}">
        <span class="topic-icon"><svg viewBox="0 0 24 24">${ICONS[topic.icon]}</svg></span>
        <span class="topic-name">${topic.name[lang]}<span class="topic-law">${topic.law}</span></span>
        <svg class="topic-chevron" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>
      </button>
      <div class="topic-examples"><div></div></div>`;
    const inner = item.querySelector(".topic-examples > div");
    topic.examples.forEach((q) => {
      const b = document.createElement("button");
      b.dir = "auto"; b.textContent = q;
      b.addEventListener("click", () => { $("question").value = q; ask(q); });
      inner.append(b);
    });
    item.querySelector("button").addEventListener("click", () => {
      openTopic = openTopic === i ? null : i;
      renderTopics();
    });
    list.append(item);
  });
}

// ---------- asking (streamed progress, then the checked answer) ----------
const STEP_ORDER = ["understood", "sources", "writing", "answer"];
function markStep(name) {
  const reached = STEP_ORDER.indexOf(name);
  document.querySelectorAll("#steps li").forEach((li) => {
    const i = STEP_ORDER.indexOf(li.dataset.step);
    li.classList.toggle("done", i < reached || name === "done");
    li.classList.toggle("active", i === reached && name !== "done");
  });
}

async function ask(question) {
  question = question.trim();
  if (question.length < 2) return;
  const button = document.querySelector(".ask-btn");
  button.disabled = true;
  current = null;
  $("workspace").classList.remove("idle");
  $("result").hidden = false;
  $("asked").textContent = question;
  $("answer").hidden = true;
  $("error").hidden = true;
  $("thinking").hidden = false;
  markStep("understood");
  $("result").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });

  try {
    const response = await fetch("/ask/stream", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }),
    });
    if (!response.ok) throw new Error((await response.json()).detail || response.statusText);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let cut;
      while ((cut = buffer.indexOf("\n\n")) >= 0) {
        const block = buffer.slice(0, cut); buffer = buffer.slice(cut + 2);
        const event = /event: (.*)/.exec(block)?.[1];
        const data = JSON.parse(/data: (.*)/s.exec(block)?.[1] ?? "null");
        if (event === "understood") markStep("sources");
        else if (event === "sources") markStep("writing");
        else if (event === "writing") markStep(data.attempt > 1 ? "answer" : "writing");
        else if (event === "answer") { markStep("done"); current = data; renderAnswer(data, true); remember(data); }
        else if (event === "error") throw new Error(data.message);
      }
    }
  } catch (error) {
    $("thinking").hidden = true;
    $("error").textContent = t("error") + error.message;
    $("error").hidden = false;
  } finally {
    button.disabled = false;
  }
}

document.querySelectorAll(".scripts button").forEach((b) => b.addEventListener("click", () => {
  $("question").value = b.textContent; ask(b.textContent);
}));
$("ask").addEventListener("submit", (e) => { e.preventDefault(); ask($("question").value); });
$("question").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask($("question").value); }
});
$("question").addEventListener("input", (e) => { e.target.style.height = "auto"; e.target.style.height = `${e.target.scrollHeight}px`; });

// ---------- the answer ----------
function escapeHtml(s) { return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

function renderAnswer(data, animate) {
  $("thinking").hidden = true;
  const box = $("answer");
  box.hidden = false;
  box.style.animation = animate ? "" : "none";
  const text = $("answer-text");
  text.dir = RTL_LANGUAGES.has(data.language) ? "rtl" : "ltr";
  const cited = new Set(data.citations.map((c) => c.number));
  text.innerHTML = escapeHtml(data.text)
    .split(/\n{2,}/).map((p) => `<p>${p.replace(/\n/g, "<br>")}</p>`).join("")
    .replace(/\[(\d+)\]/g, (m, n) => cited.has(+n)
      ? `<button class="cite" data-n="${n}" aria-expanded="false" aria-label="${t("article")} ${n}">${n}</button>` : "");
  text.querySelectorAll(".cite").forEach((b) => b.addEventListener("click", () => openArticle(+b.dataset.n, b)));

  $("flag").hidden = data.verified && data.status === "answered";
  $("flag").textContent = data.status === "not_covered" ? t("notCovered") : t("unverified");

  const list = $("cited");
  list.innerHTML = "";
  data.citations.forEach((c, i) => {
    const b = document.createElement("button");
    if (animate) { b.className = "reveal"; b.style.setProperty("--i", i); }
    b.innerHTML = `<b>${c.number}</b><span>${escapeHtml(c.law_title)} — ${t("article")} ${escapeHtml(c.article_number)}</span>`;
    b.addEventListener("click", () => openArticle(c.number, b));
    list.append(b);
  });
  const total = Object.values(data.seconds).reduce((a, b) => a + b, 0);
  $("meta").textContent = t("seconds", total.toFixed(1));
}

function citationText(data) {
  const sources = data.citations.map((c) => `[${c.number}] ${c.law_title}, ${t("article")} ${c.article_number}`);
  return `${data.question}\n\n${data.text}\n\n${sources.join("\n")}\n\n— Qanoun AI`;
}
function toast(message) {
  const el = $("toast"); el.textContent = message; el.hidden = false;
  clearTimeout(toast.timer); toast.timer = setTimeout(() => { el.hidden = true; }, 2200);
}
$("copy").addEventListener("click", async () => {
  if (!current) return;
  try { await navigator.clipboard.writeText(citationText(current)); toast(t("copied")); } catch { /* clipboard blocked */ }
});
$("share").addEventListener("click", async () => {
  if (!current) return;
  const text = citationText(current);
  if (navigator.share) { try { await navigator.share({ title: "Qanoun AI", text }); return; } catch { return; } }
  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener");
});

// ---------- side panels ----------
let opener = null;
function openPanel(id, from) {
  opener = from || document.activeElement;
  $(id).classList.add("open"); $(id).setAttribute("aria-hidden", "false");
  $("scrim").hidden = false;
  $(id).focus();
}
function closePanels() {
  document.querySelectorAll(".panel.open").forEach((p) => { p.classList.remove("open"); p.setAttribute("aria-hidden", "true"); });
  document.querySelectorAll('.cite[aria-expanded="true"]').forEach((c) => c.setAttribute("aria-expanded", "false"));
  $("scrim").hidden = true;
  opener?.focus?.();
}
$("scrim").addEventListener("click", closePanels);
$("panel-close").addEventListener("click", closePanels);
$("history-close").addEventListener("click", closePanels);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closePanels(); });

function openArticle(number, from) {
  const c = current?.citations.find((x) => x.number === number);
  if (!c) return;
  document.querySelectorAll(`.cite[data-n="${number}"]`).forEach((b) => b.setAttribute("aria-expanded", "true"));
  const rtl = c.id.includes("-ar-");
  $("panel-body").innerHTML = `
    <div dir="${rtl ? "rtl" : "ltr"}">
      <span class="badge">${c.official ? t("official") : t("translation")}</span>
      <h2>${rtl ? "المادة" : "Article"} ${escapeHtml(c.article_number)}${c.title ? ` — ${escapeHtml(c.title)}` : ""}</h2>
      <p class="law">${escapeHtml(c.law_title)}</p>
      <ul class="path">${c.hierarchy.map((h) => `<li>${escapeHtml(h)}</li>`).join("")}</ul>
      <p class="article-text">${escapeHtml(c.text)}</p>
      <a class="pdf" href="${escapeHtml(c.source_url)}" target="_blank" rel="noopener">${t("openPdf")}</a>
    </div>`;
  openPanel("panel", from);
}

// ---------- history (this device only) ----------
function remember(data) {
  const items = store.get("qanoun.history", []).filter((h) => h.question !== data.question);
  items.unshift({ question: data.question, at: Date.now(), answer: data });
  store.set("qanoun.history", items.slice(0, 30));
}
function renderHistory() {
  const items = store.get("qanoun.history", []);
  const list = $("history-list");
  list.innerHTML = items.length ? "" : `<li>${t("emptyHistory")}</li>`;
  items.forEach((h) => {
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.dir = "auto";
    const when = new Date(h.at).toLocaleString(lang === "fr" ? "fr-FR" : "ar-MA", { dateStyle: "medium", timeStyle: "short" });
    b.innerHTML = `${escapeHtml(h.question)}<small dir="${lang === "fr" ? "ltr" : "rtl"}">${when}</small>`;
    b.addEventListener("click", () => {
      closePanels();
      current = h.answer;
      $("workspace").classList.remove("idle");
      $("result").hidden = false; $("error").hidden = true;
      $("asked").textContent = h.question;
      markStep("done");
      renderAnswer(h.answer, true);
      $("result").scrollIntoView({ block: "start" });
    });
    li.append(b); list.append(li);
  });
}
$("history-open").addEventListener("click", (e) => { renderHistory(); openPanel("history", e.currentTarget); });
$("history-clear").addEventListener("click", () => { store.set("qanoun.history", []); renderHistory(); });

applyLanguage();
