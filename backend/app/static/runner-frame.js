/* An opaque sandbox frame owns the worker. It has no credentials and cannot fetch backend APIs. */
(() => {
  "use strict";
  let initialized = false;
  window.addEventListener("message", event => {
    if (event.source !== parent || initialized || event.data?.type !== "init" || !event.ports[0]) return;
    initialized = true;
    const port = event.ports[0], canvas = document.getElementById("canvas");
    if (!canvas.transferControlToOffscreen) { port.postMessage({type:"error", text:"Dieser Browser unterstützt die Programmausführung nicht. Bitte einen aktuellen Browser verwenden."}); return; }
    const url = URL.createObjectURL(new Blob([event.data.worker], {type:"text/javascript"}));
    const worker = new Worker(url, {credentials:"omit"});
    worker.addEventListener("message", () => URL.revokeObjectURL(url), {once:true});
    const outputTypes = new Set(["output", "status", "done", "error", "database"]);
    const files = new Map(event.data.files.map(file => [file.name, file]));
    const players = new Map(), objectUrls = new Map(), pendingAudio = new Set();
    const enableAudio = document.createElement("button");
    enableAudio.textContent = "Ton aktivieren"; enableAudio.hidden = true;
    document.body.prepend(enableAudio);
    function playAudio(audio) {
      audio.play().catch(error => {
        if (error.name === "NotAllowedError") { pendingAudio.add(audio); enableAudio.hidden = false; }
        else port.postMessage({type:"output", text:"Die Audiodatei konnte nicht abgespielt werden."});
      });
    }
    enableAudio.addEventListener("click", () => {
      for (const audio of pendingAudio) playAudio(audio);
      pendingAudio.clear(); enableAudio.hidden = true;
    });
    function stopAudio(id) {
      const audio = players.get(id);
      if (audio) { worker.postMessage({type:"audio-state", channel:id, busy:false}); audio.pause(); audio.remove(); pendingAudio.delete(audio); players.delete(id); }
    }
    function audioCommand(data) {
      if (typeof data.channel !== "string" || data.channel.length > 32) return;
      const id = data.channel;
      if (data.action === "play") {
        const file = files.get(data.name);
        if (!file || !/\.(mp3|ogg|wav)$/i.test(file.name)) return;
        stopAudio(id);
        if (players.size >= 64) stopAudio(players.keys().next().value);
        if (!objectUrls.has(file.name)) objectUrls.set(file.name, URL.createObjectURL(new Blob([file.content])));
        const audio = new Audio(objectUrls.get(file.name));
        audio.hidden = true; document.body.append(audio);
        audio.dataset.filename = file.name;
        audio.volume = Math.max(0, Math.min(1, Number(data.volume) || 0));
        audio.loop = data.loops === -1;
        let repeats = Math.max(0, Math.min(1000, Number(data.loops) || 0));
        audio.addEventListener("ended", () => {
          if (repeats-- > 0) { audio.currentTime = 0; playAudio(audio); }
          else stopAudio(id);
        });
        audio.addEventListener("playing", () => worker.postMessage({type:"audio-state", channel:id, busy:true}));
        audio.addEventListener("pause", () => worker.postMessage({type:"audio-state", channel:id, busy:false}));
        players.set(id, audio); playAudio(audio);
      } else if (data.action === "stop_path") {
        for (const [key, audio] of players) if (audio.dataset.filename === data.name) stopAudio(key);
      } else {
        const audio = players.get(id); if (!audio) return;
        if (data.action === "stop") stopAudio(id);
        if (data.action === "pause") audio.pause();
        if (data.action === "resume") playAudio(audio);
        if (data.action === "volume") audio.volume = Math.max(0, Math.min(1, Number(data.volume) || 0));
        if (data.action === "fadeout") {
          const start = performance.now(), volume = audio.volume, duration = Math.max(1, Math.min(60000, Number(data.duration) || 1));
          const timer = setInterval(() => {
            const progress = (performance.now() - start) / duration;
            audio.volume = Math.max(0, volume * (1 - progress));
            if (progress >= 1 || !players.has(id)) { clearInterval(timer); stopAudio(id); }
          }, 30);
        }
      }
    }
    worker.onmessage = e => {
      if (e.data?.type === "audio") audioCommand(e.data);
      else if (e.data && outputTypes.has(e.data.type)) port.postMessage(e.data);
    };
    worker.onerror = e => port.postMessage({type:"error", text:e.message || "Die Laufzeit konnte nicht gestartet werden."});
    const offscreen = canvas.transferControlToOffscreen();
    worker.postMessage({...event.data, type:"boot", canvas:offscreen, worker:undefined}, [offscreen]);
    for (const type of ["keydown", "keyup", "mousedown", "mouseup", "mousemove"]) {
      canvas.addEventListener(type, e => {
        const bounds = canvas.getBoundingClientRect();
        worker.postMessage({type:"input", event:type, key:e.key, code:e.code, keyCode:e.keyCode, repeat:e.repeat, ctrlKey:e.ctrlKey, shiftKey:e.shiftKey, altKey:e.altKey, metaKey:e.metaKey, button:e.button, buttons:e.buttons, movementX:e.movementX, movementY:e.movementY,
          x:Math.round((e.clientX - bounds.left) * canvas.width / bounds.width),
          y:Math.round((e.clientY - bounds.top) * canvas.height / bounds.height)});
        if (type === "keydown") e.preventDefault();
        if (type === "mousedown") canvas.focus();
      });
    }
  });
})();
