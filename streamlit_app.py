"""
streamlit_app.py
------------------
AI-Powered Voice Appointment Booking Agent — main Streamlit entry point.
Run with:
    streamlit run streamlit_app.py
"""

import html
import os
import streamlit as st
from dotenv import load_dotenv

from modules.utils import load_config, get_categories_for_business, get_logger
from modules.conversation_manager import ConversationManager
from modules.appointment_manager import AppointmentManager
from modules.speech_to_text import transcribe_audio
from modules.text_to_speech import synthesize_speech

load_dotenv()
logger = get_logger(__name__)

st.set_page_config(page_title="Voice Appointment Booking Agent", page_icon="🎙️", layout="wide")

# --------------------------------------------------------------------------- #
# Custom CSS
# --------------------------------------------------------------------------- #
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap');

:root {
  --bg-0:#070b1a; --bg-1:#0d1330; --glass:rgba(255,255,255,.055); --glass-b:rgba(255,255,255,.12);
  --text:#e8ecff; --muted:#9aa4d0; --accent:#7c6cff; --accent-2:#22d3ee; --ok:#34d399; --warn:#fbbf24; --err:#f87171;
  --radius:18px; --ease:cubic-bezier(.4,0,.2,1);
}
html, body, [class*="css"] { font-family:'Inter',sans-serif; }
.stApp {
  background: radial-gradient(900px 500px at 12% -8%, rgba(124,108,255,.28), transparent 60%),
              radial-gradient(800px 500px at 100% 0%, rgba(34,211,238,.16), transparent 55%),
              linear-gradient(180deg,var(--bg-1),var(--bg-0)) !important;
  color: var(--text);
}
header[data-testid="stHeader"] { background: transparent !important; }
.main .block-container { max-width:1180px; padding:1.5rem 1.5rem 3rem !important; }
.stApp, .stApp p, .stApp label, .stApp li, .stApp span, .stApp div { color: var(--text); }
h1,h2,h3,h4 { font-family:'Sora','Inter',sans-serif !important; color:#fff !important; letter-spacing:-.01em; }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
hr { border-color: var(--glass-b) !important; }

/* Sidebar */
[data-testid="stSidebar"] { background: rgba(9,13,34,.85) !important; border-right:1px solid var(--glass-b); backdrop-filter: blur(14px); }
[data-testid="stSidebar"] label p { color: var(--muted) !important; font-size:.75rem !important; font-weight:600 !important; text-transform:uppercase; letter-spacing:.07em; }
.brand { display:flex; align-items:center; gap:.7rem; padding:.2rem 0 1rem; border-bottom:1px solid var(--glass-b); margin-bottom:1rem; }
.brand-mark { width:38px; height:38px; border-radius:12px; display:grid; place-items:center; font-size:1.1rem;
  background:linear-gradient(135deg,var(--accent),var(--accent-2)); box-shadow:0 6px 18px rgba(124,108,255,.45), inset 0 1px 0 rgba(255,255,255,.35); }
.brand-name { font-family:'Sora',sans-serif; font-weight:700; font-size:1.05rem; color:#fff; line-height:1.1; }
.brand-sub { font-size:.72rem; color:var(--muted); }

/* Hero */
.hero { position:relative; border-radius:24px; padding:1.6rem 2rem; margin-bottom:1.4rem; overflow:hidden;
  background:linear-gradient(135deg,rgba(124,108,255,.28),rgba(34,211,238,.10)); border:1px solid var(--glass-b);
  box-shadow:0 20px 50px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.14); }
.hero h2 { margin:0 !important; font-size:clamp(1.4rem,3.4vw,2rem) !important; font-weight:800 !important;
  text-shadow:0 1px 0 rgba(255,255,255,.25), 0 6px 24px rgba(124,108,255,.55); }
.hero p { margin:.4rem 0 0; color:var(--muted); font-size:.95rem; }
.hero .chip { display:inline-block; margin-top:.8rem; padding:.2rem .7rem; border-radius:999px; font-size:.75rem; font-weight:600;
  background:rgba(255,255,255,.08); border:1px solid var(--glass-b); color:var(--text); }

/* Glass cards */
.glass { background:var(--glass); border:1px solid var(--glass-b); border-radius:var(--radius); padding:1.1rem 1.25rem;
  box-shadow:0 12px 32px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.08); backdrop-filter: blur(12px); }
