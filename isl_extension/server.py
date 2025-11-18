from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # This allows the Chrome Extension to talk to this server

@app.route('/process-audio', methods=['POST'])
def process_audio():
    # 1. Check if audio arrived
    if 'audio_chunk' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio_chunk']
    
    # 2. Print the size to prove we received it
    audio_file.seek(0, os.SEEK_END)
    size = audio_file.tell()
    print(f"✅ RECEIVED AUDIO CHUNK: {size} bytes")

    # 3. Pretend we processed it and return a dummy video
    # (This is a sample video URL for testing)
    dummy_video = "https://www.w3schools.com/html/mov_bbb.mp4" 

    return jsonify({
        "video_url": dummy_video,
        "message": "Chunk processed successfully"
    })

if __name__ == '__main__':
    print("🚀 Fake ISL Model Server Running on port 5000...")
    app.run(port=5000, debug=True)