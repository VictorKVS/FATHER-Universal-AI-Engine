"""Dependency-free API contract smoke test; uses no real model."""
import importlib.util
import json
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import urlopen, Request
from urllib.error import HTTPError

source = Path(__file__).resolve().parents[1] / "server" / "father_voice_server.py"
spec = importlib.util.spec_from_file_location("father_voice_server", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

server = ThreadingHTTPServer(("127.0.0.1", 0), module.make_handler(None, "", None))
thread = Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{server.server_port}"
try:
    with urlopen(base + "/api/tts/health") as resp:
        data = json.load(resp)
        assert data["ready"] is False and "xenia" in data["voices"]
    request = Request(base + "/api/tts/local", data=json.dumps({"text":"Привет","voice":"xenia"}).encode(), headers={"Content-Type":"application/json"})
    try:
        urlopen(request)
        raise AssertionError("Expected 503")
    except HTTPError as e:
        assert e.code == 503
        assert json.load(e)["error"] == "Silero model not loaded"
    print("PASS: health and missing-model contract")
finally:
    server.shutdown()
    server.server_close()
