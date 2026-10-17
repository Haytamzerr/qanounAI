// Qanoun AI — the interface. Plain JavaScript, no build step: it runs wherever the API runs.
"use strict";

const STRINGS = {
  ar: {
    heroTitle: "اسأل عن القانون المغربي",
    heroSub: "اكتب سؤالك كما تقوله: بالدارجة، بالعربية أو بالفرنسية. نجيبك من النص الرسمي، مع المادة بالضبط.",
    placeholder: "مثلاً: شحال ديال الكونجي عندي فالعام؟",
    ask: "اسأل",
    scriptsNote: "كل هذه الصيغ مفهومة.",
    corpus: (n, laws) => `${n} مادة من ${laws} نصا قانونيا مغربيا، من الدستور إلى مدونة السير`,
    stepUnderstand: "فهم السؤال", stepSearch: "البحث في النصوص", stepWrite: "صياغة الجواب", stepCheck: "التحقق من المراجع",
    copy: "نسخ", share: "مشاركة", copied: "تم النسخ مع المراجع",
    topicsTitle: "مواضيع", topicsSub: "أمثلة لأسئلة شائعة، اضغط لطرحها.",
    allTopics: (n) => `كل المواضيع (${n})`, fewerTopics: "أهم المواضيع فقط", updated: "النص محين بتاريخ", published: "نسخة منشورة على موقع عدالة بتاريخ",
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
    corpus: (n, laws) => `${n} articles de ${laws} textes marocains, de la Constitution au Code de la route`,
    stepUnderstand: "Comprendre la question", stepSearch: "Chercher dans les textes", stepWrite: "Rédiger la réponse", stepCheck: "Vérifier les citations",
    copy: "Copier", share: "Partager", copied: "Copié avec les sources",
    topicsTitle: "Thèmes", topicsSub: "Des questions fréquentes, à poser en un clic.",
    allTopics: (n) => `Tous les thèmes (${n})`, fewerTopics: "Les principaux thèmes", updated: "Texte mis à jour au", published: "Version publiée sur Adala le",
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
    corpus: (n, laws) => `${n} مادة من ${laws} ديال القوانين المغربية، من الدستور حتى لمدونة السير`,
    stepUnderstand: "فهمنا السؤال", stepSearch: "كنقلبو فالنصوص", stepWrite: "كنكتبو الجواب", stepCheck: "كنتأكدو من المواد",
    copy: "نسخ", share: "بارطاجي", copied: "تنسخ مع المواد",
    topicsTitle: "مواضيع", topicsSub: "أسئلة كيتسولو بزاف، ضغط باش تسولها.",
    allTopics: (n) => `كاع المواضيع (${n})`, fewerTopics: "غير المواضيع المهمين", updated: "النص محين ف", published: "النسخة تنشرات فعدالة نهار",
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
  home: '<path d="M4 11l8-7 8 7M6 9.5V20h12V9.5M10 20v-5h4v5"/>',
  penal: '<path d="M12 4v16M7 20h10M5 8h14M5 8l-2.5 6a2.5 2.5 0 0 0 5 0zM19 8l-2.5 6a2.5 2.5 0 0 0 5 0z"/>',
  road: '<path d="M5 16l1.5-5a2 2 0 0 1 1.9-1.4h7.2a2 2 0 0 1 1.9 1.4L19 16M4 16h16v3H4zM7 19v1.5M17 19v1.5"/><circle cx="8" cy="17.5" r=".6"/><circle cx="16" cy="17.5" r=".6"/>',
  property: '<path d="M3 20h18M5 20V10l7-5 7 5v10M9 20v-6h6v6"/>',
  contract: '<path d="M7 3h7l4 4v14H7zM14 3v4h4M10 12h5M10 16h5"/>',
  business: '<path d="M4 20V8h6v12M10 20V4h10v16M7 11h0M7 14h0M13 8h4M13 12h4M13 16h4"/>',
  court: '<path d="M4 10h16M6 10v8M10 10v8M14 10v8M18 10v8M3 20h18M12 3l9 5H3z"/>',
  id: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2.2"/><path d="M5.5 16c.6-1.6 2-2.4 3.5-2.4s2.9.8 3.5 2.4M15 10h3M15 13h3"/>',
  shield: '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
  city: '<path d="M3 20h18M5 20V9h5v11M10 20V5h9v15M7 12h1M7 15h1M13 8h3M13 11h3M13 14h3"/>',
  care: '<path d="M12 20s-7-4.4-7-9.5A3.8 3.8 0 0 1 12 8a3.8 3.8 0 0 1 7 2.5C19 15.6 12 20 12 20z"/>',
};

// The first FEATURED themes are shown; the others open with "all themes".
const FEATURED = 5;
const TOPICS = [
  { icon: "work", name: { ar: "الشغل", fr: "Travail", darija: "الخدمة" }, law: "مدونة الشغل · 65.99",
    examples: ["chhal dyal lconji 3ndi f l3am?", "ما هي مدة فترة الاختبار في عقد الشغل غير محدد المدة؟", "Mon employeur peut-il me licencier sans motif ?"] },
  { icon: "family", name: { ar: "الأسرة", fr: "Famille", darija: "العائلة" }, law: "مدونة الأسرة · 70.03",
    examples: ["ila chi mra mtel9a tzewjat, wach kaymchiwlha lwlad?", "شحال خاص يكون عمر البنت باش تزوج؟", "Que doit le mari à son épouse après un divorce ?"] },
  { icon: "home", name: { ar: "الكراء والسكن", fr: "Logement et loyer", darija: "الكرا والدار" }, law: "67.12 · 49.16 · 07.03",
    examples: ["mol dar bgha ykharjni, wach y9der bla 7okm?", "واش مول الدار يقدر يزيد فالكرا كل عام؟", "Le propriétaire refuse de réparer une fuite : que faire ?"] },
  { icon: "penal", name: { ar: "الجرائم والعقوبات", fr: "Pénal", darija: "الجرائم والحبس" }, law: "مجموعة القانون الجنائي",
    examples: ["chno l3o9oba dyal sser9a?", "واش الدفاع الشرعي كيعفي من العقوبة؟", "Quelle est la peine pour coups et blessures ?"] },
  { icon: "road", name: { ar: "السير والسياقة", fr: "Route et permis", darija: "السوقان والبيرمي" }, law: "مدونة السير · 52.05",
    examples: ["chhal dyal lghrama ila sou9t b tilifoun f yddi?", "شنو كيوقع إلا سقت بلا رخصة السياقة؟", "Que risque-t-on en cas d'excès de vitesse ?"] },
  { icon: "consumer", name: { ar: "المستهلك", fr: "Consommation", darija: "المستهلك" }, law: "حماية المستهلك · 31.08",
    examples: ["chrit chi haja mn internet, chhal 3ndi bach nraj3ha?", "ما هي حقوقي إذا كان المنتوج الذي اشتريته معيبا؟", "En combien de temps le vendeur doit-il me rembourser ?"] },
  { icon: "data", name: { ar: "المعطيات الشخصية", fr: "Données personnelles", darija: "المعطيات الشخصية" }, law: "القانون 09.08",
    examples: ["wach chi charika t9der tsifti liya messages publicitaires bla idn dyali?", "هل يحق لي أن أطلب تصحيح معطياتي الشخصية؟", "Puis-je m'opposer à l'utilisation de mes données ?"] },
  { icon: "property", name: { ar: "العقار والملكية", fr: "Immobilier", darija: "العقار والأرض" }, law: "39.08 · 18.00 · التحفيظ العقاري",
    examples: ["chrina terrain b jouj w bgha ybi3 bou7do, wach y9der?", "ما هي شروط اكتساب الملكية بالحيازة؟", "Qui paie les charges communes d'un immeuble en copropriété ?"] },
  { icon: "contract", name: { ar: "العقود والديون", fr: "Contrats et dettes", darija: "العقود والديون" }, law: "قانون الالتزامات والعقود",
    examples: ["sellft chi flous l wa7ed w ma bghach yrdhom, chno ndir?", "متى يكون العقد باطلا؟", "Combien de temps ai-je pour réclamer une dette ?"] },
  { icon: "business", name: { ar: "التجارة والشركات", fr: "Commerce et sociétés", darija: "التجارة والشركات" }, law: "مدونة التجارة · 15.95 · 17.95",
    examples: ["chhal mn wa9t bach yt9adem chek bla rassid?", "ما هي شروط تأسيس شركة المساهمة؟", "Qu'est-ce qu'un fonds de commerce ?"] },
  { icon: "court", name: { ar: "المحاكم والمساطر", fr: "Tribunaux et procédures", darija: "المحاكم والمساطر" }, law: "المسطرة المدنية 58.25 · المسطرة الجنائية 22.01",
    examples: ["ila tchedit, chhal y9der yb9ani lbolis 9bel ma nchouf l2avocat?", "ما هو أجل استئناف حكم مدني؟", "Quels sont mes droits pendant la garde à vue ?"] },
  { icon: "id", name: { ar: "الحالة المدنية والجنسية", fr: "État civil et nationalité", darija: "الوثائق والجنسية" }, law: "36.21 · قانون الجنسية",
    examples: ["wlidi tzad f lkharij, wach kayakhod ljinsiya lmaghribiya?", "كيف أصرح بولادة في الحالة المدنية؟", "Peut-on acquérir la nationalité marocaine par mariage ?"] },
  { icon: "shield", name: { ar: "حوادث الشغل والضمان الاجتماعي", fr: "Accidents du travail et CNSS", darija: "حوادث الخدمة ولاكنوب" }, law: "18.12 · الضمان الاجتماعي",
    examples: ["tjre7t f lkhdma, chkoun li khaso y3wedni?", "ما هي التعويضات المستحقة عن حادثة شغل؟", "Quelles prestations verse la CNSS ?"] },
  { icon: "city", name: { ar: "التعمير والبناء", fr: "Urbanisme et construction", darija: "البني والرخص" }, law: "12.90 · 66.12",
    examples: ["jari bna bla rokhsa w sedd 3liya dow, fin nchki?", "ما هي العقوبة على البناء بدون رخصة؟", "Faut-il une autorisation pour agrandir sa maison ?"] },
  { icon: "care", name: { ar: "المرأة والطفل", fr: "Femmes et enfants", darija: "المرا والدراري" }, law: "103.13 · كفالة الأطفال 15.01",
    examples: ["rajli kaydrebni, chno kay9oul l9anoun?", "ما هي شروط كفالة طفل مهمل؟", "Que prévoit la loi contre le harcèlement sexuel ?"] },
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
let allTopics = false;
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
    if (articleCount === null) articleCount = await (await fetch("/health")).json();
    const fmt = (n) => n.toLocaleString(lang === "fr" ? "fr-FR" : "ar-MA");
    $("corpus").textContent = t("corpus", fmt(articleCount.articles), fmt(articleCount.laws ?? 0));
  } catch { $("corpus").textContent = ""; }
}

