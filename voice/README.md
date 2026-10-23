# FATHER Voice Template (FATHER-VOICE/1.0)

Universal TTS registry and adapter contract for avatars, agents, Telegram, web and other clients.

## Provenance
First integration proven by user in CyberED on Windows: Silero v5_ru local model, Python server, `GET /api/tts/health`, `POST /api/tts/local`, WAV playback and frontend tracing. The FATHER package itself is a **template**, not yet end-to-end validated.

Reference implementation: https://github.com/VictorKVS/CyberED/blob/feature/alina-avatar-assets/tools/cybered_tts_server.py

## Standard contract
- `GET /api/tts/health` returns provider, ready, available voices, model_configured.
- `POST /api/tts/local` accepts JSON `{"text":"Привет","voice":"xenia"}`; returns `audio/wav` on success.
- Error response: JSON with `error` and optional `hint`; 503 means model unavailable.
- Never mark provider ready based on file existence or registry declaration alone.
- TTS request traces: provider, voice, input length, status, elapsed milliseconds, output bytes, error code. Do not log speech text or credentials by default.
- Voice is character configuration, not hardcoded into synthesis.
- Character defaults: alina→xenia; father→eugene. All voices can be selected via UI.
- External providers must be independent adapters; no vendor keys in browser or repository.
- Local model paths supplied via environment/CLI; do not commit weights.
- Respect audio consent, browser playback restrictions and reduced-motion; lip-sync remains a separate contract.

## Acceptance gates
1. Model loads in intended environment and health returns ready=true.
2. All declared voice IDs are probed; failures flagged, not silently skipped.
3. POST yields playable WAV with valid RIFF header and nonzero samples.
4. Failure paths (model missing, unknown voice, invalid text) return structured errors.
5. UI selection survives reload and audio stops on user request.
6. Real avatar/client integration passes smoke test. Only then mark READY.

## Integration
CyberED is the reference consumer. Do not duplicate TTS models in each project. Reuse one local service and standard client; proxy only with explicit origin and access controls.
