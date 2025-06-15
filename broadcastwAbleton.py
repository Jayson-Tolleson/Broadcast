from gevent import monkey
monkey.patch_all()
import ssl
from flask_socketio import SocketIO, emit
from flask import Flask, Response, request, render_template, jsonify
from flask_cors import CORS
import subprocess
import os

app = Flask(__name__, static_folder='broadcastjs')
app.url_map.strict_slashes = False
CORS(app) 
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins='*')
broadcaster_sid = None
viewers = {}
wine_proc = None
vnc_proc = None
xvfb_proc = None
websockify_proc = None

@app.route('/start', methods=['GET'])
def start_wine():
    global wine_proc, vnc_proc, xvfb_proc, websockify_proc

    # Clean up old processes
    for proc in [wine_proc, vnc_proc, xvfb_proc, websockify_proc]:
        if proc:
            proc.terminate()
            proc.wait()

    env = os.environ.copy()
    env["DISPLAY"] = ":99"

    # Start Xvfb
    xvfb_proc = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x800x24"], env=env)
    time.sleep(1)  # Allow Xvfb to initialize

    # Add Xauth
    subprocess.call("xauth add :99 . $(mcookie)", shell=True, env=env)

    # Start Wine app (can replace "winecfg" with your app.exe)
    wine_proc = subprocess.Popen(["winecfg"], env=env)

    # Start x11vnc
    vnc_proc = subprocess.Popen([
        "x11vnc", "-display", ":99", "-forever", "-nopw", "-shared", "-auth", "guess"
    ], env=env)

    # Start websockify
    websockify_proc = subprocess.Popen([
        "websockify",
        "--web=/usr/share/novnc/",
        "--cert=security/fullchain.pem",
        "--key=security/privkey.pem",
        "6080", "localhost:5900"], env=env)

    return jsonify(status="WINE, Xvfb, VNC, and Websockify started")

@app.route('/stop', methods=['GET'])
def stop_wine():
    global wine_proc, vnc_proc, xvfb_proc, websockify_proc

    for proc in [wine_proc, vnc_proc, xvfb_proc, websockify_proc]:
        if proc:
            proc.terminate()
            proc.wait()

    return jsonify(status="All processes stopped")
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
@socketio.on('disconnect')
def handle_disconnect():
    global broadcaster_sid
    print(f"Client disconnected: {request.sid}")
    if request.sid == broadcaster_sid:
        for viewer_id in viewers:
            emit('disconnectPeer', request.sid, room=viewer_id)
        broadcaster_sid = None
    viewers.pop(request.sid, None)
    broadcast_viewer_count()
@socketio.on('broadcaster')
def handle_broadcaster():
    global broadcaster_sid
    broadcaster_sid = request.sid
    print("Broadcaster connected")
    broadcast_viewer_count()
@socketio.on('watcher')
def handle_watcher():
    viewers[request.sid] = True
    if broadcaster_sid:
        emit('watcher', request.sid, room=broadcaster_sid)
        broadcast_viewer_count()
@socketio.on('offer')
def handle_offer(data):
    emit('offer', {'id': request.sid, 'offer': data['offer']}, room=data['target'])
@socketio.on('answer')
def handle_answer(data):
    emit('answer', {'id': request.sid, 'answer': data['answer']}, room=data['target'])
@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    emit('ice-candidate', {'id': request.sid, 'candidate': data['candidate']}, room=data['target'])
def broadcast_viewer_count():
    if broadcaster_sid:
        socketio.emit('viewerCount', {'count': len(viewers)}, room=broadcaster_sid)
@socketio.on('videoSettingsChanged')
def handle_video_settings_changed(data):
    print("📡 Video settings changed:", data)
    emit('settingsBroadcast', data, broadcast=True)
