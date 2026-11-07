"""Local Qwen (or compatible) via llama.cpp GGUF – same role as mobile MediaPipe Qwen."""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("llm")

SYSTEM = """You are an offline educational assistant for school textbooks.
Answer using ONLY the course context below the user's message.
The context may include a short internet snippet labeled as curriculum web search;
prefer textbook passages when both are present, but use a strong web snippet if it
clearly answers the question from Hungarian school material.
If the context mentions the answer (even briefly), state it clearly.
Hungarian names may appear with English spelling (Zeusz=Zeus, Athéné=Athena).
Reply in English in 2–4 short factual sentences.
Do not invent facts. Do not copy the instructions. Do not repeat yourself.
If the context truly lacks the answer, reply exactly: I do not know from the course material.
"""

PLANT_SYSTEM = """You answer factory troubleshooting questions for shop-floor staff and supervisors.
Use ONLY the document excerpts in the user message. They were uploaded by the plant.
Write in the language requested in the user message.
If an excerpt contains a fault code, symptom, cause, or action, state those clearly and name the source file.
If the excerpts do not contain the answer, say that the uploaded documents do not contain it.
Do not add steps, setpoints, tools, or safety rules that are not written in the excerpts.
Do not use outside knowledge. Keep the answer short enough to read on a shop floor.
"""


class LocalLlm:
    def __init__(
        self,
        model_path: Path | None,
        *,
        n_ctx: int = 1024,
        n_threads: int = 4,
        max_tokens: int = 256,
        temperature: float = 0.3,
    ):
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_threads = n_threads
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._llm = None

    @property
    def ready(self) -> bool:
        return self._llm is not None

    def load(self) -> None:
        if self._model_path is None or not Path(self._model_path).exists():
            log.error(
                "LLM GGUF missing at %s – set LLM_MODEL_PATH "
                "(e.g. Qwen2.5-1.5B-Instruct Q4_K_M). Chat will return 503.",
                self._model_path,
            )
            return
        from llama_cpp import Llama

        log.info("Loading GGUF %s (n_ctx=%s n_threads=%s)", self._model_path, self._n_ctx, self._n_threads)
        self._llm = Llama(
            model_path=str(self._model_path),
            n_ctx=self._n_ctx,
            n_threads=self._n_threads,
            verbose=False,
        )
        log.info("LLM ready")

    def generate(self, *, english_question: str, context: str) -> str:
        if self._llm is None:
            raise RuntimeError("LLM not loaded")

        if not context.strip():
            return "I do not know from the course material."

        user = f"""Course context:
{context}

Question: {english_question}

Write a direct answer from the course context above.
"""
        result = self._llm.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        try:
            text = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            text = ""
        text = (text or "").strip()
        return text or "I do not know from the course material."

    def generate_plant(self, question: str, context: str, language: str) -> str:
        """Shop-floor answer from uploaded plant excerpts only."""
        if self._llm is None:
            raise RuntimeError("LLM not loaded")
        if not context.strip():
            return ""
        lang_name = "Hungarian" if language == "hu" else "English"
        user = (
            f"Language: {lang_name}\n\n"
            f"Document excerpts:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer from the excerpts only."
        )
        result = self._llm.create_chat_completion(
            messages=[
                {"role": "system", "content": PLANT_SYSTEM},
                {"role": "user", "content": user},
            ],
            max_tokens=self._max_tokens,
            temperature=min(self._temperature, 0.2),
        )
        try:
            text = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            text = ""
        return (text or "").strip()
