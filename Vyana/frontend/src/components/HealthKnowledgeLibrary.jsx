import { useEffect, useState } from "react";
import VolumeUpIcon from "@mui/icons-material/VolumeUp";
import StopIcon from "@mui/icons-material/Stop";
import SearchIcon from "@mui/icons-material/Search";
import ClearIcon from "@mui/icons-material/Clear";
import WarningIcon from "@mui/icons-material/Warning";
import api from "../api/axios";

const KNOWLEDGE_TOPICS_HI = [
  {
    id: 1,
    category: "nutrition",
    icon: "🥗",
    tag_hi: "आहार और पोषण",
    tag_en: "Nutrition & Diet",
    title_hi: "गर्भावस्था में क्या खाएं और क्या न खाएं",
    title_en: "Essential Foods & Supplements",
    desc_hi: "हरी पत्तेदार सब्जियां, दालें, दूध, और गुड़-चना भरपूर खाएं। हर रोज एक आयरन और कैल्शियम की गोली जरूर लें। चाय और कॉफी कम पिएं।",
    desc_en: "Eat leafy greens, lentils, dairy, and iron-rich foods. Take your prescribed daily Iron and Calcium tablets.",
    audio_text_hi: "गर्भावस्था में हरी पत्तेदार सब्जियां, दालें, दूध, और गुड़-चना भरपूर खाएं। हर रोज एक आयरन और कैल्शियम की गोली जरूर लें।",
    audio_text_en: "Eat leafy greens, lentils, dairy, and iron-rich foods. Take your prescribed daily Iron and Calcium tablets.",
    danger_level: "LOW",
  },
  {
    id: 2,
    category: "danger",
    icon: "🚨",
    tag_hi: "खतरे के 5 निशान",
    tag_en: "5 Danger Signs",
    title_hi: "तुरंत अस्पताल कब जाना चाहिए?",
    title_en: "When to Seek Immediate Medical Help",
    desc_hi: "1. आंखों के आगे अंधेरा या तेज सिरदर्द, 2. पैरों या चेहरे पर अचानक सूजन, 3. तेज रक्तस्राव (ब्लीडिंग), 4. तेज बुखार, 5. बच्चे की हलचल कम होना।",
    desc_en: "1. Severe headache or blurred vision, 2. Sudden swelling, 3. Vaginal bleeding, 4. High fever, 5. Decreased fetal movement. Call 108.",
    audio_text_hi: "खतरे के मुख्य निशान: आंखों के आगे अंधेरा, अचानक सूजन, ब्लीडिंग, तेज बुखार, या बच्चे की हलचल बंद होना। ऐसा होने पर तुरंत 108 पर फोन करें।",
    audio_text_en: "Critical danger signs include blurred vision, sudden swelling, bleeding, high fever, or reduced baby kicks. Call 108 emergency.",
    danger_level: "HIGH",
  },
  {
    id: 3,
    category: "baby",
    icon: "👶",
    tag_hi: "शिशु की हलचल",
    tag_en: "Baby Movements",
    title_hi: "बच्चे की हलचल (किक काउंट) कैसे गिनें",
    title_en: "Counting Baby Kicks (Fetal Movement)",
    desc_hi: "28वें हफ्ते के बाद खाना खाने के बाद बाईं करवट लेटें। 2 घंटे में कम से कम 10 बार हलचल महसूस होनी चाहिए। कम होने पर आशा दीदी को बताएं।",
    desc_en: "After week 28, lie on your left side after meals. You should feel at least 10 kicks or flutters within 2 hours.",
    audio_text_hi: "28वें हफ्ते के बाद खाना खाने के बाद बाईं करवट लेटें। 2 घंटे में कम से कम 10 बार हलचल महसूस होनी चाहिए।",
    audio_text_en: "Lie on your left side after meals. You should feel at least 10 baby movements within 2 hours.",
    danger_level: "MEDIUM",
  },
  {
    id: 4,
    category: "schemes",
    icon: "🏛️",
    tag_hi: "सरकारी लाभ",
    tag_en: "Govt Schemes",
    title_hi: "जननी सुरक्षा योजना (JSY) व PMMVY",
    title_en: "Janani Suraksha (JSY) & PMMVY Benefits",
    desc_hi: "सरकारी अस्पताल में प्रसव कराने पर ₹1,400 की सीधी सहायता मिलती है। प्रधानमंत्री मातृ वंदना योजना के तहत ₹5,000 तीन किश्तों में दिए जाते हैं।",
    desc_en: "Get ₹1,400 financial assistance for institutional delivery under JSY and up to ₹5,000 in three installments under PMMVY.",
    audio_text_hi: "सरकारी अस्पताल में प्रसव कराने पर ₹1,400 सहायता मिलती है। मातृ वंदना योजना में ₹5,000 मिलते हैं। अपने कागजात आशा दीदी को जमा कराएं।",
    audio_text_en: "Receive ₹1,400 for institutional delivery under JSY and ₹5,000 under PMMVY. Contact your ASHA worker for documentation.",
    danger_level: "LOW",
  },
  {
    id: 5,
    category: "care",
    icon: "💧",
    tag_hi: "दैनिक देखभाल",
    tag_en: "Daily Wellness",
    title_hi: "पर्याप्त आराम और पानी पीना",
    title_en: "Hydration & Rest Guidelines",
    desc_hi: "दिन में कम से कम 8-10 गिलास साफ पानी पिएं। दोपहर में 2 घंटे और रात में 8 घंटे की नींद जरूर लें। भारी वजन उठाने से बचें।",
    desc_en: "Drink 8-10 glasses of clean water daily. Take 2 hours of rest in the afternoon and 8 hours of sleep at night. Avoid heavy lifting.",
    audio_text_hi: "दिन में कम से कम 8-10 गिलास पानी पिएं। दोपहर में 2 घंटे और रात में 8 घंटे आराम करें।",
    audio_text_en: "Drink plenty of water daily and ensure 2 hours afternoon rest and 8 hours night sleep.",
    danger_level: "LOW",
  },
  {
    id: 6,
    category: "vaccine",
    icon: "💉",
    tag_hi: "टीकाकरण",
    tag_en: "Vaccines",
    title_hi: "टीटी और टिटनेस के टीके",
    title_en: "Tetanus (TT) Immunization Schedule",
    desc_hi: "गर्भावस्था के दौरान टिटनेस (TT) के दो टीके लगवाना बहुत जरूरी है। यह मां और बच्चे दोनों को संक्रमण से सुरक्षित रखता है।",
    desc_en: "Two doses of Tetanus Toxoid (TT) vaccines during pregnancy protect both the mother and newborn from severe infections.",
    audio_text_hi: "गर्भावस्था में टिटनेस के 2 टीके समय पर जरूर लगवाएं। यह मां और बच्चे को सुरक्षित रखता है।",
    audio_text_en: "Ensure both TT vaccine doses are completed on schedule to safeguard mother and newborn.",
    danger_level: "LOW",
  },
];

