# ================================================================
# AI Smart Insulin Pump Research Agent
# Streamlit Web App
#
# Student: Hugo Silva | ID: 74964557
# ITU | SPRING 2026 | HCM 535 – Data Analytics in Healthcare
#
# HOW TO RUN LOCALLY:
#   pip install streamlit anthropic python-pptx
#   streamlit run app.py
#
# HOW TO DEPLOY FREE:
#   1. Push this file to a GitHub repo
#   2. Go to share.streamlit.io
#   3. Connect your repo → Deploy
#   4. Add ANTHROPIC_API_KEY in Streamlit Secrets
# ================================================================

import streamlit as st
import anthropic
import json
import re
import os
from datetime import datetime
from io import BytesIO

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── PAGE CONFIG ─────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Insulin Pump Agent",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Serif+Display:ital@0;1&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

/* Header */
.main-header {
    background: linear-gradient(135deg, #042F2E 0%, #0F766E 100%);
    padding: 2rem 2.5rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    border-left: 6px solid #F59E0B;
}
.main-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    color: #CCFBF1;
    margin: 0 0 0.3rem 0;
}
.main-header p {
    color: #5EEAD4;
    font-size: 0.9rem;
    margin: 0;
    opacity: 0.85;
}
.student-badge {
    background: rgba(245,158,11,0.15);
    border: 1px solid #F59E0B;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    color: #FCD34D;
    font-size: 0.8rem;
    margin-top: 0.8rem;
    display: inline-block;
}

/* Cards */
.metric-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.2rem;
    border-top: 3px solid #14B8A6;
    margin-bottom: 0.8rem;
}
.metric-card h3 {
    font-size: 2rem;
    font-weight: 800;
    color: #0F766E;
    margin: 0;
    font-family: 'DM Serif Display', serif;
}
.metric-card p {
    font-size: 0.75rem;
    color: #64748B;
    margin: 0.2rem 0 0 0;
}

/* Steps */
.step-box {
    background: #042F2E;
    border: 1px solid #0F766E;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.6rem;
    color: #CCFBF1;
    font-size: 0.85rem;
}
.step-box strong {
    color: #F59E0B;
}

/* Report area */
.report-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.5rem;
    max-height: 500px;
    overflow-y: auto;
    font-size: 0.88rem;
    line-height: 1.7;
    color: #0F172A;
    white-space: pre-wrap;
}