@app.route('/')
def index():
    indexhtml="""
<html> <style> 
div#container { background: black;
  margin: 24px auto;
        color: white;
        border-radius: 1 em;
        width:3880px;
    height: 2200px;
    overflow:hidden; /* if you don't want a scrollbar, set to hidden */
    overflow-x:hidden; /* hides horizontal scrollbar on newer browsers */
    /* resize and min-height are optional, allows user to resize viewable area */
    -webkit-resize:vertical;
    -moz-resize:vertical;
}
iframe#embed {
    width:3840px; /* set this to approximate width of entire page you're embedding */
    height:2160px; /* determines where the bottom of the page cuts off */
    margin-left:0px; /* clipping left side of page */
    margin-top:0px; /* clipping top of page */
    overflow:hidden;
    /* resize seems to inherit in at least Firefox */
    -webkit-resize:none;
    -moz-resize:none;
    resize:none;
}
div#container1 { background: black;
  margin: 24px auto;
        color: white;
        border-radius: 1 em;
        width:4050px;
    height:3060px;
    overflow:hidden; /* if you don't want a scrollbar, set to hidden */
    overflow-x:hidden; /* hides horizontal scrollbar on newer browsers */
    /* resize and min-height are optional, allows user to resize viewable area */
    -webkit-resize:vertical;
    -moz-resize:vertical;
}
iframe#embed1 {
    width:4032px; /* set this to approximate width of entire page you're embedding */
    height:3040px; /* determines where the bottom of the page cuts off */
    margin-left:0px; /* clipping left side of page */
    margin-top:0px; /* clipping top of page */
    overflow:hidden;
    /* resize seems to inherit in at least Firefox */
    -webkit-resize:none;
    -moz-resize:none;
    resize:none;
}
body {
  margin: 0;
  width: 100%;
  /*border: 1px solid orange;*/ font: normal 2.2em 'trebuchet ms', arial, sans-serif;
  background: #1339de;
  color: #777;
}
</style>
<h1> :::LFTR.biz </h1>
<br><hr>
<body>
    <div id="container1"><iframe id="embed1" scrolling="no" src="https://lftr.biz/watch"></iframe></div>
<br><hr>
    <div id="container1"><iframe id="embed1" scrolling="no" src="https://lftr.biz:8080/fishmap"></iframe></div>
<br><hr>
    <div id="container"><iframe id="embed" scrolling="no" src="https://www.youtube.com/embed/videoseries?list=PLVIftPRSOIthwubkq9WzCSk7B-mqaJ89B" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>
</body> </html>
"""
    return Response(indexhtml)
