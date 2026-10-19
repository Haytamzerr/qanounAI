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
    modeLabel: "نوع الجواب", modeQuick: "جواب سريع", modeAnalysis: "تحليل وضعيتي",
    hintQuick: "جواب قصير من المواد الأقرب إلى سؤالك.",
    hintAnalysis: "يفهم وضعيتك، يبحث في عدة قوانين، ثم يشرح ما ينطبق عليك والخطوات الممكنة.",
    stepPlan: "تخطيط البحث", searched: "بحثنا في:", newChat: "محادثة جديدة", understoodAs: "فهمنا سؤالك هكذا:",
    followupPlaceholder: "سؤال متابعة… مثلاً: وإذا كان عندي أطفال؟", earlier: "عرض المزيد",
    secSituation: "وضعيتك", secLaw: "ماذا يقول القانون", secApplication: "ماذا يعني ذلك بالنسبة لك",
    secSteps: "ما يمكنك فعله", secMissing: "معلومات تنقصنا",
    allTopics: (n) => `كل المواضيع (${n})`, fewerTopics: "أهم المواضيع فقط", updated: "النص محين بتاريخ", published: "نسخة منشورة على موقع عدالة بتاريخ",
    disclaimer: "قانون AI يقدم معلومات قانونية عامة وليس استشارة قانونية. النص العربي المنشور في الجريدة الرسمية هو النص الرسمي.",
    history: "الأسئلة السابقة", clearHistory: "مسح السجل", emptyHistory: "لا توجد أسئلة بعد.",
    close: "إغلاق", theme: "الوضع الليلي", interfaceLanguage: "لغة الواجهة",
    unverified: "تنبيه: لم يجتز هذا الجواب التحقق الكامل من المراجع. راجع المواد المذكورة قبل الاعتماد عليه.",
    notCovered: "لا يغطي هذا السؤال أي نص من النصوص المتوفرة.",
    article: "المادة", official: "النص الرسمي", translation: "ترجمة", openPdf: "فتح النص الكامل (PDF)",
    seconds: (s) => `${s} ث`, error: "تعذّر الجواب: ",
    ctaSituation: "حلّل وضعيتي خطوة بخطوة", backHome: "سؤال سريع", editFile: "تعديل الملف", print: "طباعة / PDF",
    bTitle: "احكِ لنا ما وقع", bSub: "خطوات قصيرة. نكتب ملفك ونحن نتقدم، ثم نحلله من النصوص الرسمية.",
    stepOf: (i, n) => `الخطوة ${i} من ${n}`, next: "التالي", back: "رجوع", skip: "تخطي", analyse: "حلّل وضعيتي",
    qTheme: "ما موضوع المشكل؟", qRole: "من أنت في هذه القصة؟", qStory: "ماذا وقع؟", qWhen: "متى وقع ذلك؟", qGoal: "ماذا تريد؟", qReview: "راجع ملفك",
    hStory: "بكلماتك وبأي لغة. لا نحتاج الأسماء ولا أرقام البطاقة أو الهاتف.", hWhen: "الآجال القانونية قد تغيّر الجواب.", hGoal: "اختر واحدا أو أكثر.",
    hReview: "كل سطر في الملف قابل للتعديل: اضغط عليه. بعد ذلك:",
    reviewSteps: ["نحدد الأسئلة القانونية التي تطرحها وضعيتك", "نبحث في عدة قوانين عن المواد التي تنطبق عليها", "نكتب لك خمسة أقسام، وكل مرجع متحقق منه"],
    storyPlaceholder: "مثلا: أكتري شقة منذ سنتين، والسقف صار يقطر، والمالك يرفض الإصلاح…", minStory: "اكتب جملة أو جملتين على الأقل.",
    qProof: "ماذا لديك؟", dictate: "إملاء صوتي", listening: "أستمع…",
    privacy: "يبدو أن نصك يحتوي على رقم هاتف أو بطاقة أو بريد إلكتروني. لا نحتاجها.", hide: "إخفاؤها",
    fileTitle: "ملفك", fileTheme: "الموضوع", fileRole: "أنا", fileStory: "ما وقع", fileProof: "لدي", fileWhen: "متى", fileGoal: "أريد",
    fileNote: "لا يُحفظ ملفك على أي خادم.", otherTheme: "موضوع آخر", tapMissing: "اضغط على سؤال لتجيب عنه:",
    whens: ["هذا الأسبوع", "هذا الشهر", "من شهر إلى سنة", "منذ أكثر من سنة", "ما زال مستمرا"],
    goals: ["معرفة حقوقي", "استرجاع مال أو تعويض", "إيقاف ما يحدث", "الدفاع عن نفسي", "الخطوات وأين أذهب", "الوثائق التي أحتاجها"],
    proofs: ["عقد مكتوب", "وصولات أو أداءات", "رسائل أو صور", "شهود", "شكاية سبق تقديمها", "لا شيء بعد"],
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
    modeLabel: "Type de réponse", modeQuick: "Réponse rapide", modeAnalysis: "Analyser ma situation",
    hintQuick: "Une réponse courte, tirée des articles les plus proches.",
    hintAnalysis: "Comprend votre situation, cherche dans plusieurs lois, puis explique ce qui s'applique à vous et les démarches.",
    stepPlan: "Planifier la recherche", searched: "Recherches effectuées :", newChat: "Nouvelle conversation", understoodAs: "Question comprise ainsi :",
    followupPlaceholder: "Question de suivi… ex. : et si j'ai des enfants ?", earlier: "Voir plus",
    secSituation: "Votre situation", secLaw: "Ce que dit la loi", secApplication: "Ce que cela signifie pour vous",
    secSteps: "Ce que vous pouvez faire", secMissing: "Ce qu'il faudrait savoir",
    allTopics: (n) => `Tous les thèmes (${n})`, fewerTopics: "Les principaux thèmes", updated: "Texte mis à jour au", published: "Version publiée sur Adala le",
    disclaimer: "Qanoun AI donne une information juridique générale, pas un conseil juridique. Le texte arabe publié au Bulletin officiel fait foi.",
    history: "Questions précédentes", clearHistory: "Effacer l'historique", emptyHistory: "Aucune question pour l'instant.",
    close: "Fermer", theme: "Mode sombre", interfaceLanguage: "Langue de l'interface",
    unverified: "Attention : cette réponse n'a pas passé toute la vérification des citations. Vérifiez les articles cités avant de vous y fier.",
    notCovered: "Aucun des textes disponibles ne couvre cette question.",
    article: "Article", official: "Texte officiel", translation: "Traduction", openPdf: "Ouvrir le texte complet (PDF)",
    seconds: (s) => `${s} s`, error: "Réponse impossible : ",
    ctaSituation: "Analyser ma situation, étape par étape", backHome: "Question rapide", editFile: "Modifier le dossier", print: "Imprimer / PDF",
    bTitle: "Racontez-nous ce qui s'est passé", bSub: "Quelques étapes courtes. Votre dossier s'écrit au fur et à mesure, puis nous l'analysons à partir des textes officiels.",
    stepOf: (i, n) => `Étape ${i} sur ${n}`, next: "Suivant", back: "Retour", skip: "Passer", analyse: "Analyser ma situation",
    qTheme: "De quoi s'agit-il ?", qRole: "Qui êtes-vous dans cette histoire ?", qStory: "Que s'est-il passé ?", qWhen: "Quand cela s'est-il passé ?", qGoal: "Qu'attendez-vous ?", qReview: "Relisez votre dossier",
    hStory: "Avec vos mots, dans la langue que vous voulez. Pas besoin de noms, de numéro de CIN ou de téléphone.", hWhen: "Les délais légaux peuvent changer la réponse.", hGoal: "Choisissez-en un ou plusieurs.",
    hReview: "Chaque ligne du dossier se modifie d'un clic. Ensuite :",
    reviewSteps: ["Nous repérons les questions juridiques que pose votre situation", "Nous cherchons les articles applicables dans plusieurs lois", "Nous rédigeons cinq parties, chaque citation vérifiée"],
    storyPlaceholder: "Ex. : je loue un appartement depuis deux ans, le plafond fuit et le propriétaire refuse de réparer…", minStory: "Écrivez au moins une ou deux phrases.",
    qProof: "Qu'avez-vous en main ?", dictate: "Dicter", listening: "J'écoute…",
    privacy: "Votre texte semble contenir un numéro de téléphone, de CIN ou un e-mail. Nous n'en avons pas besoin.", hide: "Les masquer",
    fileTitle: "Votre dossier", fileTheme: "Sujet", fileRole: "Je suis", fileStory: "Les faits", fileProof: "J'ai", fileWhen: "Quand", fileGoal: "Je veux",
    fileNote: "Votre dossier n'est enregistré sur aucun serveur.", otherTheme: "Autre sujet", tapMissing: "Touchez une question pour y répondre :",
    whens: ["Cette semaine", "Ce mois-ci", "Il y a 1 à 12 mois", "Il y a plus d'un an", "Ça continue"],
    goals: ["Connaître mes droits", "Récupérer de l'argent ou une indemnité", "Faire cesser la situation", "Me défendre", "Les démarches et où aller", "Les documents à préparer"],
    proofs: ["Un contrat écrit", "Des reçus ou paiements", "Des messages ou photos", "Des témoins", "Une plainte déjà déposée", "Rien pour l'instant"],
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
    modeLabel: "نوع الجواب", modeQuick: "جواب دغيا", modeAnalysis: "حلل ليا الوضعية",
    hintQuick: "جواب قصير من المواد اللي قراب لسؤالك.",
    hintAnalysis: "كيفهم الوضعية ديالك، كيقلب فبزاف ديال القوانين، ومن بعد كيشرح ليك شنو كيتطبق عليك وشنو تقدر دير.",
    stepPlan: "كنخططو للبحث", searched: "قلبنا على:", newChat: "محادثة جديدة", understoodAs: "فهمنا السؤال هكا:",
    followupPlaceholder: "سول على نفس الموضوع… بحال: وإلا عندي الدراري؟", earlier: "شوف كثر",
    secSituation: "الوضعية ديالك", secLaw: "شنو كيقول القانون", secApplication: "شنو كيعني هادشي ليك",
    secSteps: "شنو تقدر دير", secMissing: "شنو خاصنا نعرفو",
    allTopics: (n) => `كاع المواضيع (${n})`, fewerTopics: "غير المواضيع المهمين", updated: "النص محين ف", published: "النسخة تنشرات فعدالة نهار",
    disclaimer: "قانون AI كيعطي معلومات قانونية عامة، ماشي استشارة ديال محامي. النص العربي ديال الجريدة الرسمية هو اللي كيتعتامد.",
    history: "الأسئلة اللي فاتو", clearHistory: "مسح كلشي", emptyHistory: "مازال ما سولتي والو.",
    close: "سد", theme: "الوضع ديال الليل", interfaceLanguage: "لغة الواجهة",
    unverified: "رد البال: هاد الجواب ما دازش التحقق كامل. شوف المواد المذكورة قبل ما تعتامد عليه.",
    notCovered: "حتى نص من النصوص اللي عندنا ما كيجاوب على هاد السؤال.",
    article: "المادة", official: "النص الرسمي", translation: "ترجمة", openPdf: "حل النص كامل (PDF)",
    seconds: (s) => `${s} ث`, error: "ما قدرناش نجاوبو: ",
    ctaSituation: "حلل ليا الوضعية ديالي، خطوة بخطوة", backHome: "سؤال دغيا", editFile: "بدل الملف", print: "طبع / PDF",
    bTitle: "عاود لينا شنو وقع", bSub: "شي خطوات قصار. الملف ديالك كيتكتب وانتا كتزيد، ومن بعد كنحللوه من النصوص الرسمية.",
    stepOf: (i, n) => `الخطوة ${i} من ${n}`, next: "زيد", back: "رجع", skip: "دوز", analyse: "حلل ليا الوضعية",
    qTheme: "على شنو المشكل؟", qRole: "شكون نتا فهاد القصة؟", qStory: "شنو وقع؟", qWhen: "إمتى وقع هادشي؟", qGoal: "شنو بغيتي؟", qReview: "راجع الملف ديالك",
    hStory: "بالهضرة ديالك، بأي لغة. ما محتاجينش الأسماء ولا رقم البطاقة ولا التيليفون.", hWhen: "الآجال ديال القانون يقدرو يبدلو الجواب.", hGoal: "ختار واحد ولا كثر.",
    hReview: "كل سطر فالملف تقدر تبدلو: ضغط عليه. من بعد:",
    reviewSteps: ["كنحددو الأسئلة القانونية اللي كتطرح الوضعية ديالك", "كنقلبو فبزاف ديال القوانين على المواد اللي كتطبق عليها", "كنكتبو ليك خمسة ديال الأجزاء، وكل مادة متأكدين منها"],
    storyPlaceholder: "بحال: كاري شقة هادي عامين، السقف ولا كيقطر، ومول الدار ما بغاش يصلح…", minStory: "كتب جملة ولا جوج على الأقل.",
    qProof: "شنو عندك فيدك؟", dictate: "هضر", listening: "كنسمع…",
    privacy: "بان لينا فالنص رقم تيليفون ولا بطاقة ولا إيميل. ما محتاجينهمش.", hide: "خبيهم",
    fileTitle: "الملف ديالك", fileTheme: "الموضوع", fileRole: "أنا", fileStory: "شنو وقع", fileProof: "عندي", fileWhen: "إمتى", fileGoal: "بغيت",
    fileNote: "الملف ديالك ما كيتسجل فحتى سيرفور.", otherTheme: "حاجة أخرى", tapMissing: "ضغط على سؤال باش تجاوب عليه:",
    whens: ["هاد السيمانة", "هاد الشهر", "من شهر لعام", "كثر من عام", "مازال كيوقع"],
    goals: ["نعرف الحقوق ديالي", "نرجع فلوسي ولا ناخد تعويض", "نوقف هادشي", "ندافع على راسي", "شنو ندير وفين نمشي", "الوراق اللي خاصني"],
    proofs: ["عقد مكتوب", "وصولات ولا خلاص", "ميساجات ولا تصاور", "شهود", "سبق ليا درت شكاية", "والو حتى لدابا"],
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
let mode = "quick";        // the conversation's mode: the top box asks quickly, the builder analyses (81)
let facts = [];            // what the person chose in the situation builder (theme, role, when…)
let conversation = [];     // earlier answers of this conversation (decision 76)
const SECTIONS = [["situation", "secSituation"], ["law", "secLaw"], ["application", "secApplication"], ["steps", "secSteps"], ["missing", "secMissing"]];
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
  renderThread();
  if (!$("builder").hidden) { renderDossier(); renderBuilder(); }
  loadCorpus();
  if (current) renderAnswer(current, false);
}

