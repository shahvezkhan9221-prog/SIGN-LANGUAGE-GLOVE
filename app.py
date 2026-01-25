import serial
import time
import win32com.client
import threading
from flask import Flask, jsonify
from flask_cors import CORS

# ======================
#  CONFIG
# ======================
PORT = "COM27"      # Change this if your port changes
BAUD = 115200
SPEAK_DELAY = 3     

# Global Data Shared with Website
global_state = {
    "text": "",      # Starts empty
    "sensors": [0,0,0,0,0]
}

def serial_worker():
    global global_state
    
    # 1. Voice Setup
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Rate = 0
        speaker.Volume = 100
    except:
        speaker = None

    # 2. Serial Setup
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.5) # Lower timeout for faster reset
        print(f"✅ Connected to {PORT}")
    except:
        print("❌ Connect Glove first!")
        return

    last_word = ""
    last_time = 0

    while True:
        try:
            # Read from Arduino
            line = ser.readline().decode(errors="ignore").strip()
            now = time.time()

            if line:
                # --- GESTURE DETECTED ---
                global_state["text"] = line
                global_state["sensors"] = [90, 90, 90, 90, 90] # Fake visual effect

                # Speak Logic
                if line != last_word or (now - last_time) > SPEAK_DELAY:
                    print(f"🗣️ Speaking: {line}")
                    if speaker: speaker.Speak(line)
                    last_word = line
                    last_time = now
            else:
                # --- SILENCE (Crucial Fix) ---
                # If no gesture is detected, reset text to empty.
                # This allows the website to detect the NEXT gesture as "new".
                global_state["text"] = "" 
                global_state["sensors"] = [10, 10, 10, 10, 10]

        except:
            pass

# Start Server
app = Flask(__name__)
CORS(app)

@app.route('/data')
def get_data():
    return jsonify(global_state)

if __name__ == '__main__':
    t = threading.Thread(target=serial_worker)
    t.daemon = True
    t.start()
    print("🌐 Server Ready. Open communication.html")
    app.run(host='0.0.0.0', port=5000)