@app.route('/broadcast')
def broadcast():
    broadcasthtml="""<!DOCTYPE html>    
<html lang="en">
<head>
<meta charset="utf-8" />
<title>JAY VISION Broadcaster</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body {
    background: #111;
    color: #eee;
    font-family: sans-serif;
    margin: 0;
    padding: 0;
    text-align: center;
  }
  video {
    width: 96%;
    max-height: 40vh;
    border-radius: 10px;
    background: black;
  }
  select, button {
    margin: 5px;
    font-size: 16px;
    padding: 10px;
    width: 90%;
    max-width: 400px;
  }
  #viewerCount {
    font-size: 18px;
    margin-top: 10px;
  }
</style>

<script src="https://webrtc.github.io/adapter/adapter-latest.js"></script>
<script src="https://cdn.socket.io/4.8.1/socket.io.min.js"></script>
</head>
<body>

<h2>🎥 JAY VISION Broadcast</h2>
<div id="viewerCount">👁️ Viewers: 0</div>

<video id="videoInput" autoplay playsinline muted></video>

<select id="cameraSelect" title="Select Camera"></select>

<select id="resolutionSelect" title="Select Resolution">
  <option value="1080p">1080p</option>
  <option value="4k">4K</option>
  <option value="6k">6K</option>
</select>

<select id="streamModeSelect" title="Select Stream Mode">
  <option value="camera">🎦 Camera</option>
  <option value="screen+mic">🖥️ Screen Share + Mic</option>
  <option value="screen">🖥️ Screen Only</option>
</select>

<label for="micSelect">🎤 Mic:</label>
<select id="micSelect" title="Select Microphone"></select>

<label for="speakerSelect">🔊 Speaker:</label>
<select id="speakerSelect" title="Select Speaker"></select>

<br/>

<button id="switchCameraBtn">🔄 Switch Camera</button>
<button id="fullscreenBtn">⛶ Fullscreen</button>
<button id="recordBtn">⏺ Start Recording</button>
<button id="pipBtn">📺 PiP Mode</button>

<hr />
  <h2>Ableton Live via WINE</h2>
  <button onclick="start()">Start Ableton</button>
  <button onclick="stop()">Stop Ableton</button>
  <br/><br/>
<iframe src="https://lftr.biz:6080/vnc.html"     style="width:1280px; height:800px; border:none;"></iframe>

  <script>
    async function start() {
      await fetch('https://localhost/start');
      alert('Started WINE + VNC server');
    }
    async function stop() {
      await fetch('https://localhost/stop');
      alert('Stopped WINE + VNC server');
    }
  </script>
</body>
</html>

<script>
'use strict';

const videoInput = document.getElementById('videoInput');
const cameraSelect = document.getElementById('cameraSelect');
const resolutionSelect = document.getElementById('resolutionSelect');
const streamModeSelect = document.getElementById('streamModeSelect');
const micSelect = document.getElementById('micSelect');
const speakerSelect = document.getElementById('speakerSelect');

const viewerCountDisplay = document.getElementById('viewerCount');
const switchCameraBtn = document.getElementById('switchCameraBtn');
const fullscreenBtn = document.getElementById('fullscreenBtn');
const recordBtn = document.getElementById('recordBtn');
const pipBtn = document.getElementById('pipBtn');

let stream = null;
let usingFront = true;
let currentDeviceId = null;
let audioDeviceId = null;

const socket = io();
const peerConnections = {};
const config = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }], sdpSemantics: 'unified-plan' };

let isRecording = false;
let mediaRecorder;
let recordedChunks = [];

function getResConstraints() {
  const val = resolutionSelect.value;
  return val === '4k' ? { width: { ideal: 3840 }, height: { ideal: 2160 } } :
         val === '6k' ? { width: { ideal: 6144 }, height: { ideal: 3160 } } :
                        { width: { ideal: 1920 }, height: { ideal: 1080 } };
}

function stopStream() {
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
}

async function setupStream() {
  videoInput.srcObject = stream;

  for (const id in peerConnections) {
    const pc = peerConnections[id];
    const senders = pc.getSenders();
    stream.getTracks().forEach(track => {
      const sender = senders.find(s => s.track?.kind === track.kind);
      if (sender) sender.replaceTrack(track);
    });
  }
}

async function updateStreamSettingsAuto() {
  stopStream();

  const mode = streamModeSelect.value;
  audioDeviceId = micSelect.value || null;

  try {
    if (mode === 'camera') {
      const constraints = {
        audio: audioDeviceId ? { deviceId: { exact: audioDeviceId } } : true,
        video: {
          facingMode: usingFront ? 'user' : 'environment',
          deviceId: currentDeviceId ? { exact: currentDeviceId } : undefined,
          ...getResConstraints()
        }
      };
      stream = await navigator.mediaDevices.getUserMedia(constraints);
    } else if (mode === 'screen+mic') {
      const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
      const micStream = await navigator.mediaDevices.getUserMedia({ audio: audioDeviceId ? { deviceId: { exact: audioDeviceId } } : true });
      
      // Combine audio tracks from screen + mic
      const audioContext = new AudioContext();
      const destination = audioContext.createMediaStreamDestination();

      if (screenStream.getAudioTracks().length) {
        const screenSource = audioContext.createMediaStreamSource(screenStream);
        screenSource.connect(destination);
      }
      const micSource = audioContext.createMediaStreamSource(micStream);
      micSource.connect(destination);

      const combinedStream = new MediaStream();
      screenStream.getVideoTracks().forEach(track => combinedStream.addTrack(track));
      destination.stream.getAudioTracks().forEach(track => combinedStream.addTrack(track));

      stream = combinedStream;
    } else if (mode === 'screen') {
      stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
    }

    await setupStream();
  } catch (err) {
    console.error('Error accessing media devices:', err);
    alert(`Error accessing media devices:\n${err.name}: ${err.message}`);
    videoInput.style.display = 'none';
    viewerCountDisplay.insertAdjacentHTML('afterend',
      `<p style="color:tomato;">Camera/mic access is required for broadcasting.</p>`);
  }
}

function setVideoSink() {
  if ('setSinkId' in videoInput) {
    videoInput.setSinkId(speakerSelect.value).catch(e => console.warn('setSinkId error:', e));
  }
}

// Event Handlers
switchCameraBtn.onclick = () => {
  usingFront = !usingFront;
  updateStreamSettingsAuto();
};

fullscreenBtn.onclick = () => {
  videoInput.requestFullscreen?.();
};

pipBtn.onclick = async () => {
  try {
    if (document.pictureInPictureElement) {
      await document.exitPictureInPicture();
    } else {
      await videoInput.requestPictureInPicture();
    }
  } catch (e) {
    console.warn('PiP error:', e);
  }
};

recordBtn.onclick = () => {
  if (!stream) return alert("Start streaming first");
  if (!MediaRecorder.isTypeSupported('video/webm')) return alert("Recording not supported in your browser");

  if (!isRecording) {
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm; codecs=vp8,opus' });
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recordedChunks.push(e.data); };
    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: 'video/webm' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'recording.webm';
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);
    };
    mediaRecorder.start();
    recordBtn.textContent = '⏹ Stop Recording';
    isRecording = true;
  } else {
    mediaRecorder.stop();
    recordBtn.textContent = '⏺ Start Recording';
    isRecording = false;
  }
};

// Populate Camera Select
async function getCameras() {
  const devices = await navigator.mediaDevices.enumerateDevices();
  cameraSelect.innerHTML = '';
  devices.filter(d => d.kind === 'videoinput').forEach((device, i) => {
    const option = document.createElement('option');
    option.value = device.deviceId;
    option.text = device.label || `Camera ${i + 1}`;
    cameraSelect.appendChild(option);
  });
  if (cameraSelect.options.length > 0) {
    currentDeviceId = cameraSelect.value = cameraSelect.options[0].value;
  }
}

// Populate Mic and Speaker Selects
async function getAudioDevices() {
  const devices = await navigator.mediaDevices.enumerateDevices();
  micSelect.innerHTML = '';
  speakerSelect.innerHTML = '';
  devices.forEach(device => {
    const option = document.createElement('option');
    option.value = device.deviceId;
    option.text = device.label || `${device.kind} ${device.deviceId.slice(-4)}`;
    if (device.kind === 'audioinput') micSelect.appendChild(option);
    if (device.kind === 'audiooutput') speakerSelect.appendChild(option);
  });
}

micSelect.onchange = () => {
  audioDeviceId = micSelect.value;
  updateStreamSettingsAuto();
};

speakerSelect.onchange = () => {
  setVideoSink();
};

cameraSelect.onchange = () => {
  currentDeviceId = cameraSelect.value;
  updateStreamSettingsAuto();
};

resolutionSelect.onchange = updateStreamSettingsAuto;
streamModeSelect.onchange = updateStreamSettingsAuto;

navigator.mediaDevices.ondevicechange = () => {
  getCameras();
  getAudioDevices();
};

// WebRTC Signaling Handlers
socket.emit('broadcaster');

socket.on('watcher', id => {
  const pc = new RTCPeerConnection(config);
  peerConnections[id] = pc;

  if (stream) {
    stream.getTracks().forEach(track => pc.addTrack(track, stream));
  }

  pc.onicecandidate = event => {
    if (event.candidate) {
      socket.emit('ice-candidate', { target: id, candidate: event.candidate });
    }
  };

  pc.createOffer()
    .then(offer => pc.setLocalDescription(offer))
    .then(() => {
      socket.emit('offer', { target: id, offer: pc.localDescription });
    });
});

socket.on('answer', ({ id, answer }) => {
  const pc = peerConnections[id];
  if (pc) pc.setRemoteDescription(answer);
});

socket.on('ice-candidate', ({ id, candidate }) => {
  const pc = peerConnections[id];
  if (pc) pc.addIceCandidate(candidate);
});

socket.on('disconnectPeer', id => {
  const pc = peerConnections[id];
  if (pc) {
    pc.close();
    delete peerConnections[id];
  }
});

socket.on('viewerCount', data => {
  viewerCountDisplay.textContent = `👁️ Viewers: ${data.count}`;
});

// Initialize
async function init() {
  await getAudioDevices();
  await getCameras();
  await updateStreamSettingsAuto();
}

document.addEventListener('DOMContentLoaded', init);

</script>
</body>
</html>

"""
    return Response(broadcasthtml)

