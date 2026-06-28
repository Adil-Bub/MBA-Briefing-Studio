import streamlit as st
import os
import sys
import logging
import traceback
import time
from google import genai
from google.genai import types
from schema import DailyBriefingSchema

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  [%(levelname)-8s]  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
log = logging.getLogger("mba_briefing")
log.info("=" * 60)
log.info("MBA Briefing Studio — app boot")
log.info("Python %s", sys.version.split()[0])
log.info("=" * 60)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MBA Briefing Studio",
    page_icon="📰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

  /* ── Global reset & dark base ── */
  html, body, [class*="css"] {
    font-family: 'Source Serif 4', Georgia, serif !important;
    background: #0F0E0C !important;
    color: #E8E2D9;
  }
  .stApp { background: #0F0E0C !important; }
  .block-container {
    padding-top: 0 !important;
    padding-bottom: 6rem;
    max-width: 800px;
  }
  #MainMenu, footer, header { visibility: hidden; }

  /* ── Sticky progress bar ── */
  .sticky-progress {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 9999;
    background: #1A1814;
    border-bottom: 1px solid #2E2B26;
    padding: 0.6rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.5);
  }
  .sticky-label {
    font-family: 'Source Serif 4', Georgia, serif !important;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #7A7060;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .sticky-track {
    flex: 1;
    height: 5px;
    background: #2E2B26;
    border-radius: 100px;
    overflow: hidden;
  }
  .sticky-fill {
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, #C8972A, #E8B84B);
    transition: width 0.6s cubic-bezier(.4,0,.2,1);
  }
  .sticky-count {
    font-family: 'Source Serif 4', Georgia, serif !important;
    font-size: 0.75rem;
    font-weight: 600;
    color: #E8B84B;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .sticky-dots {
    display: flex;
    gap: 4px;
    flex-shrink: 0;
  }
  .sdot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #2E2B26;
    border: 1px solid #3E3B36;
    display: inline-block;
  }
  .sdot.done { background: #E8B84B; border-color: #C8972A; }

  /* ── Spacer so content clears sticky bar ── */
  .progress-spacer { height: 44px; }

  /* ── Masthead ── */
  .masthead {
    border-bottom: 3px double #3E3B36;
    margin-bottom: 1.5rem;
    padding: 2rem 0 1.25rem;
    text-align: center;
  }
  .masthead-eyebrow,
  .masthead-title,
  .masthead-dateline {
    font-family: 'Source Serif 4', Georgia, serif !important;
  }
  .masthead-eyebrow {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #7A7060;
    margin-bottom: 0.5rem;
  }
  .masthead-title {
    font-size: clamp(2rem, 6vw, 3.2rem);
    font-weight: 700;
    color: #F0EAE0;
    line-height: 1.05;
    letter-spacing: -0.5px;
    margin: 0 0 0.5rem;
  }
  .masthead-rule {
    border: none;
    border-top: 1px solid #3E3B36;
    margin: 0.75rem auto;
    width: 100%;
    max-width: 100%;
  }
  .masthead-dateline {
    font-size: 0.72rem;
    color: #7A7060;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  /* ── Newspaper nameplate (output page) ── */
  .nameplate {
    background: #1A1814;
    border: 1px solid #2E2B26;
    border-radius: 10px;
    padding: 1.1rem 1.5rem;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }
  .nameplate-pub {
    font-family: 'Libre Baskerville', serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #F0EAE0;
    margin: 0;
  }
  .nameplate-meta {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    align-items: center;
  }
  .nameplate-pill {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    background: #2E2B26;
    color: #A89E8A;
    padding: 0.25rem 0.65rem;
    border-radius: 100px;
    border: 1px solid #3E3B36;
  }

  /* ── Section label ── */
  .section-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #7A7060;
    margin: 2rem 0 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }
  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #2E2B26;
  }

  /* ── Cards (dark) ── */
  .briefing-card {
    background: #181612;
    border: 1px solid #2E2B26;
    border-radius: 10px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.25s ease, background 0.25s ease, filter 0.25s ease, opacity 0.25s ease;
  }
  .briefing-card.read-card {
    border-color: #4A6741;
    background: #141A12;
    filter: grayscale(0.35);
    opacity: 0.88;
  }
  .view-card {
    background: #1E1A12;
    border: 1px solid #3E3520;
    border-radius: 10px;
    padding: 1.6rem 1.75rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.25s ease, background 0.25s ease, filter 0.25s ease, opacity 0.25s ease;
  }
  .view-card.read-card {
    border-color: #4A6741;
    background: #141A12;
    filter: grayscale(0.35);
    opacity: 0.88;
  }
  .concept-card {
    background: #16141E;
    border: 1px solid #322E46;
    border-radius: 10px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.25s ease, background 0.25s ease, filter 0.25s ease, opacity 0.25s ease;
  }
  .concept-card.read-card {
    border-color: #4A6741;
    background: #141A12;
    filter: grayscale(0.35);
    opacity: 0.88;
  }
  .pulse-card {
    background: #1A1710;
    border: 1px solid #3A3420;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: border-color 0.25s ease, background 0.25s ease, filter 0.25s ease, opacity 0.25s ease;
  }
  .pulse-card.read-card {
    border-color: #4A6741;
    background: #141A12;
    filter: grayscale(0.35);
    opacity: 0.88;
  }

  /* ── Card internals ── */
  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 0.7rem;
  }
  .card-tag {
    font-family: 'Inter', sans-serif;
    font-size: 0.63rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.22rem 0.6rem;
    border-radius: 100px;
    white-space: nowrap;
  }
  .tag-macro  { background: #0D2035; color: #5CA3D4; border: 1px solid #1A3A55; }
  .tag-micro  { background: #251A08; color: #D4A035; border: 1px solid #453010; }
  .tag-concept{ background: #1A1030; color: #9B78D4; border: 1px solid #2E1E55; }
  .tag-view   { background: #0D2015; color: #52B86A; border: 1px solid #1A4025; }
  .tag-pulse  { background: #251A08; color: #E8B84B; border: 1px solid #453010; }
  .read-badge {
    font-family: 'Inter', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    color: #52B86A;
    background: #0D2015;
    border: 1px solid #1A4025;
    padding: 0.2rem 0.55rem;
    border-radius: 100px;
    white-space: nowrap;
  }
  .card-headline {
    font-family: 'Libre Baskerville', serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #F0EAE0;
    line-height: 1.4;
    margin: 0 0 0.2rem;
  }
  .card-body-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.63rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #5A5448;
    margin: 0.8rem 0 0.25rem;
  }
  .card-body-text {
    font-family: 'Source Serif 4', serif;
    font-size: 0.92rem;
    color: #B8B0A2;
    line-height: 1.7;
    margin: 0;
  }
  .concept-name {
    font-family: 'Libre Baskerville', serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #C4A8F0;
    margin: 0 0 0.5rem;
  }
  .concept-card.read-card .concept-name { color: #52B86A; }
  .concept-body {
    font-family: 'Source Serif 4', serif;
    font-size: 0.92rem;
    color: #A89EC8;
    line-height: 1.7;
    margin: 0;
  }
  .concept-card.read-card .concept-body { color: #8AB89A; }
  .pulse-icon { font-size: 1.4rem; flex-shrink: 0; }
  .pulse-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.63rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #C8972A;
    margin: 0 0 0.2rem;
  }
  .pulse-text {
    font-family: 'Source Serif 4', serif;
    font-size: 0.9rem;
    color: #C8B890;
    line-height: 1.5;
    margin: 0;
  }

  /* ── Streamlit button overrides ── */
  .stButton > button {
    font-family: 'Inter', sans-serif !important;
    background: transparent !important;
    border: 1px solid #3E3B36 !important;
    border-radius: 6px !important;
    color: #A89E8A !important;
    font-size: 0.77rem !important;
    font-weight: 500 !important;
    padding: 0.35rem 0.85rem !important;
    transition: all 0.15s ease !important;
  }
  .stButton > button:hover {
    background: #2E2B26 !important;
    border-color: #5A5448 !important;
    color: #E8E2D9 !important;
  }
  .stButton > button[kind="primary"] {
    background: #C8972A !important;
    border-color: #C8972A !important;
    color: #0F0E0C !important;
    width: 100% !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 0.65rem 1.5rem !important;
    border-radius: 8px !important;
    letter-spacing: 0.02em !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: #E8B84B !important;
    border-color: #E8B84B !important;
  }

  /* ── File uploader ── */
  [data-testid="stFileUploader"] {
    background: #181612 !important;
    border: 1.5px dashed #3E3B36 !important;
    border-radius: 10px !important;
  }
  [data-testid="stFileUploader"] * { color: #A89E8A !important; }

  /* ── Completion banner ── */
  .completion-banner {
    text-align: center;
    padding: 2.5rem 1.5rem;
    margin-top: 2rem;
    background: #141A12;
    border: 1px solid #4A6741;
    border-radius: 12px;
  }
  .completion-banner p { margin: 0; }

  /* ── Responsive ── */
  @media (max-width: 600px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .masthead-title  { font-size: 2rem; }
    .briefing-card, .view-card, .concept-card { padding: 1.1rem 1.1rem; }
    .card-top { flex-direction: column; gap: 0.4rem; }
    .nameplate { flex-direction: column; gap: 0.5rem; }
  }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
for key, default in [("briefing", None), ("read_items", set()), ("total_items", 0)]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helpers ───────────────────────────────────────────────────────────────────
def mark_read(key):
    st.session_state.read_items = set(st.session_state.read_items) | {key}

def is_read(key):
    return key in st.session_state.read_items

def read_button(key, label="Mark as read"):
    if is_read(key):
        st.markdown('<span class="read-badge">✓ Read</span>', unsafe_allow_html=True)
    else:
        if st.button(label, key=f"btn_{key}"):
            mark_read(key)
            st.rerun()


def md_to_html(md: str) -> str:
  """Convert a small subset of Markdown to HTML.

  Tries to use the `markdown` package when available. Falls back to a
  lightweight converter that supports paragraphs and bullet lists so the
  `economic_view` field renders cleanly inside the styled card.
  """
  import markdown as _md
  return _md.markdown(md)

def sticky_progress():
    total = st.session_state.total_items
    done  = len(st.session_state.read_items)
    if total == 0:
        return
    pct  = int((done / total) * 100)
    dots = "".join(
        f'<span class="sdot {"done" if i < done else ""}"></span>'
        for i in range(total)
    )
    st.markdown(f"""
    <div class="sticky-progress">
      <span class="sticky-label">Progress</span>
      <div class="sticky-track"><div class="sticky-fill" style="width:{pct}%"></div></div>
      <div class="sticky-dots">{dots}</div>
      <span class="sticky-count">{done}/{total}</span>
    </div>
    <div class="progress-spacer"></div>
    """, unsafe_allow_html=True)

# ── Masthead (always shown) ───────────────────────────────────────────────────
briefing = st.session_state.briefing
st.markdown(f"""
<div class="masthead">
  <p class="masthead-eyebrow">AI-Powered Economic Synthesis</p>
  <h1 class="masthead-title">MBA Briefing Studio</h1>
  <p class="masthead-dateline">Your daily financial newspaper, structured for MBA case prep</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD PAGE
# ══════════════════════════════════════════════════════════════════════════════
if briefing is None:
    st.markdown("""
    <p style="text-align:center;color:#7A7060;font-family:'Inter',sans-serif;
              font-size:0.85rem;margin-bottom:1.5rem;line-height:1.6;">
      Upload today's financial PDF for an instant, structured breakdown of macro themes, corporate shifts and key MBA concepts.
    </p>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop your newspaper PDF here",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.5rem;margin:0.75rem 0 1.25rem;
                    font-family:'Inter',sans-serif;font-size:0.82rem;color:#52B86A;font-weight:500;">
          <span>📄</span><span>{uploaded_file.name}</span>
          <span style="color:#5A5448;font-weight:400;">·</span>
          <span style="color:#5A5448;">{uploaded_file.size/1024:.0f} KB</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Generate today's briefing", type="primary"):
            log.info("━" * 50)
            log.info("GENERATE button clicked")
            log.info("File: %s  (%d bytes)", uploaded_file.name, uploaded_file.size)

            status_box = st.empty()
            error_box  = st.empty()
            t0 = time.time()

            def ui_status(icon, msg, detail=""):
                log.info("[UI] %s  %s", msg, detail)
                detail_html = (
                    f'<p style="font-family:Inter,sans-serif;font-size:0.75rem;'
                    f'color:#5A5448;margin:0.2rem 0 0;">{detail}</p>'
                ) if detail else ""
                status_box.markdown(f"""
                <div style="background:#181612;border:1px solid #2E2B26;border-radius:8px;
                            padding:1rem 1.25rem;margin:0.5rem 0;">
                  <p style="font-family:'Inter',sans-serif;font-size:0.88rem;font-weight:500;
                             color:#E8E2D9;margin:0;">{icon} {msg}</p>
                  {detail_html}
                </div>
                """, unsafe_allow_html=True)

            try:
                ui_status("📄", "Reading PDF…", f"{uploaded_file.name} ({uploaded_file.size:,} bytes)")
                pdf_bytes = uploaded_file.getvalue()
                log.debug("PDF bytes: %d", len(pdf_bytes))
                if len(pdf_bytes) == 0:
                    raise ValueError("Uploaded file is empty (0 bytes). Please re-upload the PDF.")
                pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")

                ui_status("🔌", "Connecting to Gemini API…", "Initialising Vertex AI client")
                log.info("GOOGLE_CLOUD_PROJECT : %s", os.environ.get("GOOGLE_CLOUD_PROJECT","<not set>"))
                log.info("GOOGLE_CLOUD_REGION  : %s", os.environ.get("GOOGLE_CLOUD_REGION", os.environ.get("GOOGLE_CLOUD_LOCATION","<not set>")))
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                log.info("genai.Client OK")

                ui_status("✍️", "Building prompt…", "Composing system instruction and schema")
                system_instruction = (
                    "You are an Expert Economic Analyst and Briefing Agent for MBA students. "
                    "Analyse the provided daily financial newspaper PDF and map all data "
                    "precisely into the requested JSON schema. "
                    "Extract the newspaper's full publication name from the masthead (e.g. 'The Economic Times'). "
                    "Extract the city edition if visible (e.g. 'Mumbai Edition'). "
                    "Balance macroeconomics with firm-level microeconomics. "
                    "Explain complex terms simply. Be specific: use real company names, figures, and policy references."
                )

                ui_status("🤖", "Calling Gemini 2.5 Flash…",
                          "Sending PDF to model ~ usually 20-60 s for a full newspaper")
                log.info("Sending to gemini-2.5-flash …")
                t_api = time.time()

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[pdf_part, "Synthesise this newspaper into the structured output format."],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=DailyBriefingSchema,
                        temperature=0.1,
                    ),
                )

                log.info("Gemini responded in %.1f s", time.time() - t_api)
                raw_text = response.text
                log.debug("Raw length: %d chars", len(raw_text) if raw_text else 0)
                log.debug("Preview: %.300s", raw_text or "<empty>")

                if not raw_text or not raw_text.strip():
                    raise ValueError(
                        "Gemini returned an empty response. "
                        "Ensure the PDF is text-based (not a scanned image) and try again."
                    )

                ui_status("🔍", "Parsing structured output…", "Validating JSON against schema")
                log.info("Pydantic parse …")
                b = DailyBriefingSchema.model_validate_json(raw_text)
                log.info("Parse OK — newspaper: %s  date: %s  city: %s",
                         b.newspaper_name, b.edition_date, b.edition_city)
                log.info("  macro: %d  micro: %d  concept: %s",
                         len(b.macro_developments), len(b.micro_shifts), b.mba_concept_name)

                ui_status("✅", "Briefing ready!",
                          f"Completed in {time.time()-t0:.1f} s — {b.newspaper_name}, {b.edition_date}")

                st.session_state.briefing = b
                st.session_state.read_items = set()
                st.session_state.total_items = (
                    1 + 1 + len(b.macro_developments) + len(b.micro_shifts) + 1
                )
                log.info("total_items: %d", st.session_state.total_items)
                log.info("Pipeline complete ✓")
                log.info("━" * 50)
                time.sleep(0.5)
                st.rerun()

            except Exception as exc:
                log.error("━" * 50)
                log.error("PIPELINE FAILED after %.1f s", time.time()-t0)
                log.error("Type    : %s", type(exc).__name__)
                log.error("Message : %s", exc)
                log.error("Traceback:\n%s", traceback.format_exc())
                log.error("━" * 50)
                status_box.empty()
                error_box.markdown(f"""
                <div style="background:#1A0E0E;border:1px solid #5A2020;border-radius:8px;
                            padding:1.25rem 1.5rem;margin:0.5rem 0;">
                  <p style="font-family:'Inter',sans-serif;font-size:0.88rem;font-weight:600;
                             color:#E86A52;margin:0 0 0.5rem;">❌ {type(exc).__name__}</p>
                  <p style="font-family:'Source Serif 4',serif;font-size:0.85rem;
                             color:#C89090;margin:0 0 0.75rem;line-height:1.55;">{exc}</p>
                  <p style="font-family:'Inter',sans-serif;font-size:0.72rem;color:#5A5448;margin:0;">
                    Full traceback printed to console / Cloud Run logs.</p>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BRIEFING PAGE
# ══════════════════════════════════════════════════════════════════════════════
else:
    b = briefing

    # Sticky progress bar (fixed, always visible while scrolling)
    sticky_progress()

    # Newspaper nameplate
    st.markdown(f"""
    <div class="nameplate">
      <p class="nameplate-pub">📰 {b.newspaper_name}</p>
      <div class="nameplate-meta">
        <span class="nameplate-pill">📅 {b.edition_date}</span>
        <span class="nameplate-pill">📍 {b.edition_city}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Reset
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("↩ Reset"):
            st.session_state.briefing = None
            st.session_state.read_items = set()
            st.session_state.total_items = 0
            st.rerun()

    # ── Market Pulse ──────────────────────────────────────────────────────────
    PULSE_KEY = "market_pulse"
    rc = "read-card" if is_read(PULSE_KEY) else ""
    st.markdown(f"""
    <div class="pulse-card {rc}">
      <div class="pulse-icon">📊</div>
      <div>
        <p class="pulse-label">Market Pulse</p>
        <p class="pulse-text">{b.market_pulse}</p>
      </div>
    </div>
    """, unsafe_allow_html=True)
    read_button(PULSE_KEY, "Mark as read")

    # ── Economic View ─────────────────────────────────────────────────────────
    VIEW_KEY = "economic_view"
    st.markdown('<div class="section-label">The Big Picture</div>', unsafe_allow_html=True)
    rc   = "read-card" if is_read(VIEW_KEY) else ""
    badge = '<span class="read-badge">✓ Read</span>' if is_read(VIEW_KEY) else ""
    paras_html = md_to_html(b.economic_view)
    st.markdown(f"""
    <div class="view-card {rc}">
      <div class="card-top">
        <span class="card-tag tag-view">Today's Economic View</span>{badge}
      </div>
      <h2 class="card-headline" style="font-size:1.15rem;margin-bottom:1rem;">
        The overarching theme of the day
      </h2>
      <div class="view-body">{paras_html}</div>
    </div>
    """, unsafe_allow_html=True)
    read_button(VIEW_KEY)

    # ── Macro Developments ────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Macro & Policy</div>', unsafe_allow_html=True)
    for i, story in enumerate(b.macro_developments):
        key = f"macro_{i}"
        rc    = "read-card" if is_read(key) else ""
        badge = '<span class="read-badge">✓ Read</span>' if is_read(key) else ""
        st.markdown(f"""
        <div class="briefing-card {rc}">
          <div class="card-top">
            <span class="card-tag tag-macro">{story.tag}</span>{badge}
          </div>
          <h3 class="card-headline">{story.headline}</h3>
          <p class="card-body-label">Context</p>
          <p class="card-body-text">{story.context}</p>
          <p class="card-body-label">Why it matters</p>
          <p class="card-body-text">{story.impact}</p>
        </div>
        """, unsafe_allow_html=True)
        read_button(key)

    # ── Micro / Corporate ─────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Micro & Corporate Shifts</div>', unsafe_allow_html=True)
    for i, story in enumerate(b.micro_shifts):
        key = f"micro_{i}"
        rc    = "read-card" if is_read(key) else ""
        badge = '<span class="read-badge">✓ Read</span>' if is_read(key) else ""
        st.markdown(f"""
        <div class="briefing-card {rc}">
          <div class="card-top">
            <span class="card-tag tag-micro">{story.sector}</span>{badge}
          </div>
          <h3 class="card-headline">{story.headline}</h3>
          <p class="card-body-label">Economic Trend</p>
          <p class="card-body-text">{story.trend}</p>
        </div>
        """, unsafe_allow_html=True)
        read_button(key)

    # ── MBA Concept ───────────────────────────────────────────────────────────
    CONCEPT_KEY = "concept"
    st.markdown('<div class="section-label">MBA Concept of the Day</div>', unsafe_allow_html=True)
    rc    = "read-card" if is_read(CONCEPT_KEY) else ""
    badge = '<span class="read-badge">✓ Read</span>' if is_read(CONCEPT_KEY) else ""
    st.markdown(f"""
    <div class="concept-card {rc}">
      <div class="card-top">
        <span class="card-tag tag-concept">Core Concept</span>{badge}
      </div>
      <p class="concept-name">💡 {b.mba_concept_name}</p>
      <p class="concept-body">{b.mba_concept_definition}</p>
    </div>
    """, unsafe_allow_html=True)
    read_button(CONCEPT_KEY)

    # ── Completion ────────────────────────────────────────────────────────────
    all_done = len(st.session_state.read_items) == st.session_state.total_items
    if all_done:
        st.markdown("""
        <div class="completion-banner">
          <div style="font-size:2.2rem;margin-bottom:0.6rem;">🎓</div>
          <p style="font-family:'Libre Baskerville',serif;font-size:1.1rem;font-weight:700;
                    color:#F0EAE0;margin-bottom:0.3rem;">Edition complete.</p>
          <p style="font-family:'Source Serif 4',serif;font-size:0.88rem;color:#7A7060;">
            You've read everything for today. Come back tomorrow with the next edition.
          </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-top:3rem;padding-top:1.5rem;border-top:1px solid #2E2B26;">
      <p style="font-family:'Inter',sans-serif;font-size:0.65rem;color:#3E3B36;
                letter-spacing:0.1em;text-transform:uppercase;">
        MBA Briefing Studio · Powered by Gemini 2.5 Flash
      </p>
    </div>
    """, unsafe_allow_html=True)