/* Status badges */
.badge-success {
    background: #EAF3DE;
    color: #27500A;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-running {
    background: #FAEEDA;
    color: #633806;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Sidebar */
.sidebar-section {
    background: #F1F5F9;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
    font-size: 0.82rem;
    color: #334155;
}

/* Divider */
.teal-divider {
    border: none;
    border-top: 2px solid #14B8A6;
    margin: 1rem 0;
    opacity: 0.3;
}

/* Download button */
.stDownloadButton button {
    background: #0F766E !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    padding: 0.6rem 1.5rem !important;
    font-size: 0.9rem !important;
    width: 100% !important;
}
.stDownloadButton button:hover {
    background: #14B8A6 !important;
}

/* Primary button */
.stButton button {
    background: #042F2E !important;
    color: #CCFBF1 !important;
    border: 1px solid #0F766E !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    width: 100% !important;
    font-size: 0.95rem !important;
}
.stButton button:hover {
    background: #0F766E !important;
    color: white !important;
}

/* Footer */
.footer {
    text-align: center;
    padding: 1.5rem;
    color: #94A3B8;
    font-size: 0.75rem;
    border-top: 1px solid #E2E8F0;
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ── STUDENT INFO ─────────────────────────────────────────────────
STUDENT = {
    "name":   "Hugo Silva",
    "id":     "74964557",
    "school": "ITU  |  SPRING 2026",
    "course": "HCM 535 – Data Analytics Application in Healthcare",
}

# ── PALETTE for PPTX ─────────────────────────────────────────────
def rgb(r, g, b): return RGBColor(r, g, b)
DARK    = rgb(0x04, 0x2F, 0x2E)
PRIMARY = rgb(0x0F, 0x76, 0x6E)
MID     = rgb(0x14, 0xB8, 0xA6)
LIGHT   = rgb(0xCC, 0xFB, 0xF1)
ACCENT  = rgb(0xF5, 0x9E, 0x0B)
WHITE   = rgb(0xFF, 0xFF, 0xFF)
OFFWHITE= rgb(0xF8, 0xFA, 0xFC)
GRAY    = rgb(0x64, 0x74, 0x8B)
LTGRAY  = rgb(0xE2, 0xE8, 0xF0)
TEXT    = rgb(0x0F, 0x17, 0x2A)
RED     = rgb(0xDC, 0x26, 0x26)
GREEN   = rgb(0x16, 0xA3, 0x4A)
FT = "Georgia"
FB = "Calibri"
FOOTER_TXT = f"{STUDENT['name']}  ·  ID {STUDENT['id']}  ·  {STUDENT['school']}  ·  {STUDENT['course']}"

# ── PPTX HELPERS ─────────────────────────────────────────────────
def add_rect(s, x, y, w, h, fill, line=None):
    shape = s.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid(); shape.fill.fore_color.rgb = fill
    if line: shape.line.color.rgb = line; shape.line.width = Pt(0.5)
    else: shape.line.fill.background()
    return shape

def add_text(s, text, x, y, w, h, size=12, bold=False,
             italic=False, color=None, align=PP_ALIGN.LEFT,
             font_name="Calibri"):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.word_wrap = True
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    run = p.add_run(); run.text = text
    run.font.size = Pt(size); run.font.bold = bold
    run.font.italic = italic; run.font.name = font_name
    run.font.color.rgb = color if color else TEXT
    return tb

def hdr(s, title, sub=None):
    add_rect(s, 0, 0, 10, 0.62, DARK)
    add_rect(s, 0, 0.62, 10, 0.05, MID)
    add_text(s, title, 0.4, 0.07, 7, 0.52, 18, True, color=WHITE, font_name=FT)
    if sub:
        add_text(s, sub, 6.8, 0.07, 2.9, 0.52, 9, False, True, color=MID,
                 align=PP_ALIGN.RIGHT)

def ftr(s, pg=None):
    add_rect(s, 0, 5.36, 10, 0.265, DARK)
    add_text(s, FOOTER_TXT, 0.3, 5.36, 8.8, 0.265, 7, color=MID,
             align=PP_ALIGN.CENTER)
    if pg:
        add_text(s, str(pg), 9.55, 5.36, 0.35, 0.265, 7, color=LIGHT,
                 align=PP_ALIGN.RIGHT)

# ── CLAUDE SYSTEM PROMPT ─────────────────────────────────────────
SYSTEM = """You are an expert AI research agent specializing in diabetes technology
and automated insulin delivery (AID) systems. You have deep knowledge of:

CLINICAL DATA 2024-2025:
- Medtronic MiniMed 780G: TIR 76-78%, GMI 6.8%, 700K+ users, AHCL algorithm
- Insulet Omnipod 5: real-world TIR 69% (n=69,902 T1D), hypo time 1.12% (lowest),
  FDA expanded to T2D 2024, tubeless design, HbA1c -0.8% T2D trial
- Tandem Control-IQ+: TIR 73.6% (from 63.6% baseline), 94% time in auto mode,
  365K+ users, MPC algorithm, Control-IQ+ launched March 2025
- Beta Bionics iLet: fully autonomous (no carb counting), strong pediatric data
- CamDiab CamAPS FX: FDA cleared 2024, app-based, best pregnancy outcomes

When returning JSON, output ONLY raw valid JSON — no markdown, no code fences."""

# ── AI FUNCTIONS ─────────────────────────────────────────────────
def get_client():
    key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
    if not key:
        st.error("⚠️ No API key found. Add ANTHROPIC_API_KEY to Streamlit Secrets.")
        st.stop()
    return anthropic.Anthropic(api_key=key)

def generate_report(client, report_type, patient_profile, depth, history):
    profile_map = {
        "General": "general patients",
        "Type 1 Diabetes": "Type 1 diabetes patients",
        "Type 2 Diabetes": "Type 2 diabetes patients",
        "Pediatric": "pediatric patients",
        "Elderly": "elderly (65+) patients",
    }
    depth_map = {
        "Executive Summary": "Be concise — 2-3 paragraphs per section.",
        "Detailed Analysis": "Be thorough and specific with data points.",
        "Clinical Deep-Dive": "Be highly technical — include trial names, n-values, statistics.",
    }
    p = profile_map.get(patient_profile, "general patients")
    d = depth_map.get(depth, depth_map["Detailed Analysis"])

    type_prompts = {
        "Full Intelligence Report": f"""Generate a comprehensive intelligence report on AI smart insulin pumps for {p}. {d}

Sections:
1. Executive Summary (3 key findings)
2. How AI Works (closed-loop, CGM, MPC/RL algorithms, decision cycle)
3. Clinical Effectiveness (TIR, HbA1c, hypoglycemia, key trials)
4. Vendor Analysis (Medtronic 780G, Omnipod 5, Control-IQ+, iLet, CamAPS FX)
5. Recommendation (top pick + runner-up with rationale)
6. Risks & Limitations
7. Future Outlook 2025-2030""",

        "AI Effectiveness Only": f"Analyze clinical effectiveness of AI insulin pumps for {p}. {d} Cover: mechanism, TIR data, HbA1c, hypoglycemia reduction, key trials, vs traditional pumps, limitations.",

        "Vendor Comparison": f"Compare all major AI insulin pump vendors for {p}. {d} Cover: Medtronic 780G, Omnipod 5, Tandem Control-IQ+, iLet, CamAPS FX. Include TIR, hypoglycemia, algorithm, CGM compatibility, price, pros/cons.",

        "Recommendation Only": f"Give a direct recommendation for {p}. {d} Include: #1 pick with full rationale, runner-up, recommendations by patient profile, cost considerations.",
    }

    prompt = type_prompts.get(report_type, type_prompts["Full Intelligence Report"])
    messages = history + [{"role": "user", "content": prompt}]

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3500,
        system=SYSTEM,
        messages=messages,
    )
    return response.content[0].text

def extract_slide_data(client, report_text, history):
    messages = history + [
        {"role": "user", "content": """Return ONLY raw JSON (no markdown, no fences):
{
  "title": "AI Smart Insulin Pumps: Intelligence Report",
  "subtitle": "Clinical Effectiveness, Vendor Analysis & Recommendation",
  "executive_summary": ["finding 1","finding 2","finding 3"],
  "key_metrics": [
    {"label":"Best Real-World TIR","value":"78%","source":"MiniMed 780G, US users"},
    {"label":"Lowest Hypoglycemia","value":"1.12%","source":"Omnipod 5 median"},
    {"label":"Largest Study","value":"69,902","source":"Omnipod 5 T1D 2024"},
    {"label":"Time in Auto Mode","value":"94%","source":"Control-IQ 12-month"},
    {"label":"HbA1c Reduction","value":"-0.8%","source":"Omnipod 5 T2D trial"},
    {"label":"TIR Gain T2D","value":"+20%","source":"~5 extra hrs/day"}
  ],
  "how_it_works": [
    {"step":"1","title":"CGM Reads Glucose","desc":"Sensor checks every 5 min"},
    {"step":"2","title":"AI Predicts Trend","desc":"Forecasts 30-60 min ahead"},
    {"step":"3","title":"Calculates Dose","desc":"MPC/RL algorithm decides amount"},
    {"step":"4","title":"Pump Delivers","desc":"Micro-bolus adjusted automatically"}
  ],
  "vendors": [
    {"name":"Medtronic","product":"MiniMed 780G","tir":"78","hypo":"2.5","algorithm":"AHCL + SmartGuard","cgm":"Guardian 4","strength":"Highest TIR","weakness":"Tubed only","fda":"Cleared","price":"~$800/mo"},
    {"name":"Insulet","product":"Omnipod 5","tir":"69","hypo":"1.12","algorithm":"Adaptive TDI","cgm":"Dexcom G6/G7","strength":"Tubeless, lowest hypo","weakness":"Lower TIR","fda":"T1D+T2D","price":"~$350/mo"},
    {"name":"Tandem","product":"Control-IQ+","tir":"74","hypo":"1.46","algorithm":"MPC (UVA)","cgm":"Dexcom G6/G7","strength":"Best algorithm transparency","weakness":"Needs carb counting","fda":"Cleared","price":"~$400/mo"},
    {"name":"Beta Bionics","product":"iLet","tir":"70","hypo":"1.8","algorithm":"Fully autonomous","cgm":"Dexcom G6","strength":"Zero setup","weakness":"Fewer integrations","fda":"Cleared","price":"~$400/mo"},
    {"name":"CamDiab","product":"CamAPS FX","tir":"70","hypo":"2.3","algorithm":"Cambridge MPC","cgm":"Dexcom G6/Libre 3","strength":"Best pregnancy data","weakness":"Limited US availability","fda":"Cleared 2024","price":"~$100/mo app"}
  ],
  "recommendation": {
    "top_pick": "Insulet Omnipod 5",
    "top_rationale": "Best combination of lowest hypoglycemia (1.12%), tubeless design, T1D+T2D clearance, and largest real-world validation (69,902 patients).",
    "runner_up": "Medtronic MiniMed 780G",
    "runner_rationale": "Highest TIR at 78% for patients prioritizing glucose control.",
    "by_profile": [
      {"profile":"Type 1 — Tech Savvy","pick":"Tandem Control-IQ+"},
      {"profile":"Type 1 — Active","pick":"Omnipod 5"},
      {"profile":"Type 2","pick":"Omnipod 5"},
      {"profile":"Pediatric","pick":"iLet or CamAPS FX"},
      {"profile":"Max TIR","pick":"MiniMed 780G"}
    ]
  },
  "risks": [
    {"title":"Sensor Dependency","desc":"AI accuracy tied entirely to CGM sensor quality"},
    {"title":"Algorithm Failures","desc":"Edge cases: exercise, illness, stress"},
    {"title":"Cybersecurity","desc":"Wireless connectivity creates attack surface"},
    {"title":"Cost & Access","desc":"$350-800/month; insurance coverage varies"}
  ],
  "future_trends": [
    "Fully closed-loop mainstream by 2027 — no meal announcements needed",
    "Bihormonal systems (insulin + glucagon) led by Beta Bionics",
    "Integration with AI health platforms like Claude for Healthcare",
    "Food image recognition for predictive meal bolusing",
    "Non-invasive CGM replacing needle-based sensors by 2029-2030"
  ]
}"""}
    ]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2500,
        system=SYSTEM,
        messages=messages,
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw.strip())

