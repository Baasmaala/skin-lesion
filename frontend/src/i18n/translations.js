export const translations = {
  en: {
    nav: {
      home: "Home",
      analyze: "Analyze",
      clinics: "Clinics",
      learn: "Learn",
      cta: "Analyze a photo",
      toggleMenu: "Toggle navigation menu",
      themeGroup: "Theme",
      themeLight: "light",
      themeDark: "dark",
      themeSystem: "system",
      languageGroup: "Language",
    },
    footer: {
      tagline:
        "AI assisted skin lesion screening, built as an academic deep learning research project.",
      disclaimer:
        "Rareflect is a research and educational tool. Its predictions are intended to support, not replace, evaluation by a qualified medical professional. Always consult a dermatologist for diagnosis and treatment decisions.",
    },
    home: {
      hero: {
        title: "Check a lesion your way.",
        subtitle:
          "Rareflect screens skin lesions with a model trained on images graded by dermatologists. Start from your phone in seconds, or visit a partner clinic for a more detailed scan and a direct path to a dermatologist if something needs a closer look.",
      },
      phonePath: {
        title: "Use your phone",
        text: "Take a photo at home and get a screening result in under a minute. It is private, free to start, and needs no appointment.",
        cta: "Analyze a photo",
      },
      clinicPath: {
        title: "Visit a clinic",
        text: "Partner clinics capture a dermatoscope scan, read by a model trained specifically on that kind of image, then connect you straight to a dermatologist if a result is flagged.",
        cta: "Find a clinic",
      },
      finePrint:
        "Rareflect is a screening aid, not a diagnosis. Results flagged as rare should always be reviewed by a dermatologist. The clinic path connects you to one directly.",
      funFact: {
        title: "Why early checks matter",
        text: "Melanoma is far less common than other skin cancers, but it causes most skin cancer deaths. Caught early, about 99% of cases are treated successfully. Catching it early is exactly what a quick phone photo can help with.",
      },
      steps: {
        heading: "Three simple steps",
        subtext: "From photo to result, Rareflect keeps the process quick and transparent.",
        items: [
          {
            number: "01",
            title: "Take or upload a photo",
            text: "Take a clear photo of a lesion yourself, or have one captured at a partner clinic.",
          },
          {
            number: "02",
            title: "The model analyzes it",
            text: "A model trained on dermatologist graded images evaluates the lesion's features.",
          },
          {
            number: "03",
            title: "Get a clear result",
            text: "See whether it looks common, uncertain, or flagged as rare, plus a clear next step.",
          },
        ],
      },
      benefits: {
        heading: "Purpose and benefits",
        subtext:
          "Built as an AI research project to explore how deep learning can support early skin lesion screening.",
        items: [
          {
            title: "Fast, private screening",
            text: "Get a read on a lesion in under a minute, with no appointment needed to start.",
          },
          {
            title: "Built on real research",
            text: "Trained on dermatologist graded dermoscopy images, evaluated with attention to rare classes.",
          },
          {
            title: "A clear next step, always",
            text: "Every result names what to do next, whether that is nothing, a follow up, or a dermatologist visit.",
          },
        ],
      },
      disclaimer: {
        label: "Medical disclaimer.",
        text: "Rareflect is a research and educational prototype. Its results are a screening aid, not a medical diagnosis, and should never replace evaluation by a qualified dermatologist.",
      },
      cta: {
        title: "Ready to try it?",
        text: "Upload a skin lesion photo and get a screening result right away.",
        button: "Analyze a photo",
      },
    },
    analyze: {
      title: "Analyze a skin lesion",
      subtitle:
        "Upload a clear, well lit photo of the lesion. For best results, keep the lesion centered and in focus.",
      tipsTitle: "How to get the best phone photo",
      tips: [
        "Use bright, natural light and avoid harsh shadows or glare.",
        "Hold the phone steady and roughly level with the skin, not at a sharp angle.",
        "Get close enough that the lesion fills a good part of the frame, but keep it in focus.",
        "Avoid using flash directly on the skin. It can wash out color and texture.",
      ],
    },
    clinics: {
      title: "Visit a partner clinic",
      subtitle:
        "Partner clinics will capture a dermatoscope scan and connect you straight to a dermatologist if a result is flagged.",
      noticeTitle: "Partner clinic listings are coming soon",
      noticeText:
        "We are onboarding the first partner clinics now. In the meantime, this page previews the dermatoscope trained side of Rareflect: the more detailed scan a clinic visit would offer, as opposed to the phone model built for ordinary camera photos.",
      tipsTitle: "How to get the closest clinic preview",
      tips: [
        "This preview is trained on dermatoscope images: close, magnified, and evenly lit.",
        "Upload an image captured with a dermatoscope, not a regular phone photo.",
        "The lesion should already fill almost the entire frame, centered and in sharp focus.",
        "Even, diffuse lighting with no shadows, hair, or reflections gives the most accurate read.",
      ],
    },
    learn: {
      title: "The seven types we screen for",
      subtitle:
        "Rareflect classifies a lesion into one of seven categories, three of them cancerous or precancerous and four of them benign. This is general information, not medical advice. A dermatologist should always confirm any diagnosis.",
      prevAria: "Previous lesion type",
      nextAria: "Next lesion type",
      dotsAria: "Lesion type",
      malignantBadge: "Cancerous or precancerous",
      benignBadge: "Usually benign",
      imageAlt: "Dermoscopic example of {name}",
      creditBefore: "Example images from the",
      creditLinkText: "ISIC Archive",
      creditAfter: ", released under CC0.",
      types: [
        {
          code: "MEL",
          name: "Melanoma",
          text: "The most serious form of skin cancer. It develops in the pigment producing cells and can spread to other parts of the body if not caught early. Often shows up as a new mole, or an existing one that changes in size, shape, or color. Early detection makes a real difference in outcomes.",
        },
        {
          code: "NV",
          name: "Melanocytic Nevus",
          text: "Commonly known as a mole. Almost everyone has several, and the vast majority stay harmless for life. Still worth keeping an eye on if one changes noticeably over time.",
        },
        {
          code: "BCC",
          name: "Basal Cell Carcinoma",
          text: "The most common form of skin cancer. It grows slowly and rarely spreads beyond the skin, but can damage surrounding tissue if left untreated. Often looks like a pearly or waxy bump, or a flat patch that will not heal.",
        },
        {
          code: "AKIEC",
          name: "Actinic Keratosis / Intraepithelial Carcinoma",
          text: "A rough, scaly patch caused by years of sun exposure, sometimes described as precancerous. A small number of cases progress into a more serious skin cancer if left untreated, so these are usually monitored or removed.",
        },
        {
          code: "BKL",
          name: "Benign Keratosis",
          text: "A group of harmless growths that become more common with age. They often look waxy, scaly, or stuck on the skin, and do not need treatment unless they become irritated.",
        },
        {
          code: "DF",
          name: "Dermatofibroma",
          text: "A small, firm, harmless nodule, often found on the legs. It is sometimes linked to a minor injury such as an insect bite, and does not require treatment.",
        },
        {
          code: "VASC",
          name: "Vascular Lesion",
          text: "A group of harmless lesions made up of blood vessels, appearing as red or purple marks on the skin. Most are present from birth or develop naturally and are not a health concern.",
        },
      ],
    },
    analyzePanel: {
      defaultTipsTitle: "How to get the best photo",
      defaultTips: [
        "Use bright, even light. Avoid harsh shadows or glare.",
        "Hold the camera directly above the lesion, not at an angle.",
        "Get close enough that the lesion fills most of the frame.",
        "Hold steady and let the camera focus before you shoot.",
      ],
      analyzeButton: "Analyze Image",
      analyzingText: "Analyzing image with the AI model…",
      errorMsg: "Something went wrong while analyzing the image. Please try again.",
    },
    stepper: {
      upload: "Upload",
      analyzing: "Analyzing",
      result: "Result",
    },
    resultCard: {
      unclearTitle: "Not a clear lesion photo",
      unclearNote:
        "The model's top confidence was only {confidence}%, too low to give a reliable classification. This usually means the photo is not a close, clear image of a lesion. Try uploading a clearer, closer photo.",
      unclearDisclaimer:
        "This is a heuristic check, not a guaranteed filter. The model can occasionally still be confidently wrong on images unlike its training data.",
      flaggedTitle: "Flagged as rare",
      flaggedLeadBefore:
        "This image shows features the model associates with rare, higher risk lesions. This is a screening result, not a diagnosis. The recommended next step is to see a dermatologist soon, or",
      flaggedLeadLink: "use the clinic path",
      flaggedLeadAfter: "for a professional scan and referral.",
      commonTitle: "Likely common",
      commonLead:
        "No follow up urgency is indicated by this result. If the lesion changes over time or you are still concerned, a dermatologist can take a closer look.",
      uncertainNote:
        "This image's internal features sit somewhat outside the model's usual range. Treat this specific result with a bit of extra caution.",
      predictedTypeLabel: "Predicted type",
      confidenceLabel: "Confidence",
      breakdownLabel: "Full breakdown, all classes",
      gradcamLabel: "Where the model looked (Grad CAM)",
      gradcamAlt: "Grad CAM heatmap showing which region of the image influenced the prediction",
      disclaimer:
        "This result is generated by an AI research prototype and is intended to support, not replace, evaluation by a qualified dermatologist. Please consult a medical professional for an official diagnosis.",
    },
    uploadArea: {
      invalidType: "Please upload a JPG, PNG, or WEBP image.",
      previewAlt: "Selected skin lesion",
      removeButton: "Remove & choose another image",
      dragTitle: "Drag & drop your image here",
      or: "or",
      takePhoto: "Take a photo",
      browseFiles: "Browse files",
      hint: "Supports JPG, PNG, WEBP",
    },
  },

  ar: {
    nav: {
      home: "الرئيسية",
      analyze: "التحليل",
      clinics: "العيادات",
      learn: "تعلم",
      cta: "حلل صورة",
      toggleMenu: "تبديل قائمة التنقل",
      themeGroup: "المظهر",
      themeLight: "فاتح",
      themeDark: "داكن",
      themeSystem: "النظام",
      languageGroup: "اللغة",
    },
    footer: {
      tagline:
        "فحص أولي للآفات الجلدية بمساعدة الذكاء الاصطناعي، بُني كمشروع بحثي أكاديمي في التعلم العميق.",
      disclaimer:
        "Rareflect أداة بحثية وتعليمية. الهدف من تنبؤاتها هو دعم تقييم أخصائي طبي مؤهل وليس استبداله. استشر دائماً طبيب الجلدية لاتخاذ قرارات التشخيص والعلاج.",
    },
    home: {
      hero: {
        title: "افحص آفتك الجلدية بطريقتك.",
        subtitle:
          "يفحص Rareflect الآفات الجلدية باستخدام نموذج مدرب على صور صنّفها أطباء الجلدية. ابدأ من هاتفك خلال ثوانٍ، أو قم بزيارة عيادة شريكة للحصول على فحص أكثر تفصيلاً ومسار مباشر إلى طبيب الجلدية إذا احتاج الأمر إلى نظرة أقرب.",
      },
      phonePath: {
        title: "استخدم هاتفك",
        text: "التقط صورة من المنزل واحصل على نتيجة فحص أولي في أقل من دقيقة. الخدمة خاصة ومجانية للبدء ولا تحتاج إلى موعد.",
        cta: "حلل صورة",
      },
      clinicPath: {
        title: "زر عيادة",
        text: "تلتقط العيادات الشريكة فحصاً بجهاز الديرماتوسكوب، يقرأه نموذج مدرب خصيصاً على هذا النوع من الصور، ثم تحوّلك مباشرة إلى طبيب الجلدية إذا صُنّفت النتيجة على أنها نادرة.",
        cta: "ابحث عن عيادة",
      },
      finePrint:
        "Rareflect أداة فحص أولي وليست تشخيصاً. يجب أن تُراجَع أي نتيجة تُصنَّف كنادرة من قبل طبيب الجلدية دائماً. مسار العيادة يوصلك بطبيب مباشرة.",
      funFact: {
        title: "لماذا يهم الفحص المبكر",
        text: "الورم الميلانيني أقل شيوعاً بكثير من أنواع سرطان الجلد الأخرى، لكنه المسؤول عن معظم الوفيات الناتجة عن سرطان الجلد. عند اكتشافه مبكراً، تُعالَج نحو 99% من الحالات بنجاح. والاكتشاف المبكر هو بالضبط ما يمكن أن تساعد فيه صورة سريعة من الهاتف.",
      },
      steps: {
        heading: "ثلاث خطوات بسيطة",
        subtext: "من الصورة إلى النتيجة، تحرص Rareflect على أن تكون العملية سريعة وواضحة.",
        items: [
          {
            number: "01",
            title: "التقط صورة أو ارفعها",
            text: "التقط صورة واضحة للآفة بنفسك، أو احصل عليها في عيادة شريكة.",
          },
          {
            number: "02",
            title: "يحلل النموذج الصورة",
            text: "يقيّم نموذج مدرب على صور صنّفها أطباء الجلدية خصائص الآفة.",
          },
          {
            number: "03",
            title: "احصل على نتيجة واضحة",
            text: "تعرف إن كانت الآفة تبدو شائعة أو غير مؤكدة أو مصنّفة كنادرة، مع خطوة تالية واضحة.",
          },
        ],
      },
      benefits: {
        heading: "الهدف والفوائد",
        subtext:
          "بُني Rareflect كمشروع بحثي في الذكاء الاصطناعي لاستكشاف كيف يمكن للتعلم العميق أن يدعم الفحص المبكر للآفات الجلدية.",
        items: [
          {
            title: "فحص سريع وخاص",
            text: "احصل على قراءة للآفة في أقل من دقيقة، دون الحاجة إلى موعد للبدء.",
          },
          {
            title: "مبني على بحث علمي حقيقي",
            text: "مدرب على صور ديرموسكوبية صنّفها أطباء الجلدية، وتم تقييمه مع اهتمام خاص بالفئات النادرة.",
          },
          {
            title: "خطوة تالية واضحة دائماً",
            text: "كل نتيجة تحدد ما ينبغي فعله بعدها، سواء لم يكن هناك ما يستدعي القلق أو كانت هناك حاجة إلى متابعة أو زيارة طبيب الجلدية.",
          },
        ],
      },
      disclaimer: {
        label: "إخلاء مسؤولية طبي.",
        text: "Rareflect نموذج أولي بحثي وتعليمي. نتائجه أداة مساعدة للفحص الأولي وليست تشخيصاً طبياً، ولا يجب أن تحل أبداً محل تقييم طبيب الجلدية المؤهل.",
      },
      cta: {
        title: "جاهز لتجربته؟",
        text: "ارفع صورة لآفة جلدية واحصل على نتيجة فحص أولي فوراً.",
        button: "حلل صورة",
      },
    },
    analyze: {
      title: "حلل آفة جلدية",
      subtitle:
        "ارفع صورة واضحة وجيدة الإضاءة للآفة. للحصول على أفضل النتائج، حافظ على أن تكون الآفة في المنتصف وفي بؤرة التركيز.",
      tipsTitle: "كيف تحصل على أفضل صورة بالهاتف",
      tips: [
        "استخدم إضاءة طبيعية ساطعة وتجنب الظلال القاسية أو الوهج.",
        "أمسك الهاتف بثبات وبمستوى قريب من الجلد، وليس بزاوية حادة.",
        "اقترب بما يكفي لتملأ الآفة جزءاً جيداً من الإطار، مع الحفاظ على وضوح التركيز.",
        "تجنب استخدام الفلاش مباشرة على الجلد، فقد يشوّه اللون والملمس.",
      ],
    },
    clinics: {
      title: "زر عيادة شريكة",
      subtitle:
        "ستلتقط العيادات الشريكة فحصاً بجهاز الديرماتوسكوب، وتحوّلك مباشرة إلى طبيب الجلدية إذا صُنّفت النتيجة على أنها نادرة.",
      noticeTitle: "قائمة العيادات الشريكة قادمة قريباً",
      noticeText:
        "نحن نعمل حالياً على ضم أولى العيادات الشريكة. في هذه الأثناء، تعرض هذه الصفحة معاينة للجانب المدرب على صور الديرماتوسكوب في Rareflect: الفحص الأكثر تفصيلاً الذي توفره زيارة العيادة، مقارنة بنموذج الهاتف المبني لصور الكاميرا العادية.",
      tipsTitle: "كيف تحصل على أقرب معاينة لتجربة العيادة",
      tips: [
        "هذه المعاينة مدربة على صور الديرماتوسكوب: قريبة ومكبرة ومضاءة بانتظام.",
        "ارفع صورة التُقطت بجهاز ديرماتوسكوب، وليست صورة عادية من الهاتف.",
        "يجب أن تملأ الآفة تقريباً كامل الإطار، وأن تكون في المنتصف وواضحة التركيز.",
        "الإضاءة المنتشرة والمتساوية دون ظلال أو شعر أو انعكاسات تعطي أدق قراءة.",
      ],
    },
    learn: {
      title: "الأنواع السبعة التي نفحصها",
      subtitle:
        "يصنّف Rareflect الآفة ضمن واحدة من سبع فئات، ثلاث منها سرطانية أو ما قبل سرطانية وأربع منها حميدة. هذه معلومات عامة وليست نصيحة طبية. يجب أن يؤكد طبيب الجلدية أي تشخيص دائماً.",
      prevAria: "النوع السابق من الآفات",
      nextAria: "النوع التالي من الآفات",
      dotsAria: "نوع الآفة",
      malignantBadge: "سرطاني أو ما قبل سرطاني",
      benignBadge: "حميد غالباً",
      imageAlt: "مثال ديرموسكوبي لـ {name}",
      creditBefore: "صور توضيحية من",
      creditLinkText: "أرشيف ISIC",
      creditAfter: "، منشورة بموجب رخصة CC0.",
      types: [
        {
          code: "MEL",
          name: "الورم الميلانيني",
          text: "أخطر أنواع سرطان الجلد. يتطور في الخلايا المنتجة للصبغة، ويمكن أن ينتشر إلى أجزاء أخرى من الجسم إن لم يُكتشف مبكراً. غالباً ما يظهر كشامة جديدة، أو شامة موجودة تتغير في الحجم أو الشكل أو اللون. الاكتشاف المبكر يُحدث فرقاً حقيقياً في النتائج.",
        },
        {
          code: "NV",
          name: "الوحمة الميلانينية",
          text: "تُعرف عادة بالشامة. يملك معظم الناس عدة شامات، وتبقى الغالبية العظمى منها غير ضارة مدى الحياة. مع ذلك يستحق الأمر المراقبة إذا تغيرت إحداها بشكل ملحوظ مع الوقت.",
        },
        {
          code: "BCC",
          name: "سرطان الخلايا القاعدية",
          text: "أكثر أنواع سرطان الجلد شيوعاً. ينمو ببطء ونادراً ما ينتشر خارج الجلد، لكنه قد يتلف الأنسجة المحيطة إذا تُرك دون علاج. غالباً ما يبدو كنتوء لامع أو شمعي، أو بقعة مسطحة لا تلتئم.",
        },
        {
          code: "AKIEC",
          name: "التقرن السفعي / السرطان داخل الظهارة",
          text: "بقعة خشنة ومتقشرة ناتجة عن سنوات من التعرض للشمس، وتوصف أحياناً بأنها حالة قد تتحول إلى سرطان. يتطور عدد صغير من الحالات إلى سرطان جلد أكثر خطورة إذا تُركت دون علاج، لذلك تخضع عادة للمراقبة أو الإزالة.",
        },
        {
          code: "BKL",
          name: "التقرن الحميد",
          text: "مجموعة من النموات غير الضارة التي تصبح أكثر شيوعاً مع التقدم في العمر. غالباً ما تبدو شمعية أو متقشرة أو كأنها ملتصقة بالجلد، ولا تحتاج إلى علاج ما لم تصبح مهيجة.",
        },
        {
          code: "DF",
          name: "الورم الليفي الجلدي",
          text: "عقدة صغيرة وصلبة وغير ضارة، توجد غالباً في الساقين. ترتبط أحياناً بإصابة بسيطة مثل لدغة حشرة، ولا تحتاج إلى علاج.",
        },
        {
          code: "VASC",
          name: "آفة وعائية",
          text: "مجموعة من الآفات غير الضارة المكونة من أوعية دموية، تظهر كعلامات حمراء أو أرجوانية على الجلد. معظمها موجود منذ الولادة أو يتطور بشكل طبيعي وليس مصدر قلق صحي.",
        },
      ],
    },
    analyzePanel: {
      defaultTipsTitle: "كيف تحصل على أفضل صورة",
      defaultTips: [
        "استخدم إضاءة ساطعة ومتساوية. تجنب الظلال القاسية أو الوهج.",
        "أمسك الكاميرا مباشرة فوق الآفة، وليس بزاوية.",
        "اقترب بما يكفي لتملأ الآفة معظم الإطار.",
        "حافظ على الثبات ودع الكاميرا تركّز قبل التقاط الصورة.",
      ],
      analyzeButton: "حلل الصورة",
      analyzingText: "جارٍ تحليل الصورة باستخدام نموذج الذكاء الاصطناعي…",
      errorMsg: "حدث خطأ أثناء تحليل الصورة. يرجى المحاولة مرة أخرى.",
    },
    stepper: {
      upload: "رفع",
      analyzing: "التحليل",
      result: "النتيجة",
    },
    resultCard: {
      unclearTitle: "ليست صورة واضحة لآفة",
      unclearNote:
        "كانت أعلى ثقة للنموذج {confidence}% فقط، وهي منخفضة جداً لإعطاء تصنيف موثوق. عادة ما يعني هذا أن الصورة ليست صورة قريبة وواضحة لآفة. حاول رفع صورة أوضح وأقرب.",
      unclearDisclaimer:
        "هذا فحص تقريبي وليس مرشحاً مضموناً. قد يكون النموذج أحياناً واثقاً وخاطئاً في صور تختلف عن بيانات تدريبه.",
      flaggedTitle: "مصنّفة كنادرة",
      flaggedLeadBefore:
        "تُظهر هذه الصورة خصائص يربطها النموذج بآفات نادرة وأعلى خطورة. هذه نتيجة فحص أولي وليست تشخيصاً. الخطوة التالية الموصى بها هي مراجعة طبيب الجلدية قريباً، أو",
      flaggedLeadLink: "استخدام مسار العيادة",
      flaggedLeadAfter: "للحصول على فحص احترافي وإحالة طبية.",
      commonTitle: "شائع على الأرجح",
      commonLead:
        "لا تشير هذه النتيجة إلى حاجة عاجلة للمتابعة. إذا تغيرت الآفة مع الوقت أو ما زلت قلقاً، يمكن لطبيب الجلدية أن يفحصها عن قرب.",
      uncertainNote:
        "تقع الخصائص الداخلية لهذه الصورة إلى حد ما خارج النطاق المعتاد للنموذج. تعامل مع هذه النتيجة تحديداً بقدر إضافي من الحذر.",
      predictedTypeLabel: "النوع المتوقع",
      confidenceLabel: "درجة الثقة",
      breakdownLabel: "التفاصيل الكاملة لجميع الفئات",
      gradcamLabel: "أين نظر النموذج (Grad CAM)",
      gradcamAlt: "خريطة حرارية Grad CAM توضح المنطقة التي أثرت في تنبؤ النموذج",
      disclaimer:
        "هذه النتيجة صادرة عن نموذج أولي بحثي للذكاء الاصطناعي، والهدف منها دعم تقييم طبيب الجلدية المؤهل وليس استبداله. يرجى استشارة أخصائي طبي للحصول على تشخيص رسمي.",
    },
    uploadArea: {
      invalidType: "يرجى رفع صورة بصيغة JPG أو PNG أو WEBP.",
      previewAlt: "آفة جلدية مختارة",
      removeButton: "إزالة واختيار صورة أخرى",
      dragTitle: "اسحب صورتك وأفلتها هنا",
      or: "أو",
      takePhoto: "التقط صورة",
      browseFiles: "تصفح الملفات",
      hint: "يدعم صيغ JPG وPNG وWEBP",
    },
    // Backend class names arrive as plain English text (result.type and
    // class_probabilities[].name), not translation keys, since they come
    // straight from backend/inference.py and inference_clinical.py's
    // CLASS_INFO. This maps those exact strings to Arabic. Covers both
    // the dermoscopic model's 7 classes (matching learn.types above) and
    // the clinical model's 6 classes (backend/inference_clinical.py),
    // which share some names (Melanoma, Basal Cell Carcinoma) but not
    // others (its "Nevus" and "Actinic Keratosis" are distinct diagnoses
    // from the dermoscopic model's "Melanocytic Nevus" and combined
    // "Actinic Keratosis / Intraepithelial Carcinoma").
    classNames: {
      "Melanoma": "الورم الميلانيني",
      "Melanocytic Nevus": "الوحمة الميلانينية",
      "Basal Cell Carcinoma": "سرطان الخلايا القاعدية",
      "Actinic Keratosis / Intraepithelial Carcinoma": "التقرن السفعي / السرطان داخل الظهارة",
      "Benign Keratosis": "التقرن الحميد",
      "Dermatofibroma": "الورم الليفي الجلدي",
      "Vascular Lesion": "آفة وعائية",
      "Actinic Keratosis": "التقرن السفعي",
      "Nevus": "وحمة",
      "Squamous Cell Carcinoma": "سرطان الخلايا الحرشفية",
      "Seborrheic Keratosis": "التقرن الدهني",
    },
  },
};
