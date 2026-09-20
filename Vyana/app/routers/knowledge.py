import difflib
import re
from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.utils.response import success_response, error_response

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

class KnowledgeTopic(BaseModel):
    id: int
    category: str
    icon: str
    tag_hi: str
    tag_en: str
    title_hi: str
    title_en: str
    desc_hi: str
    desc_en: str
    audio_text_hi: str
    audio_text_en: str
    danger_level: str = "LOW"  # LOW | MEDIUM | HIGH
    keywords: List[str] = []

MATERNAL_KNOWLEDGE_BASE: List[KnowledgeTopic] = [
    KnowledgeTopic(
        id=1,
        category="nutrition",
        icon="🥗",
        tag_hi="आहार और पोषण",
        tag_en="Nutrition & Diet",
        title_hi="गर्भावस्था में क्या खाएं और क्या न खाएं",
        title_en="Essential Foods & Supplements",
        desc_hi="हरी पत्तेदार सब्जियां, दालें, दूध, और गुड़-चना भरपूर खाएं। हर रोज एक आयरन (IFA) और कैल्शियम की गोली जरूर लें। चाय और कॉफी कम पिएं।",
        desc_en="Eat leafy greens, lentils, dairy, and iron-rich foods. Take your prescribed daily Iron & Folic Acid (IFA) and Calcium tablets. Avoid excess tea or coffee.",
        audio_text_hi="गर्भावस्था में हरी पत्तेदार सब्जियां, दालें, दूध, और गुड़-चना भरपूर खाएं। हर रोज एक आयरन और कैल्शियम की गोली जरूर लें।",
        audio_text_en="Eat leafy greens, lentils, dairy, and iron-rich foods. Take your prescribed daily Iron and Calcium tablets.",
        danger_level="LOW",
        keywords=["diet", "food", "nutrition", "iron", "calcium", "ifa", "khana", "poshan", "doodh", "sabji", "tablet"],
    ),
    KnowledgeTopic(
        id=2,
        category="danger",
        icon="🚨",
        tag_hi="खतरे के 5 निशान",
        tag_en="5 Critical Danger Signs",
        title_hi="तुरंत अस्पताल कब जाना चाहिए?",
        title_en="When to Seek Immediate Medical Help",
        desc_hi="1. आंखों के आगे अंधेरा या तेज सिरदर्द, 2. पैरों या चेहरे पर अचानक सूजन, 3. तेज रक्तस्राव (ब्लीडिंग), 4. तेज बुखार, 5. बच्चे की हलचल कम होना या बंद होना। तुरंत 108 पर कॉल करें।",
        desc_en="1. Severe headache or blurred vision, 2. Sudden hand/facial swelling, 3. Vaginal bleeding, 4. High fever, 5. Decreased fetal movement. Call 108 immediately.",
        audio_text_hi="खतरे के मुख्य निशान: आंखों के आगे अंधेरा, अचानक सूजन, ब्लीडिंग, तेज बुखार, या बच्चे की हलचल बंद होना। ऐसा होने पर तुरंत 108 पर फोन करें।",
        audio_text_en="Critical danger signs include blurred vision, sudden swelling, bleeding, high fever, or reduced baby kicks. Call 108 emergency.",
        danger_level="HIGH",
        keywords=["danger", "emergency", "bleeding", "swelling", "headache", "fever", "khatra", "khoon", "sujan", "sir dard", "bukhar", "108"],
    ),
    KnowledgeTopic(
        id=3,
        category="baby",
        icon="👶",
        tag_hi="शिशु की हलचल",
        tag_en="Fetal Movement (Baby Kicks)",
        title_hi="बच्चे की हलचल (किक काउंट) कैसे गिनें",
        title_en="Counting Baby Kicks & Activity",
        desc_hi="28वें हफ्ते के बाद भोजन के उपरांत बाईं करवट लेटें। 2 घंटे में कम से कम 10 बार हलचल महसूस होनी चाहिए। यदि हलचल कम हो तो तुरंत आशा दीदी या डॉक्टर से संपर्क करें।",
        desc_en="After week 28, lie on your left side after meals. You should feel at least 10 kicks or flutters within 2 hours. If fewer, contact your ASHA worker immediately.",
        audio_text_hi="28वें हफ्ते के बाद खाना खाने के बाद बाईं करवट लेटें। 2 घंटे में कम से कम 10 बार हलचल महसूस होनी चाहिए।",
        audio_text_en="Lie on your left side after meals. You should feel at least 10 baby movements within 2 hours.",
        danger_level="MEDIUM",
        keywords=["baby", "kick", "movement", "fetal", "halchal", "bachha", "kick count", "shishu"],
    ),
    KnowledgeTopic(
        id=4,
        category="schemes",
        icon="🏛️",
        tag_hi="सरकारी लाभ",
        tag_en="Govt Welfare Schemes",
        title_hi="जननी सुरक्षा योजना (JSY) व PMMVY",
        title_en="Janani Suraksha (JSY) & PMMVY Benefits",
        desc_hi="सरकारी अस्पताल में प्रसव कराने पर ₹1,400 की सीधी आर्थिक सहायता मिलती है। प्रधानमंत्री मातृ वंदना योजना (PMMVY) के तहत ₹5,000 तीन किश्तों में बैंक खाते में दिए जाते हैं।",
        desc_en="Receive ₹1,400 financial assistance for institutional delivery under JSY and up to ₹5,000 in three installments under PMMVY. Contact your ASHA worker to enroll.",
        audio_text_hi="सरकारी अस्पताल में प्रसव कराने पर ₹1,400 सहायता मिलती है। मातृ वंदना योजना में ₹5,000 मिलते हैं। अपने कागजात आशा दीदी को जमा कराएं।",
        audio_text_en="Receive ₹1,400 for institutional delivery under JSY and ₹5,000 under PMMVY. Contact your ASHA worker for documentation.",
        danger_level="LOW",
        keywords=["scheme", "money", "govt", "jsy", "pmmvy", "rupees", "delivery", "sarkari", "labh", "paisa", "yojana"],
    ),
    KnowledgeTopic(
        id=5,
        category="care",
        icon="💧",
        tag_hi="दैनिक देखभाल",
        tag_en="Daily Wellness & Rest",
        title_hi="पर्याप्त आराम और पानी पीना",
        title_en="Hydration & Daily Rest Guidelines",
        desc_hi="दिन में कम से कम 8-10 गिलास साफ पानी पिएं। दोपहर में 2 घंटे और रात में 8 घंटे की भरपूर नींद जरूर लें। भारी वजन उठाने और अत्यधिक थकावट से बचें।",
        desc_en="Drink 8-10 glasses of clean water daily. Take 2 hours of rest in the afternoon and 8 hours of sleep at night. Avoid heavy lifting and extreme fatigue.",
        audio_text_hi="दिन में कम से कम 8-10 गिलास पानी पिएं। दोपहर में 2 घंटे और रात में 8 घंटे आराम करें। भारी वजन न उठाएं।",
        audio_text_en="Drink plenty of water daily and ensure 2 hours afternoon rest and 8 hours night sleep.",
        danger_level="LOW",
        keywords=["rest", "sleep", "water", "care", "wellness", "pani", "aaram", "neend", "thakaan"],
    ),
    KnowledgeTopic(
        id=6,
        category="vaccine",
        icon="💉",
        tag_hi="टीकाकरण",
        tag_en="Immunization (TT)",
        title_hi="टीटी और टिटनेस के टीके",
        title_en="Tetanus (TT) Immunization Schedule",
        desc_hi="गर्भावस्था के दौरान टिटनेस (TT) के दो टीके लगवाना अत्यंत आवश्यक है। यह प्रसव के समय मां और नवजात शिशु दोनों को घातक संक्रमण से सुरक्षित रखता है।",
        desc_en="Two doses of Tetanus Toxoid (TT) vaccines during pregnancy protect both the mother and newborn from severe infections. Get them on your ANC visit.",
        audio_text_hi="गर्भावस्था में टिटनेस के 2 टीके समय पर जरूर लगवाएं। यह मां और बच्चे को सुरक्षित रखता है।",
        audio_text_en="Ensure both TT vaccine doses are completed on schedule to safeguard mother and newborn.",
        danger_level="LOW",
        keywords=["vaccine", "tt", "tetanus", "injection", "teeka", "immunization", "anc"],
    ),
]