# ── PPTX BUILDER ─────────────────────────────────────────────────
def build_pptx(d):
    prs = Presentation()
    prs.slide_width  = Inches(10)
    prs.slide_height = Inches(5.625)
    blank = prs.slide_layouts[6]

    # ── Slide 1: Title ──────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, DARK)
    add_rect(s, 0, 0, 0.22, 5.625, ACCENT)
    add_rect(s, 0.22, 1.3, 9.78, 2.55, PRIMARY)
    add_text(s, "AI RESEARCH AGENT  ·  DIABETES TECHNOLOGY",
             0.5, 0.82, 9, 0.32, 9, color=MID)
    add_text(s, d["title"], 0.5, 1.42, 9.1, 1.15,
             34, True, color=WHITE, font_name=FT)
    add_text(s, d["subtitle"], 0.5, 2.65, 9.1, 0.5,
             14, False, True, color=LIGHT)
    add_rect(s, 0.5, 3.35, 5.6, 1.65, PRIMARY)
    info = [f"Student:     {STUDENT['name']}",
            f"Student ID:  {STUDENT['id']}",
            f"Institution: {STUDENT['school']}",
            f"Course:      {STUDENT['course']}"]
    for i, line in enumerate(info):
        add_text(s, line, 0.7, 3.45+i*0.37, 5.2, 0.35, 10.5, color=WHITE)
    add_rect(s, 6.5, 3.55, 2.8, 0.42, ACCENT)
    add_text(s, "Spring 2026", 6.5, 3.55, 2.8, 0.42,
             14, True, color=DARK, align=PP_ALIGN.CENTER, font_name=FT)

    # ── Slide 2: Executive Summary ──────────────────────────────
    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, OFFWHITE)
    hdr(s, "Executive Summary", "AI Smart Insulin Pumps – 2025 Evidence")
    add_rect(s, 0.3, 0.82, 4.5, 3.85, WHITE)
    add_text(s, "3 Key Findings", 0.5, 0.95, 4.1, 0.38,
             13, True, color=PRIMARY, font_name=FT)
    fcolors = [ACCENT, MID, PRIMARY]
    for i, txt in enumerate(d.get("executive_summary", [])[:3]):
        y = 1.42 + i * 1.0
        add_rect(s, 0.5, y, 0.36, 0.36, fcolors[i])
        add_text(s, str(i+1), 0.5, y, 0.36, 0.36,
                 13, True, color=DARK, align=PP_ALIGN.CENTER, font_name=FT)
        add_text(s, txt, 1.0, y, 3.6, 0.75, 11, color=TEXT)
    add_rect(s, 5.1, 0.82, 4.55, 1.7, DARK)
    add_text(s, "Market Context", 5.3, 0.9, 4.1, 0.32,
             11, True, color=MID, font_name=FT)
    add_text(s, "AI insulin pump market projected to exceed $187.95B by 2030 (37% CAGR). "
                "ADA 2025 guidelines recommend AID as first-line therapy for T1D.",
             5.3, 1.26, 4.1, 1.18, 10, color=LIGHT)
    add_rect(s, 5.1, 2.7, 4.55, 2.0, WHITE)
    add_text(s, "AI vs Traditional Pumps", 5.3, 2.78, 4.0, 0.35,
             11, True, color=PRIMARY, font_name=FT)
    comps = [("Time in Range","+10–20%"),("HbA1c","−0.5–1.0%"),
             ("Hypoglycemia","−30–50%"),("Manual interventions","−70%")]
    for i, (lbl, val) in enumerate(comps):
        y = 3.2 + i*0.35
        add_text(s, lbl, 5.3, y, 2.0, 0.3, 10, color=GRAY)
        add_text(s, val, 7.2, y, 1.6, 0.3, 11, True, color=PRIMARY,
                 align=PP_ALIGN.RIGHT)
    ftr(s, 2)

    # ── Slide 3: Key Metrics ────────────────────────────────────
    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, OFFWHITE)
    hdr(s, "Key Clinical Metrics", "Real-world evidence 2024–2025")
    cw, ch, gx, gy = 3.0, 1.55, 0.12, 0.12
    sx, sy = 0.25, 0.92
    for i, m in enumerate(d.get("key_metrics", [])[:6]):
        col, row = i % 3, i // 3
        x = sx + col*(cw+gx); y = sy + row*(ch+gy)
        add_rect(s, x, y, cw, ch, WHITE)
        add_rect(s, x, y, cw, 0.05, MID)
        add_text(s, m["value"], x+0.15, y+0.1, cw-0.3, 0.75,
                 34, True, color=PRIMARY, font_name=FT)
        add_text(s, m["label"], x+0.15, y+0.87, cw-0.3, 0.32,
                 11, True, color=TEXT)
        add_text(s, m["source"], x+0.15, y+1.22, cw-0.3, 0.26,
                 8, False, True, color=GRAY)
    ftr(s, 3)

    # ── Slide 4: How AI Works ────────────────────────────────────
    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, DARK)
    hdr(s, "How AI-Powered Insulin Delivery Works", "Closed-Loop Architecture")
    bw, bh = 2.1, 2.55; sx2, sy2, gap = 0.28, 1.0, 0.19
    for i, st_ in enumerate(d.get("how_it_works", [])[:4]):
        x = sx2 + i*(bw+gap)
        add_rect(s, x, sy2, bw, bh, PRIMARY)
        add_rect(s, x, sy2, bw, 0.05, MID)
        add_rect(s, x+0.81, sy2+0.18, 0.46, 0.46, ACCENT)
        add_text(s, st_["step"], x+0.81, sy2+0.18, 0.46, 0.46,
                 15, True, color=DARK, align=PP_ALIGN.CENTER, font_name=FT)
        add_text(s, st_["title"], x+0.1, sy2+0.8, bw-0.2, 0.55,
                 12, True, color=WHITE, align=PP_ALIGN.CENTER, font_name=FT)
        add_text(s, st_["desc"], x+0.1, sy2+1.45, bw-0.2, 0.95,
                 10, color=LIGHT, align=PP_ALIGN.CENTER)
        if i < 3:
            add_text(s, "→", x+bw+0.02, sy2+1.0, gap, 0.5,
                     20, color=ACCENT, align=PP_ALIGN.CENTER)
    add_text(s, "Every 5 min  ·  30–60 min prediction horizon  ·  MPC / Reinforcement Learning",
             0.5, 5.08, 9, 0.24, 8, False, True,
             color=MID, align=PP_ALIGN.CENTER)
    ftr(s, 4)

    # ── Slide 5: TIR Comparison ─────────────────────────────────
    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, OFFWHITE)
    hdr(s, "Time in Range Comparison", "Real-world data per system (%)")
    bcolors = [PRIMARY, MID, rgb(0x08,0x91,0xB2),
               rgb(0x8B,0x5C,0xF6), rgb(0x06,0xB6,0xD4)]
    for i, v in enumerate(d.get("vendors", [])[:5]):
        y = 0.9 + i*0.82
        tir = float(v["tir"])
        bw2 = (tir / 82) * 5.5
        add_text(s, v["product"], 0.3, y, 2.0, 0.36, 11, True, color=TEXT)
        add_text(s, v["name"], 0.3, y+0.36, 2.0, 0.25, 8, False, True, color=GRAY)
        add_rect(s, 2.4, y+0.08, 5.5, 0.42, LTGRAY)
        add_rect(s, 2.4, y+0.08, bw2, 0.42, bcolors[i])
        add_text(s, f"{tir}%", 8.05, y+0.08, 0.7, 0.42,
                 12, True, color=bcolors[i])
        hypo = float(v["hypo"])
        hc = GREEN if hypo <= 1.5 else (PRIMARY if hypo <= 2.5 else RED)
        add_text(s, f"Hypo: {v['hypo']}%", 8.8, y+0.1, 1.1, 0.35, 9, True, color=hc)
    ftr(s, 5)

    # ── Slide 6: Vendor Table ────────────────────────────────────
    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, OFFWHITE)
    hdr(s, "Vendor Comparison", "All major AI insulin pump systems")
    headers = ["Vendor","Product","Algorithm","CGM","TIR","FDA","Price/mo"]
    col_w   = [1.15,1.35,2.1,1.4,0.65,1.05,0.95]
    col_x2  = [0.3]
    for w in col_w[:-1]: col_x2.append(col_x2[-1]+w)
    rh = 0.44; start_y = 0.82
    for j,(h2,cx,cw2) in enumerate(zip(headers,col_x2,col_w)):
        add_rect(s, cx, start_y, cw2, rh, DARK)
        add_text(s, h2, cx+0.05, start_y+0.06, cw2-0.1, rh-0.1,
                 9, True, color=WHITE, align=PP_ALIGN.CENTER)
    row_bg = [WHITE, OFFWHITE]
    for i,v in enumerate(d.get("vendors",[])[:5]):
        y = start_y + (i+1)*rh
        vals  = [v["name"],v["product"],v["algorithm"],
                 v["cgm"],v["tir"]+"%",v["fda"],v["price"]]
        bolds = [True,True,False,False,True,False,False]
        clrs  = [TEXT,PRIMARY,GRAY,GRAY,PRIMARY,GREEN,TEXT]
        for j,(val,cx,cw2) in enumerate(zip(vals,col_x2,col_w)):
            add_rect(s, cx, y, cw2, rh, row_bg[i%2])
            add_text(s, val, cx+0.05, y+0.06, cw2-0.1, rh-0.08,
                     9, bolds[j], color=clrs[j])
    ftr(s, 6)

    # ── Slide 7: Recommendation ─────────────────────────────────
    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, OFFWHITE)
    hdr(s, "Recommendation", "Evidence-based selection guide")
    rec = d.get("recommendation", {})
    add_rect(s, 0.3, 0.82, 5.9, 2.25, DARK)
    add_rect(s, 0.3, 0.82, 0.18, 2.25, ACCENT)
    add_rect(s, 0.3, 0.82, 2.0, 0.32, ACCENT)
    add_text(s, "#1 TOP PICK", 0.32, 0.82, 1.95, 0.32,
             9, True, color=DARK, align=PP_ALIGN.CENTER)
    add_text(s, rec.get("top_pick",""), 0.6, 1.18, 5.4, 0.55,
             20, True, color=WHITE, font_name=FT)
    add_text(s, rec.get("top_rationale",""), 0.6, 1.76, 5.3, 1.2, 10, color=LIGHT)
    add_rect(s, 0.3, 3.22, 5.9, 1.72, WHITE)
    add_rect(s, 0.3, 3.22, 0.18, 1.72, PRIMARY)
    add_text(s, "RUNNER-UP", 0.6, 3.28, 2.0, 0.28, 9, True, color=PRIMARY)
    add_text(s, rec.get("runner_up",""), 0.6, 3.58, 5.3, 0.42,
             15, True, color=TEXT, font_name=FT)
    add_text(s, rec.get("runner_rationale",""), 0.6, 4.02, 5.3, 0.85, 10, color=GRAY)
    add_rect(s, 6.45, 0.82, 3.25, 4.12, WHITE)
    add_text(s, "By Patient Profile", 6.6, 0.9, 2.9, 0.34,
             12, True, color=PRIMARY, font_name=FT)
    pbg = [LIGHT, OFFWHITE, LIGHT, OFFWHITE, LIGHT]
    for i,p in enumerate(rec.get("by_profile",[])[:5]):
        y = 1.36 + i*0.66
        add_rect(s, 6.55, y, 3.0, 0.58, pbg[i%2])
        add_text(s, p.get("profile",""), 6.68, y+0.05, 2.8, 0.22,
                 8, False, True, color=GRAY)
        add_text(s, p.get("pick",""), 6.68, y+0.28, 2.8, 0.26,
                 11, True, color=PRIMARY, font_name=FT)
    ftr(s, 7)

    # ── Slide 8: Risks ──────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, OFFWHITE)
    hdr(s, "Risks & Limitations", "Critical considerations before adoption")
    rcolors = [RED, rgb(0x85,0x4D,0x0E), rgb(0x7C,0x3A,0xED), PRIMARY]
    for i,r in enumerate(d.get("risks",[])[:4]):
        col,row = i%2, i//2
        x = 0.3+col*4.9; y = 0.92+row*2.12
        add_rect(s, x, y, 4.55, 1.97, WHITE)
        add_rect(s, x, y, 4.55, 0.05, rcolors[i])
        add_rect(s, x, y, 0.18, 1.97, rcolors[i])
        add_text(s, r["title"], x+0.28, y+0.12, 4.1, 0.38,
                 13, True, color=TEXT, font_name=FT)
        add_text(s, r["desc"], x+0.28, y+0.55, 4.1, 1.28, 11, color=GRAY)
    ftr(s, 8)

    # ── Slide 9: Future Outlook ─────────────────────────────────
    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, DARK)
    hdr(s, "Future Outlook 2025–2030", "Next generation AI insulin delivery")
    years = ["2026","2027","2027","2028","2029–30"]
    bw3, bh3 = 1.72, 3.05; sx3, sy3, gap3 = 0.22, 1.0, 0.1
    for i,t in enumerate(d.get("future_trends",[])[:5]):
        x = sx3+i*(bw3+gap3)
        add_rect(s, x, sy3, bw3, bh3, PRIMARY)
        add_rect(s, x, sy3, bw3, 0.05, ACCENT)
        add_rect(s, x+0.1, sy3+0.12, 1.5, 0.3, ACCENT)
        add_text(s, years[i], x+0.1, sy3+0.12, 1.5, 0.3,
                 10, True, color=DARK, align=PP_ALIGN.CENTER)
        add_text(s, t, x+0.1, sy3+0.55, bw3-0.2, 2.35, 10, color=WHITE)
    ftr(s, 9)

    # ── Slide 10: Closing ────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, DARK)
    add_rect(s, 0, 0, 0.22, 5.625, ACCENT)
    add_text(s, "Thank You", 0.5, 0.55, 9, 0.9,
             40, True, color=WHITE, font_name=FT)
    add_text(s, "AI Smart Insulin Pumps: Clinical Evidence & Strategic Recommendation",
             0.5, 1.52, 9, 0.45, 14, False, True, color=LIGHT)
    add_rect(s, 0.5, 2.15, 5.5, 1.6, PRIMARY)
    rows = [("Student", STUDENT["name"]),
            ("Student ID", STUDENT["id"]),
            ("Institution", STUDENT["school"]),
            ("Course", STUDENT["course"])]
    for i,(lbl,val) in enumerate(rows):
        add_text(s, lbl+":", 0.7, 2.27+i*0.35, 1.4, 0.3, 10, True, color=MID)
        add_text(s, val, 2.15, 2.27+i*0.35, 3.7, 0.3, 10, color=WHITE)
    add_rect(s, 0.5, 3.92, 9.0, 1.4, PRIMARY)
    add_text(s, "Key References", 0.7, 3.98, 3.0, 0.28, 10, True, color=MID, font_name=FT)
    refs = ("Forlenza et al. (2024). Real-World Evidence of Omnipod 5 in 69,902 T1D Patients. Diabetes Technology & Therapeutics.\n"
            "SMART-MD Journal of Precision Medicine (2025). AID Systems Update, Vol.2 No.2.\n"
            "Mohanadas et al. (2026). AI in Medical Devices. JMIR, 28:e72410.\n"
            "Diabetotech (2025). AID Systems Update Winter 2025.")
    add_text(s, refs, 0.7, 4.28, 8.6, 1.0, 8, color=LIGHT)

    buf = BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# ── INIT SESSION STATE ───────────────────────────────────────────
