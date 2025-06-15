# Broadcast
Broadcast with more and be viewed on a webpage.
# 🎛️ JAY VISION Broadcaster + Wine App Streamer

A hybrid Flask server that supports:
- 🎥 WebRTC-based live broadcasting with viewer count
- 🍷 Running Windows `.exe` apps (like Ableton Live) on Linux via Wine
- 🖥️ Streaming desktop GUI using `x11vnc` and noVNC over Flask
- ⚙️ WebSocket signaling using Flask-SocketIO for live communication
- 🧪 Secure control panel with viewer tracking and control toggles

---

## 🧰 Features

- ✅ WebRTC broadcaster with camera/screen/mic support
- ✅ Viewer count updates with Socket.IO
- ✅ Launch and stop `.exe` via Wine inside virtual X11 (`Xvfb`)
- ✅ Desktop stream embedded in the broadcaster interface via noVNC
- ✅ Two embedded pages + YouTube playlist iframe in homepage
- ✅ PiP, fullscreen, resolution switch, and recording toggle
- ✅ REST API: `/start` and `/stop` WINE + VNC processes

---

## 📁 Project Structure
project/
├── broadcasterwAbletonexe.py # Main Flask server with Flask-SocketIO
└── README.md # This file

## 🚀 Quick Start

### 1. Install System Dependencies (Debian/Ubuntu)
'''
sudo apt install -y python3 python3-pip xvfb x11vnc wine curl net-tools wmctrl xauth websockify supervisor && sudo pip3 install flask flask-socketio gevent gevent-websocket flask-cors && sudo git clone https://github.com/Jayson-Tolleson/Broadcast.git && cd Broadcast
'''

#### 2. Run the Server
'''
sudo python3 broadcasterwAbleton.py
'''

Starts Flask app with WebSocket signaling

Exposes REST endpoints /start and /stop to control WINE + VNC

Hosts iframe-based homepage (/) and /broadcast interface as well as /watch

####📡 Web Interface Overview

https://your-domain.com/
A large, embedded page layout that includes:

https://your-domain.com/watch (in 4K iframe)

Embedded YouTube playlist

https://your-domain.com/broadcast
An advanced broadcaster dashboard:

WebRTC camera + screen sharing

Viewer count updates via Socket.IO

VNC iframe showing desktop streamed by Wine + x11vnc

Buttons to start/stop Wine + VNC processes

🖥️ Running a .exe App via Wine
When hitting /start, the following happens:

Kills any existing Wine or VNC processes

Starts Xvfb as virtual display :99

Adds xauth cookie so Wine can access Xvfb

Runs winecfg (replace with your own .exe)

Starts x11vnc and websockify to expose the GUI at localhost:6080

To embed a Wine app like Ableton Live:
wine_proc = subprocess.Popen(["wine", "Ableton.exe"], env=env)

📺 Access VNC Desktop
The VNC desktop is accessible via:

https://localhost:6080/vnc.html?host=localhost&port=5900
