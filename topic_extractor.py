"""
topic_extractor.py
Uses HuggingFace Inference API — model: HuggingFaceH4/zephyr-7b-beta
Faster than LLaMA, no special access approval needed.
"""

import os
import json
import re

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"


@st.cache_resource(show_spinner=False)
def _get_model():
    """Build model once and reuse — cached so it doesn't reload on every click."""
    llm = HuggingFaceEndpoint(
        repo_id=MODEL_ID,
        task="text-generation",
        max_new_tokens=512,
        temperature=0.2,
        huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
    )
    return ChatHuggingFace(llm=llm)


# ── AUTO MODE ─────────────────────────────────────────────────────────────────

TOPIC_PROMPT = PromptTemplate(
    template="""You are a CBSE Class 10 Mathematics expert.
From the textbook text below, extract key topics a student needs to solve the problems.

Return ONLY a JSON array. Each item must have "topic" and "chapter" keys.
Example: [{{"topic": "Quadratic Formula", "chapter": "Quadratic Equations"}}]
No explanation, no markdown, just the JSON array.

Text:
{text}

JSON array:""",
    input_variables=["text"],
)


@st.cache_data(show_spinner=False)
def extract_topics(full_text: str, max_chars: int = 8000) -> list[dict]:
    """Extract topics from PDF text. Cached — won't re-run for same text."""
    model = _get_model()
    chain = TOPIC_PROMPT | model | StrOutputParser()

    raw = chain.invoke({"text": full_text[:max_chars]}).strip()

    # Strip markdown fences
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

    # Find JSON array
    match = re.search(r"\[.*?\]", raw, re.DOTALL)
    if match:
        raw = match.group(0)

    try:
        topics = json.loads(raw)
        return [
            {
                "topic":   t.get("topic", "").strip(),
                "chapter": t.get("chapter", "General").strip(),
            }
            for t in topics
            if isinstance(t, dict) and t.get("topic")
        ]
    except json.JSONDecodeError:
        lines = [l.strip().lstrip("-•*0123456789.)").strip() for l in raw.splitlines() if l.strip()]
        return [{"topic": l, "chapter": "General"} for l in lines if len(l) > 3]


# ── RAG MODE ──────────────────────────────────────────────────────────────────

RAG_PROMPT = PromptTemplate(
    template="""You are a CBSE Class 10 Maths tutor.
Answer the student's question using ONLY the textbook context below.
Be concise (3-5 sentences). End with: "Revise: <concept name>".

Context:
{context}

Question: {question}

Answer:""",
    input_variables=["context", "question"],
)


def answer_with_context(question: str, context: str) -> str:
    model = _get_model()
    chain = RAG_PROMPT | model | StrOutputParser()
    return chain.invoke({"context": context, "question": question}).strip()


# ── YouTube search topic extractor ────────────────────────────────────────────

TOPIC_PHRASE_PROMPT = PromptTemplate(
    template="""Extract ONLY the math concept name from the question below (2-4 words).
Must be a specific NCERT topic like 'quadratic equations' or 'Euclid division lemma'.
No verbs, no 'explain', no 'what is'. Return ONLY the concept name, nothing else.

Question: {question}
Concept name:""",
    input_variables=["question"],
)


def topic_from_question(question: str) -> str:
    model = _get_model()
    chain = TOPIC_PHRASE_PROMPT | model | StrOutputParser()
    result = chain.invoke({"question": question}).strip()
    return result.splitlines()[0].strip().strip('"')