if "history"      not in st.session_state: st.session_state.history      = []
if "report_text"  not in st.session_state: st.session_state.report_text  = ""
if "slide_data"   not in st.session_state: st.session_state.slide_data   = None
if "pptx_ready"   not in st.session_state: st.session_state.pptx_ready   = False
if "pptx_buffer"  not in st.session_state: st.session_state.pptx_buffer  = None
if "authenticated" not in st.session_state: st.session_state.authenticated = False

# ── ACCESS GATE ──────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.markdown("""
    <div class="main-header">
        <h1>🩺 AI Insulin Pump Agent</h1>
        <p>Clinical Intelligence & PowerPoint Generator</p>
        <div class="student-badge">Hugo Silva  ·  ID 74964557  ·  ITU SPRING 2026  ·  HCM 535</div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### Enter Access Code")
        code = st.text_input("Access code", type="password",
                             placeholder="Enter code to continue...")
        if st.button("Unlock Agent"):
            if code == "HCM535":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect code. Try again.")
    st.stop()

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Report Settings")

    report_type = st.selectbox(
        "Report type",
        ["Full Intelligence Report", "AI Effectiveness Only",
         "Vendor Comparison", "Recommendation Only"]
    )
    patient_profile = st.selectbox(
        "Patient profile",
        ["General", "Type 1 Diabetes", "Type 2 Diabetes", "Pediatric", "Elderly"]
    )
    depth = st.selectbox(
        "Report depth",
        ["Executive Summary", "Detailed Analysis", "Clinical Deep-Dive"]
    )

    st.markdown("---")
    st.markdown("### 💬 Follow-up Question")
    followup = st.text_area("Ask the agent anything",
                            placeholder="e.g. Which system is best for a child?",
                            height=100)
    ask_btn = st.button("Ask Agent ↗")

    st.markdown("---")
    st.markdown("""
    <div class="sidebar-section">
    <strong>About this agent</strong><br><br>
    Powered by Claude (Anthropic)<br>
    Clinical data: 2024–2025<br>
    Sources: JMIR 2026, Diabetotech,
    FDA Device Database<br><br>
    <em>Not a substitute for medical advice</em>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Reset Session"):
        for k in ["history","report_text","slide_data","pptx_ready","pptx_buffer"]:
            st.session_state[k] = [] if k=="history" else None if "data" in k or "buffer" in k else "" if "text" in k else False
        st.rerun()

# ── MAIN LAYOUT ───────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🩺 AI Smart Insulin Pump Agent</h1>
    <p>Clinical Intelligence · Vendor Analysis · PowerPoint Generator</p>
    <div class="student-badge">
        Hugo Silva  ·  ID 74964557  ·  ITU SPRING 2026  ·  HCM 535 – Data Analytics in Healthcare
    </div>
</div>
""", unsafe_allow_html=True)

