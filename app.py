"""
app.py  –  NCERT Maths Topic Analyzer & Resource Finder
Simple Streamlit UI, no custom CSS.
Two modes:
  Auto Mode  – Upload PDF -> extract topics -> YouTube videos
  Ask Mode   – Type a topic/question -> RAG answer + YouTube videos
"""

import os
import json
import tempfile

import streamlit as st
from dotenv import load_dotenv

from pdf_loader import load_pdf, get_full_text, build_vectorstore, search_vectorstore
from topic_extractor import extract_topics, answer_with_context, topic_from_question
from youtube_fetcher import fetch_videos_for_topics, fetch_videos

load_dotenv()

st.set_page_config(page_title="NCERT Maths Analyzer", page_icon="📐")

# ── Session state ─────────────────────────────────────────────────────────────
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "topics_data" not in st.session_state:
    st.session_state.topics_data = []
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("📐 NCERT Maths Analyzer")

uploaded_file = st.sidebar.file_uploader("Upload NCERT PDF", type=["pdf"])

mode = st.sidebar.radio("Mode", ["📄 Auto – Extract Topics", "💬 Ask – RAG Search"])

st.sidebar.markdown("---")
st.sidebar.caption("API keys are loaded from the .env file.")

# ── Load PDF when uploaded ────────────────────────────────────────────────────
if uploaded_file and uploaded_file.name != st.session_state.pdf_name:
    with st.spinner("Reading PDF and building search index…"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        docs = load_pdf(tmp_path)
        st.session_state.full_text   = get_full_text(docs)
        st.session_state.vectorstore = build_vectorstore(docs)
        st.session_state.pdf_name    = uploaded_file.name
        st.session_state.topics_data = []
        os.unlink(tmp_path)

    st.sidebar.success(f"✓ Loaded: {uploaded_file.name}")


# ══════════════════════════════════════════════════════════════════════════════
# MODE 1 – AUTO
# ══════════════════════════════════════════════════════════════════════════════
if "Auto" in mode:
    st.title("📄 Topic Extractor")
    st.caption("Upload an NCERT PDF → LLaMA finds topics → YouTube videos fetched for each topic")

    if not uploaded_file:
        st.info("👈 Upload an NCERT Maths PDF from the sidebar to get started.")
        st.stop()

    col1, col2 = st.columns(2)
    max_topics       = col1.slider("Max topics to extract", 5, 30, 15)
    videos_per_topic = col2.selectbox("Videos per topic", [1, 2, 3], index=1)

    if st.button("🔍 Extract Topics & Find Videos", type="primary"):
        if not os.getenv("HUGGINGFACEHUB_API_TOKEN"):
            st.error("Please enter your HuggingFace token in the sidebar.")
            st.stop()

        with st.spinner("LLaMA is reading your PDF and extracting topics…"):
            topics = extract_topics(st.session_state.full_text)
            topics = topics[:max_topics]

        if not topics:
            st.error("Could not extract topics. Try a different PDF or check your HF token.")
            st.stop()

        st.success(f"✅ Found {len(topics)} topics!")

        if os.getenv("YOUTUBE_API_KEY"):
            with st.spinner("Fetching YouTube videos…"):
                topics_with_videos = fetch_videos_for_topics(topics, max_per_topic=videos_per_topic)
        else:
            st.warning("No YouTube API key — showing topics without videos.")
            topics_with_videos = [{**t, "videos": []} for t in topics]

        st.session_state.topics_data = topics_with_videos

    # ── Display results ────────────────────────────────────────────────────────
    if st.session_state.topics_data:
        # Download button
        st.download_button(
            "⬇ Download JSON",
            data=json.dumps(st.session_state.topics_data, indent=2),
            file_name="ncert_topics_resources.json",
            mime="application/json",
        )

        st.divider()

        # Group by chapter
        chapters: dict[str, list] = {}
        for item in st.session_state.topics_data:
            ch = item.get("chapter", "General")
            chapters.setdefault(ch, []).append(item)

        for chapter, items in chapters.items():
            st.subheader(f"📚 {chapter}")
            for item in items:
                with st.expander(f"📌 {item['topic']}"):
                    videos = item.get("videos", [])
                    if videos:
                        for v in videos:
                            if v.get("url"):
                                st.markdown(f"▶ [{v['title']}]({v['url']})  \n*{v.get('channel','')}*")
                    else:
                        st.caption("No videos found for this topic.")


# ══════════════════════════════════════════════════════════════════════════════
# MODE 2 – RAG
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.title("💬 Ask About a Topic")
    st.caption("Type a topic or question → AI searches your PDF and explains it → YouTube videos shown")

    if not uploaded_file:
        st.info("👈 Upload an NCERT Maths PDF first so the AI has context to answer from.")
        st.stop()

    question     = st.text_input("Your question or topic",
                                  placeholder="e.g. How to solve quadratic equations?")
    videos_count = st.selectbox("Videos to fetch", [2, 3, 5], index=1)

    if st.button("🔎 Search & Explain", type="primary"):
        if not question.strip():
            st.warning("Please enter a question or topic.")
            st.stop()
        if not os.getenv("HUGGINGFACEHUB_API_TOKEN"):
            st.error("Please enter your HuggingFace token in the sidebar.")
            st.stop()
        if st.session_state.vectorstore is None:
            st.error("PDF not indexed. Please re-upload the file.")
            st.stop()

        with st.spinner("Searching your PDF…"):
            context = search_vectorstore(st.session_state.vectorstore, question)

        with st.spinner("LLaMA is composing an explanation…"):
            answer = answer_with_context(question, context)

        st.subheader("🤖 AI Explanation")
        st.info(answer)

        with st.expander("📖 Relevant textbook excerpt"):
            st.text(context[:1200] + ("…" if len(context) > 1200 else ""))

        if os.getenv("YOUTUBE_API_KEY"):
            with st.spinner("Finding YouTube tutorials…"):
                search_topic = topic_from_question(question)
                videos = fetch_videos(search_topic, max_results=videos_count)

            st.subheader(f"🎥 Tutorials for: {search_topic}")
            for v in videos:
                col_img, col_text = st.columns([1, 3])
                if v.get("thumbnail"):
                    col_img.image(v["thumbnail"])
                col_text.markdown(f"**[{v['title']}]({v['url']})**")
                col_text.caption(v.get("channel", ""))
        else:
            st.warning("Add a YouTube API key in the sidebar to see tutorial videos.")
