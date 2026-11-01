"""LLM providers: local Ollama, Claude API, or none (retrieval-only)."""
import httpx

from app.config import Settings

SYSTEM_PROMPT = (
    "You answer questions using ONLY the provided context from PDF documents. "
    "Cite sources inline like [file.pdf p.3]. If the context does not contain the "
    "answer, say you couldn't find it in the documents. Be concise."
)


def build_prompt(question: str, hits: list[dict]) -> str:
    context = "\n\n".join(
        f"[{h['source']} p.{h['page']}]\n{h['text']}" for h in hits
    )
    return f"Context:\n{context}\n\nQuestion: {question}"


def generate(question: str, hits: list[dict], s: Settings) -> str:
    if not hits:
        return "I couldn't find anything relevant in the ingested documents."

    provider = s.llm_provider.lower()
    prompt = build_prompt(question, hits)
    print("\n===== PROMPT SENT TO LLM =====\n", prompt)

    if provider == "none":
        top = hits[0]
        return (f"(Retrieval-only mode, no LLM configured.) Most relevant passage "
                f"[{top['source']} p.{top['page']}]: {top['text']}")

    if provider == "ollama":
        r = httpx.post(
            f"{s.ollama_url.rstrip('/')}/api/chat",
            json={"model": s.ollama_model, "stream": False,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                               {"role": "user", "content": prompt}],
                  "options": {"temperature": 0.1, "num_predict": s.max_tokens}},
            timeout=300,
        )
        r.raise_for_status()
        return r.json()["message"]["content"].strip()

    if provider == "anthropic":
        if not s.anthropic_api_key:
            raise RuntimeError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set")
        import anthropic
        client = anthropic.Anthropic(api_key=s.anthropic_api_key)
        msg = client.messages.create(
            model=s.anthropic_model, max_tokens=s.max_tokens, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()

    raise ValueError(f"Unknown LLM_PROVIDER: {s.llm_provider!r}")