export default function HealthKnowledgeLibrary({ lang }) {
  const isHi = lang === "hi";
  const [topics, setTopics] = useState(KNOWLEDGE_TOPICS_HI);
  const [activeCategory, setActiveCategory] = useState("all");
  const [speakingId, setSpeakingId] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [isLiveApi, setIsLiveApi] = useState(false);

  // Fetch topics from backend
  useEffect(() => {
    let isMounted = true;
    async function loadTopics() {
      try {
        const res = await api.get("/knowledge/topics");
        if (res.data?.success && res.data?.data?.topics?.length && isMounted) {
          setTopics(res.data.data.topics);
          setIsLiveApi(true);
        }
      } catch {
        // Fallback to local offline topics
        if (isMounted) {
          setTopics(KNOWLEDGE_TOPICS_HI);
          setIsLiveApi(false);
        }
      }
    }
    loadTopics();
    return () => { isMounted = false; };
  }, []);

  // Live fuzzy search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await api.get(`/knowledge/search?q=${encodeURIComponent(searchQuery.trim())}`);
        if (res.data?.success) {
          setSearchResults(res.data.data.results.map((r) => r.topic));
        }
      } catch {
        // Local search fallback
        const q = searchQuery.toLowerCase();
        const fallback = topics.filter(
          (t) =>
            (t.title_hi && t.title_hi.toLowerCase().includes(q)) ||
            (t.title_en && t.title_en.toLowerCase().includes(q)) ||
            (t.desc_hi && t.desc_hi.toLowerCase().includes(q)) ||
            (t.desc_en && t.desc_en.toLowerCase().includes(q))
        );
        setSearchResults(fallback);
      } finally {
        setSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery, topics]);

  const displayList = searchResults || (
    activeCategory === "all"
      ? topics
      : topics.filter((t) => t.category === activeCategory)
  );

  const playAudio = (text, id) => {
    if (!("speechSynthesis" in window)) return;

    if (speakingId === id) {
      window.speechSynthesis.cancel();
      setSpeakingId(null);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = isHi ? "hi-IN" : "en-IN";
    utterance.rate = 0.95;

    utterance.onend = () => setSpeakingId(null);
    utterance.onerror = () => setSpeakingId(null);

    setSpeakingId(id);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <section style={{ marginBottom: "36px" }}>
      <div className="vy-section-header">
        <h3 className="vy-section-title">
          <span className="vy-section-icon">📖</span>
          <span>{isHi ? "मातृ स्वास्थ्य जानकारी व नियम" : "Maternal Health Knowledge Base"}</span>
        </h3>
        <span style={{ fontSize: "12px", color: isLiveApi ? "var(--vy-teal-primary)" : "var(--vy-sage-green)", fontWeight: 700 }}>
          {isLiveApi ? (isHi ? "🟢 लाइव क्लिनिकल डेटाबेस" : "🟢 Connected Live DB") : (isHi ? "✓ ऑफलाइन उपलब्ध" : "✓ Available Offline")}
        </span>
      </div>

      {/* Fuzzy Search Bar */}
      <div style={{ position: "relative", marginBottom: "16px" }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          background: "var(--vy-surface)",
          border: "1.5px solid rgba(13, 92, 99, 0.15)",
          borderRadius: "16px",
          padding: "8px 14px",
          gap: "8px",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.03)",
        }}>
          <SearchIcon style={{ color: "var(--vy-teal-primary)", fontSize: "20px" }} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={isHi ? "लक्षण या विषय खोजें (उदा. सिर दर्द, आहार, टीका, 108)..." : "Search maternal guidance (e.g. headache, diet, kick count, schemes)..."}
            style={{
              flex: 1,
              border: "none",
              outline: "none",
              background: "transparent",
              fontSize: "14px",
              color: "var(--vy-text-body)",
              fontFamily: "inherit",
            }}
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              style={{ background: "none", border: "none", cursor: "pointer", color: "var(--vy-text-soft)", display: "flex" }}
            >
              <ClearIcon style={{ fontSize: "18px" }} />
            </button>
          )}
        </div>
      </div>

      {/* Category Pills (when not actively searching) */}
      {!searchQuery && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "20px" }}>
          {[
            { id: "all", labelHi: "सभी विषय", labelEn: "All Topics" },
            { id: "danger", labelHi: "🚨 खतरे के निशान", labelEn: "🚨 Danger Signs" },
            { id: "nutrition", labelHi: "🥗 आहार पोषण", labelEn: "🥗 Nutrition" },
            { id: "baby", labelHi: "👶 शिशु की हलचल", labelEn: "👶 Baby Kicks" },
            { id: "schemes", labelHi: "🏛️ सरकारी लाभ", labelEn: "🏛️ Govt Schemes" },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`vy-symptom-chip ${activeCategory === tab.id ? "selected" : ""}`}
              onClick={() => setActiveCategory(tab.id)}
              style={{ padding: "6px 14px", fontSize: "13px" }}
            >
              {isHi ? tab.labelHi : tab.labelEn}
            </button>
          ))}
        </div>
      )}

      {/* Cards Grid */}
      <div className="vy-knowledge-grid">
        {displayList.length === 0 ? (
          <div style={{ gridColumn: "1 / -1", textAlign: "center", padding: "30px 20px", color: "var(--vy-text-soft)" }}>
            {searching ? (isHi ? "खोज रहे हैं..." : "Searching clinical database...") : (isHi ? "कोई परिणाम नहीं मिला। कृपया दूसरा शब्द खोजें।" : "No matches found. Try a different query.")}
          </div>
        ) : (
          displayList.map((card) => {
            const title = isHi ? (card.title_hi || card.title) : (card.title_en || card.title);
            const desc = isHi ? (card.desc_hi || card.desc) : (card.desc_en || card.desc);
            const tag = isHi ? (card.tag_hi || card.tag) : (card.tag_en || card.tag);
            const audioText = isHi ? (card.audio_text_hi || card.audioText || desc) : (card.audio_text_en || card.audioText || desc);
            const isDanger = card.danger_level === "HIGH" || card.category === "danger";

            return (
              <div
                key={card.id}
                className="vy-knowledge-card"
                style={isDanger ? { borderColor: "rgba(224, 77, 77, 0.35)", background: "rgba(255, 245, 245, 0.85)" } : {}}
              >
                <div>
                  <div className="vy-kc-icon-box" style={isDanger ? { background: "var(--vy-coral-soft)" } : {}}>
                    {card.icon || "📖"}
                  </div>
                  <h4>{title}</h4>
                  <p>{desc}</p>
                </div>

                <div className="vy-kc-footer">
                  <span
                    className="vy-kc-tag"
                    style={isDanger ? { background: "var(--vy-coral-soft)", color: "var(--vy-coral-dark)" } : {}}
                  >
                    {tag}
                  </span>
                  <button
                    type="button"
                    className="vy-audio-listen-btn"
                    onClick={() => playAudio(audioText, card.id)}
                    title={isHi ? "ऑडियो में सुनें" : "Listen in audio"}
                  >
                    {speakingId === card.id ? (
                      <>
                        <StopIcon style={{ fontSize: "16px" }} />
                        <span>{isHi ? "रोकें" : "Stop"}</span>
                      </>
                    ) : (
                      <>
                        <VolumeUpIcon style={{ fontSize: "16px" }} />
                        <span>{isHi ? "सुनें" : "Listen"}</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

