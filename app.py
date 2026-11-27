"""PropDoc AI – Smart Document Intelligence (Streamlit)."""
import hashlib
import io
import os
import re

import fitz  # PyMuPDF
import pytesseract
import streamlit as st
from openai import (APIConnectionError, AuthenticationError, OpenAI,
                    RateLimitError)
from PIL import Image

# ───────────────────────── Configuration ─────────────────────────
MAX_CHARS = 60_000   # max characters of document text sent to the AI
MAX_PAGES = 40       # max pages processed per PDF (OCR is slow)
OCR_LANGS = {
    "Marathi + English + Hindi": "mar+eng+hin",
    "Marathi + English": "mar+eng",
    "Hindi + English": "hin+eng",
    "English only": "eng",
}
OCR_MODES = ["Auto (OCR only unclear pages)", "Force OCR on all pages", "Text only (no OCR)"]
AI_LANGS = {"English": "English", "Marathi": "Marathi (मराठी)", "Hindi": "Hindi (हिन्दी)"}
NAV = ["📁 Document Workspace", "🤖 AI Analysis", "🔍 Document Verification", "💬 AI Assistant"]

st.set_page_config(page_title="PropDoc AI – Smart Document Intelligence",
                   page_icon="📄", layout="wide")

# ───────────────────────── Liquid-glass styling ─────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700;800&display=swap');
:root{--ink:#f5efdc;--muted:#b9c2e6;--gold:#e3c26b;--gold2:#b8902f;--navy:#070b26;--royal:#2a3aa8;}
html,body,.stApp{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Inter",system-ui,sans-serif;}
.stApp{background:
 radial-gradient(55% 45% at 88% 0%,rgba(227,194,107,.22) 0%,transparent 62%),
 radial-gradient(65% 55% at 0% 100%,rgba(70,95,255,.38) 0%,transparent 62%),
 radial-gradient(45% 40% at 40% 45%,rgba(60,80,210,.22) 0%,transparent 65%),
 linear-gradient(160deg,#060a24 0%,#0f1a55 55%,#0a1238 100%);background-attachment:fixed;}
.stApp,.stApp *{color:var(--ink);}
[data-testid="stHeader"]{background:transparent;}
#MainMenu,footer{visibility:hidden;}
.block-container{padding-top:2.2rem;max-width:1100px;}
h1,h2,h3,h4{letter-spacing:-.01em;}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] *{color:var(--muted);}
a{color:var(--gold)!important;}

/* royal glass cards */
[class*="st-key-card"]{
 background:linear-gradient(145deg,rgba(255,255,255,.14),rgba(255,255,255,.04));
 -webkit-backdrop-filter:blur(26px) saturate(170%);backdrop-filter:blur(26px) saturate(170%);
 border:1px solid rgba(255,255,255,.2);border-radius:28px;padding:1.4rem 1.6rem;margin-bottom:1.1rem;
 box-shadow:inset 0 1.5px 1px rgba(255,255,255,.4),inset 0 -2px 10px rgba(80,100,255,.15),0 24px 50px rgba(0,0,10,.45);}
.hero{padding:.4rem 0 1.2rem;}
.hero h1{font-family:"Playfair Display",Georgia,serif;font-size:3.3rem;font-weight:800;margin:0;line-height:1.05;
 background:linear-gradient(180deg,#fff6d8,#e3c26b);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.hero h1 *{-webkit-text-fill-color:inherit;}
.hero h2{font-family:"Playfair Display",Georgia,serif;font-size:1.5rem;font-weight:600;color:var(--gold);margin:.3rem 0 .7rem;}
.hero p{font-size:1.05rem;color:var(--muted);max-width:60ch;margin:0;}
.disclaimer{margin-top:1.1rem;padding:.85rem 1.2rem;border-radius:20px;font-size:.88rem;color:var(--muted);
 background:rgba(255,255,255,.07);border:1px solid rgba(227,194,107,.35);
 -webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);box-shadow:inset 0 1px 1px rgba(255,255,255,.25);}
.disclaimer b{color:var(--gold);}
.chip{display:inline-block;margin:0 .5rem .5rem 0;padding:.35rem .95rem;border-radius:999px;font-size:.85rem;font-weight:600;
 background:radial-gradient(120% 140% at 30% 0%,rgba(255,255,255,.35),rgba(255,255,255,.05) 60%);
 border:1px solid rgba(227,194,107,.5);box-shadow:inset 0 1px 1px rgba(255,255,255,.5),0 6px 14px rgba(0,0,10,.35);}
.brand{font-family:"Playfair Display",Georgia,serif;font-size:1.6rem;font-weight:700;margin:0;color:var(--gold);}
.brand-sub{color:var(--muted)!important;font-size:.9rem;margin:0 0 1.2rem;}

/* sidebar */
[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.03));
 -webkit-backdrop-filter:blur(30px) saturate(180%);backdrop-filter:blur(30px) saturate(180%);
 border-right:1px solid rgba(227,194,107,.3);box-shadow:8px 0 40px rgba(0,0,10,.4);}
[data-testid="stSidebar"]>div:first-child{background:transparent;}
[data-testid="stSidebar"] [role="radiogroup"]{gap:.5rem;}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:.75rem 1.1rem;border-radius:18px;width:100%;cursor:pointer;
 background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.18);
 box-shadow:inset 0 1px 1px rgba(255,255,255,.3);transition:all .2s ease;}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-of-type{display:none!important;}
