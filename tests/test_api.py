from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_rejects_non_pdf():
    r = client.post("/upload", files={"file": ("notes.txt", b"hi", "text/plain")})
    assert r.status_code == 400


def test_upload_ask_and_delete(make_pdf):
    pdf = make_pdf("policy.pdf", [
        "Annual leave: employees get 18 days of paid leave per year.",
        "Laptops: report a lost laptop to the IT helpdesk within 24 hours.",
    ])
    with open(pdf, "rb") as f:
        r = client.post("/upload", files={"file": ("policy.pdf", f, "application/pdf")})
    assert r.status_code == 200, r.text
    assert r.json() == {"source": "policy.pdf", "pages": 2, "chunks": 2}

    assert client.get("/documents").json()["documents"] == {"policy.pdf": 2}

    r = client.post("/ask", json={"question": "How do I report a lost laptop?"})
    assert r.status_code == 200
    body = r.json()
    assert body["sources"][0]["page"] == 2          # the right page ranks first
    assert "helpdesk" in body["answer"]

    # re-uploading the same file replaces it instead of duplicating chunks
    with open(pdf, "rb") as f:
        client.post("/upload", files={"file": ("policy.pdf", f, "application/pdf")})
    assert client.get("/documents").json()["documents"] == {"policy.pdf": 2}

    client.delete("/documents/policy.pdf")
    assert client.get("/documents").json()["documents"] == {}


def test_ask_validation():
    assert client.post("/ask", json={"question": ""}).status_code == 422