CRITICAL_DANGER_SIGNS = [
    {
        "id": "ds_1",
        "name_hi": "तेज रक्तस्राव (Bleeding)",
        "name_en": "Vaginal Bleeding",
        "action_hi": "बिना देर किए 108 पर कॉल करें और तुरंत नजदीकी अस्पताल पहुंचें।",
        "action_en": "Call 108 immediately and reach the nearest health facility.",
        "urgency": "EMERGENCY_IMMEDIATE",
    },
    {
        "id": "ds_2",
        "name_hi": "आंखों के आगे अंधेरा या तेज सिरदर्द",
        "name_en": "Severe Headache / Blurred Vision",
        "action_hi": "यह हाई बीपी (प्री-एक्लेम्पसिया) का लक्षण हो सकता है। तुरंत बीपी नपवाएं।",
        "action_en": "Possible Pre-eclampsia indicator. Check blood pressure immediately.",
        "urgency": "HIGH",
    },
    {
        "id": "ds_3",
        "name_hi": "हाथ, पैर व चेहरे पर अचानक सूजन",
        "name_en": "Sudden Facial / Extremity Swelling",
        "action_hi": "आशा दीदी को बुलाएं और मूत्र जांच (प्रोटीन) करवाएं।",
        "action_en": "Call ASHA worker for urgent urine albumin and BP checkup.",
        "urgency": "HIGH",
    },
    {
        "id": "ds_4",
        "name_hi": "तेज बुखार व कंपकंपी",
        "name_en": "High Fever & Chills",
        "action_hi": "संक्रमण का खतरा। डॉक्टर से जांच कराकर दवा लें।",
        "action_en": "Infection risk. Consult a doctor for diagnostic workup.",
        "urgency": "HIGH",
    },
    {
        "id": "ds_5",
        "name_hi": "शिशु की हलचल बंद या बहुत कम होना",
        "name_en": "Reduced or Absent Fetal Movement",
        "action_hi": "बाईं करवट लेटकर 1 घंटा देखें, हलचल न हो तो तुरंत अस्पताल जाएं।",
        "action_en": "Lie on left side for 1 hour; if no movement, visit hospital immediately.",
        "urgency": "HIGH",
    },
]