// ---------- the conversation: earlier answers stay above the current one ----------
function renderThread() {
  const box = $("thread");
  box.innerHTML = "";
  conversation.forEach((turn) => {
    const el = document.createElement("div");
    el.className = "turn";
    el.innerHTML = `<p class="turn-q" dir="auto"></p><p class="turn-a" dir="auto"></p><button type="button">${t("earlier")}</button>`;
    el.querySelector(".turn-q").textContent = turn.question;
    el.querySelector(".turn-a").textContent = turn.text.replace(/\[(\d+)\]/g, "");
    el.querySelector("button").addEventListener("click", () => el.classList.toggle("open"));
    box.append(el);
  });
}
function newConversation() {
  conversation = []; current = null; mode = "quick"; facts = [];
  $("edit-file").hidden = true;
  renderThread();
  $("result").hidden = true; $("followup").hidden = true;
  $("workspace").classList.add("idle");
  $("question").value = ""; $("question").focus();
}
$("new-chat").addEventListener("click", newConversation);
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
const STEP_ORDER = ["understood", "planned", "sources", "writing", "answer"];
function markStep(name) {
  const reached = STEP_ORDER.indexOf(name);
  document.querySelectorAll("#steps li").forEach((li) => {
    const i = STEP_ORDER.indexOf(li.dataset.step);
    li.classList.toggle("done", i < reached || name === "done");
    li.classList.toggle("active", i === reached && name !== "done");
  });
}