.summary { background:linear-gradient(135deg,rgba(124,108,255,.18),rgba(34,211,238,.08)); border:1px solid rgba(124,108,255,.45);
  border-radius:var(--radius); padding:1.2rem 1.4rem; margin-bottom:1rem; box-shadow:0 14px 36px rgba(124,108,255,.18); }
.summary h4 { margin:0 0 .2rem !important; }
.summary-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:.75rem 1.5rem; margin-top:.9rem; }
.summary-item small { display:block; color:var(--muted); font-size:.7rem; text-transform:uppercase; letter-spacing:.07em; }
.summary-item span { font-weight:600; word-break:break-word; }
.badge { display:inline-block; padding:.2rem .75rem; border-radius:999px; font-size:.7rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  background:rgba(251,191,36,.15); color:var(--warn); border:1px solid rgba(251,191,36,.4); }

/* Voice orb */
.stage { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:1rem; padding:1.4rem 1rem 1.2rem; min-height:442px; }
.orb-wrap { position:relative; width:150px; height:150px; display:grid; place-items:center; perspective:600px; }
.orb { width:104px; height:104px; border-radius:50%; position:relative; transform-style:preserve-3d;
  background: radial-gradient(circle at 32% 28%, #fff 0, var(--orb-a) 18%, var(--orb-b) 62%, #0b1030 100%);
  box-shadow: 0 0 0 1px rgba(255,255,255,.18) inset, 0 18px 40px var(--orb-glow), 0 0 70px var(--orb-glow);
  animation: var(--orb-anim) var(--orb-dur) var(--ease) infinite; }
.orb::after { content:""; position:absolute; inset:-14px; border-radius:50%; border:2px solid var(--orb-glow); opacity:.0; animation: var(--ring-anim) 2s ease-out infinite; }
.state-idle      { --orb-a:#8b8fff; --orb-b:#4b3fd1; --orb-glow:rgba(124,108,255,.55); --orb-anim:float; --orb-dur:5s; --ring-anim:none; }
.state-processing{ --orb-a:#67e8f9; --orb-b:#2563eb; --orb-glow:rgba(34,211,238,.6);  --orb-anim:spin3d; --orb-dur:1.6s; --ring-anim:ring; }
.state-speaking  { --orb-a:#a78bfa; --orb-b:#7c3aed; --orb-glow:rgba(167,139,250,.7); --orb-anim:pulse; --orb-dur:1s; --ring-anim:ring; }
.state-confirming{ --orb-a:#fde68a; --orb-b:#d97706; --orb-glow:rgba(251,191,36,.5);  --orb-anim:float; --orb-dur:3s; --ring-anim:ring; }
.state-confirmed { --orb-a:#6ee7b7; --orb-b:#059669; --orb-glow:rgba(52,211,153,.6);  --orb-anim:float; --orb-dur:4s; --ring-anim:none; }
.state-cancelled { --orb-a:#cbd5e1; --orb-b:#475569; --orb-glow:rgba(148,163,184,.4); --orb-anim:float; --orb-dur:6s; --ring-anim:none; }
@keyframes float  { 0%,100%{transform:translateY(0) rotateX(0)} 50%{transform:translateY(-8px) rotateX(8deg)} }
@keyframes pulse  { 0%,100%{transform:scale(1)} 50%{transform:scale(1.1)} }
@keyframes spin3d { from{transform:rotateY(0)} to{transform:rotateY(360deg)} }
@keyframes ring   { 0%{transform:scale(.85);opacity:.7} 100%{transform:scale(1.5);opacity:0} }
.wave { display:flex; align-items:center; justify-content:center; gap:5px; height:44px; }
.wave i { width:5px; height:10px; border-radius:3px; background:linear-gradient(var(--accent-2),var(--accent)); opacity:.55; }
.wave-host.state-speaking .wave i, .wave-host.state-processing .wave i { opacity:1; animation: bar 1s ease-in-out infinite; }
.wave i:nth-child(2n){animation-delay:.12s!important} .wave i:nth-child(3n){animation-delay:.27s!important} .wave i:nth-child(5n){animation-delay:.4s!important}
@keyframes bar { 0%,100%{height:10px} 50%{height:40px} }
.status-pill { display:inline-flex; align-items:center; gap:.5rem; padding:.3rem .9rem; border-radius:999px; font-weight:600; font-size:.82rem;
  background:rgba(255,255,255,.07); border:1px solid var(--glass-b); }
.status-pill .dot { width:8px; height:8px; border-radius:50%; background:var(--orb-glow); box-shadow:0 0 10px var(--orb-glow); }
.status-hint { color:var(--muted); font-size:.82rem; text-align:center; max-width:320px; }
.track { display:flex; flex-wrap:wrap; justify-content:center; gap:.35rem; margin-top:.2rem; }
.track span { font-size:.68rem; padding:.15rem .55rem; border-radius:999px; color:var(--muted); border:1px solid var(--glass-b); }
.track span.on { color:#fff; background:linear-gradient(135deg,var(--accent),#5b4bd8); border-color:transparent; }

/* Chat */
[data-testid="stChatMessage"] { background:transparent !important; padding:.25rem 0 !important; }
[data-testid="stChatMessageContent"] { background:var(--glass) !important; border:1px solid var(--glass-b) !important; border-radius:14px !important; padding:.7rem 1rem !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  background:linear-gradient(135deg,#5b4bd8,#7c6cff) !important; border:none !important; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius:var(--radius) !important; border-color:var(--glass-b) !important; background:rgba(255,255,255,.03); }

/* Buttons */
.stButton > button, .stFormSubmitButton > button { border-radius:12px !important; font-weight:600 !important; padding:.55rem 1.2rem !important;
  transition: transform .2s var(--ease), box-shadow .2s var(--ease), background .2s var(--ease) !important; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:linear-gradient(135deg,#6d5bff,#8b7bff) !important; color:#fff !important; border:none !important;
  box-shadow:0 8px 22px rgba(124,108,255,.4), inset 0 1px 0 rgba(255,255,255,.3) !important; }
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover { transform:translateY(-2px); box-shadow:0 12px 28px rgba(124,108,255,.55) !important; }
.stButton > button:not([kind="primary"]) { background:var(--glass) !important; color:var(--text) !important; border:1px solid var(--glass-b) !important; }
.stButton > button:not([kind="primary"]):hover { background:rgba(255,255,255,.12) !important; transform:translateY(-1px); }
.stButton > button:focus-visible, input:focus-visible { outline:2px solid var(--accent-2) !important; outline-offset:2px; }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input { border-radius:12px !important; background:rgba(255,255,255,.06) !important; color:var(--text) !important;
  border:1px solid var(--glass-b) !important; }
.stTextInput input:focus, .stNumberInput input:focus { border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(124,108,255,.25) !important; }
[data-baseweb="select"] > div { background:rgba(255,255,255,.06) !important; border-radius:12px !important; border-color:var(--glass-b) !important; }
[data-testid="stAudioInput"] { border-radius:14px !important; border:1px dashed rgba(124,108,255,.6) !important; background:rgba(124,108,255,.08) !important; padding:.5rem !important; }
[data-testid="stForm"] { background:var(--glass) !important; border:1px solid var(--glass-b) !important; border-radius:var(--radius) !important; }

/* Metrics / tables / tabs */
[data-testid="stMetric"] { background:var(--glass); border:1px solid var(--glass-b); border-radius:var(--radius); padding:1.1rem 1.3rem;
  box-shadow:0 12px 30px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.08); transition:transform .2s var(--ease); }
[data-testid="stMetric"]:hover { transform:translateY(-3px); }
[data-testid="stMetricValue"] { font-family:'Sora',sans-serif; color:#fff !important; }
[data-testid="stMetricLabel"] p { color:var(--muted) !important; font-weight:600; text-transform:uppercase; letter-spacing:.06em; font-size:.75rem; }
[data-testid="stDataFrame"] { border-radius:14px; overflow:hidden; border:1px solid var(--glass-b); }
.stTabs [data-baseweb="tab-list"] { background:var(--glass); border-radius:12px; padding:4px; gap:4px; border:1px solid var(--glass-b); }
.stTabs [data-baseweb="tab"] { border-radius:9px; font-weight:600; color:var(--muted); }
.stTabs [aria-selected="true"] { background:rgba(124,108,255,.3) !important; color:#fff !important; }
.stTabs [data-baseweb="tab-highlight"] { display:none; }
[data-testid="stAlert"] { border-radius:14px; border:1px solid var(--glass-b); }

/* Input visibility: readable in both light and dark browser modes */
[data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"], [data-testid="stTextAreaRootElement"] { background:#141b3d !important; border:1px solid var(--glass-b) !important; border-radius:12px !important; }
[data-testid="stTextInputRootElement"]:focus-within, [data-testid="stNumberInputContainer"]:focus-within { border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(124,108,255,.25) !important; }
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"] { background:rgba(255,255,255,.08) !important; border-radius:12px !important; border-color:var(--glass-b) !important; }
.stTextInput input, .stNumberInput input, .stTextArea textarea { background:transparent !important; color:#fff !important; -webkit-text-fill-color:#fff !important; caret-color:var(--accent-2) !important; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color:var(--muted) !important; -webkit-text-fill-color:var(--muted) !important; opacity:1; }
.stNumberInput button { background:rgba(255,255,255,.08) !important; color:#fff !important; }
[data-baseweb="select"] * { color:var(--text) !important; }
[data-baseweb="popover"] ul, [data-baseweb="menu"] { background:#141b3d !important; }
[data-baseweb="popover"] li { color:var(--text) !important; }

[data-testid="stSelectbox"] [data-baseweb="select"] > div { background:#141b3d !important; border:1px solid var(--glass-b) !important; }
[data-testid="stAudioInput"] > div { background:#141b3d !important; border-radius:12px !important; }
[data-testid="stAudioInput"] canvas { opacity:1 !important; }
[data-testid="stAudioInputWaveformTimeCode"] { background:transparent !important; color:var(--text) !important; font-weight:600; }
[data-testid="stAudioInput"] button, [data-testid="stAudioInput"] svg { color:#c7cdff !important; }
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] { background:linear-gradient(135deg,#6d5bff,#8b7bff) !important; color:#fff !important; border:none !important; border-radius:12px !important; box-shadow:0 8px 22px rgba(124,108,255,.4), inset 0 1px 0 rgba(255,255,255,.3) !important; }
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"] { background:var(--glass) !important; color:var(--text) !important; border:1px solid var(--glass-b) !important; border-radius:12px !important; }

/* Footer */
.app-footer { margin-top:2.5rem; text-align:center; color:var(--muted); font-size:.75rem; }

/* Responsive */
@media (max-width: 768px) {
  .main .block-container { padding:1rem .75rem 2rem !important; }
  .hero { padding:1.2rem 1.1rem; border-radius:18px; }
  .orb-wrap { width:130px; height:130px; } .orb { width:88px; height:88px; }
}
@media (prefers-reduced-motion: reduce) { .orb, .orb::after, .wave i { animation:none !important; } }
html, body, .stApp { overflow-x:hidden; }
</style>
""", unsafe_allow_html=True)

# The mic recorder draws its icon/waveform from Streamlit's own theme. If that theme is
# not dark (e.g. .streamlit/config.toml was not found because `streamlit run` was started
# from another folder), use a light recorder card so everything stays readable.
_LIGHT_RECORDER_CSS = """
[data-testid="stAudioInput"] > div { background:#eef0ff !important; }
[data-testid="stAudioInputWaveformTimeCode"] { color:#1e1b4b !important; }
[data-testid="stAudioInput"] button, [data-testid="stAudioInput"] svg { color:#4338ca !important; }
"""
_theme_base = st.get_option("theme.base")
if _theme_base == "light":
    st.markdown(f"<style>{_LIGHT_RECORDER_CSS}</style>", unsafe_allow_html=True)
elif _theme_base is None:  # theme follows the browser / OS preference
    st.markdown(
        f"<style>@media (prefers-color-scheme: light) {{{_LIGHT_RECORDER_CSS}}}</style>",
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------------- #
# Config & managers
# --------------------------------------------------------------------------- #
try:
    CONFIG = load_config()
except (FileNotFoundError, ValueError) as exc:
    logger.error("Could not load configuration: %s", exc)
    st.error("The application is not configured correctly. Please contact the administrator.")
    st.stop()

APPOINTMENT_MANAGER = AppointmentManager(CONFIG)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_manager" not in st.session_state:
    st.session_state.conversation_manager = None
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None
if "voice_reply_enabled" not in st.session_state:
    st.session_state.voice_reply_enabled = True
if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def start_new_conversation(business_type: str):
    manager = ConversationManager(CONFIG, business_type)
    st.session_state.conversation_manager = manager
    greeting = manager.greeting_message()
    st.session_state.messages = [{"role": "assistant", "text": greeting}]
    st.session_state.last_audio_id = None
    speak_if_enabled(greeting)


def push_message(role: str, text: str):
    st.session_state.messages.append({"role": role, "text": text})


def speak_if_enabled(text: str):
    if not st.session_state.voice_reply_enabled:
        st.session_state.pending_audio = None
        return
    audio_path = synthesize_speech(text)
    st.session_state.pending_audio = audio_path


ORB_STATES = {
    "idle":       ("Ready", "Tap the mic or type a reply to continue."),
    "processing": ("Processing", "Understanding your response…"),
    "speaking":   ("Speaking", "The assistant is replying."),
    "confirming": ("Awaiting confirmation", "Review your details below."),
    "confirmed":  ("Booking confirmed", "Your appointment has been saved."),
    "cancelled":  ("Cancelled", "Start a new booking any time."),
}
TRACK_ORDER = ["idle", "processing", "speaking", "confirming", "confirmed"]


def orb_html(state_key: str) -> str:
    """Pure-CSS assistant visualisation (presentation only, no audio data needed)."""
    label, hint = ORB_STATES[state_key]
    track = "".join(
        f'<span class="{"on" if k == state_key else ""}">{ORB_STATES[k][0].split()[0]}</span>'
        for k in TRACK_ORDER
    )
    bars = "<i></i>" * 17
    return (
        f'<div class="glass stage" role="status" aria-live="polite">'
        f'<div class="orb-wrap"><div class="orb state-{state_key}"></div>'
        f'</div>'
        f'<div class="state-{state_key}"><span class="status-pill"><span class="dot"></span>{label}</span></div>'
        f'<div class="state-{state_key} wave-host" style="width:100%"><div class="wave">{bars}</div></div>'
        f'<div class="status-hint">{hint}</div><div class="track">{track}</div></div>'
    )


def current_orb_state(manager) -> str:
    if manager.state == manager.STATE_DONE:
        return "confirmed"
    if manager.state == manager.STATE_CANCELLED:
        return "cancelled"
    if manager.state == manager.STATE_CONFIRMING:
        return "confirming"
    if st.session_state.pending_audio:
        return "speaking"
    return "idle"


def process_user_text(user_text: str):
    manager: ConversationManager = st.session_state.conversation_manager
    if manager is None:
        return
    push_message("user", user_text)
    try:
        result = manager.handle_message(user_text)
    except Exception as exc:  # noqa: BLE001
        logger.error("Conversation handling failed: %s", exc)
        push_message("assistant", "Something went wrong. Please try again.")
        return
    if result["done"]:
        try:
            appointment_id = APPOINTMENT_MANAGER.book_appointment(result["appointment"])
            success_text = manager.render_message("success_message", appointment_id=appointment_id)
        except Exception as exc:
            logger.error("Failed to save appointment: %s", exc)
            success_text = "We couldn't complete the booking. Please try again."
        push_message("assistant", success_text)
        speak_if_enabled(success_text)
    else:
        push_message("assistant", result["reply"])
        speak_if_enabled(result["reply"])


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
st.sidebar.markdown(
    '<div class="brand"><div class="brand-mark">🎙️</div><div><div class="brand-name">VoiceBook AI</div>'
    '<div class="brand-sub">Voice appointment agent</div></div></div>',
    unsafe_allow_html=True,
)

business_types = CONFIG.get("business_types", [])
selected_business_type = st.sidebar.selectbox("Business Type", business_types, index=0)

st.session_state.voice_reply_enabled = st.sidebar.toggle(
    "Speak responses (Text-to-Speech)",
    value=st.session_state.voice_reply_enabled
)

if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("GROQ_API_KEY"):
    st.sidebar.info("Running in rule-based mode (no AI key configured).")

if st.sidebar.button("↻  Start New Booking", use_container_width=True, type="primary"):
    start_new_conversation(selected_business_type)

PAGE_BOOK, PAGE_HISTORY, PAGE_MANAGE = "🎙️  Book Appointment", "📊  History & Dashboard", "🛠️  Manage Appointment"
page = st.sidebar.radio("Navigate", [PAGE_BOOK, PAGE_HISTORY, PAGE_MANAGE])

# Auto-start
if st.session_state.conversation_manager is None:
    start_new_conversation(selected_business_type)
elif st.session_state.conversation_manager.business_type != selected_business_type:
    start_new_conversation(selected_business_type)


# --------------------------------------------------------------------------- #
# Page 1 — Booking
# --------------------------------------------------------------------------- #
def render_booking_page():
    st.markdown(f"""
    <div class="hero">
        <h2>Book by voice, in seconds.</h2>
        <p>Speak or type — your AI assistant collects the details and confirms your appointment. Ask about hours, services, or pricing anytime.</p>
        <span class="chip">{html.escape(str(selected_business_type))}</span>
    </div>
    """, unsafe_allow_html=True)

    manager: ConversationManager = st.session_state.conversation_manager

    col_orb, col_chat = st.columns([1, 1.6], gap="large")
    orb_slot = col_orb.empty()
    orb_slot.markdown(orb_html(current_orb_state(manager)), unsafe_allow_html=True)

    # Chat transcript
    col_chat.markdown("### Conversation")
    chat_box = col_chat.container(height=380, border=True)
    with chat_box:
        if not st.session_state.messages:
            st.info("Start a conversation by speaking or typing below.")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["text"])

    st.markdown("")

    # Play the agent's latest voice reply (if any) with autoplay
    if st.session_state.pending_audio:
        st.audio(st.session_state.pending_audio, format="audio/wav", autoplay=True)

    st.markdown("")
    if manager.state == manager.STATE_CONFIRMING:
        render_summary_card(manager.answers)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm appointment", type="primary", use_container_width=True):
                process_user_text("yes")
                st.rerun()
        with col2:
            if st.button("Edit details", use_container_width=True):
                process_user_text("no")
                st.rerun()

    elif manager.state in (manager.STATE_DONE, manager.STATE_CANCELLED):
        if manager.state == manager.STATE_DONE:
            st.success("Appointment booked successfully!")
        else:
            st.info("Booking cancelled. Click 'Start New Booking' to begin again.")

    else:
        col_voice, col_text = st.columns(2, gap="large")

        with col_voice:
            st.markdown("#### 🎤 Voice input")
            st.caption("Tap the mic and speak your response")
            audio_value = st.audio_input("Record your response")
            if audio_value is not None:
                audio_bytes = audio_value.getvalue()
                audio_id = hash(audio_bytes)
                if audio_id != st.session_state.last_audio_id:
                    st.session_state.last_audio_id = audio_id
                    orb_slot.markdown(orb_html("processing"), unsafe_allow_html=True)
                    with st.spinner("Transcribing…"):
                        ok, text_or_error = transcribe_audio(audio_bytes)
                    if ok:
                        process_user_text(text_or_error)
                        st.rerun()
                    else:
                        st.error(text_or_error)

        with col_text:
            st.markdown("#### ⌨️ Type a response")
            st.caption("Prefer typing? Use the box below")
            with st.form(key="text_input_form", clear_on_submit=True):
                text_value = st.text_input(
                    "Your message",
                    placeholder="Type here and press Enter...",
                    label_visibility="collapsed"
                )
                submitted = st.form_submit_button("Send Message →", use_container_width=True, type="primary")
            if submitted:
                if text_value.strip() == "":
                    st.warning("Please enter a message.")
                else:
                    process_user_text(text_value)
                    st.rerun()


def render_summary_card(answers: dict):
    def item(label: str, key: str) -> str:
        value = html.escape(str(answers.get(key, "-")))
        return f'<div class="summary-item"><small>{label}</small><span>{value}</span></div>'

    st.markdown(
        '<div class="summary"><h4>Appointment summary</h4><span class="badge">Please review &amp; confirm</span>'
        '<div class="summary-grid">'
        + item("Business", "business_type") + item("Category", "category") + item("Name", "full_name")
        + item("Phone", "phone") + item("Date", "appointment_date") + item("Time", "appointment_time")
        + item("Purpose", "purpose")
        + '</div></div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Page 2 — History & Dashboard
# --------------------------------------------------------------------------- #
def render_history_page():
    st.markdown("""
    <div class="hero"><h2>History &amp; dashboard</h2>
    <p>View all bookings, metrics, and appointment records.</p></div>
    """, unsafe_allow_html=True)

    scope = st.radio(
        "Show appointments for:",
        ["All Businesses", selected_business_type],
        horizontal=True
    )
    filter_type = None if scope == "All Businesses" else selected_business_type

    try:
        metrics = APPOINTMENT_MANAGER.get_metrics(filter_type)
        history = APPOINTMENT_MANAGER.get_history(filter_type)
    except Exception as exc:
        logger.error("Could not load appointment data: %s", exc)
        st.error("We couldn't load your appointments right now. Please try again.")
        return

    st.markdown("")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total appointments", metrics["total"])
    m2.metric("Confirmed", metrics["confirmed"])
    m3.metric("Cancelled", metrics["cancelled"])

    st.markdown("---")
    st.markdown("### All appointments")
    if history:
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.info("No appointments yet. Book one from the Booking page!")


# --------------------------------------------------------------------------- #
# Page 3 — Manage
# --------------------------------------------------------------------------- #
def render_manage_page():
    st.markdown("""
    <div class="hero"><h2>Manage appointments</h2>
    <p>Reschedule or cancel an existing appointment by ID.</p></div>
    """, unsafe_allow_html=True)

    st.markdown("### Appointment ID")
    appointment_id = st.number_input(
        "Enter the Appointment ID (find it in History page)",
        min_value=1, step=1,
        label_visibility="visible"
    )

    st.markdown("")
    tab1, tab2 = st.tabs(["📅 Reschedule Appointment", "🗑️ Cancel Appointment"])

    with tab1:
        st.markdown("#### Enter New Schedule")
        col1, col2 = st.columns(2)
        with col1:
            new_date = st.text_input(
                "📅 New Date",
                placeholder="e.g. 2026-07-15 or 15th July",
                key="resched_date"
            )
        with col2:
            new_time = st.text_input(
                "🕐 New Time",
                placeholder="e.g. 3 PM or 15:00",
                key="resched_time"
            )
        st.markdown("")
        if st.button("🔄 Reschedule Appointment", type="primary", use_container_width=True):
            if not new_date.strip() or not new_time.strip():
                st.warning("Please provide both a new date and a new time.")
            else:
                ok, result = APPOINTMENT_MANAGER.reschedule_appointment(
                    int(appointment_id), new_date, new_time
                )
                if ok:
                    st.success(
                        f"✅ Appointment #{int(appointment_id)} rescheduled to "
                        f"**{result['appointment_date']}** at **{result['appointment_time']}**."
                    )
                else:
                    st.error(result if isinstance(result, str) else "We couldn't reschedule this appointment.")

    with tab2:
        st.markdown("#### Cancel Appointment")
        st.warning(
            "⚠️ **Warning:** This action cannot be undone. "
            "The appointment will be permanently marked as CANCELLED."
        )
        st.markdown("")
        if st.button("🗑️ Cancel This Appointment", type="primary", use_container_width=True):
            ok, message = APPOINTMENT_MANAGER.cancel_appointment(int(appointment_id))
            if ok:
                st.success(f"✅ {message}")
            else:
                st.error(message)


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
try:
    if page == PAGE_BOOK:
        render_booking_page()
    elif page == PAGE_HISTORY:
        render_history_page()
    else:
        render_manage_page()
except Exception as exc:  # noqa: BLE001 - never show a traceback to end users
    logger.exception("Unhandled UI error: %s", exc)
    st.error("Something went wrong. Please try again.")

st.markdown('<div class="app-footer">VoiceBook AI · Voice appointment booking</div>', unsafe_allow_html=True)
