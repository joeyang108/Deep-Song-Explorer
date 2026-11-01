"""Automated unit and integration tests for Mobile PWA API and static routes."""
import json
import threading
import time
import urllib.request
import pytest
import uvicorn
from song_explorer.server import app


@pytest.fixture(scope="module")
def live_server():
    """Spins up a lightweight uvicorn instance on port 8999 for test verification."""
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8999, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(0.8)
    yield "http://127.0.0.1:8999"
    server.should_exit = True


def test_api_health(live_server):
    req = urllib.request.urlopen(f"{live_server}/api/health")
    assert req.status == 200
    data = json.loads(req.read())
    assert data["status"] == "ok"


def test_api_history(live_server):
    req = urllib.request.urlopen(f"{live_server}/api/history")
    assert req.status == 200
    data = json.loads(req.read())
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1


def test_api_dossier_cached(live_server):
    url = f"{live_server}/api/dossier?artist=Steely%20Dan&song=Deacon%20Blues"
    req = urllib.request.urlopen(url)
    assert req.status == 200
    data = json.loads(req.read())
    assert "dossier" in data
    assert data["source"] == "cache"
    assert data["dossier"]["song"]["title"] == "Deacon Blues"


def test_pwa_static_assets(live_server):
    for path in ["/", "/manifest.json", "/sw.js", "/icon.svg", "/static/style.css", "/static/app.js"]:
        req = urllib.request.urlopen(f"{live_server}{path}")
        assert req.status == 200, f"Failed asset: {path}"


def test_api_chat(live_server):
    payload = json.dumps({
        "artist": "Steely Dan",
        "song": "Deacon Blues",
        "prompt": "What is the key takeaway of this song?",
        "history": []
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{live_server}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req, timeout=10)
    assert res.status == 200
    data = json.loads(res.read())
    assert "reply" in data
    assert len(data["reply"]) > 10
