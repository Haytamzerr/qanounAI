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

// ---------- strings for the situation tools (decisions 82–86) ----------
Object.assign(STRINGS.ar, {
  listen: "استمع", stopListen: "إيقاف", startFrom: "ابدأ من وضعية شائعة", readDoc: "اقرأ وثيقتي: عقد، رسالة، حكم",
  readDocNote: "تُرسل الوثيقة إلى Gemini من Google لقراءتها. أخفِ الأرقام الشخصية إن استطعت.", reading: "نقرأ الوثيقة…",
  docTitle: "ما تقوله وثيقتك", docImage: "قُرئت من صورة: قارنها بالوثيقة قبل الاعتماد عليها.", fileDoc: "الوثيقة",
  exactDate: "التاريخ بالضبط (اختياري)", deadlinesTitle: "الآجال القانونية", deadlineFrom: "ابتداء من", startDate: "يبدأ الأجل في",
  dueOn: (d) => `آخر أجل: ${d}`, daysLeft: (n) => (n >= 0 ? `بقي ${n} يوما` : `انقضى الأجل منذ ${-n} يوما`),
  addCalendar: "أضف إلى التقويم", units: { days: "يوم", months: "شهر", years: "سنة", hours: "ساعة" },
  calcTitle: "احسب", calculate: "احسب", fromArticles: "المصدر:", notEligible: "لا حق في هذا في حالتك:",
  calcs: { dismissal_indemnity: "التعويض عن الفصل", abusive_dismissal: "التعويض عن الضرر (فصل تعسفي)", annual_leave: "أيام العطلة السنوية", rent_increase: "أقصى زيادة في الكراء" },
  inputs: { years: "سنوات العمل", monthly_wage: "الأجرة الشهرية (درهم)", months_worked: "الشهور المشتغلة هذه السنة", years_of_service: "سنوات العمل", monthly_rent: "الكراء الشهري (درهم)", years_since_last_revision: "سنوات منذ العقد أو آخر زيادة", use: "نوع المحل", agricultural: "نشاط فلاحي", representative: "مندوب أجراء أو ممثل نقابي", under_18: "أقل من 18 سنة" },
  uses: { housing: "سكنى", professional: "مهني" },
  calcSteps: {
    hourly_wage: (v, d) => `الأجر بالساعة: ${v} درهم (الأجرة × 12 ÷ ${d.hours_per_year} ساعة في السنة)`,
    band: (v, d) => `${d.years} سنة × ${d.hours} ساعة (من السنة ${d.from} ${d.to ? `إلى ${d.to}` : "فما فوق"}) = ${v} درهم`,
    representative: (v) => `+100% لمندوب الأجراء أو الممثل النقابي: ${v} درهم`,
    months: (v, d) => `${d.years} سنة × ${d.per_year} شهر = ${v} شهر من الأجرة`,
    cap: (v) => `السقف القانوني: ${v}`, per_month: (v, d) => `${d.months} شهر × ${d.per_month} يوم = ${v} يوم`,
    seniority: (v, d) => `+1.5 يوم عن كل 5 سنوات (${d.periods}) = ${v} يوم`, increase: (v, d) => `الزيادة القصوى ${d.rate}%: ${v} درهم`,
    too_early: (v, d) => `لا زيادة قبل ${d.years} سنوات: بقي ${v} سنة`,
  },
  calcNotes: { under_six_months: "لا يُستحق قبل ستة أشهر من الشغل.", average_52_weeks: "يُحسب على معدل أجور 52 أسبوعا الأخيرة: أدخل هذا المعدل إن كان مختلفا.", part_year: "جزء السنة حُسب بالتناسب، وقد تحسبه المحكمة بطريقة أخرى.", minimum_wage: "لا يقل الأجر المعتمد عن الحد الأدنى القانوني للأجر.", court_decides: "هذا ما يسمح به القانون كحد أقصى، والمحكمة هي التي تحدد المبلغ.", capped: "طُبق السقف القانوني.", working_days: "أيام شغل فعلي، لا أيام تقويمية.", better_contract: "قد ينص العقد أو الاتفاقية الجماعية على أكثر.", too_early: "لم تمر بعد ثلاث سنوات منذ العقد أو آخر مراجعة.", agreement: "النسبة حد أقصى، ويمكن الاتفاق على أقل." },
  letterTitle: "اكتب رسالة", letterKinds: { notice: "إشعار / إنذار", complaint: "شكاية", request: "طلب" }, letterIn: { ar: "بالعربية", fr: "بالفرنسية" },
  writingLetter: "نكتب الرسالة…", letterDraft: "مسودة: راجعها وأكمل ما بين [ ] قبل التوقيع.", downloadWord: "تحميل Word", printLetter: "طباعة الرسالة",
});
Object.assign(STRINGS.fr, {
  listen: "Écouter", stopListen: "Arrêter", startFrom: "Partir d'une situation courante", readDoc: "Lire mon document : contrat, lettre, jugement",
  readDocNote: "Le document est envoyé à Gemini (Google) pour être lu. Masquez les numéros personnels si vous le pouvez.", reading: "Lecture du document…",
  docTitle: "Ce que dit votre document", docImage: "Lu depuis une image : comparez avec le document avant de vous y fier.", fileDoc: "Document",
  exactDate: "Date exacte (facultatif)", deadlinesTitle: "Délais légaux", deadlineFrom: "À compter de", startDate: "Le délai commence le",
  dueOn: (d) => `Échéance : ${d}`, daysLeft: (n) => (n >= 0 ? `${n} jours restants` : `Délai dépassé de ${-n} jours`),
  addCalendar: "Ajouter au calendrier", units: { days: "jours", months: "mois", years: "ans", hours: "heures" },
  calcTitle: "Calculer", calculate: "Calculer", fromArticles: "Source :", notEligible: "Pas de droit dans votre cas :",
  calcs: { dismissal_indemnity: "Indemnité de licenciement", abusive_dismissal: "Dommages pour licenciement abusif", annual_leave: "Jours de congé annuel", rent_increase: "Hausse de loyer maximale" },
  inputs: { years: "Années de travail", monthly_wage: "Salaire mensuel (MAD)", months_worked: "Mois travaillés cette année", years_of_service: "Années de travail", monthly_rent: "Loyer mensuel (MAD)", years_since_last_revision: "Années depuis le bail ou la dernière hausse", use: "Type de local", agricultural: "Activité agricole", representative: "Délégué du personnel ou syndical", under_18: "Moins de 18 ans" },
  uses: { housing: "Habitation", professional: "Professionnel" },
  calcSteps: {
    hourly_wage: (v, d) => `Salaire horaire : ${v} MAD (salaire × 12 ÷ ${d.hours_per_year} h par an)`,
    band: (v, d) => `${d.years} an(s) × ${d.hours} h (années ${d.from}${d.to ? `–${d.to}` : " et plus"}) = ${v} MAD`,
    representative: (v) => `+100 % pour un délégué ou représentant syndical : ${v} MAD`,
    months: (v, d) => `${d.years} an(s) × ${d.per_year} mois = ${v} mois de salaire`,
    cap: (v) => `Plafond légal : ${v}`, per_month: (v, d) => `${d.months} mois × ${d.per_month} jour(s) = ${v} jours`,
    seniority: (v, d) => `+1,5 jour par période de 5 ans (${d.periods}) = ${v} jours`, increase: (v, d) => `Hausse maximale de ${d.rate} % : ${v} MAD`,
    too_early: (v, d) => `Pas de hausse avant ${d.years} ans : encore ${v} an(s)`,
  },
  calcNotes: { under_six_months: "Pas de droit avant six mois de travail.", average_52_weeks: "Calculé sur la moyenne des salaires des 52 dernières semaines : saisissez cette moyenne si elle diffère.", part_year: "La fraction d'année est comptée au prorata ; un tribunal peut la compter autrement.", minimum_wage: "Le salaire retenu ne peut être inférieur au salaire minimum légal.", court_decides: "C'est le maximum que permet la loi ; le tribunal fixe le montant.", capped: "Le plafond légal s'applique.", working_days: "Jours de travail effectif, pas des jours calendaires.", better_contract: "Le contrat ou la convention collective peut prévoir plus.", too_early: "Trois ans ne sont pas encore passés depuis le bail ou la dernière révision.", agreement: "Le taux est un maximum ; une hausse plus faible peut être convenue." },
  letterTitle: "Rédiger une lettre", letterKinds: { notice: "Mise en demeure", complaint: "Plainte", request: "Demande" }, letterIn: { ar: "En arabe", fr: "En français" },
  writingLetter: "Rédaction de la lettre…", letterDraft: "Brouillon : relisez-le et complétez les [ ] avant de signer.", downloadWord: "Télécharger Word", printLetter: "Imprimer la lettre",
});
Object.assign(STRINGS.darija, {
  listen: "سمع", stopListen: "حبس", startFrom: "بدا من شي وضعية معروفة", readDoc: "قرا الوثيقة ديالي: عقد، برية، حكم",
  readDocNote: "الوثيقة كتمشي لـ Gemini ديال Google باش يقراها. خبي الأرقام الشخصية إلا قدرتي.", reading: "كنقراو الوثيقة…",
  docTitle: "شنو كتقول الوثيقة ديالك", docImage: "تقرات من تصويرة: قارنها مع الوثيقة قبل ما تعتامد عليها.", fileDoc: "الوثيقة",
  exactDate: "التاريخ بالضبط (إلا عرفتيه)", deadlinesTitle: "الآجال ديال القانون", deadlineFrom: "من", startDate: "الأجل كيبدا نهار",
  dueOn: (d) => `آخر نهار: ${d}`, daysLeft: (n) => (n >= 0 ? `باقي ${n} نهار` : `فات الأجل بـ ${-n} نهار`),
  addCalendar: "زيدها للأجندة", units: { days: "نهار", months: "شهر", years: "عام", hours: "ساعة" },
  calcTitle: "حسب", calculate: "حسب", fromArticles: "المصدر:", notEligible: "ما عندكش هاد الحق فالحالة ديالك:",
  calcs: { dismissal_indemnity: "التعويض على الطرد", abusive_dismissal: "التعويض على الطرد التعسفي", annual_leave: "أيام الكونجي", rent_increase: "أكبر زيادة فالكرا" },
  inputs: { years: "شحال من عام خدمتي", monthly_wage: "الخلصة فالشهر (درهم)", months_worked: "شحال من شهر خدمتي هاد العام", years_of_service: "شحال من عام خدمتي", monthly_rent: "الكرا فالشهر (درهم)", years_since_last_revision: "شحال من عام من العقد ولا آخر زيادة", use: "نوع المحل", agricultural: "خدمة فلاحية", representative: "مندوب ولا ممثل نقابي", under_18: "عندي أقل من 18 عام" },
  uses: { housing: "سكنى", professional: "مهني" },
  calcSteps: {
    hourly_wage: (v, d) => `الخلصة فالساعة: ${v} درهم (الخلصة × 12 ÷ ${d.hours_per_year} ساعة فالعام)`,
    band: (v, d) => `${d.years} عام × ${d.hours} ساعة (من العام ${d.from} ${d.to ? `حتى ${d.to}` : "ولفوق"}) = ${v} درهم`,
    representative: (v) => `+100% للمندوب ولا الممثل النقابي: ${v} درهم`,
    months: (v, d) => `${d.years} عام × ${d.per_year} شهر = ${v} شهر ديال الخلصة`,
    cap: (v) => `السقف ديال القانون: ${v}`, per_month: (v, d) => `${d.months} شهر × ${d.per_month} نهار = ${v} نهار`,
    seniority: (v, d) => `+1.5 نهار على كل 5 سنين (${d.periods}) = ${v} نهار`, increase: (v, d) => `أكبر زيادة ${d.rate}%: ${v} درهم`,
    too_early: (v, d) => `ما كايناش زيادة قبل ${d.years} سنين: باقي ${v} عام`,
  },
  calcNotes: { under_six_months: "ما كاينش هاد الحق قبل ستة شهور ديال الخدمة.", average_52_weeks: "كيتحسب على المعدل ديال الخلصة فـ52 سيمانة اللخرين: دخل هاد المعدل إلا كان مختلف.", part_year: "الجزء ديال العام تحسب بالنسبة، والمحكمة تقدر تحسبو بطريقة أخرى.", minimum_wage: "الخلصة اللي كتعتامد ما تقدرش تكون تحت السميك.", court_decides: "هادا هو الأقصى اللي كيسمح بيه القانون، والمحكمة هي اللي كتحدد المبلغ.", capped: "تطبق السقف ديال القانون.", working_days: "أيام ديال الخدمة، ماشي أيام الكالاندري.", better_contract: "العقد ولا الاتفاقية الجماعية يقدرو يعطيو كثر.", too_early: "مازال ما دازوش ثلاث سنين من العقد ولا آخر زيادة.", agreement: "النسبة هي الأقصى، وتقدرو تتافقو على أقل." },
  letterTitle: "كتب برية", letterKinds: { notice: "إشعار ولا إنذار", complaint: "شكاية", request: "طلب" }, letterIn: { ar: "بالعربية", fr: "بالفرنساوية" },
  writingLetter: "كنكتبو البرية…", letterDraft: "مسودة: راجعها وكمل اللي بين [ ] قبل ما تسني.", downloadWord: "حمل Word", printLetter: "طبع البرية",
});