async function ask(question, followUp = false, options = {}) {
  question = question.trim();
  if (question.length < 2) return;
  if (!followUp) { mode = options.mode || "quick"; facts = options.facts || []; }
  $("edit-file").hidden = !(mode === "analysis" && facts.length);
  const buttons = document.querySelectorAll(".ask-btn");
  buttons.forEach((b) => { b.disabled = true; });
  if (followUp && current) conversation.push(current);   // the last answer joins the thread
  else conversation = [];                                  // a question from the top starts afresh
  conversation = conversation.slice(-6);
  renderThread();
  const history = conversation.slice(-4).map((c) => ({
    question: c.question, answer: c.text.slice(0, 3500), sources: c.citations.map((x) => x.id).slice(0, 12),
  }));
  current = null;
  $("followup").hidden = true;
  $("understood-as").hidden = true;
  $("mode-badge").textContent = t(mode === "analysis" ? "modeAnalysis" : "modeQuick");
  document.querySelector('#steps li[data-step="planned"]').hidden = mode !== "analysis";
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
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question, mode, history, facts: followUp ? [] : facts }),
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
        if (event === "understood") markStep(mode === "analysis" ? "planned" : "sources");
        else if (event === "planned") markStep("sources");
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
    buttons.forEach((b) => { b.disabled = false; });
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
$("followup").addEventListener("submit", (e) => {
  e.preventDefault();
  const q = $("followup-q").value; $("followup-q").value = ""; ask(q, true);
});
$("followup-q").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("followup").requestSubmit(); }
});

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
  const paragraphs = (s) => escapeHtml(s).split(/\n{2,}/).map((p) => `<p>${p.replace(/\n/g, "<br>")}</p>`).join("");
  let html = "";
  if (data.plan?.length) {
    html += `<div class="plan"><span>${t("searched")}</span><ol>${data.plan.map((q) => `<li dir="rtl">${escapeHtml(q)}</li>`).join("")}</ol></div>`;
  }
  if (data.sections) {
    SECTIONS.forEach(([key, label], i) => {
      const value = data.sections[key];
      if (!value) return;
      let body = paragraphs(value);
      const steps = key === "steps" && listItems(value);
      const questions = key === "missing" && missingQuestions(value);
      if (steps) {  // what you can do: a checklist to tick
        body = `<ul class="checklist">${steps.map((s) => `<li><label><input type="checkbox"><span>${escapeHtml(s)}</span></label></li>`).join("")}</ul>`;
      } else if (questions) {  // what is missing: one tap answers it in the follow-up box
        body = `<p class="tap-hint">${t("tapMissing")}</p>${questions.map((q) => `<button type="button" class="missing-q" dir="auto">${escapeHtml(q)}</button>`).join("")}`;
      }
      html += `<section class="section sec-${key}"><h3><i>${i + 1}</i>${t(label)}</h3>${body}</section>`;
    });
  } else {
    html += paragraphs(data.text);
  }
  text.innerHTML = html.replace(/\[(\d+)\]/g, (m, n) => cited.has(+n)
    ? `<button class="cite" data-n="${n}" aria-expanded="false" aria-label="${t("article")} ${n}">${n}</button>` : "");
  if (data.standalone) {
    $("understood-as").innerHTML = `${t("understoodAs")} <b dir="auto"></b>`;
    $("understood-as").querySelector("b").textContent = data.standalone;
    $("understood-as").hidden = false;
  }
  $("mode-badge").textContent = t(data.mode === "analysis" ? "modeAnalysis" : "modeQuick");
  $("followup").hidden = false;
  text.querySelectorAll(".cite").forEach((b) => b.addEventListener("click", () => openArticle(+b.dataset.n, b)));
  text.querySelectorAll(".missing-q").forEach((b) => b.addEventListener("click", () => {
    const box = $("followup-q");
    box.value = `${b.textContent.replace(/\s*\d+\s*$/, "").trim()} `;
    $("followup").scrollIntoView({ block: "center" });
    box.focus(); box.setSelectionRange(box.value.length, box.value.length);
  }));

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

