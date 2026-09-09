"""MultiMeet Notes Generator."""

import gc
import html
import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from src.services.audio_processor import MeetingProcessor

load_dotenv()

APP_NAME = "MultiMeet Notes Generator"

LANGUAGE_NAMES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "hi": "Hindi", "zh": "Chinese",
    "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "ru": "Russian",
    "nl": "Dutch", "tr": "Turkish", "pl": "Polish", "uk": "Ukrainian",
    "vi": "Vietnamese", "id": "Indonesian",
}


def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🎤", layout="wide")
    _styles()

    if "current_result" not in st.session_state:
        st.session_state.current_result = None

    # ---------- Sidebar ----------
    with st.sidebar:
        st.markdown('<div class="sidebar-title">Configuration</div>', unsafe_allow_html=True)

        st.markdown('<div class="field-label">AssemblyAI API Key</div>', unsafe_allow_html=True)
        assemblyai_key = st.text_input(
            "AssemblyAI API Key", type="password", label_visibility="collapsed",
            help="Used for transcription, language detection, and speaker diarization."
        )

        st.markdown('<div class="field-label top-gap">OpenAI API Key</div>', unsafe_allow_html=True)
        openai_key = st.text_input(
            "OpenAI API Key", type="password", label_visibility="collapsed",
            help="Used for summaries and action-item analysis."
        )

        keys_ready = bool(assemblyai_key and openai_key)
        if keys_ready:
            st.markdown('<div class="side-status success">✅ API keys configured</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="side-status warning">⚠️ Add both API keys to start</div>', unsafe_allow_html=True)

        st.markdown('<div class="side-divider"></div>', unsafe_allow_html=True)
        if st.button("🗑️ Reset", use_container_width=True, key="reset_button"):
            st.session_state.current_result = None
            gc.collect()
            st.rerun()

    # ---------- Header ----------
    st.markdown(
        f"""
        <div class="hero">
            <h1>{APP_NAME}</h1>
            <p>Application for Multiple language meeting Notes and AI-powered notes</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.current_result:
        st.markdown('<div class="main-status success">✅ Meeting processed successfully</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="main-status info">Upload an audio file to get started</div>', unsafe_allow_html=True)

    # ---------- Audio Input ----------
    st.markdown('<div class="section-title">Audio Input</div>', unsafe_allow_html=True)
    st.markdown('<div class="field-label main-label">Choose your audio file</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose your audio file",
        type=["mp3", "wav", "m4a", "mp4", "webm", "flac"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.audio(uploaded_file)

        if not keys_ready:
            st.markdown(
                '<div class="main-status warning">⚠️ Add both API keys in the sidebar before processing.</div>',
                unsafe_allow_html=True,
            )
        elif st.button("Start Processing", type="primary"):
            if len(assemblyai_key.strip()) < 20 or len(openai_key.strip()) < 20:
                st.markdown('<div class="main-status error">❌ Invalid API key format.</div>', unsafe_allow_html=True)
            else:
                result = _process_audio(uploaded_file, assemblyai_key, openai_key)
                if result:
                    st.session_state.current_result = result
                    st.rerun()

    # ---------- Results ----------
    if st.session_state.current_result:
        st.markdown('<div class="page-divider"></div>', unsafe_allow_html=True)
        _display_results(st.session_state.current_result)

    st.markdown('<div class="page-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="footer">{APP_NAME} • Powered by AssemblyAI</div>',
        unsafe_allow_html=True,
    )


def _display_results(result):
    language = _language_name(result.language)

    # Overview
    st.markdown('<div class="section-title blue">📌 Meeting Overview</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card"><span>Duration</span><strong>{result.duration // 60}m {result.duration % 60}s</strong></div>
            <div class="metric-card"><span>Speakers</span><strong>{len(result.speakers)}</strong></div>
            <div class="metric-card"><span>Action Items</span><strong>{len(result.action_items)}</strong></div>
            <div class="metric-card"><span>Detected Language</span><strong>{html.escape(language)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Summary
    st.markdown('<div class="section-title blue">📝 Meeting Summary</div>', unsafe_allow_html=True)
    st.markdown(result.summary if result.summary else "No meeting summary is available.")

    # Speakers
    st.markdown('<div class="section-title blue">👥 Speaker Diarization</div>', unsafe_allow_html=True)
    if not result.speakers:
        st.write("No speaker information available.")
    else:
        for speaker in result.speakers:
            speaking_time = f"{speaker.speaking_time // 60}m {speaker.speaking_time % 60}s"
            st.markdown(
                f'<div class="speaker-line"><strong>{html.escape(str(speaker.name))}</strong> '
                f'— {speaking_time} ({speaker.word_count} words)</div>',
                unsafe_allow_html=True,
            )
            speaker_segments = [s for s in result.segments if s.speaker_id == speaker.id]
            if speaker_segments:
                with st.expander(f"View all statements from {speaker.name}"):
                    for i, segment in enumerate(speaker_segments, 1):
                        timestamp = f"{segment.start_time // 60000:02d}:{segment.start_time // 1000 % 60:02d}"
                        st.markdown(f"**Statement {i}** ({timestamp})")
                        st.write(segment.text)
                        if segment.confidence < 0.7:
                            st.caption(f"Low confidence: {segment.confidence:.2f}")
            else:
                st.caption("No statements found.")

    # Action items
    st.markdown('<div class="section-title blue">✅ Action Items</div>', unsafe_allow_html=True)
    if not result.action_items:
        st.write("No action items were identified in this meeting.")
    else:
        for i, item in enumerate(result.action_items, 1):
            details = []
            if item.assignee:
                details.append(f"Assigned to: {html.escape(str(item.assignee))}")
            if item.due_date:
                details.append(f"Due: {html.escape(str(item.due_date))}")
            if item.priority:
                details.append(f"Priority: {html.escape(str(item.priority).title())}")
            detail_text = " • ".join(details)
            st.markdown(
                f"""
                <div class="action-card">
                    <div><strong>{i}.</strong> {html.escape(str(item.description))}</div>
                    {f'<small>{detail_text}</small>' if detail_text else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Transcript
    st.markdown('<div class="section-title blue">📄 Meeting Transcript</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="language-badge">🌐 Detected Audio Language: <strong>{html.escape(language)}</strong> '
        f'<span>({html.escape(str(result.language))})</span></div>',
        unsafe_allow_html=True,
    )

    c1, c2, _ = st.columns([1, 1, 4])
    with c1:
        show_timestamps = st.checkbox("Show timestamps", value=True)
    with c2:
        show_confidence = st.checkbox("Show confidence", value=False)

    transcript_parts = []
    for segment in result.segments:
        timestamp = f"{segment.start_time // 60000:02d}:{segment.start_time // 1000 % 60:02d}"
        meta = html.escape(str(segment.speaker_id))
        if show_timestamps:
            meta += f" ({timestamp})"
        if show_confidence:
            meta += f" [Confidence: {segment.confidence:.2f}]"
        transcript_parts.append(
            f'<div class="transcript-row"><strong>{meta}:</strong> {html.escape(segment.text)}</div>'
        )

    st.markdown(
        f'<div class="transcript-box">{"".join(transcript_parts)}</div>',
        unsafe_allow_html=True,
    )

    # Statistics
    total_words = result.total_words
    avg_confidence = result.avg_confidence
    unique_speakers = result.unique_speakers_count
    st.markdown('<div class="section-title blue">📊 Transcript Statistics</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card"><span>Total Segments</span><strong>{len(result.segments)}</strong></div>
            <div class="metric-card"><span>Total Words</span><strong>{total_words}</strong></div>
            <div class="metric-card"><span>Avg Confidence</span><strong>{avg_confidence:.2f}</strong></div>
            <div class="metric-card"><span>Unique Speakers</span><strong>{unique_speakers}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Export
    st.markdown('<div class="section-title blue">💾 Export Meeting Notes</div>', unsafe_allow_html=True)
    st.download_button(
        "📥 Download as Markdown",
        _generate_markdown(result),
        file_name=f"meeting_notes_{result.processed_at.strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown",
    )


def _styles():
    st.markdown(
        """
        <style>
        html { color-scheme: light !important; }
        .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stHeader"]{background:#fff!important;color:#182235!important}
        .block-container{max-width:1180px;padding-top:1.8rem;padding-bottom:2rem}
        [data-testid="stSidebar"],[data-testid="stSidebar"]>div{background:#F7F9FC!important}
        [data-testid="stSidebar"]{border-right:1px solid #E2E8F0!important}

        .sidebar-title{font-size:24px;font-weight:700;color:#182235;margin:12px 0 22px}
        .field-label{font-size:14px;font-weight:600;color:#334155!important;margin:4px 0 6px}
        .top-gap{margin-top:16px}.main-label{margin:2px 0 8px}.side-divider,.page-divider{height:1px;background:#E2E8F0;margin:24px 0}

        .hero{text-align:center;margin-bottom:20px}.hero h1{color:#1C59C3!important;font-size:42px;margin:0 0 8px}.hero p{color:#64748B!important;font-size:16px;margin:0}
        .section-title{color:#182235!important;font-size:28px;font-weight:700;margin:30px 0 14px}.section-title.blue{color:#1C59C3!important}
        .footer{text-align:center;color:#64748B!important;font-size:12px;margin-bottom:10px}

        .main-status,.side-status{border-radius:9px;font-weight:500}.main-status{padding:16px 18px;margin:16px 0 28px}.side-status{padding:12px 14px;margin-top:14px;font-size:14px}
        .info{background:#E8F3FF;color:#164E83!important}.success{background:#EAF7EE;color:#166534!important}.warning{background:#FFF7D6;color:#7A5700!important}.error{background:#FDECEC;color:#991B1B!important}

        [data-testid="stTextInput"] [data-baseweb="input"],[data-testid="stTextInput"] input,[data-testid="stTextInput"] button{background:#fff!important;color:#111827!important}
        [data-testid="stTextInput"] [data-baseweb="input"]{border:1px solid #94A3B8!important}
        [data-testid="stTextInput"] input{-webkit-text-fill-color:#111827!important}
        [data-testid="stTextInput"] svg{color:#475569!important;fill:#475569!important}

        [data-testid="stFileUploaderDropzone"]{background:#F8FAFC!important;border:1.5px dashed #94A3B8!important;border-radius:10px!important}
        [data-testid="stFileUploaderDropzone"] p,[data-testid="stFileUploaderDropzone"] small,[data-testid="stFileUploaderDropzone"] span{color:#334155!important}
        [data-testid="stFileUploaderDropzone"] button{background:#1C59C3!important;border-color:#1C59C3!important;color:#fff!important}
        [data-testid="stFileUploaderDropzone"] button *{color:#fff!important;-webkit-text-fill-color:#fff!important}

        [data-testid="stSidebar"] .stButton button{background:#2B2D36!important;border-color:#2B2D36!important;color:#fff!important}
        [data-testid="stSidebar"] .stButton button *{color:#fff!important;-webkit-text-fill-color:#fff!important}
        .stButton button[kind="primary"],[data-testid="stDownloadButton"] button{background:#1C59C3!important;border-color:#1C59C3!important;color:#fff!important}
        .stButton button[kind="primary"] *,[data-testid="stDownloadButton"] button *{color:#fff!important;-webkit-text-fill-color:#fff!important}

        [data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] h1,[data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,[data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,[data-testid="stMarkdownContainer"] h6{color:#182235!important}
        .hero h1,.section-title.blue{color:#1C59C3!important}
        [data-testid="stCheckbox"] label,[data-testid="stCheckbox"] p{color:#182235!important}
        [data-testid="stExpander"]{background:#fff!important;border:1px solid #E2E8F0!important;border-radius:8px!important}
        [data-testid="stExpander"] summary,[data-testid="stExpander"] summary:hover{background:#fff!important;color:#182235!important}
        [data-testid="stExpander"] summary p,[data-testid="stExpander"] summary span{color:#182235!important}

        .metric-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:8px 0 26px}
        .metric-card{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:16px}.metric-card span{display:block;color:#64748B!important;font-size:14px;margin-bottom:6px}.metric-card strong{display:block;color:#111827!important;font-size:25px}
        .speaker-line{color:#182235!important;margin:12px 0 6px;font-size:16px}.action-card{background:#F8FAFC;border:1px solid #E2E8F0;border-left:4px solid #1C59C3;border-radius:8px;padding:14px 16px;margin:10px 0;color:#182235!important}.action-card small{display:block;color:#64748B!important;margin-top:6px}
        .language-badge{display:inline-block;background:#EEF4FF;color:#1E3A8A!important;border-radius:8px;padding:9px 12px;margin:0 0 14px}.language-badge span{color:#64748B!important}
        .transcript-box{background:#F8FAFC;border:1px solid #CBD5E1;border-radius:10px;padding:18px;max-height:400px;overflow-y:auto;margin:14px 0 24px}.transcript-row{color:#334155!important;font-size:15px;line-height:1.6;margin-bottom:14px}.transcript-row strong{color:#182235!important}

        @media(max-width:800px){.metric-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.hero h1{font-size:32px}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _process_audio(uploaded_file, assemblyai_key, openai_key):
    temp_path = None
    try:
        suffix = "." + uploaded_file.name.rsplit(".", 1)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name

        processor = MeetingProcessor(
            assemblyai_api_key=assemblyai_key,
            openai_api_key=openai_key,
        )
        with st.spinner("Processing audio..."):
            return processor.process_meeting_audio(audio_file_path=temp_path)
    except Exception as error:
        st.markdown(
            f'<div class="main-status error">❌ Processing failed: {html.escape(str(error))}</div>',
            unsafe_allow_html=True,
        )
        return None
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def _language_name(code):
    if not code:
        return "Unknown"
    normalized = str(code).lower().replace("-", "_").split("_")[0]
    return LANGUAGE_NAMES.get(normalized, str(code).upper())


def _generate_markdown(result):
    text = f"# {result.title}\n\n**Detected Language:** {_language_name(result.language)} ({result.language})\n\n## Meeting Summary\n\n{result.summary}\n\n## Action Items\n\n"
    for item in result.action_items:
        text += f"- {item.description}\n"
    text += "\n## Full Transcript\n\n"
    for segment in result.segments:
        text += f"**{segment.speaker_id}:** {segment.text}\n\n"
    return text


if __name__ == "__main__":
    main()
