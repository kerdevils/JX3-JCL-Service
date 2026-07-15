import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestHealthEndpoint:
    def test_returns_ok(self):
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestIndexPage:
    def test_serves_html(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "战斗时间(秒)" in resp.text
        assert "/ 16" in resp.text


class TestJclConvertEndpoint:
    def test_accepts_valid_jcl(self):
        with open(os.path.join(FIXTURES_DIR, "TEST.jcl"), "rb") as f:
            resp = client.post(
                "/v1/jcl/convert",
                files={"file": ("test.jcl", f, "application/octet-stream")},
                data={"target_level": 134},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["player"]["kungfuId"] == 10627
        assert body["player"]["name"] != "无方"
        assert "data" in body
        assert "diagnostics" in body

    def test_rejects_empty_file(self):
        resp = client.post(
            "/v1/jcl/convert",
            files={"file": ("empty.jcl", b"", "application/octet-stream")},
        )
        assert resp.status_code == 422
        assert "empty" in resp.json()["detail"].lower()

    def test_rejects_oversized_file(self):
        big = b"x" * (51 * 1024 * 1024)
        resp = client.post(
            "/v1/jcl/convert",
            files={"file": ("big.jcl", big, "application/octet-stream")},
        )
        assert resp.status_code == 413

    def test_rejects_bad_extension(self):
        resp = client.post(
            "/v1/jcl/convert",
            files={"file": ("bad.exe", b"content", "application/octet-stream")},
        )
        assert resp.status_code == 415

    def test_rejects_invalid_target_level(self):
        with open(os.path.join(FIXTURES_DIR, "TEST.jcl"), "rb") as f:
            resp = client.post(
                "/v1/jcl/convert",
                files={"file": ("test.jcl", f, "application/octet-stream")},
                data={"target_level": 999},
            )
        assert resp.status_code == 422
        assert "target_level" in resp.json()["detail"].lower()

    def test_handles_missing_file(self):
        resp = client.post("/v1/jcl/convert")
        assert resp.status_code == 422