// "1) Write to the landlord. 2) Wait a month…" → items, for the checklist
function listItems(value) {
  let items = value.split(/(?:^|\n|[.!؟?:،]\s*)\s*\d{1,2}\s*[).]\s+/).map((s) => s.trim()).filter(Boolean);
  if (items.length < 2) items = value.split(/\n+/).map((s) => s.replace(/^\s*[-•]\s*/, "").trim()).filter(Boolean);
  return items.length >= 2 ? items : null;
}
function missingQuestions(value) {
  const items = value.split(/(?<=[?؟])\s+|\n+/).map((s) => s.replace(/^\s*[-•\d.)]+\s*/, "").trim()).filter((s) => s.length > 3);
  return items.length && items.some((s) => /[?؟]\s*(\[\d+\])*$/.test(s)) ? items : null;
}

function citationText(data) {
  const sources = data.citations.map((c) => `[${c.number}] ${c.law_title}, ${c.label || t("article")} ${c.article_number}`);
  const body = data.sections
    ? SECTIONS.filter(([key]) => data.sections[key]).map(([key, label]) => `${t(label)}\n${data.sections[key]}`).join("\n\n")
    : data.text;
  return `${data.question}\n\n${body}\n\n${sources.join("\n")}\n\n— Qanoun AI`;
}
function toast(message) {
  const el = $("toast"); el.textContent = message; el.hidden = false;
  clearTimeout(toast.timer); toast.timer = setTimeout(() => { el.hidden = true; }, 2200);
}
$("copy").addEventListener("click", async () => {
  if (!current) return;
  try { await navigator.clipboard.writeText(citationText(current)); toast(t("copied")); } catch { /* clipboard blocked */ }
});
$("print").addEventListener("click", () => window.print());
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
      conversation = []; renderThread();
      current = h.answer; mode = h.answer.mode || "quick"; facts = [];
      $("edit-file").hidden = true;
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

