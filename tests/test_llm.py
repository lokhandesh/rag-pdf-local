import httpx
import pytest

from app import llm
from app.config import Settings

HITS = [{"source": "a.pdf", "page": 2, "text": "Meal allowance is SGD 80.", "score": 0.9}]


def test_prompt_contains_context_and_citation_tag():
    p = llm.build_prompt("What is the meal allowance?", HITS)
    assert "[a.pdf p.2]" in p and "SGD 80" in p and "Question:" in p


def test_ollama_provider_calls_chat_api(monkeypatch):
    seen = {}

    def fake_post(url, json, timeout):
        seen["url"], seen["body"] = url, json
        return httpx.Response(200, json={"message": {"content": " SGD 80 [a.pdf p.2] "}},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(llm.httpx, "post", fake_post)
    s = Settings(llm_provider="ollama", ollama_url="http://ollama:11434/", ollama_model="m")
    assert llm.generate("q", HITS, s) == "SGD 80 [a.pdf p.2]"
    assert seen["url"] == "http://ollama:11434/api/chat"
    assert seen["body"]["model"] == "m"


def test_no_hits_short_circuits():
    assert "couldn't find" in llm.generate("q", [], Settings(llm_provider="ollama"))


def test_anthropic_requires_key():
    with pytest.raises(RuntimeError):
        llm.generate("q", HITS, Settings(llm_provider="anthropic", anthropic_api_key=None))
