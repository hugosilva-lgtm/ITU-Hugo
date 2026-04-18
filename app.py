import json
import os
import re
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

import streamlit as st
from anthropic import Anthropic
from anthropic._exceptions import APIError, AuthenticationError, RateLimitError
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt


# ================================================================
# DIABETES AI AGENT — Fixed Version
# Improvements:
# - Safer config handling
# - No hardcoded access code fallback requirement in production
# - More robust JSON extraction and repair
# - Better error messages for Anthropic failures
# - Cleaner session reset logic
# - Safer rendering of LLM text
# ================================================================


# ── PAGE CONFIG ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Diabetes AI Agent | Hugo Silva",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CONFIG HELPERS ──────────────────────────────────────────────
def get_secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, os.environ.get(name, default)))
    except Exception:
        return os.environ.get(name, default)


def get_access_code() -> str:
    return get_secret("APP_ACCESS_CODE", "")


def get_anthropic_api_key() -> str:
    return get_secret("ANTHROPIC_API_KEY", "")


def safe_rerun() -> None:
    try:
        st.rerun()
    except Exception:
        pass


# ── CUSTOM CSS ──────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Serif+Display:ital@0;1&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

.main-header {
    background: #1C1C1E;
    padding: 2rem 2.5rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    border-left: 6px solid #990011;
    border-bottom: 1px solid #3C3C3E;
}
.main-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    color: #FCF6F5;
    margin: 0 0 0.3rem 0;
}
.main-header p { color: #B0B0B0; font-size: 0.9rem; margin: 0; }
.student-badge {
    background: rgba(153,0,17,0.18);
    border: 1px solid #990011;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    color: #FF6B6B;
    font-size: 0.8rem;
    margin-top: 0.8rem;
    display: inline-block;
}

.module-card {
    background: #FFF5F5;
    border: 0.5px solid #FECDD3;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.6rem;
    border-left: 4px solid #990011;
}
.module-card h4 { margin: 0 0 4px 0; font-size: 0.9rem; color: #7F1D1D !important; }
.module-card p  { margin: 0; font-size: 0.78rem; color: #9F1239 !important; }

.metric-card {
    background: #FFFFFF;
    border: 0.5px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.2rem;
    border-top: 3px solid #990011;
    margin-bottom: 0.8rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.metric-card h3 {
    font-size: 2rem;
    font-weight: 800;
    color: #990011;
    margin: 0;
    font-family: 'DM Serif Display', serif;
}
.metric-card p { font-size: 0.75rem; color: #6B7280; margin: 0.2rem 0 0 0; }

.stDownloadButton button {
    background: #990011 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    padding: 0.6rem 1.5rem !important;
    font-size: 0.9rem !important;
    width: 100% !important;
}
.stDownloadButton button:hover { background: #B30014 !important; }

.stButton button {
    background: #1C1C1E !important;
    color: #FCF6F5 !important;
    border: 1px solid #990011 !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    width: 100% !important;
    font-size: 0.95rem !important;
}
.stButton button:hover { background: #990011 !important; color: white !important; }

.teal-divider {
    border: none;
    border-top: 2px solid #990011;
    margin: 1rem 0;
    opacity: 0.3;
}

section[data-testid="stSidebar"] { background: #1C1C1E !important; }
section[data-testid="stSidebar"] > * { color: #FCF6F5 !important; }
section[data-testid="stSidebar"] label { color: #B0B0B0 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextArea label {
    color: #B0B0B0 !important;
    font-size: 0.82rem !important;
}
section[data-testid="stSidebar"] h3 { color: #FF6B6B !important; font-size: 0.95rem !important; }
section[data-testid="stSidebar"] hr { border-color: #3C3C3E !important; }
section[data-testid="stSidebar"] .stButton button {
    background: #2C2C2E !important;
    border-color: #990011 !important;
    color: #FCF6F5 !important;
}
section[data-testid="stSidebar"] .stButton button:hover { background: #990011 !important; }

.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #990011; }
.stTabs [data-baseweb="tab"] {
    background: #F9FAFB;
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
    font-weight: 600;
    color: #374151;
    border: 0.5px solid #E5E7EB;
}
.stTabs [aria-selected="true"] {
    background: #990011 !important;
    color: white !important;
    border-color: #990011 !important;
}

.stProgress > div > div > div > div { background: #990011 !important; }

.badge-success {
    background: #FFF5F5; color: #7F1D1D;
    border: 1px solid #FECDD3;
    border-radius: 20px; padding: 3px 12px;
    font-size: 0.75rem; font-weight: 600;
}
.badge-running {
    background: #1C1C1E; color: #FF6B6B;
    border-radius: 20px; padding: 3px 12px;
    font-size: 0.75rem; font-weight: 600;
}

.footer {
    text-align: center; padding: 1.5rem;
    color: #9CA3AF; font-size: 0.75rem;
    border-top: 1px solid #E5E7EB; margin-top: 2rem;
    background: #FAFAFA; border-radius: 0 0 12px 12px;
}

.stTextInput input { border-radius: 8px !important; border: 1px solid #E5E7EB !important; }
.stTextInput input:focus { border-color: #990011 !important; box-shadow: 0 0 0 1px #990011 !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ── STUDENT INFO ────────────────────────────────────────────────
STUDENT = {
    "name": "Hugo Silva",
    "id": "74964557",
    "school": "ITU  |  SPRING 2026",
    "course": "HCM 535 – Data Analytics Application in Healthcare",
}
FOOTER_TXT = f"{STUDENT['name']}  ·  ID {STUDENT['id']}  ·  {STUDENT['school']}  ·  {STUDENT['course']}"


# ── MODULE DEFINITIONS ──────────────────────────────────────────
MODULES: Dict[str, Dict[str, str]] = {
    "🩺 Full Diabetes AI Platform": {
        "icon": "🩺",
        "color": "#990011",
        "desc": "Complete overview of all AI applications in diabetes care",
        "tag": "Comprehensive",
    },
    "💉 AI Insulin Delivery (Smart Pumps)": {
        "icon": "💉",
        "color": "#B30014",
        "desc": "Closed-loop AID systems, CGM integration, vendor comparison",
        "tag": "Clinical",
    },
    "🩸 AI Glucose Monitoring (CGM)": {
        "icon": "🩸",
        "color": "#DC2626",
        "desc": "Continuous glucose monitors, accuracy, non-invasive sensing",
        "tag": "Devices",
    },
    "🧠 AI Diagnostics & Early Detection": {
        "icon": "🧠",
        "color": "#7F1D1D",
        "desc": "T2D prediction, retinopathy screening, complication risk AI",
        "tag": "Diagnostics",
    },
    "💊 AI Drug Management (GLP-1 & Meds)": {
        "icon": "💊",
        "color": "#9F1239",
        "desc": "GLP-1 drugs, smart pens, adherence AI, dosing algorithms",
        "tag": "Pharmacology",
    },
    "🥗 AI Nutrition & Lifestyle Coaching": {
        "icon": "🥗",
        "color": "#BE123C",
        "desc": "Meal planning AI, carb counting, activity coaching, apps",
        "tag": "Lifestyle",
    },
    "📊 Population Health & Analytics": {
        "icon": "📊",
        "color": "#881337",
        "desc": "Predictive risk models, payer analytics, clinical trial AI",
        "tag": "Analytics",
    },
    "⚖️ Vendor Comparison Only": {
        "icon": "⚖️",
        "color": "#4B5563",
        "desc": "Side-by-side comparison of all major diabetes AI vendors",
        "tag": "Comparison",
    },
    "🎯 Recommendation Only": {
        "icon": "🎯",
        "color": "#374151",
        "desc": "Direct evidence-based recommendation by patient profile",
        "tag": "Decision",
    },
}


# ── PPTX PALETTE ────────────────────────────────────────────────
def rgb(r: int, g: int, b: int) -> RGBColor:
    return RGBColor(r, g, b)


DARK = rgb(0x1C, 0x1C, 0x1E)
CHARCOAL = rgb(0x2C, 0x2C, 0x2E)
CRIMSON = rgb(0x99, 0x00, 0x11)
CRIMSON2 = rgb(0xB3, 0x00, 0x14)
LIGHT = rgb(0xFC, 0xF6, 0xF5)
PINK = rgb(0xFF, 0x6B, 0x6B)
WHITE = rgb(0xFF, 0xFF, 0xFF)
OFFWHITE = rgb(0xFA, 0xFA, 0xFA)
GRAY = rgb(0x6B, 0x72, 0x80)
LTGRAY = rgb(0xE5, 0xE7, 0xEB)
TEXT = rgb(0x11, 0x18, 0x27)
FT = "Georgia"


# ── PPTX HELPERS ────────────────────────────────────────────────
def add_rect(slide, x, y, w, h, fill, line=None):
    shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line:
        shape.line.color.rgb = line
        shape.line.width = Pt(0.5)
    else:
        shape.line.fill.background()
    return shape


def add_text(slide, text, x, y, w, h, size=12, bold=False,
             italic=False, color=None, align=PP_ALIGN.LEFT, font_name="Calibri"):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.word_wrap = True
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = str(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font_name
    run.font.color.rgb = color if color else TEXT
    return tb


def hdr(slide, title: str, sub: Optional[str] = None) -> None:
    add_rect(slide, 0, 0, 10, 0.62, DARK)
    add_rect(slide, 0, 0.62, 10, 0.05, CRIMSON)
    add_text(slide, title, 0.4, 0.07, 7, 0.52, 18, True, color=LIGHT, font_name=FT)
    if sub:
        add_text(
            slide,
            sub,
            6.8,
            0.07,
            2.9,
            0.52,
            9,
            False,
            True,
            color=PINK,
            align=PP_ALIGN.RIGHT,
        )


def ftr(slide, pg: Optional[int] = None) -> None:
    add_rect(slide, 0, 5.36, 10, 0.265, DARK)
    add_text(slide, FOOTER_TXT, 0.3, 5.36, 8.8, 0.265, 7, color=PINK, align=PP_ALIGN.CENTER)
    if pg is not None:
        add_text(slide, str(pg), 9.55, 5.36, 0.35, 0.265, 7, color=LIGHT, align=PP_ALIGN.RIGHT)


# ── SYSTEM PROMPTS ──────────────────────────────────────────────
MODULE_SYSTEMS = {
    "🩺 Full Diabetes AI Platform": """You are an expert AI research agent covering ALL aspects of AI in diabetes management.
Be specific with clinical data when available, but do not invent data.
If uncertainty exists, say so.
When returning JSON return ONLY raw JSON.""",
    "💉 AI Insulin Delivery (Smart Pumps)": """You are an expert in automated insulin delivery (AID) systems.
Be specific with clinical evidence and note uncertainty where needed.
When returning JSON return ONLY raw JSON.""",
    "🩸 AI Glucose Monitoring (CGM)": """You are an expert in continuous glucose monitoring (CGM).
Be specific with clinical evidence and note uncertainty where needed.
When returning JSON return ONLY raw JSON.""",
    "🧠 AI Diagnostics & Early Detection": """You are an expert in AI diagnostics for diabetes complications.
Be specific with clinical evidence and note uncertainty where needed.
When returning JSON return ONLY raw JSON.""",
    "💊 AI Drug Management (GLP-1 & Meds)": """You are an expert in AI diabetes drug management.
Be specific with clinical evidence and note uncertainty where needed.
When returning JSON return ONLY raw JSON.""",
    "🥗 AI Nutrition & Lifestyle Coaching": """You are an expert in AI nutrition for diabetes.
Be specific with clinical evidence and note uncertainty where needed.
When returning JSON return ONLY raw JSON.""",
    "📊 Population Health & Analytics": """You are an expert in AI population health for diabetes.
Be specific with clinical evidence and note uncertainty where needed.
When returning JSON return ONLY raw JSON.""",
    "⚖️ Vendor Comparison Only": """You are an expert comparing diabetes AI vendors.
Include product, status, clinical outcomes, pricing if available, target patient, strengths, and limitations.
When returning JSON return ONLY raw JSON.""",
    "🎯 Recommendation Only": """You are an expert providing direct diabetes AI recommendations.
Be specific, actionable, and clear about uncertainty.
When returning JSON return ONLY raw JSON.""",
}


# ── REPORT PROMPT HELPERS ───────────────────────────────────────
def build_prompt(module: str, profile: str, depth: str) -> str:
    profile_map = {
        "General": "general diabetes patients",
        "Type 1 Diabetes": "Type 1 diabetes patients",
        "Type 2 Diabetes": "Type 2 diabetes patients",
        "Prediabetes / At-Risk": "prediabetes and at-risk individuals",
        "Pediatric": "pediatric diabetes patients",
        "Elderly (65+)": "elderly patients (65+) with diabetes",
        "Newly Diagnosed": "newly diagnosed diabetes patients",
        "Healthcare Provider": "endocrinologists and diabetes care teams",
    }
    depth_map = {
        "Executive Summary": "Be concise — 2-3 paragraphs per section.",
        "Detailed Analysis": "Be thorough with specific numbers and study names when supported.",
        "Clinical Deep-Dive": "Be technical — include trial details when supported. Avoid invented p-values.",
    }
    patient_context = profile_map.get(profile, "general diabetes patients")
    depth_context = depth_map.get(depth, depth_map["Detailed Analysis"])

    prompts = {
        "🩺 Full Diabetes AI Platform": f"""Generate a comprehensive intelligence report on AI applications in diabetes management for {patient_context}. {depth_context}

Sections:
1. Executive Summary
2. AI Insulin Delivery
3. AI Glucose Monitoring
4. AI Diagnostics
5. AI Drug Management
6. AI Nutrition & Lifestyle
7. Population Health AI
8. Overall Recommendation
9. Future Outlook 2025-2030
10. Risks & Limitations""",
        "💉 AI Insulin Delivery (Smart Pumps)": f"""Comprehensive report on AI smart insulin pumps for {patient_context}. {depth_context}
Sections: Executive Summary, How AI Works, Clinical Effectiveness, Vendor Comparison, Recommendation, Risks, Future Outlook.""",
        "🩸 AI Glucose Monitoring (CGM)": f"""Comprehensive report on AI glucose monitoring for {patient_context}. {depth_context}
Sections: Executive Summary, How CGM+AI Works, Clinical Evidence, Device Comparison, Non-Invasive Future, Recommendation, Costs.""",
        "🧠 AI Diagnostics & Early Detection": f"""Comprehensive report on AI diagnostics for {patient_context}. {depth_context}
Sections: Executive Summary, Retinopathy AI, T2D Prediction Models, Neuropathy & Wound Care AI, Kidney Disease Detection, Vendor Comparison, Recommendation, Limitations.""",
        "💊 AI Drug Management (GLP-1 & Meds)": f"""Comprehensive report on AI drug management for {patient_context}. {depth_context}
Sections: Executive Summary, GLP-1 Revolution, Smart Insulin Pens, AI Adherence Platforms, Digital Therapeutics, Vendor Comparison, Recommendation, Safety.""",
        "🥗 AI Nutrition & Lifestyle Coaching": f"""Comprehensive report on AI nutrition coaching for {patient_context}. {depth_context}
Sections: Executive Summary, CGM-Guided Nutrition, Meal Planning AI, Physical Activity AI, Behavioral Platforms, App Comparison, Clinical Evidence, Recommendation.""",
        "📊 Population Health & Analytics": f"""Comprehensive report on AI population health for {patient_context}. {depth_context}
Sections: Executive Summary, Global Burden, Risk Stratification AI, CMS Programs, Payer Analytics, Clinical Trial AI, Health Equity, ROI Evidence, Recommendation.""",
        "⚖️ Vendor Comparison Only": f"""Detailed vendor comparison across diabetes AI categories for {patient_context}. {depth_context}
Return structured comparisons for AID Systems, CGM Devices, Diagnostic AI, Drug Management, and Nutrition Apps.""",
        "🎯 Recommendation Only": f"""Direct AI recommendations for {patient_context}. {depth_context}
Structure: Decision Framework, By Sub-Category, Complete Ecosystem, Cost Considerations, What to Avoid, Next Steps.""",
    }
    return prompts.get(module, prompts["🩺 Full Diabetes AI Platform"])


JSON_PROMPT = """Based on your report, return ONLY raw valid JSON (no markdown, no fences) with this schema:
{
  "title": "AI in Diabetes Management: Intelligence Report",
  "subtitle": "Comprehensive Clinical Analysis & Recommendations",
  "module": "Full Diabetes AI Platform",
  "executive_summary": ["finding 1", "finding 2", "finding 3"],
  "key_metrics": [
    {"label": "Metric 1", "value": "Value 1", "source": "Source 1"},
    {"label": "Metric 2", "value": "Value 2", "source": "Source 2"}
  ],
  "categories": [
    {"name": "Category", "top_product": "Product", "key_outcome": "Outcome", "fda": "Status"}
  ],
  "recommendation": {
    "top_pick": "Top recommendation",
    "rationale": "Why",
    "by_profile": [
      {"profile": "Type 1", "pick": "Recommendation"}
    ]
  },
  "risks": [
    {"title": "Risk title", "desc": "Risk description"}
  ],
  "future_trends": ["Trend 1", "Trend 2"]
}"""


# ── API CLIENT ──────────────────────────────────────────────────
def get_client() -> Anthropic:
    api_key = get_anthropic_api_key()
    if not api_key:
        st.error("⚠️ Missing ANTHROPIC_API_KEY. Add it to Streamlit Secrets or environment variables.")
        st.stop()
    return Anthropic(api_key=api_key)


def model_name(preferred: str, fallback: str) -> str:
    return get_secret(preferred, get_secret(fallback, "")) or fallback


def call_anthropic(client: Anthropic, system: str, messages: List[Dict[str, str]], max_tokens: int, preferred_model_env: str, fallback_model: str) -> str:
    model = model_name(preferred_model_env, fallback_model)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text
    except AuthenticationError:
        st.error("Authentication failed. Please verify your Anthropic API key.")
        raise
    except RateLimitError:
        st.error("Rate limit reached. Please try again in a moment.")
        raise
    except APIError as exc:
        st.error(f"Anthropic API error: {exc}")
        raise
    except Exception as exc:
        st.error(f"Unexpected API error: {exc}")
        raise


def generate_report(client: Anthropic, module: str, profile: str, depth: str, history: List[Dict[str, str]]) -> str:
    prompt = build_prompt(module, profile, depth)
    system = MODULE_SYSTEMS.get(module, MODULE_SYSTEMS["🩺 Full Diabetes AI Platform"])
    messages = history + [{"role": "user", "content": prompt}]
    return call_anthropic(
        client=client,
        system=system,
        messages=messages,
        max_tokens=4000,
        preferred_model_env="ANTHROPIC_REPORT_MODEL",
        fallback_model="claude-3-5-sonnet-latest",
    )


# ── JSON REPAIR ─────────────────────────────────────────────────
def extract_json_block(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start:end + 1]

    return cleaned


def try_parse_json(raw: str) -> Dict[str, Any]:
    candidate = extract_json_block(raw)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        repaired = candidate
        repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
        repaired = repaired.replace("\u201c", '"').replace("\u201d", '"')
        repaired = repaired.replace("\u2018", "'").replace("\u2019", "'")
        return json.loads(repaired)


def normalize_slide_data(data: Dict[str, Any], module: str) -> Dict[str, Any]:
    return {
        "title": data.get("title", "AI in Diabetes Management: Intelligence Report"),
        "subtitle": data.get("subtitle", "Comprehensive Clinical Analysis & Recommendations"),
        "module": data.get("module", module),
        "executive_summary": list(data.get("executive_summary", []))[:3],
        "key_metrics": list(data.get("key_metrics", []))[:6],
        "categories": list(data.get("categories", []))[:6],
        "recommendation": data.get("recommendation", {}),
        "risks": list(data.get("risks", []))[:4],
        "future_trends": list(data.get("future_trends", []))[:5],
    }


def extract_slide_data(client: Anthropic, module: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    system = MODULE_SYSTEMS.get(module, MODULE_SYSTEMS["🩺 Full Diabetes AI Platform"])
    messages = history + [{"role": "user", "content": JSON_PROMPT}]

    raw = call_anthropic(
        client=client,
        system=system,
        messages=messages,
        max_tokens=2500,
        preferred_model_env="ANTHROPIC_JSON_MODEL",
        fallback_model="claude-3-5-sonnet-latest",
    )

    try:
        parsed = try_parse_json(raw)
        return normalize_slide_data(parsed, module)
    except Exception:
        repair_messages = messages + [{
            "role": "user",
            "content": (
                "Your last response was not valid JSON. Return ONLY valid JSON that matches the schema exactly. "
                "No markdown fences, no commentary, no trailing commas."
            ),
        }]
        retry_raw = call_anthropic(
            client=client,
            system=system,
            messages=repair_messages,
            max_tokens=2500,
            preferred_model_env="ANTHROPIC_JSON_MODEL",
            fallback_model="claude-3-5-sonnet-latest",
        )
        parsed = try_parse_json(retry_raw)
        return normalize_slide_data(parsed, module)


# ── PPTX BUILDER ────────────────────────────────────────────────
def build_pptx(d: Dict[str, Any], module_name: str) -> BytesIO:
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)
    blank = prs.slide_layouts[6]

    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, DARK)
    add_rect(s, 0, 0, 0.22, 5.625, CRIMSON)
    add_rect(s, 0.22, 1.2, 9.78, 2.7, CHARCOAL)
    add_text(s, "AI RESEARCH AGENT  ·  DIABETES TECHNOLOGY  ·  HCM 535", 0.5, 0.75, 9, 0.32, 9, color=PINK)
    add_text(s, d.get("title", "AI in Diabetes Management"), 0.5, 1.32, 9.1, 1.1, 32, True, color=LIGHT, font_name=FT)
    add_text(s, d.get("subtitle", ""), 0.5, 2.5, 9.1, 0.5, 14, False, True, color=rgb(0xB0, 0xB0, 0xB0))
    mod_short = module_name.split(" ", 1)[1] if " " in module_name else module_name
    add_rect(s, 0.5, 3.15, 4.5, 0.38, CRIMSON)
    add_text(s, mod_short, 0.55, 3.15, 4.4, 0.38, 11, True, color=LIGHT)
    add_rect(s, 0.5, 3.7, 5.6, 1.55, CHARCOAL)
    info = [
        f"Student:     {STUDENT['name']}",
        f"Student ID:  {STUDENT['id']}",
        f"Institution: {STUDENT['school']}",
        f"Course:      {STUDENT['course']}",
    ]
    for i, line in enumerate(info):
        add_text(s, line, 0.7, 3.8 + i * 0.34, 5.2, 0.32, 10, color=LIGHT)
    add_rect(s, 6.5, 3.8, 2.8, 0.42, CRIMSON)
    add_text(s, "Spring 2026", 6.5, 3.8, 2.8, 0.42, 14, True, color=LIGHT, align=PP_ALIGN.CENTER, font_name=FT)

    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, OFFWHITE)
    hdr(s, "Executive Summary", "AI in Diabetes — 2025 Evidence")
    add_rect(s, 0.3, 0.82, 4.5, 3.85, WHITE)
    add_text(s, "3 Key Findings", 0.5, 0.95, 4.1, 0.38, 13, True, color=CRIMSON, font_name=FT)
    findings = d.get("executive_summary", ["Finding 1", "Finding 2", "Finding 3"])
    fcolors = [CRIMSON, CRIMSON2, rgb(0x7F, 0x1D, 0x1D)]
    for i, txt in enumerate(findings[:3]):
        y = 1.42 + i * 1.0
        add_rect(s, 0.5, y, 0.36, 0.36, fcolors[i])
        add_text(s, str(i + 1), 0.5, y, 0.36, 0.36, 13, True, color=LIGHT, align=PP_ALIGN.CENTER, font_name=FT)
        add_text(s, txt, 1.0, y, 3.6, 0.85, 10.5, color=TEXT)
    add_rect(s, 5.1, 0.82, 4.55, 1.65, DARK)
    add_text(s, "Snapshot", 5.3, 0.9, 4.1, 0.32, 11, True, color=PINK, font_name=FT)
    add_text(s, "This slide summarizes the most important findings generated by the AI agent for the selected diabetes module.", 5.3, 1.26, 4.1, 1.1, 10, color=LIGHT)
    add_rect(s, 5.1, 2.62, 4.55, 2.08, WHITE)
    add_text(s, "AI Impact Highlights", 5.3, 2.72, 4.0, 0.32, 11, True, color=CRIMSON, font_name=FT)
    impacts = d.get("key_metrics", [])[:5]
    for i, metric in enumerate(impacts):
        y = 3.1 + i * 0.3
        add_text(s, metric.get("label", "Metric"), 5.3, y, 2.5, 0.28, 9.5, color=GRAY)
        add_text(s, metric.get("value", "—"), 7.8, y, 1.7, 0.28, 10, True, color=CRIMSON, align=PP_ALIGN.RIGHT)
    ftr(s, 2)

    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, OFFWHITE)
    hdr(s, "Key Metrics", "Structured evidence summary")
    cw, ch, gx, gy = 3.0, 1.55, 0.12, 0.12
    sx, sy = 0.25, 0.92
    for i, m in enumerate(d.get("key_metrics", [])[:6]):
        col, row = i % 3, i // 3
        x = sx + col * (cw + gx)
        y = sy + row * (ch + gy)
        add_rect(s, x, y, cw, ch, WHITE)
        add_rect(s, x, y, cw, 0.05, CRIMSON)
        add_text(s, m.get("value", "—"), x + 0.15, y + 0.1, cw - 0.3, 0.72, 32, True, color=CRIMSON, font_name=FT)
        add_text(s, m.get("label", ""), x + 0.15, y + 0.84, cw - 0.3, 0.32, 11, True, color=TEXT)
        add_text(s, m.get("source", ""), x + 0.15, y + 1.19, cw - 0.3, 0.26, 8, False, True, color=GRAY)
    ftr(s, 3)

    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, DARK)
    hdr(s, "AI Categories in Diabetes Management", "Six pillars of AI-driven diabetes care")
    cat_colors = [CRIMSON, CRIMSON2, rgb(0x9F, 0x12, 0x39), rgb(0x7F, 0x1D, 0x1D), rgb(0xBE, 0x12, 0x3C), rgb(0x88, 0x13, 0x37)]
    categories = d.get("categories", [])[:6]
    positions = [(0.25, 0.82), (3.38, 0.82), (6.51, 0.82), (0.25, 2.72), (3.38, 2.72), (6.51, 2.72)]
    bw, bh = 2.95, 1.75
    for i, cat in enumerate(categories):
        x, y = positions[i]
        cc = cat_colors[i % len(cat_colors)]
        add_rect(s, x, y, bw, bh, CHARCOAL)
        add_rect(s, x, y, bw, 0.05, cc)
        add_rect(s, x, y, 0.12, bh, cc)
        add_text(s, cat.get("name", ""), x + 0.2, y + 0.1, bw - 0.3, 0.38, 12, True, color=LIGHT, font_name=FT)
        add_text(s, "Top: " + cat.get("top_product", ""), x + 0.2, y + 0.55, bw - 0.3, 0.3, 9.5, color=rgb(0xB0, 0xB0, 0xB0))
        add_text(s, cat.get("key_outcome", ""), x + 0.2, y + 0.88, bw - 0.3, 0.5, 9, False, True, color=PINK)
        add_rect(s, x + 0.2, y + 1.42, 1.5, 0.22, cc)
        add_text(s, cat.get("fda", ""), x + 0.2, y + 1.42, 1.5, 0.22, 8, True, color=LIGHT, align=PP_ALIGN.CENTER)
    ftr(s, 4)

    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, OFFWHITE)
    hdr(s, "Recommendation", "Evidence-based selection guide")
    rec = d.get("recommendation", {})
    add_rect(s, 0.3, 0.82, 5.9, 2.15, DARK)
    add_rect(s, 0.3, 0.82, 0.18, 2.15, CRIMSON)
    add_rect(s, 0.3, 0.82, 2.1, 0.32, CRIMSON)
    add_text(s, "#1 TOP RECOMMENDATION", 0.32, 0.82, 2.05, 0.32, 8, True, color=LIGHT, align=PP_ALIGN.CENTER)
    add_text(s, rec.get("top_pick", ""), 0.6, 1.18, 5.4, 0.6, 16, True, color=LIGHT, font_name=FT)
    add_text(s, rec.get("rationale", ""), 0.6, 1.84, 5.3, 1.0, 10, color=rgb(0xB0, 0xB0, 0xB0))
    add_rect(s, 6.45, 0.82, 3.25, 4.12, WHITE)
    add_text(s, "By Patient Profile", 6.6, 0.9, 2.9, 0.34, 12, True, color=CRIMSON, font_name=FT)
    pbg = [rgb(0xFF, 0xF5, 0xF5), OFFWHITE, rgb(0xFF, 0xF5, 0xF5), OFFWHITE, rgb(0xFF, 0xF5, 0xF5)]
    for i, p in enumerate(rec.get("by_profile", [])[:5]):
        y = 1.36 + i * 0.66
        add_rect(s, 6.55, y, 3.0, 0.58, pbg[i % 2])
        add_text(s, p.get("profile", ""), 6.68, y + 0.04, 2.8, 0.22, 8, False, True, color=GRAY)
        add_text(s, p.get("pick", ""), 6.68, y + 0.27, 2.8, 0.27, 10.5, True, color=CRIMSON, font_name=FT)
    ftr(s, 5)

    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, OFFWHITE)
    hdr(s, "Risks & Limitations", "Critical considerations")
    rcolors = [CRIMSON, rgb(0x7F, 0x1D, 0x1D), rgb(0x9F, 0x12, 0x39), rgb(0x4B, 0x55, 0x63)]
    for i, r in enumerate(d.get("risks", [])[:4]):
        col, row = i % 2, i // 2
        x = 0.3 + col * 4.9
        y = 0.92 + row * 2.12
        add_rect(s, x, y, 4.55, 1.97, WHITE)
        add_rect(s, x, y, 4.55, 0.05, rcolors[i])
        add_rect(s, x, y, 0.18, 1.97, rcolors[i])
        add_text(s, r.get("title", ""), x + 0.28, y + 0.12, 4.1, 0.38, 13, True, color=TEXT, font_name=FT)
        add_text(s, r.get("desc", ""), x + 0.28, y + 0.55, 4.1, 1.28, 11, color=GRAY)
    ftr(s, 6)

    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, DARK)
    hdr(s, "Future Outlook 2025–2030", "Next generation AI diabetes care")
    years = ["2026", "2027", "2027", "2028", "2029–30"]
    bw3, bh3 = 1.72, 3.05
    sx3, sy3, gap3 = 0.22, 1.0, 0.1
    for i, t in enumerate(d.get("future_trends", [])[:5]):
        x = sx3 + i * (bw3 + gap3)
        add_rect(s, x, sy3, bw3, bh3, CHARCOAL)
        add_rect(s, x, sy3, bw3, 0.05, CRIMSON)
        add_rect(s, x + 0.1, sy3 + 0.12, 1.5, 0.3, CRIMSON)
        add_text(s, years[i], x + 0.1, sy3 + 0.12, 1.5, 0.3, 10, True, color=LIGHT, align=PP_ALIGN.CENTER)
        add_text(s, t, x + 0.1, sy3 + 0.55, bw3 - 0.2, 2.35, 10, color=LIGHT)
    ftr(s, 7)

    s = prs.slides.add_slide(blank)
    add_rect(s, 0, 0, 10, 5.625, DARK)
    add_rect(s, 0, 0, 0.22, 5.625, CRIMSON)
    add_text(s, "Thank You", 0.5, 0.55, 9, 0.9, 40, True, color=LIGHT, font_name=FT)
    add_text(s, "AI in Diabetes Management: Clinical Evidence & Recommendation", 0.5, 1.52, 9, 0.45, 13, False, True, color=rgb(0xB0, 0xB0, 0xB0))
    add_rect(s, 0.5, 2.15, 5.5, 1.6, CHARCOAL)
    rows = [
        ("Student", STUDENT["name"]),
        ("Student ID", STUDENT["id"]),
        ("Institution", STUDENT["school"]),
        ("Course", STUDENT["course"]),
    ]
    for i, (lbl, val) in enumerate(rows):
        add_text(s, lbl + ":", 0.7, 2.27 + i * 0.35, 1.4, 0.3, 10, True, color=PINK)
        add_text(s, val, 2.15, 2.27 + i * 0.35, 3.7, 0.3, 10, color=LIGHT)
    add_rect(s, 0.5, 3.92, 9.0, 1.4, CHARCOAL)
    add_text(s, "References", 0.7, 3.98, 3.0, 0.28, 10, True, color=PINK, font_name=FT)
    add_text(s, "Add verified references here before final academic submission.", 0.7, 4.28, 8.6, 1.0, 8, color=rgb(0xB0, 0xB0, 0xB0))

    buf = BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


# ── SESSION STATE ───────────────────────────────────────────────
def default_state() -> Dict[str, Any]:
    return {
        "history": [],
        "report_text": "",
        "slide_data": None,
        "pptx_buffer": None,
        "pptx_ready": False,
        "authenticated": False,
        "current_module": "",
    }


def initialize_session_state() -> None:
    for key, value in default_state().items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_generation_state() -> None:
    st.session_state.history = []
    st.session_state.report_text = ""
    st.session_state.slide_data = None
    st.session_state.pptx_buffer = None
    st.session_state.pptx_ready = False
    st.session_state.current_module = ""


initialize_session_state()


# ── ACCESS GATE ─────────────────────────────────────────────────
def render_login() -> None:
    st.markdown(
        """
        <div class="main-header">
            <h1>🩺 Diabetes AI Agent</h1>
            <p>AI Applications in Diabetes Management — Full Platform</p>
            <div class="student-badge">
                Hugo Silva  ·  ID 74964557  ·  ITU SPRING 2026  ·  HCM 535
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    access_code = get_access_code()
    if not access_code:
        st.warning("No APP_ACCESS_CODE configured. The app is unlocked for this session.")
        st.session_state.authenticated = True
        safe_rerun()
        return

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("### Enter Access Code")
        code = st.text_input("Access code", type="password", placeholder="Enter code to continue...")
        if st.button("Unlock Agent"):
            if code == access_code:
                st.session_state.authenticated = True
                safe_rerun()
            else:
                st.error("Incorrect code.")


if not st.session_state.authenticated:
    render_login()
    st.stop()


# ── SIDEBAR ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔬 Research Module")
    module = st.selectbox("Select module", list(MODULES.keys()))
    info = MODULES[module]
    st.markdown(
        f"""
        <div class="module-card">
            <h4>{info['icon']} {info['tag']}</h4>
            <p>{info['desc']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ⚙️ Settings")
    profile = st.selectbox(
        "Patient profile",
        [
            "General",
            "Type 1 Diabetes",
            "Type 2 Diabetes",
            "Prediabetes / At-Risk",
            "Pediatric",
            "Elderly (65+)",
            "Newly Diagnosed",
            "Healthcare Provider",
        ],
    )
    depth = st.selectbox("Report depth", ["Executive Summary", "Detailed Analysis", "Clinical Deep-Dive"])

    st.markdown("---")
    st.markdown("### 💬 Follow-up")
    followup = st.text_area("Ask the agent", placeholder="e.g. Which CGM is best for a child?", height=80)
    ask_btn = st.button("Ask ↗")

    st.markdown("---")
    st.markdown(
        f"""
        <div style="background:#2C2C2E;border-radius:10px;padding:0.8rem;
                    font-size:0.78rem;color:#B0B0B0">
        <strong style="color:#FF6B6B">Modules available:</strong><br><br>
        {'<br>'.join([f"{v['icon']} {k.split(' ',1)[1] if ' ' in k else k}" for k, v in MODULES.items()])}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 Reset"):
        reset_generation_state()
        safe_rerun()


# ── MAIN ────────────────────────────────────────────────────────
st.markdown(
    """
<div class="main-header">
    <h1>🩺 Diabetes AI Agent</h1>
    <p>AI Applications in Diabetes Management — 6 Research Modules
       · Clinical Intelligence · PowerPoint Generator</p>
    <div class="student-badge">
        Hugo Silva  ·  ID 74964557  ·  ITU SPRING 2026
        ·  HCM 535 – Data Analytics in Healthcare
    </div>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
metrics = [
    ("537M", "People with diabetes globally"),
    ("6", "AI research modules"),
    ("78%", "Best AID system TIR"),
    ("60%", "T2D reversal rate (example metric)"),
]
for col, (val, lbl) in zip([c1, c2, c3, c4], metrics):
    with col:
        st.markdown(f'<div class="metric-card"><h3>{val}</h3><p>{lbl}</p></div>', unsafe_allow_html=True)

st.markdown('<hr class="teal-divider">', unsafe_allow_html=True)
st.markdown(f"**Selected module:** {module} — *{MODULES[module]['desc']}*")

col_btn, col_status = st.columns([2, 3])
with col_btn:
    gen_btn = st.button("▶  Generate Report + PPT", use_container_width=True)
with col_status:
    if st.session_state.report_text:
        st.markdown('<span class="badge-success">✓ Report ready</span>', unsafe_allow_html=True)


# ── GENERATION PIPELINE ─────────────────────────────────────────
if gen_btn:
    client = get_client()
    prog = st.progress(0)
    status = st.empty()
    try:
        status.markdown(f"**Step 1/3** — Generating {module} report...")
        prog.progress(10)
        report = generate_report(client, module, profile, depth, st.session_state.history)
        st.session_state.report_text = report
        st.session_state.current_module = module
        st.session_state.history.append({"role": "user", "content": f"Generate: {module}, {profile}, {depth}"})
        st.session_state.history.append({"role": "assistant", "content": report})
        prog.progress(45)

        status.markdown("**Step 2/3** — Extracting structured slide data...")
        slide_data = extract_slide_data(client, module, st.session_state.history)
        st.session_state.slide_data = slide_data
        prog.progress(75)

        status.markdown("**Step 3/3** — Building PowerPoint presentation...")
        buf = build_pptx(slide_data, module)
        st.session_state.pptx_buffer = buf
        st.session_state.pptx_ready = True
        prog.progress(100)
        status.markdown("✅ **Done!** Report and PPT ready.")
    except Exception as exc:
        st.error(f"Generation error: {exc}")
        prog.empty()
        status.empty()


# ── FOLLOW-UP ───────────────────────────────────────────────────
if ask_btn and followup.strip():
    if not st.session_state.history:
        st.warning("Generate a report first.")
    else:
        client = get_client()
        with st.spinner("Thinking..."):
            try:
                system = MODULE_SYSTEMS.get(st.session_state.current_module, MODULE_SYSTEMS["🩺 Full Diabetes AI Platform"])
                msgs = st.session_state.history + [{"role": "user", "content": followup.strip()}]
                ans = call_anthropic(
                    client=client,
                    system=system,
                    messages=msgs,
                    max_tokens=1500,
                    preferred_model_env="ANTHROPIC_CHAT_MODEL",
                    fallback_model="claude-3-5-sonnet-latest",
                )
                st.session_state.history.append({"role": "user", "content": followup.strip()})
                st.session_state.history.append({"role": "assistant", "content": ans})
                st.session_state.report_text += f"\n\n---\n\n**Q: {followup.strip()}**\n\n{ans}"
            except Exception as exc:
                st.error(f"Follow-up error: {exc}")


# ── RESULTS ────────────────────────────────────────────────────
if st.session_state.report_text:
    tab1, tab2 = st.tabs(["📄 Research Report", "📊 Slide Data"])
    with tab1:
        st.markdown(st.session_state.report_text)
    with tab2:
        if st.session_state.slide_data:
            st.json(st.session_state.slide_data)

    st.markdown('<hr class="teal-divider">', unsafe_allow_html=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label="⬇️  Download Report (.txt)",
            data=st.session_state.report_text.encode("utf-8"),
            file_name=f"diabetes_AI_report_{ts}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with dl2:
        if st.session_state.pptx_ready and st.session_state.pptx_buffer:
            st.download_button(
                label="⬇️  Download Presentation (.pptx)",
                data=st.session_state.pptx_buffer,
                file_name=f"diabetes_AI_agent_{ts}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )


# ── FOOTER ──────────────────────────────────────────────────────
st.markdown(
    """
<div class="footer">
    Hugo Silva  ·  ID 74964557  ·  ITU | SPRING 2026
    ·  HCM 535 – Data Analytics Application in Healthcare<br>
    Powered by Anthropic Claude  ·  Not a substitute for medical advice<br>
    For academic use, verify all clinical claims and references before submission.
</div>
""",
    unsafe_allow_html=True,
)