// ---------- "Analyse my situation": the case file writes itself (decision 81) ----------
// Themes come from TOPICS; each has the roles a person can have in it.
const ROLES = {
  work: [["أجير", "Salarié(e)", "خدام"], ["مشغّل", "Employeur", "باطرون"], ["عامل منزلي", "Employé(e) de maison", "خدام فالديور"], ["باحث عن شغل", "En recherche d'emploi", "كنقلب على خدمة"]],
  family: [["زوجة", "Épouse", "المرا"], ["زوج", "Époux", "الراجل"], ["أب أو أم", "Parent", "الواليد ولا الواليدة"], ["ابن أو بنت", "Enfant", "الولد ولا البنت"]],
  home: [["مكتري", "Locataire", "كاري"], ["مكري", "Propriétaire bailleur", "مول الدار"], ["جار", "Voisin(e)", "جار"], ["مشتري", "Acheteur", "شاري"]],
  penal: [["ضحية", "Victime", "ضحية"], ["متهم", "Mis(e) en cause", "متهم"], ["شاهد", "Témoin", "شاهد"]],
  road: [["سائق", "Conducteur", "سايق"], ["راجل أو ضحية حادثة", "Piéton ou victime", "مترجل ولا ضحية"], ["مالك العربة", "Propriétaire du véhicule", "مول الطوموبيل"]],
  consumer: [["مستهلك", "Client(e)", "الكليان"], ["بائع", "Vendeur", "البياع"]],
  contract: [["دائن", "Créancier (on me doit)", "سلفت لشي حد"], ["مدين", "Débiteur (je dois)", "عليا الكريدي"], ["طرف في عقد", "Partie à un contrat", "طرف فعقد"]],
  other: [["شخص", "Particulier", "شخص عادي"], ["مقاولة", "Entreprise", "شركة"]],
};
const BUILDER_THEMES = ["work", "family", "home", "penal", "road", "consumer", "contract", "other"];
const LANG_INDEX = { ar: 0, fr: 1, darija: 2 };
const STEPS = ["theme", "role", "story", "when", "goal", "review"];
const file = { theme: null, role: null, story: "", proofs: [], when: null, goals: [] };
let stepIndex = 0;

