/* FATHER-VOICE/1.0: browser-compatible client; no hardcoded host or credentials. */
export class FatherVoiceClient {
  constructor({baseUrl = '', onTrace = () => {}} = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.onTrace = onTrace;
    this.audio = null;
    this.objectUrl = null;
  }
  async health() {
    const response = await fetch(this.baseUrl + '/api/tts/health', {cache:'no-store'});
    if (!response.ok) throw new Error('Health HTTP ' + response.status);
    return response.json();
  }
  stop() {
    if (this.audio) {this.audio.pause(); this.audio.src = ''; this.audio = null;}
    if (this.objectUrl) {URL.revokeObjectURL(this.objectUrl); this.objectUrl = null;}
    this.onTrace({event:'audio_stop'});
  }
  async speak({text, voice='xenia'} = {}) {
    if (typeof text !== 'string' || !text.trim()) throw new Error('Nonempty text required');
    this.stop();
    const started = performance.now();
    this.onTrace({event:'tts_request',voice,textLength:text.length});
    const response = await fetch(this.baseUrl + '/api/tts/local', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text,voice})
    });
    this.onTrace({event:'tts_response',status:response.status,elapsedMs:Math.round(performance.now()-started)});
    if (!response.ok) {
      let reason = 'HTTP ' + response.status;
      try {const err=await response.json();reason=err.error || reason;} catch {}
      throw new Error(reason);
    }
    const blob = await response.blob();
    if (!blob.type.startsWith('audio/')) throw new Error('Unexpected audio content type');
    this.objectUrl = URL.createObjectURL(blob);
    this.audio = new Audio(this.objectUrl);
    this.audio.onended = () => {this.onTrace({event:'audio_end'});this.stop();};
    this.audio.onerror = () => this.onTrace({event:'audio_error',code:this.audio?.error?.code});
    await this.audio.play();
    this.onTrace({event:'audio_play',bytes:blob.size,voice});
  }
}