[data-testid="stSidebar"] [role="radiogroup"] label p{font-size:1rem;font-weight:500;color:var(--ink);}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{transform:translateX(4px);background:rgba(255,255,255,.14);}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
 background:radial-gradient(120% 150% at 25% 0%,rgba(255,255,255,.4),rgba(255,255,255,.06) 55%),linear-gradient(135deg,rgba(227,194,107,.45),rgba(184,144,47,.25));
 border-color:rgba(227,194,107,.8);box-shadow:inset 0 2px 2px rgba(255,255,255,.55),0 10px 24px rgba(227,194,107,.25);}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{font-weight:700;color:#fff;}

/* glass-drop buttons */
.stButton button,.stDownloadButton button,[data-testid="stFormSubmitButton"] button,[data-testid="stFileUploaderDropzone"] button{
 position:relative;overflow:hidden;border-radius:999px;padding:.6rem 1.8rem;font-weight:650;
 background:radial-gradient(130% 150% at 28% 0%,rgba(255,255,255,.55) 0%,rgba(255,255,255,.12) 42%,rgba(255,255,255,.04) 100%),rgba(70,95,255,.28);
 -webkit-backdrop-filter:blur(18px) saturate(190%);backdrop-filter:blur(18px) saturate(190%);
 border:1px solid rgba(255,255,255,.4);
 box-shadow:inset 0 2px 2px rgba(255,255,255,.7),inset 0 -9px 16px rgba(20,30,140,.45),0 12px 26px rgba(0,0,15,.5);
 transition:transform .18s cubic-bezier(.3,1.5,.5,1),box-shadow .2s ease;}
.stButton button::after,.stDownloadButton button::after,[data-testid="stFormSubmitButton"] button::after,[data-testid="stFileUploaderDropzone"] button::after{
 content:"";position:absolute;top:5%;left:9%;width:46%;height:42%;border-radius:50%;pointer-events:none;
 background:linear-gradient(180deg,rgba(255,255,255,.7),rgba(255,255,255,0));filter:blur(1px);}
.stButton button p,.stDownloadButton button p,[data-testid="stFormSubmitButton"] button p,[data-testid="stFileUploaderDropzone"] button span{color:var(--ink);position:relative;z-index:1;}
.stButton button:hover,.stDownloadButton button:hover,[data-testid="stFormSubmitButton"] button:hover,[data-testid="stFileUploaderDropzone"] button:hover{
 transform:translateY(-3px) scale(1.03);border-color:rgba(227,194,107,.9);
 box-shadow:inset 0 2px 2px rgba(255,255,255,.8),inset 0 -9px 16px rgba(20,30,140,.5),0 18px 34px rgba(0,0,15,.6),0 0 22px rgba(227,194,107,.3);}
.stButton button:active,.stDownloadButton button:active,[data-testid="stFormSubmitButton"] button:active{transform:translateY(1px) scale(.96);}
button[kind="primary"],button[kind="primaryFormSubmit"]{
 background:radial-gradient(130% 150% at 28% 0%,rgba(255,255,255,.75) 0%,rgba(255,255,255,.15) 40%,rgba(255,255,255,0) 100%),linear-gradient(160deg,#f0d27a,#b8902f)!important;
 border-color:rgba(255,240,190,.9)!important;
 box-shadow:inset 0 2px 3px rgba(255,255,255,.9),inset 0 -10px 18px rgba(120,80,0,.4),0 14px 30px rgba(227,194,107,.35)!important;}
button[kind="primary"] p,button[kind="primaryFormSubmit"] p{color:#2a1c00!important;font-weight:700;}
button:focus-visible{outline:3px solid rgba(227,194,107,.7)!important;outline-offset:2px;}

/* inputs, uploader, chat, expanders */
[data-baseweb="textarea"],[data-baseweb="input"],[data-baseweb="select"]>div{border-radius:18px!important;
 background:rgba(255,255,255,.08)!important;border:1px solid rgba(255,255,255,.25)!important;box-shadow:inset 0 2px 6px rgba(0,0,20,.3);}
textarea,input{color:var(--ink)!important;background:transparent!important;-webkit-text-fill-color:var(--ink)!important;}
[data-baseweb="popover"] *{background-color:#101a52;color:var(--ink);}
[data-testid="stFileUploaderDropzone"]{border-radius:24px;background:rgba(255,255,255,.07);border:1.5px dashed rgba(227,194,107,.6);}
[data-testid="stFileUploaderDropzone"] small,[data-testid="stFileUploaderDropzone"] span{color:var(--muted);}
[data-testid="stChatMessage"]{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);border-radius:22px;
 -webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);}
[data-testid="stExpander"]{border-radius:20px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.2);}
[data-testid="stAlert"]{border-radius:18px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.25);}
[data-testid="stProgress"]>div>div>div{background:linear-gradient(90deg,#b8902f,#f0d27a);}
/* sidebar nav buttons */
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{overflow-x:hidden;}
[data-testid="stSidebar"] *{box-sizing:border-box;}
[data-testid="stSidebar"] .stButton{margin-bottom:.35rem;}
[data-testid="stSidebar"] .stButton button{width:100%;justify-content:flex-start;padding:.75rem 1.2rem;}
[data-testid="stSidebar"] .stButton button p{font-size:1rem;}
@media (max-width:700px){.hero h1{font-size:2.3rem}.hero h2{font-size:1.2rem}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ───────────────────────── Helpers ─────────────────────────
class AIError(Exception):
    pass


def get_secret(name, default=None):
    """Read from Streamlit Secrets, falling back to environment variables."""
    try:
        value = st.secrets[name]
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


def init_state():
    for key, default in {"doc1": None, "doc2": None, "analysis": None,
                         "comparison": None, "chat": []}.items():
        st.session_state.setdefault(key, default)


def pages_to_text(pages):
    return "\n\n".join(f"[Page {n}]\n{t}" for n, t in pages)


def build_context(pages, limit=MAX_CHARS, query=None):
    """Return (text, truncated). Keeps the request within `limit` characters."""
    blocks = [(n, f"[Page {n}]\n{t}") for n, t in pages]
    if sum(len(b) for _, b in blocks) <= limit:
        return "\n\n".join(b for _, b in blocks), False
    order = blocks
    cap = max(limit // max(len(blocks), 1), 1500)
    if query:  # prioritise pages that share words with the question
        words = set(re.findall(r"\w{3,}", query.lower()))
        order = sorted(blocks, key=lambda x: -sum(w in x[1].lower() for w in words))
        cap = limit // 3
    chosen, used = [], 0
    for n, b in order:
        room = limit - used
        if room < 300:
            break
        b = b[:min(cap, room)]
        chosen.append((n, b))
        used += len(b)
    chosen.sort(key=lambda x: x[0])
    return "\n\n".join(b for _, b in chosen), True


def call_ai(system, user):
    key = get_secret("OPENAI_API_KEY")
    if not key:
        raise AIError("OpenAI API key is missing. Add OPENAI_API_KEY in Streamlit Secrets "
                      "(App settings → Secrets) and reboot the app.")
    try:
        client = OpenAI(api_key=key, timeout=120)
        resp = client.chat.completions.create(
            model=get_secret("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}])
        return (resp.choices[0].message.content or "").strip()
    except AuthenticationError:
        raise AIError("The OpenAI API key was rejected. Check OPENAI_API_KEY in Secrets.")
    except RateLimitError:
        raise AIError("OpenAI rate limit or quota reached. Check your billing/usage and try again shortly.")
    except APIConnectionError:
        raise AIError("Could not reach OpenAI. Check the connection and try again.")
    except Exception as exc:
        raise AIError(f"AI request failed: {exc}")


RULES = """You are PropDoc AI, a careful document-reading assistant. The document can be of ANY type
(property, legal, educational, business, financial, identity, government or general) - never assume it is property-related.
Strict rules:
- Use ONLY information found in the provided document text. Never invent or guess information.
- If something is not in the document, write exactly "Not found".
- Mention page numbers (e.g. "Page 2") or a short supporting phrase whenever possible.
- Clearly separate FACTS stated in the document from POSSIBLE CONCERNS (label them "Fact" and "Possible concern").
- The text may come from OCR and contain errors; say so when text looks unclear instead of guessing.
- Never claim a document is authentic, genuine, forged or legally valid.
- Never give definitive legal or financial advice; suggest consulting a qualified professional where relevant.
Write in clear, simple language, using Markdown."""

ANALYSIS_SECTIONS = """## 1. Document Type
## 2. Simple Document Summary
## 3. Important Information
## 4. Names and Organizations
## 5. Important Dates and Reference Numbers
## 6. Amounts, Payments and Financial Details
## 7. Important Clauses and Conditions
## 8. Missing or Unclear Information
## 9. Possible Inconsistencies
## 10. Important Things to Remember"""

COMPARE_SECTIONS = """## 1. Document Type
## 2. Overall Summary
## 3. Matching Information
## 4. Differences Found  (confirmed differences only)
## 5. Missing Information
## 6. Possible Conflicts  (possible concerns, clearly labelled as not confirmed)
## 7. Important Changes
## 8. Final Comparison Summary"""


def extract_pdf(data, mode, lang, label):
    """Extract text per page; OCR scanned pages. Returns dict or raises ValueError."""
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        raise ValueError("This PDF could not be opened. The file may be corrupted.")
    if doc.needs_pass:
        raise ValueError("This PDF is password-protected. Remove the password and upload it again.")
    total = len(doc)
    n = min(total, MAX_PAGES)
    pages, ocr_pages, warnings = [], 0, []
    if total > MAX_PAGES:
        warnings.append(f"Only the first {MAX_PAGES} of {total} pages were processed.")
    bar = st.progress(0.0, text=f"Reading {label}…")
    for i in range(n):
        page = doc[i]
        text = page.get_text("text").strip() if not mode.startswith("Force") else ""
        needs_ocr = mode.startswith("Force") or (mode.startswith("Auto") and len(text) < 40)
        if needs_ocr:
            try:
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img, lang=lang).strip() or text
                ocr_pages += 1
            except pytesseract.TesseractNotFoundError:
                raise ValueError("Tesseract OCR is not installed on this server. On Streamlit Cloud, "
                                 "make sure packages.txt is in the repo, then reboot the app.")
            except Exception as exc:
                warnings.append(f"OCR failed on page {i + 1} (language data may be missing): {exc}")
        pages.append((i + 1, text))
        bar.progress((i + 1) / n, text=f"{label}: page {i + 1} of {n}" + (" (OCR)" if needs_ocr else ""))
    bar.empty()
    if not any(t.strip() for _, t in pages):
        raise ValueError("No text was found. Try 'Force OCR on all pages' or a different OCR language.")
    return {"pages": pages, "ocr": ocr_pages, "warnings": warnings, "total": total}


def run_extraction(uploaded, slot, label):
    mode, lang = st.session_state.get("ocr_mode", OCR_MODES[0]), OCR_LANGS[st.session_state.get("ocr_lang", "Marathi + English + Hindi")]
    try:
        result = extract_pdf(uploaded.getvalue(), mode, lang, label)
    except ValueError as exc:
        st.error(f"❌ {exc}")
        return
    result["name"] = uploaded.name
    result["hash"] = hashlib.md5(uploaded.getvalue()).hexdigest()
    st.session_state[slot] = result
    if slot == "doc1":
        st.session_state.update(analysis=None, chat=[], comparison=None)
    else:
        st.session_state["comparison"] = None
    for w in result["warnings"]:
        st.warning(w)
    st.success(f"✅ {uploaded.name} processed.")


def chips(items):
    st.markdown("".join(f'<span class="chip">{i}</span>' for i in items), unsafe_allow_html=True)


def require_doc():
    if not st.session_state.doc1:
        st.info("📁 Upload and extract a document in **Document Workspace** first.")
        return False
    return True


# ───────────────────────── Sidebar ─────────────────────────
init_state()
with st.sidebar:
    st.markdown('<p class="brand">📄 PropDoc AI</p><p class="brand-sub">Smart Document Intelligence</p>',
                unsafe_allow_html=True)
    st.session_state.setdefault("nav", NAV[0])
    for i, item in enumerate(NAV):
        if st.button(item, key=f"nav_{i}", type="primary" if st.session_state.nav == item else "secondary"):
            st.session_state.nav = item
            st.rerun()
    page = st.session_state.nav
    st.markdown("&nbsp;", unsafe_allow_html=True)
    with st.expander("⚙️ OCR settings"):
        st.selectbox("OCR language", list(OCR_LANGS), key="ocr_lang")
        st.selectbox("OCR mode", OCR_MODES, key="ocr_mode")
    st.caption("🟢 OpenAI connected" if get_secret("OPENAI_API_KEY") else "🔴 OpenAI key missing")

# ───────────────────────── Header ─────────────────────────
st.markdown("""
<div class="hero"><h1>📄 PropDoc AI</h1><h2>Smart Document Intelligence</h2>
<p>Upload, read, compare and understand any document with Artificial Intelligence.</p>
<div class="disclaimer"><b>Disclaimer:</b> PropDoc AI provides document-reading assistance only. It is not legal advice,
does not verify that any document is authentic or legally valid, and may make mistakes (especially with scanned text).
Consult a qualified professional before acting on important documents.</div></div>
""", unsafe_allow_html=True)

# ───────────────────────── Pages ─────────────────────────
if page == NAV[0]:
    with st.container(key="card_1"):
        st.subheader("Upload your PDF")
        up = st.file_uploader("Choose a PDF document", type=["pdf"], key="up1")
        if up and st.button("✨ Extract text", type="primary", key="ex1"):
            run_extraction(up, "doc1", "Document")
    d = st.session_state.doc1
    if d:
        with st.container(key="card_2"):
            st.subheader("Recognized text")
            chips([f"📄 {d['name']}", f"{len(d['pages'])} pages", f"{d['ocr']} OCR pages",
                   f"{sum(len(t) for _, t in d['pages']):,} characters"])
            text = pages_to_text(d["pages"])
            st.text_area("Extracted text", text, height=360)
            st.download_button("⬇️ Download as .txt", text, file_name=f"{d['name'].rsplit('.', 1)[0]}_text.txt",
                               mime="text/plain")

elif page == NAV[1]:
    if require_doc():
        d = st.session_state.doc1
        with st.container(key="card_3"):
            st.subheader("AI document analysis")
            chips([f"📄 {d['name']}"])
            lang = st.selectbox("Response language", list(AI_LANGS), key="an_lang")
            if st.button("🤖 Analyze document", type="primary"):
                ctx, cut = build_context(d["pages"])
                prompt = (f"Analyze the document below. Respond in {AI_LANGS[lang]}, using exactly these "
                          f"sections as Markdown headings (translate the headings):\n{ANALYSIS_SECTIONS}\n\n"
                          f"{'NOTE: the document was too long; only part of it is included.' if cut else ''}\n"
                          f"=== DOCUMENT TEXT ===\n{ctx}")
                with st.spinner("Analyzing your document…"):
                    try:
                        st.session_state.analysis = call_ai(RULES, prompt)
                    except AIError as exc:
                        st.error(f"❌ AI analysis failed. {exc}")
                if cut:
                    st.warning("Document is long – the AI analyzed a condensed portion of it.")
        if st.session_state.analysis:
            with st.container(key="card_4"):
                st.markdown(st.session_state.analysis)
                st.download_button("⬇️ Download analysis (.txt)", st.session_state.analysis,
                                   file_name="analysis_report.txt", mime="text/plain")

elif page == NAV[2]:
    if require_doc():
        d1 = st.session_state.doc1
        with st.container(key="card_5"):
            st.subheader("Compare with a second document")
            chips([f"Document A: {d1['name']}"])
            up2 = st.file_uploader("Upload the second PDF", type=["pdf"], key="up2")
            if up2 and st.button("✨ Extract second document", key="ex2"):
                run_extraction(up2, "doc2", "Second document")
            d2 = st.session_state.doc2
            if d2:
                chips([f"Document B: {d2['name']}", f"{len(d2['pages'])} pages"])
                lang = st.selectbox("Report language", list(AI_LANGS), key="cmp_lang")
                if st.button("🔍 Compare documents", type="primary"):
                    c1, cut1 = build_context(d1["pages"], MAX_CHARS // 2)
                    c2, cut2 = build_context(d2["pages"], MAX_CHARS // 2)
                    prompt = (f"Compare Document A and Document B. Respond in {AI_LANGS[lang]}, using exactly these "
                              f"sections as Markdown headings (translate the headings):\n{COMPARE_SECTIONS}\n\n"
                              "Compare names, dates, amounts, addresses, reference numbers, clauses and other important "
                              "details. Keep CONFIRMED differences separate from POSSIBLE concerns (e.g. OCR errors).\n\n"
                              f"=== DOCUMENT A ({d1['name']}) ===\n{c1}\n\n=== DOCUMENT B ({d2['name']}) ===\n{c2}")
                    with st.spinner("Comparing documents…"):
                        try:
                            st.session_state.comparison = call_ai(RULES, prompt)
                        except AIError as exc:
                            st.error(f"❌ Document comparison failed. {exc}")
                    if cut1 or cut2:
                        st.warning("One or both documents were long and were condensed before comparison.")
        if st.session_state.comparison:
            with st.container(key="card_6"):
                st.markdown(st.session_state.comparison)
                st.download_button("⬇️ Download comparison (.txt)", st.session_state.comparison,
                                   file_name="comparison_report.txt", mime="text/plain")

else:  # AI Assistant
    if require_doc():
        d = st.session_state.doc1
        with st.container(key="card_7"):
            st.subheader("Ask about your document")
            chips([f"📄 {d['name']}"])
            for m in st.session_state.chat:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])
            with st.form("ask_form", clear_on_submit=True):
                q = st.text_input("Your question", placeholder="e.g. What dates and amounts are mentioned?")
                lang = st.selectbox("Answer language", list(AI_LANGS), key="chat_lang")
                sent = st.form_submit_button("💬 Ask", type="primary")
            if sent and q.strip():
                ctx, _ = build_context(d["pages"], query=q)
                history = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in st.session_state.chat[-6:])
                prompt = (f"Answer the question using ONLY the document text. Respond in {AI_LANGS[lang]}. "
                          "If the answer is not in the text or the OCR is unclear, say so clearly.\n\n"
                          f"=== DOCUMENT TEXT ===\n{ctx}\n\n=== PREVIOUS CHAT ===\n{history or 'None'}\n\n"
                          f"=== QUESTION ===\n{q.strip()}")
                with st.spinner("Thinking…"):
                    try:
                        ans = call_ai(RULES, prompt)
                        st.session_state.chat += [{"role": "user", "content": q.strip()},
                                                  {"role": "assistant", "content": ans}]
                        st.rerun()
                    except AIError as exc:
                        st.error(f"❌ {exc}")
            if st.session_state.chat and st.button("🗑️ Clear chat"):
                st.session_state.chat = []
                st.rerun()