// ---------- topics: a side option ----------
function renderTopics() {
  const list = $("topics");
  list.innerHTML = "";
  TOPICS.forEach((topic, i) => {
    if (!allTopics && i >= FEATURED && openTopic !== i) return;
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
  const more = document.createElement("button");
  more.className = "topics-more";
  more.setAttribute("aria-expanded", String(allTopics));
  more.innerHTML = `<span>${allTopics ? t("fewerTopics") : t("allTopics", TOPICS.length)}</span><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>`;
  more.addEventListener("click", () => { allTopics = !allTopics; renderTopics(); });
  list.append(more);
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

  $("flag").hidden = data.verified && data.status !== "not_covered";
  $("flag").textContent = data.status === "not_covered" ? t("notCovered") : t("unverified");

  const list = $("cited");
  list.innerHTML = "";
  data.citations.forEach((c, i) => {
    const b = document.createElement("button");
    if (animate) { b.className = "reveal"; b.style.setProperty("--i", i); }
    b.innerHTML = `<b>${c.number}</b><span>${escapeHtml(c.law_title)} — ${escapeHtml(c.label || t("article"))} ${escapeHtml(c.article_number)}</span>`;
    b.addEventListener("click", () => openArticle(c.number, b));
    list.append(b);
  });
  const total = Object.values(data.seconds).reduce((a, b) => a + b, 0);
  $("meta").textContent = t("seconds", total.toFixed(1));
}

function citationText(data) {
  const sources = data.citations.map((c) => `[${c.number}] ${c.law_title}, ${c.label || t("article")} ${c.article_number}`);
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
      <h2>${escapeHtml(c.label)} ${escapeHtml(c.article_number)}${c.title ? ` — ${escapeHtml(c.title)}` : ""}</h2>
      <p class="law">${escapeHtml(c.law_title)}</p>
      ${c.updated ? `<p class="version">${t(/^\d{4}-\d{2}-\d{2}$/.test(c.updated) ? "published" : "updated")} ${escapeHtml(c.updated)}</p>` : ""}
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