# ── METRICS ROW ───────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<div class="metric-card"><h3>78%</h3><p>Best real-world TIR (MiniMed 780G)</p></div>',
                unsafe_allow_html=True)
with c2:
    st.markdown('<div class="metric-card"><h3>1.12%</h3><p>Lowest hypoglycemia (Omnipod 5)</p></div>',
                unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric-card"><h3>69,902</h3><p>Patients in largest real-world study</p></div>',
                unsafe_allow_html=True)
with c4:
    st.markdown('<div class="metric-card"><h3>5</h3><p>AI systems compared</p></div>',
                unsafe_allow_html=True)

st.markdown('<hr class="teal-divider">', unsafe_allow_html=True)

# ── GENERATE BUTTON ───────────────────────────────────────────────
col_btn, col_status = st.columns([2, 3])
with col_btn:
    generate_btn = st.button("▶  Generate Report + PPT", use_container_width=True)
with col_status:
    if st.session_state.report_text:
        st.markdown('<span class="badge-success">✓ Report ready</span>',
                    unsafe_allow_html=True)
    elif generate_btn:
        st.markdown('<span class="badge-running">● Running...</span>',
                    unsafe_allow_html=True)

# ── GENERATE PIPELINE ─────────────────────────────────────────────
if generate_btn:
    client = get_client()

    progress = st.progress(0)
    status   = st.empty()

    try:
        status.markdown("**Step 1/3** — Generating research report with Claude...")
        progress.progress(10)
        report = generate_report(
            client, report_type, patient_profile, depth,
            st.session_state.history
        )
        st.session_state.report_text = report
        st.session_state.history.append({"role": "user",
            "content": f"Generate report: {report_type}, {patient_profile}, {depth}"})
        st.session_state.history.append({"role": "assistant", "content": report})
        progress.progress(45)

        status.markdown("**Step 2/3** — Extracting structured data for slides...")
        slide_data = extract_slide_data(client, report,
                                        st.session_state.history)
        st.session_state.slide_data = slide_data
        st.session_state.history.append({"role": "assistant",
            "content": json.dumps(slide_data)})
        progress.progress(75)

        status.markdown("**Step 3/3** — Building PowerPoint presentation...")
        buf = build_pptx(slide_data)
        st.session_state.pptx_buffer = buf
        st.session_state.pptx_ready  = True
        progress.progress(100)
        status.markdown("✅ **Done!** Report and PPT ready.")

    except Exception as e:
        st.error(f"Error: {e}")
        progress.empty()
        status.empty()

