/* No auth, DOM, storage, API RPC, or parent-window access in this worker. */
let pyodide = null, runtimeCanvas = null;
const audioStates = new Map();
const eventHandlers = new Map();
function addEventListenerCompat(type, callback) {
  if (!eventHandlers.has(type)) eventHandlers.set(type, new Set());
  eventHandlers.get(type).add(callback);
}
function removeEventListenerCompat(type, callback) { eventHandlers.get(type)?.delete(callback); }
const send = (type, text) => postMessage({type, text:String(text ?? "")});
const decode = value => Uint8Array.from(atob(value), c => c.charCodeAt(0));
function syncDatabase() {
  if (!pyodide) return;
  try {
    const name = pyodide.FS.readdir("/project").find(f => /\.(db|sqlite)$/.test(f));
    if (!name) return;
    const bytes = pyodide.FS.readFile("/project/" + name);
    let binary = "";
    for (let i = 0; i < bytes.length; i += 32768) binary += String.fromCharCode(...bytes.subarray(i, i + 32768));
    postMessage({type:"database", content:btoa(binary)});
  } catch (_) { /* database not yet created */ }
}
self.onmessage = async event => {
  const data = event.data;
  if (data.type === "audio-state") {
    audioStates.set(data.channel, {busy:!!data.busy});
    return;
  }
  if (data.type === "input") {
    const synthetic = {
      type:data.event, key:data.key, code:data.code, keyCode:data.keyCode, which:data.keyCode,
      charCode:0, location:0, repeat:data.repeat, ctrlKey:data.ctrlKey, shiftKey:data.shiftKey,
      altKey:data.altKey, metaKey:data.metaKey, button:data.button, buttons:data.buttons,
      clientX:data.x, clientY:data.y, screenX:data.x, screenY:data.y,
      pageX:data.x, pageY:data.y, movementX:data.movementX || 0, movementY:data.movementY || 0,
      timeStamp:performance.now(), target:runtimeCanvas, preventDefault(){}
    };
    for (const callback of eventHandlers.get(data.event) || []) callback(synthetic);
    return;
  }
  if (data.type !== "boot" || pyodide) return;
  try {
    send("status", "Python wird geladen…");
    const {loadPyodide} = await import(data.config.pyodide_base + "pyodide.mjs");
    runtimeCanvas = data.canvas;
    self.screen = {width:1920, height:1080, availWidth:1920, availHeight:1080};
    self.devicePixelRatio = 1;
    data.canvas.id = "canvas";
    data.canvas.style = {};
    data.canvas.addEventListener = addEventListenerCompat;
    data.canvas.removeEventListener = removeEventListenerCompat;
    data.canvas.getBoundingClientRect = () => ({left:0, top:0, width:data.canvas.width, height:data.canvas.height});
    // SDL2 needs document-shaped event targets. These contain no host DOM or storage.
    self.document = {
      title:"miniworlds", hidden:false, visibilityState:"visible",
      documentElement:{style:{}}, body:{style:{}, appendChild(){}},
      addEventListener:addEventListenerCompat, removeEventListener:removeEventListenerCompat,
      querySelector:selector => selector === "#canvas" ? data.canvas : null,
      getElementById:id => id === "canvas" ? data.canvas : null,
      createElement:tag => tag === "canvas" ? new OffscreenCanvas(1, 1) : {style:{}}
    };
    pyodide = await loadPyodide({indexURL:data.config.pyodide_base, stdout:text => send("output", text), stderr:text => send("output", text)});
    pyodide.canvas.setCanvas2D(data.canvas);
    send("status", "miniworlds wird vorbereitet…");
    await pyodide.loadPackage(["numpy", "pygame-ce"]);
    pyodide.FS.writeFile("/miniworlds.zip", new Uint8Array(data.wheel));
    await pyodide.runPythonAsync(`
import zipfile, os, sys
with zipfile.ZipFile('/miniworlds.zip') as _wheel:
    _wheel.extractall('/miniworlds')
sys.path.insert(0, '/miniworlds')
os.makedirs('/project', exist_ok=True)
os.chdir('/project')
sys.path.insert(0, '/project')
os.environ['SDL_AUDIODRIVER'] = 'dummy'
`);
    pyodide.FS.writeFile("/project/main.py", data.source);
    if (data.db) pyodide.FS.writeFile("/project/save.db", decode(data.db));
    for (const file of data.files) pyodide.FS.writeFile("/project/" + file.name, new Uint8Array(file.content));
    self.mwAudio = raw => {
      const command = JSON.parse(raw);
      if (command.action === "play" || command.action === "resume") audioStates.set(command.channel, {busy:true});
      if (command.action === "pause" || command.action === "stop") audioStates.set(command.channel, {busy:false});
      postMessage({type:"audio", ...command});
    };
    self.mwAudioState = id => JSON.stringify(audioStates.get(id) || {busy:false});
    await pyodide.runPythonAsync(data.audioCode);
    setInterval(syncDatabase, 2000);
    send("status", "Programm läuft…");
    await pyodide.runPythonAsync("import runpy\nrunpy.run_path('/project/main.py', run_name='__main__')\n");
    syncDatabase(); send("status", "Programm gestartet / Ausführung beendet."); send("done");
  } catch (error) { syncDatabase(); send("error", error.message || error); }
};
