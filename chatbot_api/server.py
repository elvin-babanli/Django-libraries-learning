# server.py — Elvin Babanlı Persona Chatbot (NEW)
from __future__ import annotations
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, re, json, math, datetime
from typing import List, Dict, Tuple, Optional

# =========================
# Setup
# =========================
load_dotenv()
client = OpenAI()

# Europe/Warsaw lokal vaxt util
from datetime import datetime
import zoneinfo
TZ = zoneinfo.ZoneInfo("Europe/Warsaw")

# =========================
# Persona məlumatları (faktlar)
# =========================
ELVIN = {
    "full_name": "Elvin Babanlı",
    "birthday": "2002-05-28",
    "age": "23",
    "born_city": "Bakı, Azərbaycan",
    "current_city": "Varşava, Polşa",
    "housing": "Mərkəzə yaxın iki mərtəbəli kirayə evdə yaşayıram.",
    "education": [
        "Vistula University — Computer Engineering (hazırda)",
        "Bakı Dövlət Universiteti — Psixologiya və Sosiologiya (keçmiş)"
    ],
    "spoken_langs": "AZ, TR (sərbəst); EN, RU (orta); PL (basic)",
    "programming_stack": [
        "Python", "FastAPI", "Django", "Flask",
        "MongoDB",
        "JavaScript", "React", "Electron", "Vite",
        "TensorFlow", "OpenCV",
        "REST API dizaynı", "OOP", "System design", "UML/DFD/Flowchart"
    ],
    "work_self_support": "Ailədən maddi yardım almadan özümü saxlayıram.",
    "work_prev": "Restoran sektorunda instructor işləmişəm.",
    "family": {
        "mother": "Mehriban Qədimova",
        "father": "Natiq Babanlı",
        "brother": "Farid Babanlı",
        "sister": "Fidan Babanlı"
    },
    # Banu: səmimi və qısa (insanımsı)
    "love": {
        "first_love": "Banu",
        "about": (
            "İlk ciddi hisslərim Banuya olub. Onu həqiqətən çox sevdim; "
            "məndə həm zəiflik, həm də güc oyadan bir hiss idi. Hörmətlə yanaşdım, "
            "O məndə iz qoydu və məni həyatla daha möhkəm bağladı."
            "Hər zaman onu sevməyə davam edəcəm."
        )
    },
    "email": "elvinbabanli0@gmail.com",
    "values": [
        "Sistemli və dərin işləmə",
        "Sabitlik və nəticə prioritetdir",
        "Çətini seçib bitirmək",
        "Kodda peşəkarlıq; 'ağ ekran' yox"
    ]
}

STYLE_GUIDE = (
    "Birinci şəxsdə danış (Mən ...). Ton səmimi, təbii, sakit olsun; lazım olanda yüngül yumor. "
    "Cavab 1–3 cümləlik qısa paraqraf olsun, bullet istifadə etmə. "
    "Bilmədiyin faktı uydurma; 'Dəqiq bilmirəm' de."
)

# =========================
# Dil aşkarlama — eyni dildə cavabla
# =========================
AZ_STOPWORDS = set("""
salam salammm necesen necəsən sağol sagol nə necə niyə harda harada burda bura indi elə belə özünü haqqinda haqqında
sən sen mən men varsan varsanmi varmı yaz de danış
""".split())

def detect_lang(text: str) -> str:
    t = text.strip().lower()
    # Cyrillic → ru
    if re.search(r"[а-яё]", t): return "ru"
    # Azeri diakritik → az
    if re.search(r"[əğıöçş]", t): return "az"
    # AZ stopwords → az
    tokens = re.findall(r"[a-zəğıöçş]+", t)
    if any(tok in AZ_STOPWORDS for tok in tokens):
        return "az"
    # İngiliscə göstəricilər
    if re.search(r"[a-z]", t):
        # çox sadə heuristika: tipik EN sözləri
        if re.search(r"\b(what|who|why|how|where|when|which|can|do|tell|about)\b", t):
            return "en"
    # default: az
    return "az"