@router.get("/topics")
def get_all_topics(category: Optional[str] = None):
    topics = MATERNAL_KNOWLEDGE_BASE
    if category and category.lower() != "all":
        topics = [t for t in topics if t.category.lower() == category.lower()]
    return success_response({"topics": [t.dict() for t in topics]})


@router.get("/danger-signs")
def get_danger_signs():
    return success_response({"danger_signs": CRITICAL_DANGER_SIGNS})


def _fuzzy_score(query: str, text: str) -> float:
    query = query.lower().strip()
    text = text.lower().strip()
    if query in text:
        return 1.0
    return difflib.SequenceMatcher(None, query, text).ratio()


@router.get("/search")
def search_knowledge(q: str = Query(..., min_length=1)):
    try:
        query_norm = q.lower().strip()
        matches = []
        for t in MATERNAL_KNOWLEDGE_BASE:
            score = 0.0
            # Check keywords
            for kw in t.keywords:
                s = _fuzzy_score(query_norm, kw)
                if s > score:
                    score = s
            # Check title and descriptions
            title_score = max(_fuzzy_score(query_norm, t.title_hi), _fuzzy_score(query_norm, t.title_en))
            desc_score = max(_fuzzy_score(query_norm, t.desc_hi), _fuzzy_score(query_norm, t.desc_en))
            final_score = max(score, title_score * 0.9, desc_score * 0.7)

            if final_score >= 0.4 or any(w in query_norm for w in t.keywords):
                matches.append({
                    "topic": t.dict(),
                    "relevance": round(final_score, 2),
                    "is_danger": t.danger_level == "HIGH",
                })

        matches.sort(key=lambda m: m["relevance"], reverse=True)
        return success_response({
            "query": q,
            "total_matches": len(matches),
            "results": matches,
        })
    except Exception as exc:
        return error_response(f"Search failed: {exc}", 500)