# ── FOLLOW-UP ─────────────────────────────────────────────────────
if ask_btn and followup.strip():
    if not st.session_state.history:
        st.warning("Generate a report first before asking follow-up questions.")
    else:
        client = get_client()
        with st.spinner("Thinking..."):
            try:
                messages = st.session_state.history + \
                           [{"role": "user", "content": followup}]
                response = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=1500,
                    system=SYSTEM,
                    messages=messages,
                )
                answer = response.content[0].text
                st.session_state.history.append({"role": "user",    "content": followup})
                st.session_state.history.append({"role": "assistant","content": answer})
                st.session_state.report_text += f"\n\n---\n\n**Q: {followup}**\n\n{answer}"
            except Exception as e:
                st.error(f"Follow-up error: {e}")

# ── RESULTS ───────────────────────────────────────────────────────
if st.session_state.report_text:
    tab1, tab2 = st.tabs(["📄 Research Report", "📊 Slide Data Preview"])

    with tab1:
        st.markdown(f"""
        <div class="report-box">{st.session_state.report_text}</div>
        """, unsafe_allow_html=True)

    with tab2:
        if st.session_state.slide_data:
            st.json(st.session_state.slide_data)
        else:
            st.info("Slide data will appear here after generation.")

    st.markdown('<hr class="teal-divider">', unsafe_allow_html=True)

    # Download buttons
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label="⬇️  Download Report (.txt)",
            data=st.session_state.report_text.encode(),
            file_name=f"insulin_pump_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with dl2:
        if st.session_state.pptx_ready and st.session_state.pptx_buffer:
            st.download_button(
                label="⬇️  Download Presentation (.pptx)",
                data=st.session_state.pptx_buffer,
                file_name=f"insulin_pump_agent_{datetime.now().strftime('%Y%m%d_%H%M')}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )
        else:
            st.info("PPT will be ready after generation.")

# ── FOOTER ────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
    Hugo Silva  ·  ID 74964557  ·  ITU | SPRING 2026  ·  HCM 535 – Data Analytics Application in Healthcare<br>
    Powered by Claude (Anthropic)  ·  Not a substitute for medical advice
</div>
""", unsafe_allow_html=True)