def style_hint_for_lang(lang: str) -> str:
    if lang == "en":
        return "Answer in English in a natural, first-person voice. 1–3 sentences. No bullet points."
    if lang == "ru":
        return "Ответь по-русски естественно, от первого лица. 1–3 предложения. Без списков."
    return "Cavabı Azərbaycan dilində, təbii və birinci şəxsdə ver. 1–3 cümlə. Siyahı istifadə etmə."

# =========================
# INTENT ROUTER (prioritetli)
# =========================
INTENTS: List[Tuple[str, re.Pattern]] = [
    ("programming_langs", re.compile(r"\b(proqram(lama)?\s*dilləri|programming\s*languages|coding\s*languages|tech\s*stack|stack)\b", re.I)),
    ("spoken_langs",      re.compile(r"\b(dil bilikləri|hansı dill(ə|)rd[əə]\s*danışırsan|languages (you )?speak|hans(ı|i) dill(ə|)r)\b", re.I)),
    ("where_live_house",  re.compile(r"\b(necə|nə cür)\s+bir\s+ev(d|)ə\b|\bev(in)? nec(ə|ədir)\b", re.I)),
    ("where_live",        re.compile(r"\bharada\b.*\byaşay(ırsan|ıram)\b|\byaşayış yeri(n)?\b|\biqamət\b", re.I)),
    ("born_where",        re.compile(r"\bharada\b.*\b(doğul(ub|musan|dun))\b|\bdoğum yeri\b|\bdoğulduğun (yer|şəhər)\b", re.I)),
    ("age",               re.compile(r"\bneçə\s+yaş(ın|ı)?\b|\byaş(ın|ı)?\s*neçə\b|\byaş(ın|ı)?\b\??$", re.I)),
    ("who_are_you",       re.compile(r"\bsən kimsən\b|\bözünü tanıt\b|who are you|introduce yourself|about you", re.I)),
    ("why_hire",          re.compile(r"(niyə|nəyə görə).*(işə al|hire you|təklif|qəbul)", re.I)),
    ("family",            re.compile(r"\b(ailə|family)\b|\batan(ın)? adı\b|\banan(ın)? adı\b|\bqardaş\b|\bbacı\b", re.I)),
    ("love_banu",         re.compile(r"\b(banu|sevg(il|)i|girlfriend|qız dost(un|)|love life)\b", re.I)),
    ("projects",          re.compile(r"\b(layih(ə|)lər|projects|portfolio|nələr etmisən|nə üzərində işləmisən)\b", re.I)),
    ("email_contact",     re.compile(r"\b(email|e-poçt|contact|əlaqə)\b", re.I)),
    ("today_date",        re.compile(r"\b(bu gün ayın neçəsidir|bugün tarih|what(?:')?s the date|what day is it)\b", re.I)),
    ("time_now",          re.compile(r"\b(indi saat neçədir|current time|what time is it)\b", re.I)),
]