const themeName = (key) => key === "other" ? t("otherTheme") : TOPICS.find((x) => x.icon === key)?.name[lang];
const roleName = (key, i) => ROLES[key][i][LANG_INDEX[lang]];
const PRIVATE = /(?:\+212|\b0)[5-7](?:[\s.-]?\d){8}\b|\b[A-Z]{1,2}\d{5,7}\b|[\w.+-]+@[\w-]+\.[\w.]+/gi;

function chip(label, selected, onPick, cls = "") {
  const b = document.createElement("button");
  b.type = "button"; b.className = `chip ${cls}`; b.setAttribute("aria-pressed", String(selected));
  b.dir = "auto"; b.innerHTML = label;
  b.addEventListener("click", onPick);
  return b;
}
function advanceSoon() { setTimeout(() => goStep(stepIndex + 1), 220); }

function renderBuilder() {
  const step = STEPS[stepIndex];
  const box = $("b-step");
  box.innerHTML = "";
  $("b-progress").innerHTML = STEPS.map((_, i) => `<span class="${i < stepIndex ? "done" : i === stepIndex ? "now" : ""}"></span>`).join("");
  const head = document.createElement("div");
  head.className = "b-head";
  const q = { theme: "qTheme", role: "qRole", story: "qStory", when: "qWhen", goal: "qGoal", review: "qReview" }[step];
  const hint = { story: "hStory", when: "hWhen", goal: "hGoal", review: "hReview" }[step];
  head.innerHTML = `<p class="b-count">${t("stepOf", stepIndex + 1, STEPS.length)}</p><h2>${t(q)}</h2>${hint ? `<p class="b-hint">${t(hint)}</p>` : ""}`;
  box.append(head);
  const grid = document.createElement("div");
  box.append(grid);

  if (step === "theme") {
    grid.className = "tiles";
    BUILDER_THEMES.forEach((key) => {
      const icon = key === "other" ? '<circle cx="12" cy="12" r="8"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6M12 16.5h0"/>' : ICONS[key];
      grid.append(chip(`<span class="tile-icon"><svg viewBox="0 0 24 24">${icon}</svg></span><span>${themeName(key)}</span>`,
        file.theme === key, () => { if (file.theme !== key) file.role = null; file.theme = key; renderDossier(); advanceSoon(); }, "tile"));
    });
  } else if (step === "role") {
    grid.className = "chips big";
    ROLES[file.theme || "other"].forEach((_, i) => grid.append(chip(escapeHtml(roleName(file.theme || "other", i)), file.role === i,
      () => { file.role = i; renderDossier(); advanceSoon(); })));
  } else if (step === "story") {
    grid.className = "story";
    grid.innerHTML = `
      <div class="story-box"><textarea id="b-story" rows="5" maxlength="1000" dir="auto"></textarea>
        <button type="button" class="ghost mic" id="b-mic" hidden><svg viewBox="0 0 24 24"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg><span>${t("dictate")}</span></button></div>
      <p class="privacy" id="b-privacy" hidden><span>${t("privacy")}</span> <button type="button" class="link" id="b-hide">${t("hide")}</button></p>
      <p class="b-error" id="b-story-error" hidden>${t("minStory")}</p>
      <h3>${t("qProof")}</h3><div class="chips" id="b-proofs"></div>`;
    const area = grid.querySelector("#b-story");
    area.placeholder = t("storyPlaceholder");
    area.value = file.story;
    const check = () => {
      file.story = area.value;
      PRIVATE.lastIndex = 0;
      $("b-privacy").hidden = !PRIVATE.test(area.value);
      $("b-story-error").hidden = true;
      renderDossier();
    };
    area.addEventListener("input", check);
    $("b-hide").addEventListener("click", () => { area.value = area.value.replace(PRIVATE, "•••"); check(); area.focus(); });
    const proofs = grid.querySelector("#b-proofs");
    t("proofs").forEach((label, i) => proofs.append(chip(escapeHtml(label), file.proofs.includes(i), (e) => {
      const last = i === t("proofs").length - 1;   // "nothing yet" excludes the others
      file.proofs = file.proofs.includes(i) ? file.proofs.filter((x) => x !== i) : last ? [i] : [...file.proofs.filter((x) => x !== t("proofs").length - 1), i];
      renderDossier(); renderBuilder();
    })));
    setupDictation(area, check);
    check();
    setTimeout(() => area.focus(), 60);
  } else if (step === "when") {
    grid.className = "chips big";
    t("whens").forEach((label, i) => grid.append(chip(escapeHtml(label), file.when === i, () => { file.when = i; renderDossier(); advanceSoon(); })));
  } else if (step === "goal") {
    grid.className = "chips big";
    t("goals").forEach((label, i) => grid.append(chip(escapeHtml(label), file.goals.includes(i), () => {
      file.goals = file.goals.includes(i) ? file.goals.filter((x) => x !== i) : [...file.goals, i];
      renderDossier(); renderBuilder();
    })));
  } else {
    grid.className = "review";
    grid.innerHTML = `<ol class="review-steps">${t("reviewSteps").map((x) => `<li>${x}</li>`).join("")}</ol>`;
  }

  $("b-back").hidden = stepIndex === 0;
  const next = $("b-next");
  const optional = step === "role" || step === "when" || step === "goal";
  next.querySelector("span").textContent = step === "review" ? t("analyse") : optional && !chosen(step) ? t("skip") : t("next");
  next.classList.toggle("final", step === "review");
  next.hidden = step === "theme";
  $("dossier").classList.toggle("complete", step === "review");
}
function chosen(step) {
  return { role: file.role !== null, when: file.when !== null, goal: file.goals.length > 0 }[step];
}

