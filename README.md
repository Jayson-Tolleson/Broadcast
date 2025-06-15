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

sudo apt install -y python3 python3-pip xvfb x11vnc wine curl net-tools wmctrl xauth websockify supervisor && sudo pip3 install flask flask-socketio gevent gevent-websocket flask-cors && sudo git clone https://github.com/Jayson-Tolleson/Broadcast.git && cd Broadcast


#### 2. Run the Server

sudo python3 broadcasterwAbleton.py

INDEX IS VIEWABLE @ HTTPS://your-domain.com
BROADCASTER IS VIEWABLE @ https://your-domain.com/broadcast