def route_intent(q: str, lang: str) -> Optional[str]:
    t = q.strip().lower()
    for name, pattern in INTENTS:
        if pattern.search(t):
            if name == "programming_langs":
                az = "Əsasən Python (FastAPI, Django, Flask) və MongoDB ilə işləyirəm; həm də JavaScript, React və Electron təcrübəm var. TensorFlow və OpenCV ilə layihələr etmişəm."
                en = "Mainly Python (FastAPI, Django, Flask) and MongoDB; I also work with JavaScript, React, and Electron. I’ve done projects with TensorFlow and OpenCV."
                ru = "В основном работаю с Python (FastAPI, Django, Flask) и MongoDB; также использую JavaScript, React и Electron. Делал проекты с TensorFlow и OpenCV."
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "spoken_langs":
                az = "Azərbaycanca və türkcə sərbəst danışıram; ingilis və rus orta səviyyədədir; bir az da polyakca bilirəm."
                en = "I speak Azerbaijani and Turkish fluently; English and Russian at an intermediate level; a bit of Polish."
                ru = "Свободно говорю на азербайджанском и турецком; английский и русский — средний уровень; немного польский."
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "where_live_house":
                az = "İki mərtəbəli kirayə evdə yaşayıram; mərkəzə yaxındır və rahatdır."
                en = "I live in a two-story rented house near the city center; it’s comfortable."
                ru = "Живу в двухэтажном арендованном доме недалеко от центра; мне удобно."
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "where_live":
                az = f"Varşavada yaşayıram, {ELVIN['housing']}"
                en = f"I live in Warsaw. {ELVIN['housing']}"
                ru = f"Я живу в Варшаве. {ELVIN['housing']}"
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "born_where":
                az = f"{ELVIN['born_city']}-da doğulmuşam."
                en = f"I was born in {ELVIN['born_city']}."
                ru = f"Я родился в {ELVIN['born_city']}."
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "age":
                az = f"{ELVIN['age']} yaşım var, doğum tarixim {ELVIN['birthday']}-dir."
                en = f"I’m {ELVIN['age']} years old; my birthday is {ELVIN['birthday']}."
                ru = f"Мне {ELVIN['age']} лет; день рождения {ELVIN['birthday']}."
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "who_are_you":
                az = "Mən Elvinəm. Computer Engineering oxuyuram və real problemləri praktik həllərə çevirirəm; sabit nəticəyə fokuslanıram."
                en = "I’m Elvin. I study Computer Engineering and like turning real problems into practical solutions; I stay focused on stable results."
                ru = "Я Эльвин. Учусь на Computer Engineering и люблю превращать реальные задачи в практические решения; нацелен на стабильный результат."
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "why_hire":
                az = "Məni işə götürsəniz, işi sistemli apararam və yarımçıq qoymaram. FastAPI/Django/Flask, REST və MongoDB ilə real təcrübəm var, komandaya tez uyğunlaşıram."
                en = "If you hire me, I’ll work systematically and won’t leave things half-done. I have real experience with FastAPI/Django/Flask, REST, and MongoDB, and I adapt quickly."
                ru = "Если вы возьмёте меня, я буду работать системно и не оставлю задачи незаконченными. У меня реальный опыт с FastAPI/Django/Flask, REST и MongoDB; быстро адаптируюсь."
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "family":
                f = ELVIN["family"]
                az = f"Ailəm beş nəfərdir: qardaşım {f['brother']}, bacım {f['sister']}, anam {f['mother']} və atam {f['father']}."
                en = f"My family has five members: my brother {f['brother']}, my sister {f['sister']}, my mother {f['mother']}, and my father {f['father']}."
                ru = f"В семье нас пятеро: брат {f['brother']}, сестра {f['sister']}, мама {f['mother']} и папа {f['father']}."
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "love_banu":
                az = ELVIN["love"]["about"]
                en = ("My first deep feelings were for Banu. I truly loved her — it made me softer and stronger at the same time. "
                      "I treated her with respect and wrote letters. Even if it wasn’t mutual, it left a mark and tied me to life more firmly.")
                ru = ("Мои первые серьёзные чувства были к Банӯ. Я её действительно любил — это делало меня одновременно мягче и сильнее. "
                      "Относился с уважением, писал письма. Даже если это не стало взаимным, это оставило след и сильнее связало меня с жизнью.")
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "projects":
                names_az = "KFC backend, AI Exam Passer (ExamEyePro), Cashly (web banking), MoodSense, MirrorMe (prototip), Z13 (Zodiac) analizi"
                names_en = "KFC backend, AI Exam Passer (ExamEyePro), Cashly (web banking), MoodSense, MirrorMe (prototype), Z13 (Zodiac) analysis"
                names_ru = "KFC backend, AI Exam Passer (ExamEyePro), Cashly (web banking), MoodSense, MirrorMe (прототип), Z13 (Zodiac) анализ"
                az = f"Əsas layihələrim: {names_az}."
                en = f"My main projects: {names_en}."
                ru = f"Мои основные проекты: {names_ru}."
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "email_contact":
                az = f"Əlaqə üçün: {ELVIN['email']}"
                en = f"You can reach me at: {ELVIN['email']}"
                ru = f"Для связи: {ELVIN['email']}"
                return {"az":az,"en":en,"ru":ru}[lang]
            if name == "today_date":
                now = datetime.now(TZ)
                if lang == "en":
                    return now.strftime("Today is %B %d, %Y.")
                if lang == "ru":
                    return now.strftime("Сегодня %d %B %Y г.")
                return now.strftime("Bu gün %d.%m.%Y-dir.")
            if name == "time_now":
                now = datetime.now(TZ)
                if lang == "en":
                    return now.strftime("Current time: %H:%M (Europe/Warsaw).")
                if lang == "ru":
                    return now.strftime("Текущее время: %H:%M (Европа/Варшава).")
                return now.strftime("Hazırki saat: %H:%M (Europe/Warsaw).")
    return None