function renderDossier() {
  const line = (label, value, step) => `
    <div class="d-line${value ? "" : " empty"}"><dt>${label}</dt>
      <dd><button type="button" data-step="${step}" dir="auto">${value ? escapeHtml(value) : "…"}</button></dd></div>`;
  const theme = file.theme ? themeName(file.theme) : "";
  const role = file.theme && file.role !== null ? roleName(file.theme, file.role) : "";
  const proofs = file.proofs.map((i) => t("proofs")[i]).join("، ");
  $("dossier-body").innerHTML = line(t("fileTheme"), theme, 0) + line(t("fileRole"), role, 1)
    + line(t("fileStory"), file.story.trim(), 2) + line(t("fileProof"), proofs, 2)
    + line(t("fileWhen"), file.when !== null ? t("whens")[file.when] : "", 3)
    + line(t("fileGoal"), file.goals.map((i) => t("goals")[i]).join("، "), 4);
  $("dossier-body").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => goStep(+b.dataset.step)));
}

function goStep(i) {
  if (STEPS[stepIndex] === "story" && i > stepIndex && file.story.trim().length < 15) {
    $("b-story-error").hidden = false; $("b-story").focus(); return;
  }
  if (i >= STEPS.length) { submitFile(); return; }
  stepIndex = Math.max(0, i);
  renderBuilder();
  $("b-step").scrollIntoView({ block: "nearest" });
}
$("b-next").addEventListener("click", () => goStep(stepIndex + 1));
$("b-back").addEventListener("click", () => goStep(stepIndex - 1));