// Common situations: one tap fills the file, then the person adjusts it (decision 85)
const SCENARIOS = [
  { theme: "work", role: 0, proofs: [0], when: 1, goals: [0, 1], label: ["فصل دون سبب", "Licencié sans motif", "جراو عليا بلا سبب"],
    story: ["فصلني المشغل من العمل دون سبب ولا إخطار بعد سبع سنوات من الشغل.", "Mon employeur m'a licencié sans motif ni préavis après sept ans de travail.", "الباطرون جرا عليا بلا سبب وبلا ما يعلمني، من بعد سبع سنين ديال الخدمة."] },
  { theme: "work", role: 0, proofs: [1], when: 1, goals: [1, 4], label: ["أجرة غير مؤداة", "Salaire impayé", "ما خلصونيش"],
    story: ["لم يؤد لي المشغل أجرتي منذ شهرين رغم أنني أعمل بشكل عادي.", "Mon employeur ne me paie plus depuis deux mois alors que je travaille normalement.", "الباطرون ما خلصنيش هادي جوج شهور وأنا خدام عادي."] },
  { theme: "home", role: 0, proofs: [0, 2], when: 4, goals: [0, 4], label: ["المالك لا يصلح", "Le propriétaire ne répare pas", "مول الدار ما بغاش يصلح"],
    story: ["أكتري شقة منذ سنتين، والسقف صار يقطر، والمكري يرفض الإصلاح.", "Je loue un appartement depuis deux ans, le plafond fuit et le propriétaire refuse de réparer.", "كاري شقة هادي عامين، السقف ولا كيقطر، ومول الدار ما بغاش يصلح."] },
  { theme: "home", role: 0, proofs: [0], when: 0, goals: [0, 3], label: ["إفراغ دون حكم", "Expulsion sans jugement", "بغا يخرجني بلا حكم"],
    story: ["يريد المكري إخراجي من الشقة الآن دون أي حكم قضائي.", "Mon propriétaire veut m'expulser tout de suite, sans décision de justice.", "مول الدار بغا يخرجني دابا من الدار بلا حتى حكم."] },
  { theme: "contract", role: 0, proofs: [2], when: 2, goals: [1, 4], label: ["دين لم يُرد", "Dette non remboursée", "سلفت وما ردوش"],
    story: ["أقرضت شخصا مبلغا من المال ولم يرده رغم وعوده.", "J'ai prêté de l'argent à quelqu'un qui ne me rembourse pas malgré ses promesses.", "سلفت شي فلوس لواحد وما بغاش يردهم واخا وعدني."] },
  { theme: "contract", role: 0, proofs: [1], when: 1, goals: [1, 4], label: ["شيك بدون رصيد", "Chèque sans provision", "شيك بلا رصيد"],
    story: ["تسلمت شيكا مقابل بضاعة، ورفضه البنك لعدم وجود رصيد.", "J'ai reçu un chèque pour une marchandise et la banque l'a refusé faute de provision.", "خداو ليا شيك على سلعة والبنك رفضو حيت ما فيهش الرصيد."] },
  { theme: "consumer", role: 0, proofs: [1], when: 0, goals: [1], label: ["منتوج معيب", "Produit défectueux", "حاجة خاسرة"],
    story: ["اشتريت هاتفا فتبين أنه معيب، والبائع يرفض استبداله أو إرجاع ثمنه.", "J'ai acheté un téléphone défectueux et le vendeur refuse de l'échanger ou de me rembourser.", "شريت تيليفون طلع خاسر، والبياع ما بغاش يبدلو ولا يرجع ليا الفلوس."] },
  { theme: "road", role: 1, proofs: [3], when: 1, goals: [1, 4], label: ["حادثة سير", "Accident de la route", "حادثة"],
    story: ["صدمتني سيارة وأنا أمشي، وأصبت بجروح ولم أعد أعمل منذ أسابيع.", "J'ai été renversé par une voiture en marchant ; je suis blessé et ne travaille plus depuis des semaines.", "ضربتني طوموبيل وأنا ماشي على رجلي، تجرحت وهادي سيمانات ما خدمتش."] },
  { theme: "family", role: 0, proofs: [], when: 2, goals: [0, 1], label: ["الحضانة والنفقة", "Garde et pension", "الحضانة والنفقة"],
    story: ["طلقني زوجي، وأريد حضانة أطفالي والنفقة.", "Mon mari a divorcé ; je veux la garde de nos enfants et une pension.", "راجلي طلقني، وبغيت الحضانة ديال الولاد والنفقة."] },
];

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
  renderTools(data);
  setupListen(data);
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
const file = { theme: null, role: null, story: "", proofs: [], when: null, date: "", goals: [], doc: null };
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
    const starters = document.createElement("div");
    starters.className = "starters";
    starters.innerHTML = `<h3>${t("startFrom")}</h3><div class="chips" id="b-scenarios"></div>
      <button type="button" class="doc-btn" id="b-doc"><svg viewBox="0 0 24 24"><path d="M7 3h7l4 4v14H7zM14 3v4h4M12 11v6M9 14l3 3 3-3"/></svg><span>${t("readDoc")}</span></button>
      <p class="doc-note" id="b-doc-status">${t("readDocNote")}</p>`;
    box.insertBefore(starters, grid);
    SCENARIOS.forEach((sc) => starters.querySelector("#b-scenarios").append(chip(escapeHtml(sc.label[LANG_INDEX[lang]]), false, () => {
      Object.assign(file, { theme: sc.theme, role: sc.role, story: sc.story[LANG_INDEX[lang]], proofs: [...sc.proofs], when: sc.when, goals: [...sc.goals], doc: null });
      renderDossier(); goStep(STEPS.indexOf("story"));
    }, "scenario")));
    starters.querySelector("#b-doc").addEventListener("click", () => $("doc-input").click());
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
      <h3>${t("qProof")}</h3><div class="chips" id="b-proofs"></div>${file.doc ? docPanel(file.doc) : ""}`;
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
    t("whens").forEach((label, i) => grid.append(chip(escapeHtml(label), file.when === i, () => { file.when = i; renderDossier(); if (!file.date) advanceSoon(); })));
    const exact = document.createElement("label");
    exact.className = "exact-date";
    exact.innerHTML = `<span>${t("exactDate")}</span><input type="date" id="b-date">`;
    box.append(exact);
    const input = exact.querySelector("input");
    input.value = file.date; input.max = new Date().toISOString().slice(0, 10);
    input.addEventListener("change", () => { file.date = input.value; renderDossier(); });
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
    + line(t("fileWhen"), [file.when !== null ? t("whens")[file.when] : "", file.date].filter(Boolean).join(" · "), 3)
    + (file.doc ? line(t("fileDoc"), file.doc.summary, 0) : "")
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
  if (file.when !== null || file.date) out.push(`${t("fileWhen")}: ${[file.when !== null ? t("whens")[file.when] : "", file.date].filter(Boolean).join(", ")}`);
  if (file.doc) out.push(`${t("fileDoc")}: ${file.doc.summary}`.slice(0, 200));
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

// ---------- reading the person's document (decision 86) ----------
function docPanel(doc) {
  const clauses = doc.clauses.map((c) => `<li><q dir="auto">${escapeHtml(c.quote)}</q><span dir="auto">${escapeHtml(c.meaning)}</span></li>`).join("");
  const facts = [...doc.dates.map((d) => `${d.what}: ${d.date}`), ...doc.amounts.map((a) => `${a.what}: ${a.amount}`)];
  return `<div class="doc-panel"><h3>${t("docTitle")}</h3><p dir="auto">${escapeHtml(doc.summary)}</p>
    ${facts.length ? `<p class="doc-facts" dir="auto">${facts.map(escapeHtml).join(" · ")}</p>` : ""}
    ${clauses ? `<ul class="clauses">${clauses}</ul>` : ""}
    ${doc.read_as === "image" ? `<p class="doc-note">${t("docImage")}</p>` : ""}</div>`;
}
$("doc-input").addEventListener("change", async (e) => {
  const f = e.target.files[0];
  e.target.value = "";
  if (!f) return;
  const status = $("b-doc-status");
  const mime = f.type || (f.name.endsWith(".pdf") ? "application/pdf" : "text/plain");
  if (status) status.textContent = t("reading");
  $("b-doc")?.setAttribute("disabled", "");
  try {
    const data = await new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(String(r.result).split(",")[1] || "");
      r.onerror = () => reject(new Error(f.name));
      r.readAsDataURL(f);
    });
    const response = await fetch("/read-document", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mime, data, language: lang }),
    });
    const out = await response.json();
    if (!response.ok) throw new Error(out.detail || response.statusText);
    Object.assign(file, { theme: out.theme, role: null, story: out.story || file.story, doc: out });
    renderDossier(); goStep(STEPS.indexOf("role"));
  } catch (error) {
    if (status) { status.textContent = t("error") + error.message; status.classList.add("b-error"); }
    $("b-doc")?.removeAttribute("disabled");
  }
});

// ---------- tools under an answer: deadlines, calculators, letters (decisions 82–84) ----------
const CALCULATORS = {
  dismissal_indemnity: { inputs: [["years", 7], ["monthly_wage", 4000], ["agricultural", false], ["representative", false]],
    articles: ["41", "43", "51", "52", "53", "55", "59", "61", "62", "63", "65"].map((n) => `loi-65-99-ar-art-${n}`), theme: "work" },
  abusive_dismissal: { inputs: [["years", 7], ["monthly_wage", 4000]],
    articles: ["35", "39", "40", "41", "59", "61", "62", "63", "65"].map((n) => `loi-65-99-ar-art-${n}`), theme: "work" },
  annual_leave: { inputs: [["months_worked", 12], ["years_of_service", 3], ["under_18", false]],
    articles: ["231", "232", "233", "240", "241", "242", "243", "244", "245"].map((n) => `loi-65-99-ar-art-${n}`), theme: "work" },
  rent_increase: { inputs: [["monthly_rent", 2000], ["years_since_last_revision", 3], ["use", "housing"]],
    articles: [...["31", "32", "33", "34", "35", "36"].map((n) => `loi-67-12-ar-art-${n}`), ...["2", "3", "4", "5"].map((n) => `loi-07-03-ar-art-${n}`)], theme: "home" },
};
// "2 160,5" in every language: "2.160" (ar-MA) reads like two point sixteen
const fmtNumber = (v) => Number(v).toLocaleString("fr-FR", { maximumFractionDigits: 2 });
const fmtDate = (d) => d.toLocaleDateString(lang === "fr" ? "fr-FR" : "ar-MA", { dateStyle: "long" });
const tool = (cls, icon, title) => {
  const el = document.createElement("section");
  el.className = `tool ${cls}`;
  el.innerHTML = `<h3><svg viewBox="0 0 24 24">${icon}</svg>${title}</h3>`;
  return el;
};

function renderTools(data) {
  const box = $("tools");
  box.innerHTML = "";
  const ids = new Set([...data.citations.map((c) => c.id), ...(data.sources || [])]);
  if (data.deadlines?.length) box.append(deadlinesTool(data));
  const theme = facts.length ? file.theme : null;
  const calcs = Object.entries(CALCULATORS).filter(([, c]) => c.articles.some((a) => ids.has(a)) || (data.mode === "analysis" && c.theme === theme));
  if (calcs.length && data.status === "answered") box.append(calculatorsTool(calcs));
  if (data.mode === "analysis" && data.status === "answered" && data.citations.length) box.append(letterTool(data));
}

function addTime(start, amount, unit) {
  const d = new Date(start.getTime());
  if (unit === "days") d.setDate(d.getDate() + amount);
  else if (unit === "months") d.setMonth(d.getMonth() + amount);
  else if (unit === "years") d.setFullYear(d.getFullYear() + amount);
  else d.setHours(d.getHours() + amount);
  return d;
}
function deadlinesTool(data) {
  const el = tool("deadlines", '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2.5M9 2h6"/>', t("deadlinesTitle"));
  // A deadline runs from an event that is often still to come (sending the notice): by default it
  // starts today, which answers "if I act now, what is my last day?"; the person can change it.
  const start = new Date().toISOString().slice(0, 10);
  data.deadlines.forEach((d, i) => {
    const card = document.createElement("div");
    card.className = "deadline";
    const cite = data.citations.find((c) => c.id === d.article_id);
    card.innerHTML = `
      <div class="deadline-head"><b class="amount">${d.amount} ${t("units")[d.unit]}</b><span dir="auto">${escapeHtml(d.what)}</span></div>
      ${d.from_event ? `<p class="deadline-from" dir="auto">${t("deadlineFrom")} ${escapeHtml(d.from_event)}</p>` : ""}
      <blockquote dir="auto">${escapeHtml(d.quote)} ${cite ? `<button class="cite" data-n="${cite.number}">${cite.number}</button>` : `<button class="link" data-id="${escapeHtml(d.article_id)}">${t("article")}</button>`}</blockquote>
      <div class="deadline-calc"><label><span>${t("startDate")}</span><input type="date" value="${start}"></label>
        <p class="due" aria-live="polite"></p><button type="button" class="ghost ics" hidden>${t("addCalendar")}</button></div>`;
    const input = card.querySelector("input");
    const update = () => {
      const due = card.querySelector(".due"), ics = card.querySelector(".ics");
      if (!input.value) { due.textContent = ""; ics.hidden = true; return; }
      const end = addTime(new Date(`${input.value}T09:00:00`), d.amount, d.unit);
      const today = new Date(); today.setHours(9, 0, 0, 0);
      const left = Math.round((end - today) / 86400000);
      due.innerHTML = `<b>${t("dueOn", fmtDate(end))}</b> · <span class="${left < 0 ? "late" : left <= 7 ? "soon" : ""}">${t("daysLeft", left)}</span>`;
      ics.hidden = false;
      ics.onclick = () => downloadIcs(d, end, data.question, i);
    };
    input.addEventListener("input", update);
    card.querySelector(".cite")?.addEventListener("click", (e) => openArticle(cite.number, e.currentTarget));
    card.querySelector(".link")?.addEventListener("click", (e) => openArticleById(d.article_id, e.currentTarget));
    update();
    el.append(card);
  });
  return el;
}
function downloadIcs(d, due, question, i) {
  const day = (x) => x.toISOString().slice(0, 10).replace(/-/g, "");
  const esc = (s) => String(s).replace(/[\;,]/g, (c) => `\\${c}`).replace(/\n/g, "\\n");
  const next = new Date(due.getTime() + 86400000);
  const ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Qanoun AI//Deadline//EN", "BEGIN:VEVENT",
    `UID:qanoun-${Date.now()}-${i}@qanoun.ai`, `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}Z`,
    `DTSTART;VALUE=DATE:${day(due)}`, `DTEND;VALUE=DATE:${day(next)}`, `SUMMARY:${esc(`⚖️ ${d.what}`)}`,
    `DESCRIPTION:${esc(`${d.quote}\n(${d.article_id})\n\n${question}\n\nQanoun AI`)}`,
    "BEGIN:VALARM", "TRIGGER:-P3D", "ACTION:DISPLAY", `DESCRIPTION:${esc(d.what)}`, "END:VALARM",
    "BEGIN:VALARM", "TRIGGER:-PT15H", "ACTION:DISPLAY", `DESCRIPTION:${esc(d.what)}`, "END:VALARM",
    "END:VEVENT", "END:VCALENDAR"].join("\r\n");
  saveBlob(new Blob([ics], { type: "text/calendar" }), "qanoun-deadline.ics");
}
function saveBlob(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = name;
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

function calculatorsTool(calcs) {
  const el = tool("calcs", '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h2M12 11h2M8 15h2M12 15h2M16 11v4"/>', t("calcTitle"));
  const tabs = document.createElement("div");
  tabs.className = "chips calc-tabs";
  const body = document.createElement("div");
  el.append(tabs, body);
  const show = (name) => {
    tabs.querySelectorAll(".chip").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.calc === name)));
    body.innerHTML = "";
    const form = document.createElement("form");
    form.className = "calc-form";
    CALCULATORS[name].inputs.forEach(([key, value]) => {
      const label = document.createElement("label");
      if (typeof value === "boolean") {
        label.className = "check";
        label.innerHTML = `<input type="checkbox" name="${key}"><span>${t("inputs")[key]}</span>`;
      } else if (key === "use") {
        label.innerHTML = `<span>${t("inputs")[key]}</span><select name="use">${Object.entries(t("uses")).map(([k, v]) => `<option value="${k}">${v}</option>`).join("")}</select>`;
      } else {
        label.innerHTML = `<span>${t("inputs")[key]}</span><input type="number" name="${key}" min="0" step="any" required value="${value}" inputmode="decimal">`;
      }
      form.append(label);
    });
    const go = document.createElement("button");
    go.type = "submit"; go.className = "ask-btn small"; go.textContent = t("calculate");
    form.append(go);
    const out = document.createElement("div");
    out.className = "calc-out"; out.setAttribute("aria-live", "polite");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const inputs = {};
      CALCULATORS[name].inputs.forEach(([key, value]) => {
        const field = form.elements[key];
        inputs[key] = typeof value === "boolean" ? field.checked : key === "use" ? field.value : Number(field.value);
      });
      try {
        const response = await fetch("/calculate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tool: name, inputs }) });
        const r = await response.json();
        if (!response.ok) throw new Error(r.detail || response.statusText);
        const unit = { MAD: lang === "fr" ? "MAD" : "درهم", days: t("units").days, months: t("units").months }[r.unit] || r.unit;
        const steps = r.steps.map((s) => `<li>${t("calcSteps")[s.key]?.(fmtNumber(s.value), s.detail) ?? ""}</li>`).join("");
        const articles = r.articles.map((id) => `<button type="button" class="link" data-id="${id}">${id.includes("67-12") ? "67.12" : id.includes("07-03") ? "07.03" : "65.99"} · ${id.split("-").pop()}</button>`).join(" ");
        out.innerHTML = `${r.eligible ? `<p class="calc-value">${fmtNumber(r.value)} <small>${unit}</small></p>` : `<p class="calc-value no">${t("notEligible")}</p>`}
          ${steps ? `<ol class="calc-steps">${steps}</ol>` : ""}
          <ul class="calc-notes">${r.notes.map((n) => `<li>${t("calcNotes")[n] || ""}</li>`).join("")}</ul>
          <p class="calc-src">${t("fromArticles")} ${articles}</p>`;
        out.querySelectorAll(".link").forEach((b) => b.addEventListener("click", () => openArticleById(b.dataset.id, b)));
      } catch (error) { out.innerHTML = `<p class="error">${escapeHtml(t("error") + error.message)}</p>`; }
    });
    body.append(form, out);
  };
  calcs.forEach(([name]) => {
    const b = chip(escapeHtml(t("calcs")[name]), false, () => show(name));
    b.dataset.calc = name; tabs.append(b);
  });
  show(calcs[0][0]);
  return el;
}

function letterTool(data) {
  const el = tool("letter", '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>', t("letterTitle"));
  let letterLang = lang === "fr" ? "fr" : "ar";
  el.insertAdjacentHTML("beforeend", `<div class="chips letter-kinds"></div><div class="chips small letter-lang"></div><div class="letter-out" aria-live="polite"></div>`);
  const out = el.querySelector(".letter-out");
  const langs = el.querySelector(".letter-lang");
  const drawLangs = () => {
    langs.innerHTML = "";
    ["ar", "fr"].forEach((l) => langs.append(chip(t("letterIn")[l], letterLang === l, () => { letterLang = l; drawLangs(); })));
  };
  drawLangs();
  Object.entries(t("letterKinds")).forEach(([kind, label]) => el.querySelector(".letter-kinds").append(chip(escapeHtml(label), false, async (e) => {
    el.querySelectorAll(".letter-kinds .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === e.currentTarget)));
    out.innerHTML = `<p class="muted">${t("writingLetter")}</p>`;
    try {
      const response = await fetch("/letter", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind, language: letterLang, story: data.question, facts, analysis: data.sections || { answer: data.text }, sources: data.citations.map((c) => c.id) }),
      });
      const letter = await response.json();
      if (!response.ok) throw new Error(letter.detail || response.statusText);
      showLetter(out, letter);
    } catch (error) { out.innerHTML = `<p class="error">${escapeHtml(t("error") + error.message)}</p>`; }
  })));
  return el;
}
function showLetter(out, letter) {
  const dir = letter.language === "ar" ? "rtl" : "ltr";
  out.innerHTML = `<p class="flag">${t("letterDraft")}</p>${letter.verified ? "" : `<p class="flag">${t("unverified")}</p>`}
    <article class="letter-paper" dir="${dir}"><p><b>${escapeHtml(letter.recipient)}</b></p><p><b>${escapeHtml(letter.subject)}</b></p>
      ${escapeHtml(letter.body).replace(/\[([^\]]+)\]/g, '<mark>[$1]</mark>').split("\n").map((l) => `<p>${l}</p>`).join("")}</article>
    <div class="answer-actions"><button class="ghost" data-a="word">${t("downloadWord")}</button><button class="ghost" data-a="copy">${t("copy")}</button><button class="ghost" data-a="print">${t("printLetter")}</button></div>`;
  const text = `${letter.recipient}\n${letter.subject}\n\n${letter.body}`;
  out.querySelector('[data-a="copy"]').addEventListener("click", async () => { try { await navigator.clipboard.writeText(text); toast(t("copied")); } catch { /* blocked */ } });
  out.querySelector('[data-a="word"]').addEventListener("click", async () => {
    const r = await fetch("/letter.docx", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ subject: letter.subject, recipient: letter.recipient, body: letter.body, language: letter.language }) });
    if (r.ok) saveBlob(await r.blob(), "qanoun-letter.docx");
  });
  out.querySelector('[data-a="print"]').addEventListener("click", () => {
    document.body.classList.add("printing-letter");
    out.querySelector(".letter-paper").classList.add("print-me");
    window.print();
    document.body.classList.remove("printing-letter");
    out.querySelector(".letter-paper").classList.remove("print-me");
  });
}

async function openArticleById(id, from) {
  const cited = current?.citations.find((c) => c.id === id);
  if (cited) { openArticle(cited.number, from); return; }
  try {
    const response = await fetch(`/articles/${encodeURIComponent(id)}`);
    if (!response.ok) return;
    const a = await response.json();
    const rtl = a.language === "ar";
    $("panel-body").innerHTML = `<div dir="${rtl ? "rtl" : "ltr"}"><h2>${escapeHtml(a.article_word || t("article"))} ${escapeHtml(a.article_number)}</h2>
      <p class="law">${escapeHtml(a.law_title)}</p><ul class="path">${a.hierarchy.map((h) => `<li>${escapeHtml(h)}</li>`).join("")}</ul>
      <p class="article-text">${escapeHtml(a.text)}</p><a class="pdf" href="${escapeHtml(a.source_url)}" target="_blank" rel="noopener">${t("openPdf")}</a></div>`;
    openPanel("panel", from);
  } catch { /* offline */ }
}

// ---------- listen to the answer (the browser's own voices) ----------
function setupListen(data) {
  const b = $("listen");
  const voices = "speechSynthesis" in window;
  b.hidden = !voices || data.language === "darija-latn" || data.status !== "answered";
  if (b.hidden) return;
  speechSynthesis.cancel();
  b.querySelector("span").textContent = t("listen");
  b.onclick = () => {
    if (speechSynthesis.speaking) { speechSynthesis.cancel(); b.querySelector("span").textContent = t("listen"); return; }
    const text = (data.sections ? SECTIONS.map(([k]) => data.sections[k]).filter(Boolean).join(". ") : data.text).replace(/\[\d+\]/g, "");
    const say = new SpeechSynthesisUtterance(text);
    say.lang = data.language === "fr" ? "fr-FR" : "ar-MA";
    const voice = speechSynthesis.getVoices().find((v) => v.lang.startsWith(say.lang.slice(0, 2)));
    if (voice) say.voice = voice;
    say.onend = () => { b.querySelector("span").textContent = t("listen"); };
    speechSynthesis.speak(say);
    b.querySelector("span").textContent = t("stopListen");
  };
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