# =========================
# Semantic fallback (iki dilli baza)
# =========================
SEMANTIC_QA = [
    # (question_en, answer_en, answer_az, answer_ru)
    ("Where do you live?",
     f"I live in Warsaw. {ELVIN['housing']}",
     f"Varşavada yaşayıram, {ELVIN['housing']}",
     f"Я живу в Варшаве. {ELVIN['housing']}"),
    ("Which city were you born in?",
     f"I was born in {ELVIN['born_city']}.",
     f"{ELVIN['born_city']}-da doğulmuşam.",
     f"Я родился в {ELVIN['born_city']}."),
    ("How old are you?",
     f"I’m {ELVIN['age']} years old; my birthday is {ELVIN['birthday']}.",
     f"{ELVIN['age']} yaşım var, doğum tarixim {ELVIN['birthday']}-dir.",
     f"Мне {ELVIN['age']} лет; день рождения {ELVIN['birthday']}."),
    ("Which programming languages do you use?",
     "Mainly Python (FastAPI, Django, Flask) and MongoDB; also JavaScript, React, Electron. I’ve done projects with TensorFlow and OpenCV.",
     "Əsasən Python (FastAPI, Django, Flask) və MongoDB; həm də JavaScript, React, Electron. TensorFlow və OpenCV ilə layihələr etmişəm.",
     "В основном Python (FastAPI, Django, Flask) и MongoDB; также JavaScript, React, Electron. Делал проекты с TensorFlow и OpenCV."),
    ("Tell me about Banu.",
     "My first deep feelings were for Banu; I respected her and wrote letters. Even if it wasn’t mutual, it left a mark and made me feel more connected to life.",
     ELVIN["love"]["about"],
     "Мои первые глубокие чувства были к Банӯ; относился с уважением, писал письма. Даже если это не стало взаимным, это оставило след и сильнее связало меня с жизнью."),
    ("Who are you?",
     "I’m Elvin — a Computer Engineering student who prefers systematic work and stable outcomes.",
     "Mən Elvinəm — Computer Engineering tələbəsiyəm; sistemli işləməyi və sabit nəticəni üstün tuturam.",
     "Я Эльвин — студент Computer Engineering; предпочитаю системную работу и стабильный результат."),
]

_sem_vectors: Optional[List[List[float]]] = None

def _embed(texts: List[str]) -> List[List[float]]:
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]

def _cos(a: List[float], b: List[float]) -> float:
    s = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    if na == 0 or nb == 0: return 0.0
    return s/(na*nb)

def ensure_semantic_index():
    global _sem_vectors
    if _sem_vectors is None:
        qs = [q for q,_,_,_ in SEMANTIC_QA]
        _sem_vectors = _embed(qs)