@app.route('/watch')
def watch():
    watchhtml="""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>JAY VISION Viewer</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    html, body {
      margin: 0;
      padding: 0;
      background-color: #000;
      height: 100%;
      overflow: hidden;
      font-family: sans-serif;
    }
    video {
      width: 100%;
      height: auto;
      max-height: 100vh;
      background-color: black;
    }
    #overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      display: none;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      background-color: rgba(0, 0, 0, 0.7);
      color: white;
      font-size: 1.5em;
      z-index: 10;
      text-align: center;
    }
    .spinner-pie {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: conic-gradient(
        #ff3e3e 0% 25%,
        #ffdd00 25% 50%,
        #4ade80 50% 75%,
        #3b82f6 75% 100%
      );
      animation: spin 1.5s linear infinite;
      margin-bottom: 1em;
    }
    @keyframes spin {
      from { transform: rotate(0deg); }
      to   { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div id="overlay">
    <div class="spinner-pie"></div>
    <div>🔄 Reconnecting to stream…</div>
  </div>
  <video id="watcherVideo" autoplay playsinline muted></video>

  <script src="https://cdn.socket.io/4.8.1/socket.io.min.js"></script>
  <script>
const video = document.getElementById('watcherVideo');
const overlay = document.getElementById('overlay');

let pc = null;
let streamSet = false;
let socket = null;
let connected = false;
let failureTimeout = null;

function showOverlay(message = '🔄 Reconnecting to stream…') {
  overlay.style.display = 'flex';
  overlay.querySelector('div:last-child').textContent = message;
}

function hideOverlay() {
  overlay.style.display = 'none';
}

function connectSocket() {
  if (socket) socket.disconnect();

  socket = io({
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 2000,
    reconnectionDelayMax: 5000,
  });

  socket.on('connect', () => {
    connected = true;
    streamSet = false;
    hideOverlay();
    clearTimeout(failureTimeout);
    socket.emit('watcher');
  });

  socket.on('disconnect', () => {
    connected = false;
    showOverlay();
    failureTimeout = setTimeout(() => location.reload(), 120000); // 2 min fallback
  });

  socket.on('offer', ({ id, offer }) => {
    setupPeerConnection(id, offer);

    setTimeout(() => {
      if (!streamSet && connected) {
        console.warn("No stream received, re-requesting...");
        socket.emit('watcher');
      }
    }, 5000);
  });

  socket.on('ice-candidate', ({ candidate }) => {
    if (pc) pc.addIceCandidate(new RTCIceCandidate(candidate)).catch(console.error);
  });

  socket.on('viewerCount', ({ count }) => {
    console.log(`👁 Viewer count: ${count}`);
  });
}

function setupPeerConnection(id, offer) {
  if (pc) {
    pc.close();
    pc = null;
    streamSet = false;
  }

  pc = new RTCPeerConnection({
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
  });

  pc.ontrack = event => {
    if (!streamSet) {
      video.srcObject = event.streams[0];
      streamSet = true;
      hideOverlay();
    }
  };

  pc.onicecandidate = event => {
    if (event.candidate) {
      socket.emit('ice-candidate', { target: id, candidate: event.candidate });
    }
  };

  pc.onconnectionstatechange = () => {
    if (['failed', 'disconnected', 'closed'].includes(pc.connectionState)) {
      console.warn("PeerConnection state:", pc.connectionState);
      showOverlay();
      if (pc) pc.close();
      pc = null;
      streamSet = false;
      if (connected) {
        socket.emit('watcher');
      }
    }
  };

  pc.setRemoteDescription(new RTCSessionDescription(offer))
    .then(() => pc.createAnswer())
    .then(answer => pc.setLocalDescription(answer))
    .then(() => {
      socket.emit('answer', { target: id, answer: pc.localDescription });
    })
    .catch(console.error);
}

// Request fullscreen on first click
document.addEventListener('click', () => {
  if (video.requestFullscreen) {
    video.requestFullscreen();
  } else if (video.webkitRequestFullscreen) {
    video.webkitRequestFullscreen();
  } else if (video.msRequestFullscreen) {
    video.msRequestFullscreen();
  }
}, { once: true });

// Cleanup on unload
window.onbeforeunload = () => {
  if (socket) socket.close();
  if (pc) pc.close();
};

connectSocket();
  </script>
</body>
</html>


"""
    return Response(watchhtml)
if __name__ == "__main__":
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('security/fullchain.pem', 'security/privkey.pem')
    socketio.run(app, debug=True, host='0.0.0.0', ssl_context=context, port=443)
