class Omega7Card extends HTMLElement {
  setConfig(config) { this.config = config; }
  set hass(hass) { this._hass = hass; }
  getCardSize() { return 10; }
  connectedCallback() {
    if (!this.shadowRoot) { this.attachShadow({mode:'open'}); this.render(); }
    this.active = true;
    this.pollState(); this.pollEye();
  }
  disconnectedCallback() {
    this.active = false; clearTimeout(this.stateTimer); clearTimeout(this.eyeTimer);
    this.stopRecording(false); this.stopAudio();
    if(this.outputContext){this.outputContext.close();this.outputContext=null;this.audioBlocked=true;}
  }
  async call(action, extra={}) {
    if (!this._hass) throw new Error('Waiting for Home Assistant');
    return this._hass.callWS({type:'omega7_bridge/request',action,...extra});
  }
  el(id) { return this.shadowRoot.getElementById(id); }
  status(text, error=false) { this.el('notice').textContent=text; this.el('notice').classList.toggle('error',error); }
  render() {
    this.shadowRoot.innerHTML = `
      <style>
      @font-face{font-family:O7;src:url('/local/cogitator/data.ttf')}
      :host{display:block;color:#a8ffc0;font-family:O7,monospace;--line:#25613b;--glow:#70ffa0}
      *{box-sizing:border-box} .terminal{max-width:1400px;margin:auto;padding:24px;background:#030a06;border:1px solid var(--line);min-height:80vh;position:relative}
      .terminal:after{content:'';pointer-events:none;position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent 0 3px,#0002 3px 4px);opacity:.5}
      header{display:flex;justify-content:space-between;align-items:center;gap:16px;border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:24px}
      h1{margin:0;font-size:clamp(28px,4vw,46px);letter-spacing:.12em;color:#b6ffcb;text-shadow:0 0 15px #57ff7d66} .sub{font-size:12px;letter-spacing:.17em;color:#73a984;margin-top:6px}
      .seal{font-size:12px;color:#7dffa6;text-align:right}.layout{display:grid;grid-template-columns:minmax(260px,.85fr) minmax(320px,1.4fr);gap:24px}
      .panel{border:1px solid var(--line);padding:20px;background:#07130b}h2{font-size:14px;letter-spacing:.15em;margin:0 0 18px;color:#81c997}
      .eye-shell{margin:18px auto 24px;max-width:360px;aspect-ratio:1;position:relative;border-radius:50%;border:9px solid #1b3021;box-shadow:0 0 0 2px #48684e,0 0 34px #33e36920,inset 0 0 25px #000;overflow:hidden;background:#000}
      #eye{width:100%;height:100%;object-fit:contain}.stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:13px}.stats span{display:block;color:#638e70;font-size:10px;letter-spacing:.1em;margin-bottom:5px}
      .vox{display:flex;flex-direction:column;height:62vh;min-height:400px;max-height:780px}#history{overflow:auto;flex:1;scrollbar-color:#376846 #07130b;padding-right:8px}.entry{border-left:2px solid #376f48;padding:9px 13px;margin:0 0 18px;background:#0c1c11}.entry.user{border-color:#819c74;background:#141e12}.who{color:#76ad87;font-size:11px;letter-spacing:.08em;margin-bottom:7px}.words{white-space:pre-wrap;font:16px/1.55 O7,monospace;color:#c3e6cc}
      .controls{margin-top:20px;display:flex;gap:10px;flex-wrap:wrap}button{font:14px O7,monospace;letter-spacing:.04em;cursor:pointer;border:1px solid #3c8352;color:#b1ffc7;background:#12361d;padding:13px 17px;min-height:48px}button:hover{background:#1b4c2b}button:disabled{opacity:.5;cursor:wait}#mic{flex:1;background:#1e5e32}#mic.recording{background:#682d22;border-color:#fcaa77;color:#ffe8dc}
      form{display:flex;gap:10px;margin-top:16px}input{min-width:0;flex:1;background:#020905;color:#d3ffdf;border:1px solid #396347;padding:13px;font:16px O7,monospace}input:focus{outline:1px solid #97ffb5}#notice{min-height:36px;margin:15px 0 0;font-size:13px;color:#82b890;line-height:1.4}.error{color:#ffc097!important}.hint{color:#6c9978;font-size:12px;line-height:1.6;margin-top:18px}
      @media(max-width:750px){.terminal{padding:14px}.layout{grid-template-columns:1fr;gap:15px}.eye-shell{max-width:210px;margin:8px auto 18px}.panel{padding:16px}.vox{height:48vh;min-height:340px}header{margin-bottom:16px}.seal{max-width:90px}.controls{margin-top:14px}}
      </style>
      <section class="terminal"><header><div><h1>OMEGA-7</h1><div class="sub">SERVOSKULL // VOX UPLINK</div></div><div class="seal" id="link">CONNECTING</div></header>
      <div class="layout"><div><section class="panel"><h2>OCULAR FEED / LIVE</h2><div class="eye-shell"><img id="eye" alt="Omega-7 live ocular display"></div><div class="stats"><div><span>DISPOSITION</span><b id="mood">?</b></div><div><span>CORE TEMPERATURE</span><b id="temp">?</b></div><div><span>QUIET MODE</span><b id="quiet">?</b></div><div><span>CONNECTION</span><b>PHYSICAL SKULL</b></div></div></section>
      <div class="controls"><button id="mic">TALK TO OMEGA-7</button><button id="audio">AUDIO: OFF</button></div><p id="notice" role="status" aria-live="polite">The skull's own voice, memory, and conversation.</p><p class="hint">Tap Talk to record, then tap again to send. Replies also play on the skull. Enable audio to hear them here. Use headphones if you are near the skull.</p></div>
      <section class="panel vox"><h2>VOX CHANNEL / SHARED MEMORY</h2><div id="history" role="log"><div class="hint">Establishing vox link?</div></div><form id="form"><input id="text" aria-label="Message Omega-7" placeholder="Transmit a message?" maxlength="2000" autocomplete="off"><button id="send" type="submit">SEND</button></form></section></div></section>`;
    this.queue=[];this.cursor=null;this.audioEnabled=false;
    this.el('form').onsubmit=e=>{e.preventDefault();this.sendText();};
    this.el('mic').onclick=()=>this.recording?this.stopRecording(true):this.startRecording();
    this.el('audio').onclick=()=>{this.audioEnabled=!this.audioEnabled;this.el('audio').textContent='AUDIO: '+(this.audioEnabled?'ON':'OFF');if(!this.audioEnabled)this.stopAudio();else {this.unlockAudio();}};
    this.shadowRoot.addEventListener('click',()=>{if(this.audioEnabled&&this.audioBlocked){this.unlockAudio();}});
  }
  async pollState() {
    if(!this.active)return;
    try {
      const s=await this.call('state');if(!this.active)return;
      this.el('link').textContent='? LINK ACTIVE';
      this.el('mood').textContent=s.mood||'?';this.el('temp').textContent=s.temperature||'?';this.el('quiet').textContent=s.silent_mode||'?';
      const logs=s.vox_logs||[], signature=JSON.stringify(logs);
      if(signature!==this.lastLogs){this.lastLogs=signature;const h=this.el('history');const bottom=h.scrollHeight-h.scrollTop-h.clientHeight<70;h.replaceChildren();
        for(const item of logs){const e=document.createElement('div');e.className='entry'+(item.speaker!==s.skull_name?' user':'');const who=document.createElement('div');who.className='who';who.textContent=(item.speaker||'VOX')+' / '+(item.time||item.timestamp||'');const words=document.createElement('div');words.className='words';words.textContent=item.text||'';e.append(who,words);h.append(e);}if(bottom)h.scrollTop=h.scrollHeight;}
      const ids=s.audio_ids||[];
      if(this.cursor===null)this.cursor=ids.length?Math.max(...ids):0;
      else for(const id of ids){if(id>this.cursor){this.cursor=id;if(this.audioEnabled&&!this.recording)this.queue.push(id);}}
      this.playNext();
    } catch(e){if(this.active){this.el('link').textContent='LINK UNAVAILABLE';this.status(e.message||'Cannot reach Omega-7',true);}}
    if(this.active)this.stateTimer=setTimeout(()=>this.pollState(),1200);
  }
  async pollEye(){if(!this.active)return;try{if(!document.hidden){const r=await this.call('eye');if(this.active)this.el('eye').src='data:image/jpeg;base64,'+r.data;}}catch(e){}if(this.active)this.eyeTimer=setTimeout(()=>this.pollEye(),250);}
  async sendText(){const input=this.el('text'),text=input.value.trim();if(!text)return;this.el('send').disabled=true;try{await this.call('text',{text});input.value='';this.status('Message sent to Omega-7. Awaiting his response.');}catch(e){this.status(e.message||'Transmission failed',true);}finally{this.el('send').disabled=false;}}
  async unlockAudio(){
    try {
      if(!this.outputContext||this.outputContext.state==='closed')this.outputContext=new(window.AudioContext||window.webkitAudioContext)();
      await this.outputContext.resume();
      this.audioBlocked=this.outputContext.state!=='running';
      if(this.audioBlocked)this.status('Tap Audio off, then on to allow reply playback.',true);
      else this.playNext();
    } catch(e){this.audioBlocked=true;this.status('Reply audio could not start: '+(e.message||e.name),true);}
  }
  stopAudio(){
    this.queue=[];this.audioGeneration=(this.audioGeneration||0)+1;
    if(this.outputSource){this.outputSource.onended=null;try{this.outputSource.stop();}catch(e){}this.outputSource.disconnect();this.outputSource=null;}
    this.playing=false;
  }
  async playNext(){
    if(!this.active||!this.audioEnabled||this.recording||this.playing||this.audioBlocked||!this.queue.length)return;
    if(!this.outputContext||this.outputContext.state!=='running'){
      this.audioBlocked=true;this.status('Reply ready. Tap the panel to enable audio.');return;
    }
    this.playing=true;const generation=this.audioGeneration||0;const id=this.queue.shift();
    try {
      const r=await this.call('audio',{audio_id:id});
      if(!this.active||generation!==(this.audioGeneration||0))return;
      const bytes=Uint8Array.from(atob(r.data),c=>c.charCodeAt(0));
      const buffer=await this.outputContext.decodeAudioData(bytes.buffer);
      if(!this.active||generation!==(this.audioGeneration||0))return;
      if(this.outputContext.state!=='running'){
        this.queue.unshift(id);this.playing=false;this.audioBlocked=true;
        this.status('Reply ready. Tap the panel to resume audio.');return;
      }
      const source=this.outputContext.createBufferSource();source.buffer=buffer;source.connect(this.outputContext.destination);this.outputSource=source;
      source.onended=()=>{source.disconnect();if(this.outputSource!==source)return;this.outputSource=null;this.playing=false;this.playNext();};
      source.start();
    }catch(e){
      if(generation!==(this.audioGeneration||0))return;
      this.playing=false;this.queue.unshift(id);this.audioBlocked=true;
      this.status('Reply audio paused: '+(e.message||e.name||'load failed')+'. Tap the panel to retry.',true);
    }
  }
  async startRecording(){if(this.starting)return;this.starting=true;if(this.audioEnabled)this.unlockAudio();try{this.stopAudio();if(!window.isSecureContext){const e=new Error('This HA page uses HTTP. Open https://ha.salientpoint.net/home-hub/omega7, or set the Companion app internal URL to https://ha.salientpoint.net.');e.name='InsecureContext';throw e;}if(!navigator.mediaDevices?.getUserMedia){const e=new Error('This app webview does not provide browser microphone access. Open this HTTPS dashboard in Chrome.');e.name='MissingMediaDevices';throw e;}const stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true}});if(!this.active){stream.getTracks().forEach(t=>t.stop());return;}this.stream=stream;this.context=new(window.AudioContext||window.webkitAudioContext)();await this.context.resume();this.chunks=[];this.source=this.context.createMediaStreamSource(stream);this.processor=this.context.createScriptProcessor(4096,1,1);this.processor.onaudioprocess=e=>{if(this.recording)this.chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));};this.source.connect(this.processor);this.processor.connect(this.context.destination);this.recording=true;this.el('mic').textContent='STOP & SEND';this.el('mic').classList.add('recording');this.status('Listening - tap Stop & Send when finished.');this.recordTimer=setTimeout(()=>this.stopRecording(true),25000);}catch(e){this.stopRecording(false);const messages={NotAllowedError:'Microphone permission denied. In Android Settings > Apps > Home Assistant > Permissions, allow Microphone while using the app. Also check Android microphone privacy access. If already allowed, open this dashboard in Chrome and allow its microphone prompt.',NotFoundError:'No microphone was found by this app.',NotReadableError:'The microphone could not start. Close other recording or calling apps and try again.',SecurityError:'Microphone access is blocked by this app or page security policy.'};this.status((messages[e.name]||e.message||'Microphone could not start.')+' ['+(e.name||'Error')+']',true);console.warn('Omega-7 microphone:',e.name,e.message,location.origin,window.isSecureContext);}finally{this.starting=false;}}
  async stopRecording(send){if(send&&this.audioEnabled)this.unlockAudio();clearTimeout(this.recordTimer);const was=this.recording;this.recording=false;const rate=this.context?.sampleRate||48000;const chunks=this.chunks||[];this.chunks=[];if(this.processor){this.processor.disconnect();this.processor.onaudioprocess=null;this.processor=null;}if(this.source){this.source.disconnect();this.source=null;}if(this.stream){this.stream.getTracks().forEach(t=>t.stop());this.stream=null;}if(this.context){this.context.close();this.context=null;}if(this.el('mic')){this.el('mic').textContent='TALK TO OMEGA-7';this.el('mic').classList.remove('recording');}if(!send||!was||!chunks.length)return;
    const total=chunks.reduce((n,c)=>n+c.length,0),input=new Float32Array(total);let at=0;for(const c of chunks){input.set(c,at);at+=c.length;}const count=Math.floor(total*16000/rate),buf=new ArrayBuffer(44+count*2),v=new DataView(buf);const str=(o,s)=>{for(let i=0;i<s.length;i++)v.setUint8(o+i,s.charCodeAt(i));};str(0,'RIFF');v.setUint32(4,36+count*2,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,16000,true);v.setUint32(28,32000,true);v.setUint16(32,2,true);v.setUint16(34,16,true);str(36,'data');v.setUint32(40,count*2,true);for(let i=0;i<count;i++){const x=i*rate/16000,lo=Math.floor(x),f=x-lo;const sample=Math.max(-1,Math.min(1,input[lo]*(1-f)+(input[Math.min(lo+1,total-1)]||0)*f));v.setInt16(44+i*2,sample<0?sample*32768:sample*32767,true);}let binary='';const bytes=new Uint8Array(buf);for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));this.el('mic').disabled=true;this.status('Sending voice transmission?');try{await this.call('microphone',{wav:btoa(binary)});this.status('Voice sent to Omega-7. Awaiting his response.');}catch(e){this.status(e.message||'Voice transmission failed',true);}finally{this.el('mic').disabled=false;}
  }
}
customElements.define('omega7-card',Omega7Card);