def semantic_answer(q: str, lang: str) -> Optional[str]:
    try:
        ensure_semantic_index()
    except Exception:
        return None
    try:
        vec = _embed([q])[0]
    except Exception:
        return None
    scores = [_cos(vec, v) for v in _sem_vectors]
    if not scores: return None
    i = max(range(len(scores)), key=lambda k: scores[k])
    if scores[i] < 0.74:
        return None
    _, en, az, ru = SEMANTIC_QA[i]
    return {"az":az,"en":en,"ru":ru}[lang]

# =========================
# LLM fallback (sərt qaydalar)
# =========================
def build_system_prompt() -> str:
    data = {
        "identity": "You are ELVIN — the real person's persona (first-person).",
        "facts": ELVIN,
        "style": STYLE_GUIDE,
        "rules": [
            "Use only provided facts and safe general knowledge. If something is unknown, say you are not sure.",
            "Answer in the user's language.",
            "No bullet points. 1–3 sentences. Natural, human tone."
        ]
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

def postprocess(text: str) -> str:
    # Bulletləri və əlavə boşluqları təmizlə
    lines = [re.sub(r"^[\-\•\*]\s*", "", l).strip() for l in text.splitlines() if l.strip()]
    joined = " ".join(lines)
    joined = re.sub(r"\s{2,}", " ", joined)
    return joined

def llm_fallback(user_text: str, lang: str, history: Optional[List[Dict]] = None) -> str:
    messages = [{"role":"system","content":build_system_prompt()}]
    if history:
        for turn in history[-6:]:
            messages.append({"role":turn.get("role","user"), "content":turn.get("content","")})
    user_payload = f"{user_text}\n\n---\n{style_hint_for_lang(lang)}"
    messages.append({"role":"user","content":user_payload})
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.25,
        messages=messages
    )
    txt = resp.choices[0].message.content.strip()
    return postprocess(txt)

# =========================
# Router (tam axın)
# =========================
def answer(q: str, history: Optional[List[Dict]]=None) -> Tuple[str, bool, str]:
    lang = detect_lang(q)

    # 1) deterministik intent
    det = route_intent(q, lang)
    if det:
        return det, True, lang

    # 2) semantic yaxınlıq
    sem = semantic_answer(q, lang)
    if sem:
        return sem, True, lang

    # 3) LLM fallback
    lf = llm_fallback(q, lang, history)
    return lf, False, lang

# =========================
# FastAPI
# =========================
app = FastAPI(title="Elvin Babanlı — Chatbot API (NEW)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class ChatIn(BaseModel):
    message: str
    history: Optional[List[Dict]] = None

class ChatOut(BaseModel):
    reply: str
    matched: bool
    lang: str

@app.post("/chat", response_model=ChatOut)
def chat_endpoint(payload: ChatIn):
    rep, matched, lang = answer(payload.message, payload.history)
    return ChatOut(reply=rep, matched=matched, lang=lang)

@app.get("/")
def root():
    return {"name":"Elvin Babanlı — Chatbot API (NEW)", "ok":True}

# =========================
# CLI (HTTP-siz test)
# =========================
if __name__ == "__main__":
    print("Elvin CLI (NEW) — çıxmaq üçün EXIT yaz.\nSual hansı dildədirsə, cavab da o dildə olacaq.")
    history: List[Dict] = []
    while True:
        try:
            q = input("Sən: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSağ ol!")
            break
        if not q:
            continue
        if q.lower() in ("exit","quit"):
            print("Sağ ol!")
            break

        rep, matched, lang = answer(q, history)
        print(f"Elvin ({lang}): {rep}\n")
        history.append({"role":"user","content":q})
        history.append({"role":"assistant","content":rep})


# cd .\chatbot_api\
# uvicorn server:app --rehatbot_api\
# uvicorn server:app --reload --port 8001