function fileFacts() {
  const out = [];
  if (file.theme) out.push(`${t("fileTheme")}: ${themeName(file.theme)}`);
  if (file.theme && file.role !== null) out.push(`${t("fileRole")}: ${roleName(file.theme, file.role)}`);
  if (file.proofs.length) out.push(`${t("fileProof")}: ${file.proofs.map((i) => t("proofs")[i]).join(", ")}`);
  if (file.when !== null) out.push(`${t("fileWhen")}: ${t("whens")[file.when]}`);
  if (file.goals.length) out.push(`${t("fileGoal")}: ${file.goals.map((i) => t("goals")[i]).join(", ")}`);
  return out;
}
function submitFile() {
  history.pushState(null, "", location.pathname);   // back to the answer page; "back" returns here
  route();
  ask(file.story, false, { mode: "analysis", facts: fileFacts() });
}

// Dictation where the browser offers it (Chrome, Edge, Safari); hidden elsewhere.
function setupDictation(area, onChange) {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const mic = $("b-mic");
  if (!Recognition) return;
  mic.hidden = false;
  let listening = null;
  mic.addEventListener("click", () => {
    if (listening) { listening.stop(); return; }
    const r = new Recognition();
    r.lang = lang === "fr" ? "fr-FR" : "ar-MA";
    r.interimResults = false;
    r.onresult = (e) => {
      const said = Array.from(e.results).map((x) => x[0].transcript).join(" ");
      area.value = `${area.value.trim()} ${said}`.trim(); onChange();
    };
    r.onend = () => { listening = null; mic.classList.remove("on"); mic.querySelector("span").textContent = t("dictate"); };
    r.start(); listening = r;
    mic.classList.add("on"); mic.querySelector("span").textContent = t("listening");
  });
}

// ---------- pages: home (#) and the situation builder (#situation) ----------
function route() {
  const builder = location.hash === "#situation";
  document.querySelector(".hero").hidden = builder;
  $("workspace").hidden = builder;
  $("builder").hidden = !builder;
  if (builder) {
    if (STEPS[stepIndex] !== "review" && file.story.trim().length >= 15 && current?.mode === "analysis") stepIndex = STEPS.length - 1;
    renderDossier(); renderBuilder();
    window.scrollTo(0, 0);
    $("b-title").focus({ preventScroll: true });
  }
}
window.addEventListener("hashchange", route);
route();

applyLanguage();
