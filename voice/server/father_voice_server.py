"""FATHER-VOICE/1.0: local-only Silero TTS adapter and optional static site.

Start: python voice/server/father_voice_server.py --port 8090 --silero-model PATH
Or: python voice/server/father_voice_server.py --port 8090 --site SITE_DIR --silero-model PATH
Never downloads model weights. No cross-origin access is enabled.
"""
import argparse
import array
import io
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time
import wave

LOG = logging.getLogger("father.voice")
VOICES = ("xenia", "baya", "kseniya", "aidar", "eugene")
LOCK = threading.Lock()


def load_silero(path):
    if not path:
        LOG.warning("MODEL_NOT_CONFIGURED")
        return None
    if not Path(path).is_file():
        LOG.error("MODEL_NOT_FOUND path=%s", path)
        return None
    try:
        import torch
        model = torch.package.PackageImporter(str(path)).load_pickle("tts_models", "model")
        model.to(torch.device("cpu"))
        LOG.info("MODEL_READY path=%s", path)
        return model
    except Exception:
        LOG.exception("MODEL_LOAD_FAILED")
        return None


def make_handler(model, model_path, site=None):
    base = SimpleHTTPRequestHandler if site else BaseHTTPRequestHandler

    class VoiceHandler(base):
        def __init__(self, *args, **kwargs):
            if site:
                kwargs["directory"] = str(site)
            super().__init__(*args, **kwargs)

        def log_message(self, fmt, *args):
            LOG.info("http client=%s " + fmt, self.client_address[0], *args)

        def json_response(self, code, data):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.split("?", 1)[0] == "/api/tts/health":
                return self.json_response(200, {
                    "provider": "silero", "ready": model is not None,
                    "voices": list(VOICES), "model_configured": bool(model_path)
                })
            if site:
                return super().do_GET()
            return self.json_response(404, {"error": "Unknown route"})

        def do_POST(self):
            if self.path.split("?", 1)[0] != "/api/tts/local":
                return self.json_response(404, {"error": "Unknown route"})
            started = time.monotonic()
            if model is None:
                LOG.warning("TTS_NOT_READY")
                return self.json_response(503, {"error": "Silero model not loaded"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 32768:
                    return self.json_response(413, {"error": "Invalid request size"})
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    return self.json_response(400, {"error": "Expected JSON object"})
                text = data.get("text")
                voice = data.get("voice", "xenia")
                if not isinstance(text, str) or not text.strip() or len(text) > 2000:
                    return self.json_response(400, {"error": "Invalid text"})
                if voice not in VOICES:
                    return self.json_response(400, {"error": "Unsupported voice"})
                import torch
                with LOCK, torch.inference_mode():
                    samples = model.apply_tts(text=text, speaker=voice, sample_rate=48000)
                pcm = array.array("h", (max(-32768, min(32767, int(float(x) * 32767))) for x in samples.detach().cpu().numpy()))
                out = io.BytesIO()
                with wave.open(out, "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(48000)
                    wav.writeframes(pcm.tobytes())
                payload = out.getvalue()
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(payload)
                LOG.info("TTS_OK voice=%s chars=%d bytes=%d duration_ms=%d", voice, len(text), len(payload), round((time.monotonic()-started)*1000))
            except (ValueError, json.JSONDecodeError):
                self.json_response(400, {"error": "Malformed request"})
            except Exception:
                LOG.exception("TTS_FAILED")
                self.json_response(500, {"error": "Synthesis failed; see server logs"})

    return VoiceHandler


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8090)
    p.add_argument("--site", type=Path)
    p.add_argument("--silero-model", default=os.getenv("FATHER_SILERO_MODEL", ""))
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if args.site and not args.site.is_dir():
        p.error("Site directory not found")
    model = load_silero(args.silero_model)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(model, args.silero_model, args.site))
    LOG.info("FATHER_VOICE_START port=%d ready=%s site=%s", args.port, model is not None, args.site)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOG.info("FATHER_VOICE_STOP")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
